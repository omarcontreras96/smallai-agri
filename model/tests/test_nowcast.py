import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "model"))

from nowcast import update_band, update_bands  # noqa: E402

NOW = datetime(2026, 10, 4, 3, 0, tzinfo=timezone.utc)
# beans|Mbale, shape of models/bands.json for Oct 2026
PRIOR = {"last_obs_date": "2026-04-15", "last_obs_price": 3460,
         "h1": {"p10": 2790, "p50": 3650, "p90": 4840},
         "h2": {"p10": 2760, "p50": 3640, "p90": 4950},
         "h3": {"p10": 2750, "p50": 3670, "p90": 5040}, "n_reports": 0}


def offer(price, phone, days_ago=1):
    return {"price_per_kg": price, "phone_hash": phone,
            "ts": (NOW - timedelta(days=days_ago)).isoformat()}


def width(q):
    return q["p90"] - q["p10"]


def test_no_offers_keeps_prior():
    out = update_band(PRIOR, [], now=NOW)
    assert out["h1"] == PRIOR["h1"] and out["n_reports"] == 0


def test_three_consistent_offers_shift_and_narrow():
    offers = [offer(3200, "a"), offer(3150, "b"), offer(3300, "c")]
    out = update_band(PRIOR, offers, now=NOW)
    assert out["n_reports"] == 3
    assert 3150 < out["h1"]["p50"] < PRIOR["h1"]["p50"]
    assert width(out["h1"]) < width(PRIOR["h1"])
    for h in ("h1", "h2", "h3"):
        q = out[h]
        assert q["p10"] <= q["p50"] <= q["p90"]
        assert q["p50"] < PRIOR[h]["p50"] and width(q) <= width(PRIOR[h])
    assert out["prior_h1"] == PRIOR["h1"]


def test_one_phone_cannot_move_the_band():
    spam = [offer(2000, "buyer"), offer(2000, "buyer"), offer(2000, "buyer")]
    out = update_band(PRIOR, spam, now=NOW)
    assert out["h1"] == PRIOR["h1"] and out["n_reports"] == 1
    two = [offer(3000, "a"), offer(3000, "b")]
    assert (update_band(PRIOR, two + spam, now=NOW)["h1"]
            == update_band(PRIOR, two + spam[:1], now=NOW)["h1"])


def test_lowball_outlier_is_downweighted():
    offers = [offer(3600, "a"), offer(3700, "b"), offer(1000, "c")]
    robust = update_band(PRIOR, offers, now=NOW)["h1"]["p50"]
    plain = update_band(PRIOR, offers, now=NOW, huber_k=float("inf"))["h1"]["p50"]
    assert robust > plain
    assert robust > 3200  # one lowball does not drag the reference far


def test_old_offers_ignored_and_recent_count_more():
    pair = lambda d: [offer(3000, "a", days_ago=d), offer(3000, "b", days_ago=d)]  # noqa: E731
    old = update_band(PRIOR, pair(120), now=NOW)
    assert old["h1"] == PRIOR["h1"] and old["n_reports"] == 0
    fresh = update_band(PRIOR, pair(1), now=NOW)["h1"]["p50"]
    stale = update_band(PRIOR, pair(60), now=NOW)["h1"]["p50"]
    assert fresh < stale < PRIOR["h1"]["p50"]


def test_update_bands_routes_by_crop_and_market():
    doc = {"bands": {"beans|Mbale": PRIOR, "maize|Mbale": PRIOR}}
    offers = [{**offer(3200, p), "crop": "beans", "market": "Mbale"} for p in "abc"]
    out = update_bands(doc, offers, now=NOW)
    assert out["bands"]["beans|Mbale"]["n_reports"] == 3
    assert out["bands"]["maize|Mbale"]["h1"] == PRIOR["h1"]
