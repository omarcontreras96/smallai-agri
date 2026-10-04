import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SMALLAI_DB", str(tmp_path / "test.db"))
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
