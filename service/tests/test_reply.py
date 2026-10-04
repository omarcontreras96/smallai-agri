import pytest

from service import db
from service.bands import load_bands
from service.reply import quartiles, respond, verdict

BANDS = load_bands()


@pytest.fixture
def conn(tmp_path):
    c = db.connect(tmp_path / "t.db")
    yield c
    c.close()


def say(conn, phone, *msgs):
    return [respond(conn, phone, m, BANDS) for m in msgs]


def offers(conn):
    return [dict(r) for r in conn.execute("SELECT * FROM offers")]


def test_quartiles_inside_band():
    h = {"p10": 1000, "p50": 1500, "p90": 2400}
    p25, p50, p75 = quartiles(h)
    assert 1000 < p25 < 1500 < p75 < 2400
    assert verdict(900, h) == "LOW" and verdict(1500, h) == "FAIR" and verdict(2300, h) == "GOOD"


def test_basin_asks_size_then_gives_verdict_in_swahili(conn):
    ask, out = say(conn, "a", "mahindi 15000 beseni gulu", "1")
    assert ask.startswith("Beseni ni kilo ngapi?") and "1=15kg" in ask
    assert "15,000/beseni (15kg) = 1,000/kg" in out and "CHINI" in out and "Uamuzi ni wako" in out
    [o] = offers(conn)
    assert o["price_per_kg"] == 1000 and o["verdict"] == "LOW" and o["market"] == "Gulu"


def test_size_answer_in_kg_and_english(conn):
    ask, out = say(conn, "b", "beans 300000 bag masaka", "100kg")
    assert ask.startswith("How many kg is the bag?")
    assert "3,000/kg" in out and "Offer is" in out and "You decide" in out


def test_non_answer_drops_pending_question(conn):
    _, out = say(conn, "c", "mahindi 15000 beseni gulu", "maize 1200 per kg gulu")
    assert out.startswith("Maize Gulu: 1,200/kg.")


def test_missing_unit_asks_unit(conn):
    ask, out = say(conn, "d", "mahindi 1000 gulu", "1")
    assert "1=kilo" in ask and "1,000/kg" in out


@pytest.mark.parametrize("msg,expect", [
    ("mahindi 1200 kilo kitgum", "soko 'kitgum' halipo"),      # unknown market
    ("coffee 7000 kg mbale", "only have maize and beans"),     # unknown crop
    ("maize 1000 kg lira", "vary too much"),                   # band too wide
    ("mahindi 1300 kilo mbale", "miezi 17"),                    # stale market data
])
def test_failsafes_point_to_a_person(conn, msg, expect):
    [out] = say(conn, "e", msg)
    assert expect in out
    assert "Uliza chama au afisa kilimo" in out or "Ask your co-op or extension officer" in out


def test_implausible_price_is_not_judged_or_logged(conn):
    _, out = say(conn, "f", "mahindi 900 beseni mbale", "1")
    assert "si bei ya kawaida" in out and not offers(conn)


def test_farmer_reports_refresh_stale_band(conn):
    assert "miezi 17" in say(conn, "g1", "mahindi 1300 kilo mbale")[0]
    assert "miezi 17" in say(conn, "g2", "mahindi 1250 kilo mbale")[0]
    out = say(conn, "g3", "mahindi 1200 kilo mbale")[0]
    assert "Ofa ni" in out
    verdicts = [o["verdict"] for o in offers(conn)]
    assert verdicts[:2] == ["UNSURE", "UNSURE"] and verdicts[2] in {"LOW", "FAIR", "GOOD"}


def test_price_query(conn):
    [out] = say(conn, "h", "bei ya maharagwe owino")
    assert out.startswith("Maharagwe Owino mwezi huu:") and "/kg" in out


def test_noise_gets_help(conn):
    assert say(conn, "i", "habari")[0].startswith("Tuma:")
    assert say(conn, "i", "hello")[0].startswith("Send: crop")
