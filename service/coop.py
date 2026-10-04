"""Co-op dashboard data: logged offers, model band vs nowcast band per market, offers below P10.
Rendered server-side (templates/coop.html, inline SVG) so it works offline."""
import math

from service.reply import current_band

DEMO_PREFIX = "demo-"   # phone_hash of synthetic offers from seed_demo.py


def _nice_ticks(lo: float, hi: float, n: int = 6) -> list[int]:
    raw = (hi - lo) / n
    mag = 10 ** math.floor(math.log10(raw))
    step = next(s * mag for s in (1, 2, 2.5, 5, 10) if s * mag >= raw)
    start = math.ceil(lo / step) * step
    return [int(start + i * step) for i in range(int((hi - start) // step) + 1)]


def view(conn, bands: dict, crop: str) -> dict:
    offers = [dict(r) for r in conn.execute(
        "SELECT * FROM offers WHERE price_per_kg IS NOT NULL ORDER BY id DESC")]
    for o in offers:
        o["below_p10"] = o["band_p10"] is not None and o["price_per_kg"] < o["band_p10"]
        o["demo"] = o["phone_hash"].startswith(DEMO_PREFIX)

    rows = []
    for key, base in bands["bands"].items():
        c, market = key.split("|")
        if c != crop:
            continue
        mine = [o for o in offers if o["crop"] == crop and o["market"] == market]
        band = current_band(conn, crop, market, bands) if mine else base
        rows.append({
            "market": market, "prior": base["h1"],
            "now": band["h1"] if "nowcast" in band else None,
            "gap": base.get("gap_months_h1") or 0, "n_phones": band.get("n_reports", 0),
            "offers": mine, "flagged": sum(o["below_p10"] for o in mine),
        })
    rows.sort(key=lambda r: (-len(r["offers"]), r["market"]))

    xs = [v for r in rows for v in (r["prior"]["p10"], r["prior"]["p90"])]
    xs += [o["price_per_kg"] for r in rows for o in r["offers"]]
    lo, hi = (min(xs), max(xs)) if xs else (0, 1)
    pad = (hi - lo) * 0.04
    lo, hi = max(0, lo - pad), hi + pad

    crop_offers = [o for o in offers if o["crop"] == crop]
    return {
        "crop": crop, "rows": rows, "x_lo": lo, "x_hi": hi, "ticks": _nice_ticks(lo, hi),
        "recent": offers[:50],
        "stats": {
            "offers": len(crop_offers),
            "phones": len({o["phone_hash"] for o in crop_offers}),
            "markets": sum(1 for r in rows if r["offers"]),
            "flagged": sum(o["below_p10"] for o in crop_offers),
            "nowcast": sum(1 for r in rows if r["now"]),
        },
        "any_demo": any(o["demo"] for o in offers),
        "reference_month": bands.get("reference_month"),
    }
