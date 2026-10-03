# Build plan — Uganda, maize + beans (locked Oct 3, ~8 PM ET)

Deadline: **Sun Oct 4, 9:00 AM ET.** Two builders, each with their own Claude session on this repo.
Rule: build the 3-minute demo first. Anything not in the demo flow waits.

## The demo flow (what the video shows)
1. Farmer texts: `maize 900 basin mbale` (or Swahili: `mahindi 900 beseni mbale`).
2. Reply asks one clarifying question if the unit is ambiguous (`Basin ya kg ngapi? 1=15kg 2=20kg`).
3. Reply: per-kg conversion, band for this market this month, verdict LOW/FAIR/GOOD, suggested ask, direction next 1–2 months, note that reference is market retail. In Swahili and English.
4. A second message with an unknown market or stale data → "Sijui kwa uhakika. Uliza chama/afisa kilimo." (not sure, ask the co-op / extension officer).
5. Laptop with Wi-Fi off: same exchange through the local inbox page, model file sizes on screen.
6. Co-op dashboard: offers logged, bands updated by reports, under-band buyers flagged.
7. One slide: backtest vs last-month baseline; one slide: data gaps; one slide: moonshot.

## Workstreams

### A — Data, band model, nowcaster, evidence  (Omar)
| When (ET) | Deliverable |
|---|---|
| 8:00–8:30 | `model/prepare.py`: WFP Uganda → tidy monthly series per (commodity, market), KG retail, UGX. Keep `Maize (white)` + `Maize` (pre-2011) merged, `Beans`. Town markets only (exclude "refugee settlement"). |
| 8:30–10:30 | `model/train.py`: quantile GBM (LightGBM or sklearn HistGradientBoosting, loss=quantile at 0.1/0.5/0.9). Features: lags 1,2,3,12 (last observed, with months-since-last), month, market, commodity, regional mean. Horizons: h=1,2,3 months ahead. Train ≤2024, test 2025–2026. Baseline = last observed price. Report coverage of 10–90 band and MAE vs baseline. **10:30 checkpoint.** |
| 10:30–11:00 | Export **`models/bands.json`** (contract below) + `models/metrics.json`. |
| 11:00–12:30 | `model/nowcast.py`: Bayesian update of a market band from reported offers (precision-weighted mean on log price, prior = model band). Function `update_band(band, offers) -> band`. Unit tests with 3 synthetic offers. |
| 12:30–1:30 | Evidence pack `docs/EVIDENCE.md`: backtest table, coverage, model size, data gaps (retail not farm gate, town obs end Apr 2026, camps excluded), sources with license/year. |
| 1:30– | Join video + README. |

### B — SMS service, parser, templates, dashboard  (Pepe)
| When (ET) | Deliverable |
|---|---|
| 8:00–9:00 | `service/` FastAPI app: `POST /sms` (Africa's Talking webhook form fields `from`, `text`), `GET /inbox` local simulator page (textbox + thread), SQLite `offers` table. Runs with `uv run uvicorn service.main:app`. |
| 9:00–10:30 | `service/parser.py`: lexicon + fuzzy match → `{crop, price, unit, qty, market, lang, confidence}`. Vocab: crops (maize/mahindi/kasooli, beans/maharagwe/ebijanjaalo), units (kg, basin/beseni, bag/gunia/sack 100kg, tin/debe 20kg), numbers incl. `900`, `900/=`, `shs 900`, `900 per kg`. Markets = list from `models/bands.json` + aliases. 200-message test set `service/tests/messages.jsonl` (sw/en/mixed) with expected JSON; report accuracy. |
| 10:30–11:30 | `service/reply.py`: fixed templates sw/en; clarifying-question state machine (per phone number, SQLite); unit conversion to per kg; verdict thresholds (LOW < P25, FAIR P25–P75, GOOD > P75 — or use model's P10/P90); fail-safe rules (band width > 40% of median, market obs older than 6 months, unknown crop/market, parser confidence < 0.6). Until A delivers, use `models/bands.sample.json`. |
| 11:30–12:30 | Africa's Talking sandbox: app + shortcode, callback via `cloudflared tunnel` or ngrok to `/sms`; test full exchange in simulator. |
| 12:30–1:30 | `GET /coop` dashboard: offers table, per-market band chart (plain HTML + small JS), flags for offers < P10. Calls `nowcast.update_band` when A lands it. |
| 1:30– | Join video. |

### Both — 1:30 AM onward
| When | Deliverable |
|---|---|
| 1:30–2:30 | Freeze. README (problem, how it works, run instructions, data, gaps, team). Record screen takes: simulator exchange, offline inbox, dashboard. |
| 2:30–4:00 | Video 2–5 min, five sections in the brief's order: problem sentence (template), AI capabilities + why not SMS/spreadsheet, tool demo end to end, where it sits in Noor's day + stack, our take on localizing AI. Slides in `docs/slides/`. |
| 4:00–7:00 | Sleep in shifts (one 11 PM–2:30, other 4–7) or both 4–7. |
| 7:00–8:30 | Submit draft form by 7:30, final by 8:30. Nobody touches `main` after 8:30. |

## Interface contract (so A and B never block each other)

### `models/bands.json`
```json
{
  "generated_at": "2026-10-04T03:00:00Z",
  "currency": "UGX", "unit": "KG", "price_type": "retail",
  "markets": {"Mbale": {"aliases": ["mbale"], "admin1": "Mbale", "lat": 1.08, "lon": 34.17}},
  "bands": {
    "maize|Mbale": {
      "last_obs_date": "2026-04-15", "last_obs_price": 1050,
      "h1": {"p10": 900, "p50": 1050, "p90": 1200},
      "h2": {"p10": 950, "p50": 1100, "p90": 1300},
      "h3": {"p10": 1000, "p50": 1150, "p90": 1350},
      "n_reports": 0
    }
  }
}
```
Keys are `"<crop>|<Market>"` with crop in `{maize, beans}`. `h1` = current month. B reads this file at startup; A can regenerate any time.

### Parser output (B) consumed by reply + logged to SQLite
```json
{"crop":"maize","price":900,"unit":"basin","qty":1,"market":"Mbale","lang":"sw","confidence":0.92,"raw":"mahindi 900 beseni mbale"}
```

### Offer log row (B writes, A's nowcaster reads)
`id, ts, phone_hash, crop, market, price_per_kg, unit, raw_text, verdict, band_p10, band_p50, band_p90`

### Unit table (shared, `service/units.py`)
kg=1 · basin/beseni ≈ 15 kg maize (ask: 15 or 20) · tin/debe = 20 kg · bag/gunia/sack = 100 kg maize, 100 kg beans (ask if 90/100/120) · "per kg" explicit.

## Stack
Python 3.12 via `uv`; FastAPI + uvicorn; SQLite; scikit-learn or LightGBM; pandas; Jinja2 templates; Africa's Talking python SDK; `cloudflared` for the webhook tunnel. No frontend framework. No cloud LLM anywhere in the farmer path.

## Git
`main` always runs. Branches `feat/model-*` (A) and `feat/service-*` (B). Small PRs, squash-merge yourself, pull often. Only shared files: `models/bands.json`, `service/units.py`, `docs/`. Say in Slack/WhatsApp before touching the other's folder.

## Checkpoints
- **10:30 PM:** bands.json exists with real numbers and backtest beats baseline → continue. Else: ship seasonal-median bands (no ML) and say so; still a valid Small AI entry with nowcasting.
- **12:30 AM:** full SMS exchange works in the simulator.
- **2:30 AM:** feature freeze, no exceptions.
