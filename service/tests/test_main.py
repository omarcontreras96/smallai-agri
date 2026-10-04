import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SMALLAI_DB", str(tmp_path / "test.db"))
    monkeypatch.setenv("AT_API_KEY", "")   # never send real SMS from tests (load_env does not override)
    from service.main import app
    with TestClient(app) as c:
        yield c


def test_sms_webhook_replies_and_logs(client):
    r = client.post("/sms", data={"from": "+256700000009", "text": "mahindi 900 beseni mbale", "to": "6000"})
    assert r.status_code == 200 and r.text
    page = client.get("/inbox", params={"phone": "+256700000009"})
    assert "mahindi 900 beseni mbale" in page.text
    assert r.text.split('"')[0] in page.text


def test_inbox_send_keeps_plus_in_phone(client):
    r = client.post("/inbox", data={"phone": "+256711111111", "text": "beans 4000 kg gulu"}, follow_redirects=False)
    assert r.status_code == 303 and "%2B256711111111" in r.headers["location"]
    page = client.get(r.headers["location"])
    assert "beans 4000 kg gulu" in page.text


def test_threads_are_per_phone_and_phone_not_stored(client):
    client.post("/sms", data={"from": "+256700000001", "text": "hello one"})
    assert "hello one" not in client.get("/inbox", params={"phone": "+256700000002"}).text
    from service.main import app
    dump = "\n".join(app.state.db.iterdump())
    assert "256700000001" not in dump


def test_health_reads_bands(client):
    h = client.get("/health").json()
    assert h["n_bands"] > 0 and "Mbale" in h["markets"]


def test_sms_sends_reply_via_africas_talking_when_configured(client, monkeypatch):
    from service import sms_out
    sent = []
    monkeypatch.setattr(sms_out, "enabled", lambda: True)
    monkeypatch.setattr(sms_out, "send", lambda phone, text, to=None: sent.append((phone, text, to)))
    r = client.post("/sms", data={"from": "+256700000042", "text": "habari", "to": "6000"})
    assert sent == [("+256700000042", r.text, "6000")]


def test_coop_dashboard_shows_offers_and_flags(client):
    from service import seed_demo
    from service.main import app
    assert seed_demo.seed(app.state.db, app.state.bands) > 20
    page = client.get("/coop", params={"crop": "maize"}).text
    assert "Gulu" in page and "below P10" in page and "demo" in page
    assert "Band after farmer reports" in page and "<circle" in page
    assert client.get("/coop", params={"crop": "beans"}).status_code == 200
    seed_demo.reset(app.state.db)
    assert "No offers yet" in client.get("/coop").text


def test_sms_checkpoint_exchanges(client):
    """The three Africa's Talking checkpoint exchanges, as AT posts them (from, text, to)."""
    sms = lambda phone, text: client.post("/sms", data={"from": phone, "text": text, "to": "6000"}).text

    # a) Swahili + clarifying question, two messages from the same phone
    assert sms("+256700000011", "mahindi 15000 beseni gulu").startswith("Beseni ni kilo ngapi?")
    out = sms("+256700000011", "1")
    assert out.startswith("Mahindi Gulu: 15,000/beseni (15kg) = 1,000/kg.") and "Ofa ni" in out

    # b) English, no question
    out = sms("+256700000012", "beans 3000 kg mbale")
    assert out.startswith("Beans Mbale: 3,000/kg.") and "Offer is" in out

    # c) fail-safe: market not on the list
    out = sms("+256700000013", "mahindi 1200 kilo kitgum")
    assert out.startswith("Sijui kwa uhakika") and out.endswith("Uliza chama au afisa kilimo.")

    # offers land on /coop under a hashed phone, not demo-
    page = client.get("/coop", params={"crop": "beans"}).text
    assert "Mbale" in page and "demo" not in page.split("Recent offers")[1]
