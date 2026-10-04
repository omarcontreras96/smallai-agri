"""Guards the models/bands.json contract (docs/BUILD_PLAN.md) and prepare.py rules."""

import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "model"))

from prepare import tidy  # noqa: E402


def test_bands_contract():
    b = json.loads((ROOT / "models/bands.json").read_text())
    assert (b["currency"], b["unit"], b["price_type"]) == ("UGX", "KG", "retail")
    assert b["bands"]
    for key, band in b["bands"].items():
        crop, market = key.split("|")
        assert crop in {"maize", "beans"}
        assert market in b["markets"]
        assert market.lower() in b["markets"][market]["aliases"]
        date.fromisoformat(band["last_obs_date"])
        assert band["last_obs_price"] > 0 and band["n_reports"] == 0
        for h in ("h1", "h2", "h3"):
            q = band[h]
            assert 0 < q["p10"] <= q["p50"] <= q["p90"]


def test_tidy_merges_maize_and_drops_camps():
    row = dict(date="2015-03-15", admin1="X", latitude=1.0, longitude=2.0, pricetype="Retail",
               unit="KG", currency="UGX")
    raw = pd.DataFrame([
        {**row, "market": "Lira", "commodity": "Maize", "price": 700.0},
        {**row, "market": "Lira", "commodity": "Maize (white)", "price": 800.0},
        {**row, "market": "Lira", "commodity": "Beans", "price": 3000.0},
        {**row, "market": "Lira", "commodity": "Beans", "price": 2500.0, "pricetype": "Wholesale"},
        {**row, "market": "Nakivale (refugee settlement)", "commodity": "Beans", "price": 1.0},
    ])
    out = tidy(raw)
    assert sorted(out.crop) == ["beans", "maize"]
    assert out.set_index("crop").price.to_dict() == {"maize": 800.0, "beans": 3000.0}


def test_tidy_drops_entry_errors():
    row = dict(admin1="X", latitude=1.0, longitude=2.0, pricetype="Retail", unit="KG",
               currency="UGX", market="Gulu", commodity="Maize (white)")
    prices = {"2021-04-15": 1000.0, "2021-05-15": 1222.0, "2021-06-15": 2.0,
              "2021-07-15": 1086.0, "2021-08-15": 1200.0}
    out = tidy(pd.DataFrame([{**row, "date": k, "price": v} for k, v in prices.items()]))
    assert len(out) == 4 and out.price.min() == 1000.0
