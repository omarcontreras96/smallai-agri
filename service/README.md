# service/ (workstream B)
SMS service: FastAPI app (`main.py`), parser (`parser.py`), replies (`reply.py`), co-op dashboard (`coop.py`), Africa's Talking sender (`sms_out.py`), demo seeding (`seed_demo.py`) and the Vercel demo entrypoint (`vercel_app.py`).

Run: `uv run uvicorn service.main:app --reload`, then open `/inbox` and `/coop`. See the root [README](../README.md).

## Offline (no internet, no Africa's Talking)
```
uv run uvicorn service.main:app --port 8000
```
- `http://localhost:8000/inbox`: phone simulator (type as the farmer; switch numbers in the header)
- `http://localhost:8000/coop`: co-op dashboard (auto-refreshes every 30 s)
- `curl -X POST localhost:8000/sms -d from=+256700000009 --data-urlencode "text=beans 3000 kg mbale"` returns the reply as plain text

## Africa's Talking sandbox (real SMS round trip in AT's simulator)
In the sandbox, the HTTP response to the incoming-SMS webhook is **not** delivered to the phone. The service also sends every reply through the SMS API (`sms_out.py`) when credentials are set.

1. **AT dashboard** (account.africastalking.com → *Go to sandbox app*; menu names may differ):
   - *Settings → API Key*: generate a key (shown once).
   - *SMS → Shortcodes*: create a shortcode (we used `6000`-style numbers).
2. **`.env.local`** in the repo root (gitignored, never commit it; template in `.env.example`):
   ```
   AT_USERNAME=sandbox
   AT_API_KEY=<your sandbox key>
   AT_SHORTCODE=<your shortcode>
   ```
3. **Start the service**, then check `http://localhost:8000/health` shows `"sms_out": true`:
   ```
   uv run uvicorn service.main:app --port 8000
   ```
4. **Tunnel** (install once: `winget install --id Cloudflare.cloudflared`; macOS `brew install cloudflared`):
   ```
   cloudflared tunnel --url http://localhost:8000
   ```
   Copy the `https://<random>.trycloudflare.com` URL it prints. It **changes on every restart**.
5. **AT dashboard → SMS → SMS Callback URLs → Incoming Messages**: `https://<random>.trycloudflare.com/sms`
6. **Simulator** (simulator.africastalking.com:1517): pick a +256 number, open Messages, text the shortcode.

The uvicorn log prints `AT send to <last 4 digits>: Sent to 1/1 ... Message parts: N` for each reply.

### Checkpoint exchanges (also covered by `tests/test_main.py::test_sms_checkpoint_exchanges`)
| Send | Expected reply starts with | SMS parts |
|---|---|---|
| `mahindi 15000 beseni gulu` | `Beseni ni kilo ngapi? Jibu 1=15kg 2=20kg` | 1 |
| `1` (same phone) | `Mahindi Gulu: 15,000/beseni (15kg) = 1,000/kg.` … `Ofa ni CHINI` | 2 |
| `beans 3000 kg mbale` | `Beans Mbale: 3,000/kg.` … `Offer is LOW` | 2 |
| `mahindi 1200 kilo kitgum` | `Sijui kwa uhakika: soko 'kitgum' halipo kwenye orodha yetu. Uliza chama au afisa kilimo.` | 1 |

Gotchas:
- `mahindi 900 beseni …` is 60 UGX/kg, so it gets the "check the unit" fail-safe, not a band. Use a realistic price.
- Stale-data fail-safe (`gap_months_h1 > 12`) is lifted once 2+ phones report for that crop + market. After `seed_demo`, Mbale maize no longer says "not sure"; use an unknown market or `uv run python -m service.seed_demo --reset`.
- Bands load at startup: restart uvicorn after `models/bands.json` is regenerated.
- Local data lives in `data/service.db` (gitignored). Delete it for a clean dashboard.
