"""Reply composer: clarifying questions, verdict against the band, fail-safes.

Replies come only from the fixed sw/en templates below; nothing is generated freely.
Flow per message: resume a pending question (per phone, SQLite) or parse fresh ->
missing unit / container size -> ask once -> band for crop|market, refreshed by
farmer reports via model.nowcast -> fail-safes -> verdict + suggested ask + trend.
"""
import math
import re
from datetime import datetime, timedelta, timezone

from model.nowcast import MAX_AGE_DAYS, update_band
from service import db
from service.parser import parse
from service.units import UNITS, alias_to_unit, kg_for

MIN_CONFIDENCE = 0.6
MAX_REL_WIDTH = 1.0     # (p90 - p10) / p50; wider than the median itself -> not sure
MAX_GAP_MONTHS = 12     # last market observation older than this -> not sure, unless farmer reports refreshed it
IMPLAUSIBLE = 4.0       # per-kg price 4x outside p10..p90 -> probably the wrong unit, do not judge
TREND_PCT = 0.05        # h3 vs h1 median change counted as rising / falling
STATE_TTL = timedelta(hours=1)
Z25 = 0.6744897501960817 / 1.2815515655446004   # P25 distance as a share of the P10 distance (normal, log scale)

UNIT_CHOICES = {"1": "kg", "2": "basin", "3": "bag", "4": "tin"}

T = {
    "sw": {
        "crop": {"maize": "mahindi", "beans": "maharagwe"},
        "unit": {"kg": "kilo", "basin": "beseni", "bag": "gunia", "tin": "debe"},
        "help": "Tuma: zao, bei, kipimo, soko. Mfano: mahindi 1000 kilo mbale",
        "ask_unit": "Bei {price} ni kwa kipimo gani? Jibu 1=kilo 2=beseni 3=gunia 4=debe",
        "ask_size": "{Unit} ni kilo ngapi? Jibu {opts}",
        "ask_market": "Soko gani? Mfano: {crop} {price} kilo mbale",
        "unsure": "Sijui kwa uhakika: {reason}. Uliza chama au afisa kilimo.",
        "r_crop": "tuna bei za mahindi na maharagwe tu",
        "r_market": "soko '{word}' halipo kwenye orodha yetu",
        "r_conf": "sikuelewa ujumbe vizuri",
        "r_no_band": "hatuna bei ya {crop} kwa soko la {market}",
        "r_stale": "bei za mwisho za {market} ni za miezi {gap} iliyopita",
        "r_wide": "bei za {crop} {market} zinabadilika sana",
        "r_implausible": "{ppk}/kg si bei ya kawaida, hakikisha kipimo",
        "offer": "{Crop} {market}: {offer}.",
        "band": "Bei ya soko mwezi huu: {p25}-{p75}/kg.",
        "LOW": "Ofa ni CHINI (~{pct}% chini ya wastani). Omba {ask} kwa {unit}.",
        "FAIR": "Ofa ni SAWA. Unaweza kuomba {ask} kwa {unit}.",
        "FAIR_high": "Ofa ni SAWA.",
        "GOOD": "Ofa ni NZURI.",
        "up": "Miezi 2 ijayo: bei inapanda.",
        "down": "Miezi 2 ijayo: bei inashuka.",
        "flat": "Miezi 2 ijayo: bei haibadiliki sana.",
        "caveat": "Bei ya rejareja mjini, si ya shambani. Uamuzi ni wako.",
        "query": "{Crop} {market} mwezi huu: {p25}-{p75}/kg (wastani {p50}).",
        "query_caveat": "Bei ya rejareja mjini.",
    },
    "en": {
        "crop": {"maize": "maize", "beans": "beans"},
        "unit": {"kg": "kg", "basin": "basin", "bag": "bag", "tin": "tin"},
        "help": "Send: crop, price, unit, market. Example: maize 1000 kg mbale",
        "ask_unit": "Is {price} per which unit? Reply 1=kg 2=basin 3=bag 4=tin",
        "ask_size": "How many kg is the {unit}? Reply {opts}",
        "ask_market": "Which market? Example: {crop} {price} kg mbale",
        "unsure": "Not sure: {reason}. Ask your co-op or extension officer.",
        "r_crop": "we only have maize and beans prices",
        "r_market": "market '{word}' is not on our list",
        "r_conf": "I did not fully understand the message",
        "r_no_band": "no {crop} prices for {market}",
        "r_stale": "last {market} market data is {gap} months old",
        "r_wide": "{crop} prices in {market} vary too much",
        "r_implausible": "{ppk}/kg is unusual, check the unit",
        "offer": "{Crop} {market}: {offer}.",
        "band": "Market price this month: {p25}-{p75}/kg.",
        "LOW": "Offer is LOW (~{pct}% below average). Ask {ask} per {unit}.",
        "FAIR": "Offer is FAIR. You can ask {ask} per {unit}.",
        "FAIR_high": "Offer is FAIR.",
        "GOOD": "Offer is GOOD.",
        "up": "Next 2 months: prices rising.",
        "down": "Next 2 months: prices falling.",
        "flat": "Next 2 months: prices steady.",
        "caveat": "Town retail price, not farm-gate. You decide.",
        "query": "{Crop} {market} this month: {p25}-{p75}/kg (average {p50}).",
        "query_caveat": "Town retail price.",
    },
}


def _n(x: float, step: int = 10) -> str:
    return f"{int(round(x / step) * step):,}"


def quartiles(h: dict) -> tuple[float, float, float]:
    """P25, P50, P75 from P10/P50/P90, assuming a (split) normal on log price."""
    mu = math.log(h["p50"])
    lo, hi = mu - math.log(h["p10"]), math.log(h["p90"]) - mu
    return math.exp(mu - Z25 * lo), h["p50"], math.exp(mu + Z25 * hi)


def verdict(ppk: float, h: dict) -> str:
    p25, _, p75 = quartiles(h)
    return "LOW" if ppk < p25 else "GOOD" if ppk > p75 else "FAIR"


def current_band(conn, crop: str, market: str, bands: dict) -> dict | None:
    """Model band refreshed with farmer reports from the offer log (Bayesian nowcast)."""
    band = bands["bands"].get(f"{crop}|{market}")
    if band is None:
        return None
    cutoff = (datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)).isoformat(timespec="seconds")
    rows = conn.execute(
        "SELECT ts, phone_hash, price_per_kg FROM offers "
        "WHERE crop = ? AND market = ? AND price_per_kg IS NOT NULL AND ts >= ?",
        (crop, market, cutoff),
    ).fetchall()
    return update_band(band, [dict(r) for r in rows])


def _failsafe(band: dict, L: dict, crop: str, market: str) -> str | None:
    gap = band.get("gap_months_h1") or 0
    if gap > MAX_GAP_MONTHS and "nowcast" not in band:
        return L["r_stale"].format(market=market, gap=gap)
    h = band["h1"]
    if (h["p90"] - h["p10"]) / h["p50"] > MAX_REL_WIDTH:
        return L["r_wide"].format(crop=L["crop"][crop], market=market)
    return None


def _trend(band: dict, L: dict) -> str:
    change = band["h3"]["p50"] / band["h1"]["p50"] - 1
    return L["up"] if change > TREND_PCT else L["down"] if change < -TREND_PCT else L["flat"]


def _resume(state: dict, text: str) -> dict | None:
    """Apply an answer to a pending question; None if the text is not an answer."""
    p, t = dict(state["parsed"]), text.strip().lower()
    if state["ask"] == "unit":
        unit = UNIT_CHOICES.get(t) or alias_to_unit(t)
        if not unit:
            return None
        p["unit"] = unit
        return p
    options = UNITS[p["unit"]][2] or {}
    m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*(kg|kilo)?", t)
    if not m:
        return None
    if m.group(1) in options and not m.group(2):
        p["unit_kg"] = options[m.group(1)]
    elif 5 <= float(m.group(1)) <= 150:
        p["unit_kg"] = float(m.group(1))
    else:
        return None
    return p


def respond(conn, phone_hash: str, text: str, bands: dict) -> str:
    state = db.get_state(conn, phone_hash)
    p = None
    if state and datetime.fromisoformat(state["ts"]) > datetime.now(timezone.utc) - STATE_TTL:
        p = _resume(state, text)
    if state:
        db.set_state(conn, phone_hash, None)
    if p is None:
        p = parse(text, bands["markets"])
    return answer(conn, phone_hash, p, bands)


def _ask(conn, phone_hash: str, p: dict, ask: str, msg: str) -> str:
    db.set_state(conn, phone_hash, {"parsed": p, "ask": ask, "ts": db.now()})
    return msg


def answer(conn, phone_hash: str, p: dict, bands: dict) -> str:
    L = T["en" if p["lang"] == "en" else "sw"]
    crop, market, price = p["crop"], p["market"], p["price"]
    unsure = lambda reason: L["unsure"].format(reason=reason)

    if p["intent"] == "unknown":
        return L["help"]
    if crop is None:
        return unsure(L["r_crop"])
    if market is None:
        if p["unknown"]:
            return unsure(L["r_market"].format(word=p["unknown"][-1]))
        return L["ask_market"].format(crop=L["crop"][crop], price=price or 1000)
    if p["confidence"] < MIN_CONFIDENCE:
        return unsure(L["r_conf"]) + "\n" + L["help"]

    band = current_band(conn, crop, market, bands)
    if band is None:
        return unsure(L["r_no_band"].format(crop=L["crop"][crop], market=market))
    h = band["h1"]
    p25, p50, p75 = quartiles(h)
    crop_name = L["crop"][crop]

    if p["intent"] == "query":
        if reason := _failsafe(band, L, crop, market):
            return unsure(reason)
        return "\n".join([
            L["query"].format(Crop=crop_name.capitalize(), market=market, p25=_n(p25), p75=_n(p75), p50=_n(p50)),
            _trend(band, L), L["query_caveat"]])

    # offer: make sure we know how many kg the price is for
    unit = p["unit"]
    if unit is None:
        return _ask(conn, phone_hash, p, "unit", L["ask_unit"].format(price=f"{price:,}"))
    kg = p.get("unit_kg") or kg_for(unit)
    if kg is None:
        opts = " ".join(f"{k}={v:g}kg" for k, v in UNITS[unit][2].items())
        u = L["unit"][unit]
        return _ask(conn, phone_hash, p, "size", L["ask_size"].format(Unit=u.capitalize(), unit=u, opts=opts))
    kg_total = unit == "kg" and (p.get("qty") or 0) > 1     # "50 kg 190000": price is for qty kg
    ppk = price / p["qty"] if kg_total else price / kg

    if ppk < h["p10"] / IMPLAUSIBLE or ppk > h["p90"] * IMPLAUSIBLE:
        return unsure(L["r_implausible"].format(ppk=_n(ppk)))

    reason = _failsafe(band, L, crop, market)
    v = "UNSURE" if reason else verdict(ppk, h)
    db.log_offer(conn, phone_hash, {
        "crop": crop, "market": market, "price_per_kg": round(ppk, 1), "unit": unit, "raw_text": p["raw"],
        "verdict": v, "band_p10": h["p10"], "band_p50": h["p50"], "band_p90": h["p90"]})
    if reason:
        return unsure(reason)

    u = L["unit"][unit]
    if kg_total:
        offer = f"{price:,}/{p['qty']:g}kg = {_n(ppk)}/kg"
    elif kg != 1:
        offer = f"{price:,}/{u} ({kg:g}kg) = {_n(ppk)}/kg"
    else:
        offer = f"{_n(ppk)}/kg"
    ask = _n(p50 * kg, 50 if kg == 1 else 500 if kg < 50 else 1000)
    if v == "LOW":
        line = L["LOW"].format(pct=round((1 - ppk / p50) * 100), ask=ask, unit=u)
    elif v == "FAIR":
        line = L["FAIR"].format(ask=ask, unit=u) if ppk < p50 else L["FAIR_high"]
    else:
        line = L["GOOD"]
    return "\n".join([
        L["offer"].format(Crop=crop_name.capitalize(), market=market, offer=offer),
        L["band"].format(p25=_n(p25), p75=_n(p75)),
        line, _trend(band, L), L["caveat"]])
