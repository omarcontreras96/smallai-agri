"""Entrypoint for the public judge demo on Vercel (pyproject.toml [tool.vercel] entrypoint).

Same app as service.main, plus:
- SQLite in /tmp, the only writable path on Vercel. It is per instance and wiped on restart,
  so each fresh instance re-seeds the labelled synthetic offers from seed_demo.py.
- GET / : a short landing page for judges.
AT_* keys are not set on Vercel, so this deployment never sends real SMS.
The product itself runs offline on a co-op laptop: uv run uvicorn service.main:app
"""
import os

os.environ.setdefault("SMALLAI_DB", "/tmp/service.db")

from fastapi.responses import HTMLResponse  # noqa: E402

from service import db  # noqa: E402
from service.bands import load_bands  # noqa: E402
from service.coop import DEMO_PREFIX  # noqa: E402
from service.main import app  # noqa: E402
from service.seed_demo import seed  # noqa: E402


def seed_once() -> None:
    conn = db.connect()
    try:
        if not conn.execute("SELECT 1 FROM offers WHERE phone_hash LIKE ? LIMIT 1",
                            (DEMO_PREFIX + "%",)).fetchone():
            seed(conn, load_bands())
    finally:
        conn.close()


seed_once()
app.state.public_demo = True   # inbox footer says "hosted online", not "runs locally"

# Verdict examples use markets without seeded demo offers, so the answer reflects the model band.
EXAMPLES = [
    ("mahindi 20000 beseni arua", "Swahili. Asks the basin size; reply <code>1</code> for the verdict."),
    ("beans 4000 kg jinja", "English, price per kg."),
    ("kasooli 1500 kilo arua", "Luganda word for maize. Understood; the reply is in Swahili."),
    ("maize 1200 kg wakiso", "Last market data is 18 months old: \"not sure, ask your co-op\"."),
    ("mahindi 1000 kilo kitgum", "Market not covered: \"not sure\", never a guess."),
]

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Price SMS demo</title>
<style>
  :root { --bg: #eef1ec; --card: #fff; --ink: #1d2a1d; --muted: #5b665b; --accent: #2f6b2f; --line: #d9ded6; }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--bg); color: var(--ink); font: 16px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }
  main { max-width: 680px; margin: 0 auto; padding: 32px 16px 48px; }
  h1 { font-size: 26px; line-height: 1.2; margin: 0 0 8px; }
  h2 { font-size: 18px; margin: 28px 0 8px; }
  p { margin: 0 0 12px; }
  .lede { color: var(--muted); }
  .actions { display: flex; flex-wrap: wrap; gap: 12px; margin: 20px 0 8px; }
  .btn { display: inline-block; background: var(--accent); color: #fff; text-decoration: none; border: 0;
         border-radius: 999px; padding: 10px 18px; font: inherit; cursor: pointer; }
  .btn.secondary { background: var(--card); color: var(--accent); border: 1px solid var(--accent); }
  ul.try { list-style: none; padding: 0; margin: 0; }
  ul.try li { background: var(--card); border: 1px solid var(--line); border-radius: 12px; padding: 12px 14px;
              margin-bottom: 8px; display: flex; gap: 12px; align-items: center; justify-content: space-between; }
  ul.try code { font-size: 15px; }
  ul.try small { display: block; color: var(--muted); }
  ul.try form { margin: 0; flex: none; }
  ul.try button { padding: 6px 14px; font-size: 14px; }
  .notes { font-size: 14px; color: var(--muted); }
  .notes li { margin-bottom: 6px; }
</style>
</head>
<body>
<main>
  <h1>Price SMS: is this offer fair?</h1>
  <p class="lede">At harvest a buyer names a price and a smallholder in Uganda has no independent reference.
  She texts the offer; the service replies with this month's market band for maize or beans,
  a verdict (LOW / FAIR / GOOD), what to ask for, and the price direction. When the data cannot support
  an answer it says <em>"not sure, ask your co-op or extension officer"</em>.</p>
  <div class="actions">
    <a class="btn js-phone" href="/inbox">Open the phone simulator</a>
    <a class="btn secondary" href="/coop">Open the co-op dashboard</a>
  </div>

  <h2>Try these messages</h2>
  <ul class="try">
    {examples}
  </ul>

  <h2>About this demo</h2>
  <ul class="notes">
    <li>Each visitor gets a random simulated phone number. Do not type a real one: anyone can open any number's thread here.</li>
    <li>The co-op dashboard is preloaded with synthetic farmer offers, labelled <em>demo</em>. Data resets when the server restarts.</li>
    <li>No SMS is sent from this page. The real setup runs offline on a co-op laptop and receives SMS through Africa's Talking.</li>
    <li>Reference prices: WFP retail prices, Uganda town markets (HDX, CC BY-IGO), data to Apr 2026.
    The band for the current month is a forecast from that data, refreshed by farmers' reports. It is a town retail price, not a farm-gate price; the farmer decides.</li>
    <li>Code, evidence and data sources: <a href="https://github.com/omarcontreras96/smallai-agri">github.com/omarcontreras96/smallai-agri</a>.</li>
  </ul>
</main>
<script>
  // one random simulated number per visitor, so judges do not share a conversation
  let phone;
  try { phone = localStorage.getItem("demoPhone"); } catch (e) {}
  if (!phone) {
    phone = "+2567" + String(Math.floor(Math.random() * 1e8)).padStart(8, "0");
    try { localStorage.setItem("demoPhone", phone); } catch (e) {}
  }
  document.querySelectorAll("input[name=phone]").forEach(i => { i.value = phone; });
  document.querySelectorAll("a.js-phone").forEach(a => { a.href = "/inbox?phone=" + encodeURIComponent(phone); });
</script>
</body>
</html>
"""

EXAMPLE_ROW = """<li><span><code>{text}</code><small>{note}</small></span>
      <form method="post" action="/inbox"><input type="hidden" name="phone" value="+256700000001">
      <input type="hidden" name="text" value="{text}"><button class="btn" type="submit">Send</button></form></li>"""

LANDING = PAGE.replace("{examples}", "\n    ".join(EXAMPLE_ROW.format(text=t, note=n) for t, n in EXAMPLES))


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return LANDING
