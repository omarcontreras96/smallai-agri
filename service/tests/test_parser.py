from pathlib import Path

import pytest

from service.bands import load_bands
from service.parser import evaluate, parse

MARKETS = load_bands()["markets"]


def test_accuracy_on_message_set():
    res = evaluate(Path(__file__).parent / "messages.jsonl", MARKETS)
    assert res["n"] >= 200
    assert res["exact"] >= 0.95, res["failures"][:10]


@pytest.mark.parametrize("text,crop,price,unit,market,lang", [
    ("mahindi 900 beseni mbale", "maize", 900, "basin", "Mbale", "sw"),
    ("maize 900 basin mbale", "maize", 900, "basin", "Mbale", "en"),
    ("kasooli 95,000/= ensawo owino", "maize", 95000, "bag", "Owino", "lg"),
    ("maharagwe 4200/kg fort portal", "beans", 4200, "kg", "Fort Portal", "sw"),
])
def test_demo_messages(text, crop, price, unit, market, lang):
    got = parse(text, MARKETS)
    assert (got["crop"], got["price"], got["unit"], got["market"], got["lang"]) == (crop, price, unit, market, lang)
    assert got["intent"] == "offer" and got["confidence"] >= 0.9


def test_unknown_market_is_reported_not_guessed():
    got = parse("mahindi 900 kilo kitgum", MARKETS)
    assert got["market"] is None and "kitgum" in got["unknown"]


def test_noise_has_zero_confidence():
    assert parse("habari yako", MARKETS)["confidence"] == 0.0


def test_container_size_given():
    got = parse("mahindi gunia 100kg 95000 lira", MARKETS)
    assert got["unit"] == "bag" and got["unit_kg"] == 100 and got["price"] == 95000
