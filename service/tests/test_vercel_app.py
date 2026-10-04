from fastapi.testclient import TestClient


def test_public_demo_landing_and_seeded_coop(tmp_path, monkeypatch):
    monkeypatch.setenv("SMALLAI_DB", str(tmp_path / "vercel.db"))
    monkeypatch.setenv("AT_API_KEY", "")
    from service import vercel_app
    vercel_app.seed_once()   # second call must not duplicate the demo offers
    with TestClient(vercel_app.app) as c:
        home = c.get("/")
        assert home.status_code == 200 and "mahindi 20000 beseni arua" in home.text
        assert c.get("/coop").status_code == 200
        n = c.app.state.db.execute("SELECT COUNT(*) FROM offers WHERE phone_hash LIKE 'demo-%'").fetchone()[0]
        assert 0 < n <= 40
        r = c.post("/inbox", data={"phone": "+256799999999", "text": "beans 4000 kg mbale"})
        assert r.status_code == 200 and "Mbale" in r.text
