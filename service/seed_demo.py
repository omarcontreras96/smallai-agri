"""Seed clearly-labelled synthetic farmer offers for the co-op dashboard demo.
Each goes through the real reply path (parser -> band/nowcast -> verdict -> offer log), so the
dashboard and nowcast react exactly as they would to real SMS. phone_hash starts with 'demo-'.

    uv run python -m service.seed_demo                       # add the 32-offer scenario
    uv run python -m service.seed_demo --n 200 --seconds 20  # stream ~200 offers over 20 s (filming)
    uv run python -m service.seed_demo --reset               # remove demo offers only

For filming, open /coop?refresh=2 so the dashboard reloads every 2 s while offers stream in.
"""
import argparse
import random
import time
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


# Markets with more traffic in the random stream (others get weight 1)
BUSY = {"Gulu": 4, "Mbale": 4, "Lira": 3, "Masaka": 3, "Jinja": 3, "Arua": 3, "Owino": 3, "Mbarara": 2}
WORDS = {"maize": ["mahindi", "maize", "kasooli"], "beans": ["maharagwe", "beans"]}


def stream(conn, bands, n: int, seconds: float = 0.0, rng=None) -> int:
    """n synthetic offers spread over markets and both crops, mostly farm-gate-like (~85% of the
    model median), ~8% lowball buyers below P10, one phone per offer, timestamps over the last
    3 weeks. With seconds > 0 they arrive gradually so a refreshing dashboard visibly fills up."""
    rng = rng or random.Random(11)
    keys = list(bands["bands"])
    weights = [BUSY.get(k.split("|")[1], 1) for k in keys]
    now, logged = datetime.now(timezone.utc), 0
    for i in range(n):
        key = rng.choices(keys, weights)[0]
        crop, market = key.split("|")
        h = bands["bands"][key]["h1"]
        if rng.random() < 0.08:
            ppk = h["p10"] * rng.uniform(0.6, 0.85)
        else:
            ppk = h["p50"] * min(max(rng.gauss(0.85, 0.12), 0.55), 1.3)
        before = conn.execute("SELECT MAX(id) FROM offers").fetchone()[0] or 0
        respond(conn, f"{DEMO_PREFIX}r{i}", f"{rng.choice(WORDS[crop])} {int(round(ppk, -1))} kilo {market.lower()}", bands)
        ts = (now - timedelta(days=rng.uniform(0, 21))).isoformat(timespec="seconds")
        logged += conn.execute("UPDATE offers SET ts = ? WHERE id > ?", (ts, before)).rowcount
        conn.commit()
        if seconds:
            time.sleep(seconds / n)
    return logged


def reset(conn) -> int:
    cur = conn.execute("DELETE FROM offers WHERE phone_hash LIKE ?", (DEMO_PREFIX + "%",))
    conn.execute("DELETE FROM sessions WHERE phone_hash LIKE ?", (DEMO_PREFIX + "%",))
    conn.commit()
    return cur.rowcount


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--reset", action="store_true", help="remove demo offers only")
    ap.add_argument("--n", type=int, help="stream this many random offers instead of the fixed scenario")
    ap.add_argument("--seconds", type=float, default=0.0, help="spread the stream over this many seconds")
    args = ap.parse_args()
    conn = db.connect()
    if args.reset:
        print(f"removed {reset(conn)} demo offers")
    elif args.n:
        print(f"streamed {stream(conn, load_bands(), args.n, args.seconds)} demo offers into {db.db_path()}")
    else:
        print(f"seeded {seed(conn, load_bands())} demo offers into {db.db_path()}")
