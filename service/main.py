"""SMS service. Run: uv run uvicorn service.main:app --reload

POST /sms    Africa's Talking incoming-SMS webhook (form fields `from`, `text`, `to`); returns the reply as plain text
             and, if AT_* credentials are set, also sends it as an SMS (see sms_out.py).
GET  /inbox  Local phone simulator (works with Wi-Fi off). POST /inbox sends a message from it.
GET  /coop   Co-op dashboard: offers, model vs nowcast band per market, offers below P10.
GET  /health Band file and DB info.
"""
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import quote

from fastapi import BackgroundTasks, FastAPI, Form, Request
from fastapi.responses import PlainTextResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from service import coop, db, reply, sms_out
from service.bands import MODELS, bands_path, load_bands

DEFAULT_PHONE = "+256700000001"
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    sms_out.load_env()
    app.state.db = db.connect()
    app.state.bands_path = bands_path()
    app.state.bands = load_bands(app.state.bands_path)
    yield
    app.state.db.close()


app = FastAPI(title="smallai-agri SMS service", lifespan=lifespan)


def handle(phone: str, text: str) -> str:
    conn, ph = app.state.db, db.hash_phone(phone)
    db.log_message(conn, ph, "in", text)
    out = reply.respond(conn, ph, text, app.state.bands)
    db.log_message(conn, ph, "out", out)
    return out


@app.post("/sms", response_class=PlainTextResponse)
def sms(background: BackgroundTasks, phone: str = Form(..., alias="from"), text: str = Form(""),
        to: str | None = Form(None)):
    out = handle(phone, text)
    if sms_out.enabled():
        background.add_task(sms_out.send, phone, out, to)
    return out


@app.get("/inbox")
def inbox(request: Request, phone: str = DEFAULT_PHONE):
    model_files = [(p.name, p.stat().st_size) for p in sorted(MODELS.iterdir()) if p.is_file()]
    return templates.TemplateResponse(request, "inbox.html", {
        "phone": phone,
        "messages": db.thread(app.state.db, db.hash_phone(phone)),
        "bands_file": app.state.bands_path.name,
        "generated_at": app.state.bands.get("generated_at"),
        "model_files": model_files,
        "public_demo": getattr(app.state, "public_demo", False),
    })


@app.post("/inbox")
def inbox_send(phone: str = Form(DEFAULT_PHONE), text: str = Form(...)):
    if text.strip():
        handle(phone, text)
    return RedirectResponse(f"/inbox?phone={quote(phone)}", status_code=303)


@app.get("/coop")
def coop_page(request: Request, crop: str = "maize", refresh: int = 30):
    crop = crop if crop in ("maize", "beans") else "maize"
    refresh = min(max(refresh, 1), 300)   # ?refresh=2 for filming the dashboard filling up
    return templates.TemplateResponse(request, "coop.html",
                                      {"v": coop.view(app.state.db, app.state.bands, crop), "refresh": refresh})


@app.get("/health")
def health():
    return {
        "bands_file": str(app.state.bands_path),
        "generated_at": app.state.bands.get("generated_at"),
        "n_bands": len(app.state.bands.get("bands", {})),
        "markets": sorted(app.state.bands.get("markets", {})),
        "db": str(db.db_path()),
        "sms_out": sms_out.enabled(),
    }
