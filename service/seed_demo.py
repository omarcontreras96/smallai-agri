"""Seed clearly-labelled synthetic farmer offers for the co-op dashboard demo.
Each goes through the real reply path (parser -> band/nowcast -> verdict -> offer log), so the
dashboard and nowcast react exactly as they would to real SMS. phone_hash starts with 'demo-'.

    uv run python -m service.seed_demo          # add demo offers
    uv run python -m service.seed_demo --reset  # remove demo offers only
"""
import random
import sys
from datetime import datetime, timedelta, timezone

from service import db
from service.bands import load_bands
from service.coop import DEMO_PREFIX
from service.reply import respond

# (crop word, market, n farmers, offer as share of the model median, lowball buyer offers)
SCENARIO = [
    ("mahindi", "gulu", 6, 0.80, 2),
    ("mahindi", "mbale", 4, 0.85, 0),    # stale market (17 months): farmer reports refresh it
    ("mahindi", "lira", 3, 0.75, 1),
    ("mahindi", "masaka", 3, 0.90, 0),
    ("maize", "jinja", 2, 0.85, 0),
    ("maharagwe", "mbale", 4, 0.85, 1),
    ("maharagwe", "gulu", 3, 0.80, 0),
    ("beans", "owino", 3, 0.90, 0),
]


def seed(conn, bands, rng=None) -> int:
    rng = rng or random.Random(7)
    n, now = 0, datetime.now(timezone.utc)
    crop_of = {"mahindi": "maize", "maize": "maize", "maharagwe": "beans", "beans": "beans"}
    for word, market, farmers, share, lowballs in SCENARIO:
        band = bands["bands"].get(f"{crop_of[word]}|{market.title()}")
        if not band:
            continue
        p50 = band["h1"]["p50"]
        prices = [p50 * share * rng.uniform(0.9, 1.1) for _ in range(farmers)]
        prices += [band["h1"]["p10"] * rng.uniform(0.6, 0.8) for _ in range(lowballs)]
        for i, ppk in enumerate(prices):
            phone = f"{DEMO_PREFIX}{market}-{i}"
            before = conn.execute("SELECT MAX(id) FROM offers").fetchone()[0] or 0
            respond(conn, phone, f"{word} {int(round(ppk, -1))} kilo {market}", bands)
            ts = (now - timedelta(days=rng.uniform(0, 20))).isoformat(timespec="seconds")
            conn.execute("UPDATE offers SET ts = ? WHERE id > ?", (ts, before))
            n += 1
    conn.commit()
    return n


def reset(conn) -> int:
    cur = conn.execute("DELETE FROM offers WHERE phone_hash LIKE ?", (DEMO_PREFIX + "%",))
    conn.execute("DELETE FROM sessions WHERE phone_hash LIKE ?", (DEMO_PREFIX + "%",))
    conn.commit()
    return cur.rowcount


if __name__ == "__main__":
    conn = db.connect()
    if "--reset" in sys.argv:
        print(f"removed {reset(conn)} demo offers")
    else:
        print(f"seeded {seed(conn, load_bands())} demo offers into {db.db_path()}")
