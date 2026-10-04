"""Rule + fuzzy-lexicon parser for farmer SMS (sw / en / lg / mixed).

parse("mahindi 900 beseni mbale", markets) ->
  {"crop": "maize", "price": 900, "unit": "basin", "qty": None, "unit_kg": None, "market": "Mbale",
   "lang": "sw", "intent": "offer", "confidence": 1.0, "unknown": [], "raw": "..."}

- price: quoted price for one `unit` (UGX). For unit "kg" with qty > 1 ("50 kg 45000") it is the total for qty kg.
- unit_kg: container size if the farmer gave it ("gunia 100kg"), so no clarifying question is needed.
- intent: "offer" (has a price), "query" (crop or market but no price), "unknown".
- unknown: leftover words we could not place (e.g. an unknown market name).

Run `python -m service.parser` to score against service/tests/messages.jsonl.
"""
import json
import re
import sys
from pathlib import Path

from rapidfuzz.distance import OSA

from service.units import CROPS, UNITS

FUZZY_MIN = 0.8      # normalized OSA similarity: one typo (incl. a swap) in a 5+ letter word
FUZZY_MIN_LEN = 4

PER_WORDS = {"per", "kwa", "a", "each", "every", "moja", "buli"}
KG_ALIASES = set(UNITS["kg"][0]) | {"kgs", "kilogram", "kilograms", "kilo"}
CURRENCY = {"shs", "sh", "ush", "ugx", "shillings", "shilingi", "bob", "sente", "ksh"}
STOPWORDS = CURRENCY | PER_WORDS | {
    "ya", "la", "wa", "za", "ni", "na", "the", "for", "at", "in", "of", "to", "is", "my", "i", "me",
    "price", "bei", "bbeeyi", "beeyi", "market", "soko", "sokoni", "katale", "buyer", "mnunuzi", "anataka",
    "wants", "offer", "offered", "offers", "says", "anasema", "amesema", "nimepewa", "nauza", "selling",
    "sell", "kuuza", "leo", "today", "hapa", "here", "how", "much", "ngapi", "what", "gani", "good", "ok",
    "fair", "nini", "je", "is", "it", "this", "hii", "mu", "ku", "e", "nnyo", "giving", "gave", "me",
    "wanataka", "town", "mjini", "dry", "kavu", "white", "new", "mpya", "now", "sasa", "please", "tafadhali",
}

LANG_MARKERS = {
    "sw": {"mahindi", "maharagwe", "maharage", "beseni", "gunia", "magunia", "debe", "kwa", "ya", "la", "bei",
           "ni", "na", "sokoni", "soko", "shilingi", "kilo", "mnunuzi", "anataka", "leo", "ngapi", "gani",
           "nimepewa", "nauza", "kuuza", "moja", "hapa", "sasa", "tafadhali", "wanataka", "mjini", "haragwe",
           "maindi", "besheni", "habari", "asante", "sana", "jambo", "mambo", "sawa", "ndiyo", "hapana"},
    "en": {"maize", "beans", "bean", "corn", "basin", "bag", "bags", "sack", "sacks", "tin", "per", "price",
           "for", "at", "the", "market", "buyer", "offer", "offered", "wants", "today", "selling", "each",
           "how", "much", "what", "is", "please", "town", "kg"},
    "lg": {"kasooli", "ebijanjaalo", "ensawo", "bbeeyi", "beeyi", "sente", "katale", "buli", "mu", "ku", "nnyo"},
}

# Plurals / variants that are not in the shared table but should map to a unit
EXTRA_UNIT_ALIASES = {"bags": "bag", "sacks": "bag", "basins": "basin", "mabeseni": "basin",
                      "tins": "tin", "madebe": "tin", "kgs": "kg", "kilograms": "kg"}


def _normalize(text: str) -> str:
    s = text.lower()
    s = re.sub(r"(?<=\d)[,.](?=\d{3}\b)", "", s)          # 95,000 / 95.000
    s = re.sub(r"(?<=\d)[,.](?=\d{3}\b)", "", s)          # 1,200,000 (second pass)
    s = re.sub(r"(\d+(?:\.\d+)?)\s*k\b", lambda m: str(round(float(m.group(1)) * 1000)), s)  # 95k
    s = re.sub(r"\belfu\s+(\d+)", lambda m: str(int(m.group(1)) * 1000), s)                 # elfu 15
    s = re.sub(r"(\d+)\s+elfu\b", lambda m: str(int(m.group(1)) * 1000), s)                 # 15 elfu
    s = re.sub(r"/=|/-|=/", " ", s)
    s = re.sub(r"/\s*(kg|kgs|kilo)\b", r" per \1", s)      # 900/kg
    s = s.replace("@", " at ")
    s = re.sub(r"(?<=\d)(?=[a-z])|(?<=[a-z])(?=\d)", " ", s)  # 15kg, shs900
    return s


def _vocab() -> tuple[dict, dict]:
    crops = {a: c for c, aliases in CROPS.items() for a in aliases}
    units = {a: u for u, (aliases, _, _) in UNITS.items() for a in aliases}
    units.update(EXTRA_UNIT_ALIASES)
    return crops, units


def _market_aliases(markets: dict) -> dict:
    out = {}
    for name, m in markets.items():
        for a in m.get("aliases", []) + [name.lower()]:
            out[a.lower()] = name
    return out


def _fuzzy(token: str, vocab: dict) -> tuple[str | None, str | None, float]:
    """Best (canonical, alias, similarity) for a token, or Nones if nothing is close enough."""
    if len(token) < FUZZY_MIN_LEN:
        return None, None, 0.0
    best, score = (None, None), 0.0
    for alias, canon in vocab.items():
        if len(alias) < 4:
            continue
        s = OSA.normalized_similarity(token, alias)
        if s > score:
            best, score = (canon, alias), s
    return (*best, score) if score >= FUZZY_MIN else (None, None, 0.0)


def parse(text: str, markets: dict) -> dict:
    crops, units = _vocab()
    mkt = _market_aliases(markets)
    toks = re.findall(r"[a-z]+|\d+(?:\.\d+)?", _normalize(text))
    used = [False] * len(toks)
    found = {}   # field -> (value, score)

    def take(field, value, score, *idx):
        if field not in found:
            found[field] = (value, score)
            for i in idx:
                used[i] = True

    crop_alias = None    # which crop word matched; strongest language signal

    # 1. multi-word markets ("fort portal", "st balikuddembe"), exact then fuzzy
    multi = {a: m for a, m in mkt.items() if " " in a}
    for i in range(len(toks) - 1):
        pair = f"{toks[i]} {toks[i+1]}"
        if pair in mkt or toks[i] + toks[i + 1] in mkt:
            take("market", mkt.get(pair) or mkt[toks[i] + toks[i + 1]], 1.0, i, i + 1)
        elif "market" not in found:
            canon, _, score = _fuzzy(pair, multi)
            if canon:
                take("market", canon, score, i, i + 1)

    # 2. exact lexicon matches
    for i, t in enumerate(toks):
        if used[i] or t.isdigit():
            continue
        if t in crops:
            if "crop" not in found:
                crop_alias = t
            take("crop", crops[t], 1.0, i)
        elif t in units and not (t in KG_ALIASES and "unit" in found):
            take("unit", units[t], 1.0, i)
        elif t in mkt:
            take("market", mkt[t], 1.0, i)

    # 3. fuzzy matches on what is left (typos: "mahindii", "mballe", "besen")
    for i, t in enumerate(toks):
        if used[i] or t.isdigit() or t in STOPWORDS or t in KG_ALIASES:
            continue
        for field, vocab in (("crop", crops), ("market", mkt), ("unit", units)):
            if field in found:
                continue
            canon, alias, score = _fuzzy(t, vocab)
            if canon:
                if field == "crop":
                    crop_alias = alias
                take(field, canon, score, i)
                break

    unit = found.get("unit", (None, 0))[0]
    container = unit in ("basin", "bag", "tin")

    # 4. "per kg" overrides a container ("gunia 95000 ... 950 per kg" is rare; explicit per-kg wins)
    for i in range(len(toks) - 1):
        if toks[i] in PER_WORDS and toks[i + 1] in KG_ALIASES:
            used[i] = used[i + 1] = True
            if not container:
                found["unit"] = ("kg", 1.0)
                unit = "kg"

    # 5. numbers: container size, quantity, price
    nums = [(i, float(t)) for i, t in enumerate(toks) if re.fullmatch(r"\d+(?:\.\d+)?", t)]
    unit_kg = qty = price = None
    for i, n in nums:
        near_kg = (i + 1 < len(toks) and toks[i + 1] in KG_ALIASES) or (i > 0 and toks[i - 1] in KG_ALIASES)
        if near_kg and container and n <= 150 and unit_kg is None:
            unit_kg, used[i] = n, True
        elif near_kg and not container and n <= 150 and len(nums) > 1 and qty is None:
            qty, used[i] = n, True          # "50 kg 45000" -> 45000 for 50 kg
            found.setdefault("unit", ("kg", 1.0))
    for i, n in nums:
        if not used[i] and n >= 50 and price is None:
            price, used[i] = n, True
    for i, n in nums:
        if not used[i] and n < 50 and qty is None:
            qty, used[i] = n, True
    if price is not None:
        found["price"] = (price, 1.0)

    # 6. language by marker words
    words = [t for t in toks if not t.isdigit()]
    scores = {lang: sum(w in m for w in words) + 2 * (crop_alias in m) for lang, m in LANG_MARKERS.items()}
    lang = "en" if not any(scores.values()) else max(("sw", "lg", "en"), key=lambda l: scores[l])

    unknown = [t for i, t in enumerate(toks)
               if not used[i] and not t.isdigit() and t not in STOPWORDS and t not in KG_ALIASES and len(t) > 2]

    # 7. intent + confidence
    intent = "offer" if "price" in found else "query" if ("crop" in found or "market" in found) else "unknown"
    weights = {"offer": {"crop": .35, "price": .35, "market": .3}, "query": {"crop": .5, "market": .5}}
    if intent == "unknown":
        conf = 0.0
    else:
        w = weights[intent]
        conf = sum(wt * found.get(f, (None, 0.0))[1] for f, wt in w.items()) / sum(w.values())
        conf *= 0.9 ** len(unknown)

    val = lambda f: found.get(f, (None, 0))[0]
    p = val("price")
    return {
        "crop": val("crop"), "price": int(p) if p is not None and p == int(p) else p,
        "unit": val("unit"), "qty": int(qty) if qty is not None and qty == int(qty) else qty,
        "unit_kg": unit_kg, "market": val("market"), "lang": lang, "intent": intent,
        "confidence": round(conf, 2), "unknown": unknown, "raw": text,
    }


def evaluate(path: Path, markets: dict) -> dict:
    rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    fields = ["crop", "price", "unit", "market", "qty", "unit_kg", "lang"]
    hit = {f: 0 for f in fields}
    tot = {f: 0 for f in fields}
    exact, failures = 0, []
    for r in rows:
        got = parse(r["text"], markets)
        ok = True
        for f, want in r["expect"].items():
            tot[f] += 1
            if got[f] == want:
                hit[f] += 1
            else:
                ok = False
        exact += ok
        if not ok:
            failures.append((r["text"], {f: (got[f], w) for f, w in r["expect"].items() if got[f] != w}))
    return {"n": len(rows), "exact": exact / len(rows),
            "fields": {f: hit[f] / tot[f] for f in fields if tot[f]}, "failures": failures}


if __name__ == "__main__":
    from service.bands import load_bands
    root = Path(__file__).parent
    res = evaluate(root / "tests" / "messages.jsonl", load_bands()["markets"])
    print(f"n={res['n']}  exact-match={res['exact']:.1%}")
    for f, a in res["fields"].items():
        print(f"  {f:8s} {a:.1%}")
    if "-v" in sys.argv:
        for text, diff in res["failures"]:
            print(f"  FAIL {text!r}: " + ", ".join(f"{f} got={g!r} want={w!r}" for f, (g, w) in diff.items()))
