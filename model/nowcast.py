"""Nowcaster: update a market's price band from reported offers.

Bayesian normal-normal update on log price. Prior = the model band for the
current month (h1): centre log(p50), spread from the p10..p90 width. Each report
is a noisy reading of this month's market price with log-scale noise OBS_SIGMA.

Offers come from the people the tool is meant to protect against, so a few
lowball offers must not drag the reference down:
- one vote per phone: a phone's offers are averaged and count at most once,
  and nothing moves until MIN_PHONES different phones have reported;
- robust (Huber) weight: reports more than HUBER_K predictive SDs from the
  prior centre are down-weighted;
- time decay with TAU_DAYS; reports older than MAX_AGE_DAYS are ignored.

The shift learned for h1 is carried to h2/h3 (random-walk persistence), and
their variance shrinks by the same amount of information.

Known gap: offers are farm-gate, the prior is town retail. We treat them on the
same scale; robust weighting limits the drag, it does not remove the bias.
"""

import math
from datetime import datetime, timezone

Z90 = 1.2815515655446004  # standard normal 90th percentile
OBS_SIGMA = 0.30          # log-scale noise of one offer (assumption: quality, bargaining)
HUBER_K = 1.0             # full weight within ~1 predictive SD (~ +-37% at a 6-month prior)
MIN_PHONES = 2
TAU_DAYS = 30.0
MAX_AGE_DAYS = 90.0


def _to_dt(ts) -> datetime:
    if isinstance(ts, datetime):
        dt = ts
    elif isinstance(ts, (int, float)):
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    else:
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _spread(q: dict) -> tuple[float, float, float]:
    """(mu, lower sigma, upper sigma) in log space from a p10/p50/p90 dict."""
    mu = math.log(q["p50"])
    return mu, (mu - math.log(q["p10"])) / Z90, (math.log(q["p90"]) - mu) / Z90


def _band(mu: float, s_lo: float, s_hi: float) -> dict:
    r10 = lambda x: int(round(x / 10.0) * 10)  # noqa: E731
    return {"p10": r10(math.exp(mu - Z90 * s_lo)), "p50": r10(math.exp(mu)),
            "p90": r10(math.exp(mu + Z90 * s_hi))}


def _reports(offers: list[dict], now: datetime) -> list[tuple[float, float]]:
    """Collapse offers to one (log price, time weight) per phone."""
    by_phone: dict[str, list[tuple[float, float]]] = {}
    for i, o in enumerate(offers):
        price = o.get("price_per_kg")
        if not price or price <= 0:
            continue
        age = (now - _to_dt(o["ts"])).total_seconds() / 86400 if o.get("ts") else 0.0
        if age > MAX_AGE_DAYS:
            continue
        w = math.exp(-max(age, 0.0) / TAU_DAYS)
        by_phone.setdefault(o.get("phone_hash") or f"_anon{i}", []).append((math.log(price), w))
    out = []
    for rs in by_phone.values():
        wsum = sum(w for _, w in rs)
        out.append((sum(y * w for y, w in rs) / wsum, max(w for _, w in rs)))
    return out


def update_band(band: dict, offers: list[dict], now: datetime | None = None,
                obs_sigma: float = OBS_SIGMA, huber_k: float = HUBER_K) -> dict:
    """Return a copy of a bands.json entry with h1..h3 updated from offers.

    offers: rows of the offer log; uses price_per_kg, and ts / phone_hash if present.
    """
    now = _to_dt(now) if now else datetime.now(timezone.utc)
    reports = _reports(offers, now)
    out = {**band, "n_reports": len(reports)}
    if len(reports) < MIN_PHONES:
        return out

    mu0, lo0, hi0 = _spread(band["h1"])
    s0 = (lo0 + hi0) / 2
    s_pred = math.sqrt(s0**2 + obs_sigma**2)
    prec, num = 1 / s0**2, mu0 / s0**2
    eff_n = 0.0
    for y, w in reports:
        z = abs(y - mu0) / s_pred
        w *= 1.0 if z <= huber_k else huber_k / z
        prec += w / obs_sigma**2
        num += w * y / obs_sigma**2
        eff_n += w
    mu1, s1 = num / prec, 1 / math.sqrt(prec)
    shift, gained = mu1 - mu0, s0**2 - s1**2

    out["h1"] = _band(mu1, lo0 * s1 / s0, hi0 * s1 / s0)
    for h in ("h2", "h3"):
        mu, lo, hi = _spread(band[h])
        s = (lo + hi) / 2
        s_new = math.sqrt(max(s**2 - gained, s1**2))
        out[h] = _band(mu + shift, lo * s_new / s, hi * s_new / s)
    out["prior_h1"] = band["h1"]
    out["nowcast"] = {"shift_log": round(shift, 4), "effective_n": round(eff_n, 2),
                      "updated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ")}
    return out


def update_bands(doc: dict, offers: list[dict], now: datetime | None = None) -> dict:
    """Apply update_band to every band in a bands.json document; offers carry crop+market."""
    by_key: dict[str, list[dict]] = {}
    for o in offers:
        by_key.setdefault(f"{o.get('crop')}|{o.get('market')}", []).append(o)
    bands = {k: update_band(b, by_key.get(k, []), now) for k, b in doc["bands"].items()}
    return {**doc, "bands": bands}
