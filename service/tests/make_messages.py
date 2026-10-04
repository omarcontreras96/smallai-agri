"""Builds service/tests/messages.jsonl: hand-written cases + seeded synthetic variants (sw/en/lg/mixed).
Synthetic: templates x crops x units x price formats, with random typos in crop/market words.
Run: uv run python -m service.tests.make_messages
"""
import json
import random
from pathlib import Path

N_TOTAL = 200
OUT = Path(__file__).parent / "messages.jsonl"


def E(text, crop=None, price=None, unit=None, market=None, **kw):
    return {"text": text, "expect": {"crop": crop, "price": price, "unit": unit, "market": market, **kw}}


HAND = [
    # seed set (original)
    E("maize 900 basin mbale", "maize", 900, "basin", "Mbale"),
    E("mahindi 900 beseni mbale", "maize", 900, "basin", "Mbale"),
    E("beans 4000 kg gulu", "beans", 4000, "kg", "Gulu"),
    E("maharagwe shs 3500 kwa kilo lira", "beans", 3500, "kg", "Lira"),
    E("bei ya mahindi mbarara", "maize", None, None, "Mbarara"),
    E("kasooli 95000 gunia owino", "maize", 95000, "bag", "Owino"),
    E("hello", None, None, None, None),
    # formats
    E("Mahindi 1,200/= kwa kilo Mbale", "maize", 1200, "kg", "Mbale", lang="sw"),
    E("MAIZE 95K BAG MASAKA", "maize", 95000, "bag", "Masaka", lang="en"),
    E("beans 4200/kg soroti", "beans", 4200, "kg", "Soroti", lang="en"),
    E("maharagwe elfu 60 debe tororo", "beans", 60000, "tin", "Tororo", lang="sw"),
    E("mahindi shs.950 per kg jinja", "maize", 950, "kg", "Jinja"),
    E("maize ugx 1100 @ kg hoima", "maize", 1100, "kg", "Hoima", lang="en"),
    E("mahindi 15000/- beseni iganga", "maize", 15000, "basin", "Iganga", lang="sw"),
    E("kasooli 1,000 buli kilo mukono", "maize", 1000, "kg", "Mukono"),
    # container size given -> no clarifying question
    E("mahindi gunia 100kg 95000 lira", "maize", 95000, "bag", "Lira", unit_kg=100),
    E("maize basin 20kg 18000 gulu", "maize", 18000, "basin", "Gulu", unit_kg=20),
    E("beseni ya kilo 15 mahindi 14000 mbale", "maize", 14000, "basin", "Mbale", unit_kg=15),
    E("beans sack of 90 kg 330000 arua", "beans", 330000, "bag", "Arua", unit_kg=90),
    # quantities
    E("2 bags maize 90000 each masindi", "maize", 90000, "bag", "Masindi", qty=2),
    E("magunia 3 mahindi 92000 kwa gunia lira", "maize", 92000, "bag", "Lira", qty=3),
    E("50 kg beans 190000 kasese", "beans", 190000, "kg", "Kasese", qty=50),
    # multi-word / alias markets
    E("maize 1000 kg fort portal", "maize", 1000, "kg", "Fort Portal"),
    E("beans 4500 per kg fortportal", "beans", 4500, "kg", "Fort Portal"),
    E("mahindi 1100 kilo kampala", "maize", 1100, "kg", "Owino"),
    # typos
    E("mahindii 900 besen mballe", "maize", 900, "basin", "Mbale"),
    E("maharagwee 4000 kilo gullu", "beans", 4000, "kg", "Gulu"),
    E("maze 1000 kg masakka", "maize", 1000, "kg", "Masaka"),
    # word order / extra words
    E("mnunuzi anataka kunipa 850 kwa kilo ya mahindi hapa mbale", "maize", 850, "kg", "Mbale", lang="sw"),
    E("buyer offered me 3800 per kg for my beans in gulu today", "beans", 3800, "kg", "Gulu", lang="en"),
    E("Gulu: maize 1000/kg", "maize", 1000, "kg", "Gulu"),
    # unknown market / crop / noise
    E("mahindi 900 kilo kitgum", "maize", 900, "kg", None),
    E("maize 1000 kg kabale", "maize", 1000, "kg", None),
    E("coffee 7000 kg mbale", None, 7000, "kg", "Mbale"),
    E("habari", None, None, None, None),
    E("asante sana", None, None, None, None),
    E("price of beans in lira", "beans", None, None, "Lira", lang="en"),
]

CROP_WORDS = {"sw": {"maize": ["mahindi"], "beans": ["maharagwe", "maharage"]},
              "en": {"maize": ["maize", "corn"], "beans": ["beans"]},
              "lg": {"maize": ["kasooli"], "beans": ["ebijanjaalo"]}}
UNIT_WORDS = {"sw": {"kg": ["kilo", "kg"], "basin": ["beseni"], "bag": ["gunia"], "tin": ["debe"]},
              "en": {"kg": ["kg"], "basin": ["basin"], "bag": ["bag", "sack"], "tin": ["tin"]},
              "lg": {"kg": ["kilo"], "basin": ["beseni"], "bag": ["ensawo"], "tin": ["debe"]}}
KG_PER = {"kg": 1, "basin": 15, "bag": 100, "tin": 20}
PER_KG_PRICE = {"maize": (700, 1500), "beans": (2800, 5200)}
TEMPLATES = {
    "sw": ["{crop} {price} {unit} {market}", "{crop} {price} kwa {unit} {market}",
           "bei ya {crop} {market} ni {price} kwa {unit}", "nimepewa {price} kwa {unit} ya {crop} {market}",
           "{market} {crop} {price} {unit}", "mnunuzi anataka {crop} {price} kwa {unit} soko la {market}"],
    "en": ["{crop} {price} {unit} {market}", "{crop} {price} per {unit} {market}",
           "buyer offers {price} per {unit} for {crop} at {market}", "{market} {crop} {price} {unit}",
           "{crop} {unit} {price} at {market} market"],
    "lg": ["{crop} {price} {unit} {market}", "{crop} {price} buli {unit} mu {market}"],
}
QUERY_TEMPLATES = {"sw": ["bei ya {crop} {market}", "bei ya {crop} sokoni {market} ni ngapi"],
                   "en": ["price of {crop} in {market}", "{crop} price {market}"]}


def fmt_price(p, rng):
    style = rng.choice(["plain", "plain", "eq", "shs", "comma", "dash", "k"])
    if style == "eq": return f"{p}/="
    if style == "shs": return f"{rng.choice(['shs', 'ugx', 'shs.'])} {p}"
    if style == "comma" and p >= 1000: return f"{p:,}"
    if style == "dash": return f"{p}/-"
    if style == "k" and p >= 10000 and p % 1000 == 0: return f"{p // 1000}k"
    return str(p)


def typo(word, rng):
    if len(word) < 6 or rng.random() > 0.25:
        return word
    i = rng.randrange(1, len(word) - 1)
    op = rng.choice(["drop", "dup", "swap"])
    if op == "drop": return word[:i] + word[i + 1:]
    if op == "dup": return word[:i] + word[i] + word[i:]
    return word[:i] + word[i + 1] + word[i] + word[i + 2:]


def synth(rng, markets):
    lang = rng.choices(["sw", "en", "lg"], weights=[5, 4, 1])[0]
    crop = rng.choice(["maize", "beans"])
    market = rng.choice(markets)
    cw = typo(rng.choice(CROP_WORDS[lang][crop]), rng)
    mw = typo(market.lower() if rng.random() < 0.7 else market, rng)
    if lang in QUERY_TEMPLATES and rng.random() < 0.1:
        t = rng.choice(QUERY_TEMPLATES[lang])
        return E(t.format(crop=cw, market=mw), crop, None, None, market, lang=lang)
    unit = rng.choices(["kg", "basin", "bag", "tin"], weights=[4, 3, 3, 1])[0]
    lo, hi = PER_KG_PRICE[crop]
    step = 50 if unit == "kg" else 500 if unit in ("basin", "tin") else 1000
    price = round(rng.uniform(lo, hi) * KG_PER[unit] / step) * step
    uw = rng.choice(UNIT_WORDS[lang][unit])
    text = rng.choice(TEMPLATES[lang]).format(crop=cw, price=fmt_price(price, rng), unit=uw, market=mw)
    if rng.random() < 0.15:
        text = text.upper()
    return E(text, crop, price, unit, market, lang=lang)


def main():
    from service.bands import load_bands
    markets = sorted(load_bands()["markets"])
    rng = random.Random(42)
    rows, seen = list(HAND), {r["text"] for r in HAND}
    while len(rows) < N_TOTAL:
        r = synth(rng, markets)
        if r["text"] not in seen:
            seen.add(r["text"])
            rows.append(r)
    OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    print(f"wrote {len(rows)} messages ({len(HAND)} hand-written) to {OUT}")


if __name__ == "__main__":
    main()
