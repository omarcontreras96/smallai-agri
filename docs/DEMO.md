# Video scripts: three 60-second clips

Hack-Nation wants **three videos of at most 60 seconds each**: Demo, Tech and Team. Each goes to the portal (MP4 or MOV, at most 1 GB) **and** to the Google Form. The World Bank brief wants **one video of 2 to 5 minutes** covering five points, and says entries without it will not be shortlisted.

The plan covers both:
- record the three clips so that, played back to back, they cover all five World Bank points;
- join them into one ~3-minute cut, upload it unlisted (YouTube or Drive), and link it at the top of the README.

| World Bank point | Where it is covered |
|---|---|
| 1. One-sentence problem statement | Demo clip, 0:00 |
| 2. AI capabilities, why a simpler tool would not do, guardrails | Tech clip, 0:00–0:40 |
| 3. Tool demo, end to end | Demo clip, 0:08–0:60 |
| 4. Where it sits in the user's day, tech stack | Demo clip, 0:08 (moment of sale) and Tech clip, 0:00 (stack frame) |
| 5. What localizing AI means to us | Team clip, 0:25–0:60 |

Each script is about 55 seconds of voice-over at a calm pace (2.4 words per second), leaving a margin under the 60-second limit. Time a read-through before recording. Every reply below comes from the current `main` on a fresh database, recorded in this order.

Links for both forms: demo https://smallai-agri.vercel.app · repo https://github.com/omarcontreras96/smallai-agri

## Before recording (Pepe's PC: Africa's Talking is set up there)
1. Latest code and a fresh state, with the labelled synthetic farmer offers seeded **before** recording, so the dashboard already has data:
   ```bash
   git pull && uv sync
   rm -f data/service.db && uv run python -m service.seed_demo
   uv run uvicorn service.main:app
   ```
   Being on the latest `main` matters: the bands and the example markets changed tonight, and the captions below assume them.
2. The SMS path, with **internet on**:
   - start the tunnel: `cloudflared tunnel --url http://localhost:8000`;
   - in the Africa's Talking sandbox, set the shortcode's incoming-SMS callback to the tunnel address plus `/sms` (the address changes on every tunnel restart);
   - check `http://localhost:8000/health` shows `"sms_out": true`;
   - open the Africa's Talking phone simulator with a test number. This is Noor's phone.
3. Browser at 125% zoom, two more tabs: `http://localhost:8000/inbox?phone=%2B256700000002` (the offline shot) and `http://localhost:8000/coop`.
4. Rehearse once, then **reset** (step 1) so the recording starts clean. Don't send anything else from the simulator number between the rehearsal and the take.
5. Three still frames ready (see "Still frames" at the end).
6. Recording: macOS `Cmd+Shift+5` (screen + microphone), or record the screen and the voice separately. Paste messages instead of typing them, and **cut the few seconds of waiting** for each SMS reply in the edit. Add captions for the Swahili replies.

---

## Clip 1. Demo: what we built (60 s)
Form fields: portal "Product demo", Google Form "Demo video".

| Time | On screen | Voice-over |
|---|---|---|
| 0:00–0:08 | **Frame A**: the problem sentence, Noor | "At harvest, a buyer names a price for Noor's maize. She has no way to check it. Now she can, before she agrees." |
| 0:08–0:28 | Africa's Talking simulator (Noor's phone): send `mahindi 20000 beseni arua` → SMS asks the basin size → send `1` → verdict SMS (captions below) | "At the moment of sale she texts the offer in Swahili from a basic phone. It asks her basin size, converts to a price per kilo, and checks this month's market band. Low: ask for thirty thousand five hundred. Prices are falling. She decides." |
| 0:28–0:37 | Simulator: send `maize 1200 kg wakiso` → "Not sure… Ask your co-op or extension officer." | "Data too old, market unknown, message unclear? It says: not sure, ask your co-op. It never guesses." |
| 0:37–0:48 | **Turn Wi-Fi off** on camera. Inbox tab: paste `beans 4000 kg jinja` → FAIR reply appears at once; scroll to the footer with the file sizes | "Internet off: the co-op laptop still answers. In the field it needs an SMS line, not the internet. The price bands are a twenty-one kilobyte file." |
| 0:48–0:58 | `/coop` tab: tiles, then the red dots and the Mbale row | "Every report feeds the co-op dashboard: bands refreshed by farmers' reports, and buyers paying below the band flagged in red." |

Voice-over: 130 words, about 54 s at a calm pace.

Replies on screen, with captions:
```
Beseni ni kilo ngapi? Jibu 1=15kg 2=20kg
```
*How many kg is the basin? Reply 1=15kg 2=20kg*
```
Mahindi Arua: 20,000/beseni (15kg) = 1,330/kg.
Bei ya soko mwezi huu: 1,590-2,590/kg.
Ofa ni CHINI (~34% chini ya wastani). Omba 30,500 kwa beseni.
Miezi 2 ijayo: bei inashuka.
Bei ya rejareja mjini, si ya shambani. Uamuzi ni wako.
```
*Maize, Arua: 20,000 per 15 kg basin = 1,330/kg. Market price this month: 1,590–2,590/kg. The offer is LOW (~34% below average). Ask for 30,500 per basin. Next 2 months: prices falling. Town retail price, not farm-gate. Your decision.*
```
Not sure: last Wakiso market data is 18 months old. Ask your co-op or extension officer.
```
The verdict is 231 characters, so it arrives as **two SMS parts**; the simulator may show them as one message or two. Either is fine; the captions cover the whole text.

Offline shot (local inbox, Wi-Fi off):
```
Beans Jinja: 4,000/kg.
Market price this month: 3,740-4,920/kg.
Offer is FAIR. You can ask 4,250 per kg.
Next 2 months: prices steady.
Town retail price, not farm-gate. You decide.
```
Dashboard tiles (maize tab), as seeded: 23 offers logged, 22 farmers reporting, 7 markets with reports, 5 bands updated by reports, 3 offers below P10.

---

## Clip 2. Tech: how we built it (60 s)
Form fields: portal "Technical walkthrough", Google Form "Tech video" (what was hard, how we overcame it, remaining limits).

| Time | On screen | Voice-over |
|---|---|---|
| 0:00–0:15 | **Frame B**: the stack | "Three small pieces on one co-op laptop, no cloud. A fuzzy parser reads Swahili, English and Luganda. A LightGBM quantile model, trained on WFP prices from twenty-eight towns since 2008, forecasts this month's band. A Bayesian nowcaster updates it from farmers' reports." |
| 0:15–0:33 | **Frame C**: `docs/slides/backtest.png`, then zoom on the right panel | "The hard part: the newest town prices are six to ten months old. So the model forecasts by data age, calibrated on past years. A year out, a spreadsheet band catches the real price sixty-nine percent of the time; ours, eighty." |
| 0:33–0:45 | Inbox thread with the "not sure" reply, then `service/reply.py` templates | "Guardrails: fixed reply templates, nothing generated. Not sure on stale data, wide bands or unknown markets. One vote per phone, so no single phone moves the band." |
| 0:45–0:57 | `/coop`, Gulu maize row: band after reports well below the model band | "Limits: the reference is town retail, so farm-gate reports pull bands down, as here. And we tested the parser on messages we wrote, not real farmers' texts." |

Voice-over: 137 words, about 57 s at a calm pace.

Other things worth a word if time allows (all true, all in `docs/EVIDENCE.md`): a bad record of 2 UGX/kg in the WFP data that we found and dropped; raw model bands covering only 54–69% before calibration; median error 403 vs 467 UGX/kg for the last observed price.

---

## Clip 3. Team: who we are, and what localizing AI means to us (60 s)
Form fields: portal "Team introduction", Google Form "Team video".

Filmed with faces (laptop camera is fine), or the team photo with voice-over.

| Time | Who | Voice-over (draft, edit into your own words) |
|---|---|---|
| 0:00–0:10 | Omar | "I'm Omar. **[one line: where you're from and what you do]**. I built the data pipeline, the price model and the evidence." |
| 0:10–0:20 | Pepe | "I'm Pepe. **[one line: where you're from and what you do]**. I built the SMS service, the parser and the co-op dashboard." |
| 0:20–0:25 | Either | "In one night we shipped a working tool, a live demo, open code and an honest evidence report." |
| 0:25–0:58 | Omar (or split) | "Localizing AI isn't translating an app. It's the units people sell in, a basin, a tin. The words they type, in Swahili or Luganda. Local prices with their holes stated: old data means a wider band, not false precision. And local people as the fallback. **[Omar: one sentence on the coyotes in Chiapas, the buyers who set the price because farmers can't check it, in your own words.]**" |

Voice-over: 91 words before the three bracketed lines; with them filled in (under 12 words each) it lands near 125 words, about 52 s.

---

## Still frames
Three 1920×1080 images, used inside the clips. This is not a slide deck.

| Frame | File | Used in |
|---|---|---|
| A, the problem | `docs/slides/frame_a_problem.png` | Demo 0:00–0:08 |
| B, Noor's day + stack | `docs/slides/frame_b_stack.png` | Tech 0:00–0:15 |
| C, backtest | `docs/slides/backtest.png` | Tech 0:15–0:33 |

Frames A and B are HTML in `docs/slides/frames/`. To change the text, edit the HTML and re-render with `bash docs/slides/frames/render.sh` (headless Chrome, throwaway profile). Contents:

- **Frame A (Demo, 0:00).** The problem sentence:
  > Because of this tool, a smallholder farmer like Noor will know the fair price band for her maize or beans *before* she accepts a buyer's offer, which she would otherwise do blind; we know because the Côte d'Ivoire E-Agriculture project ($70M, P160418) broadcast prices to 400K farmers and never measured whether anyone received a better price.
- **Frame B (Tech, 0:00).** The stack and the moment in the day:
  - **Day:** buyer names a price → Noor texts it → reply in seconds → she decides.
  - **Stack:** basic phone → SMS shortcode (Africa's Talking) → co-op laptop or Raspberry Pi (parser, `bands.json`, nowcaster, Swahili/English templates, SQLite) → co-op dashboard.
  - **Monthly:** WFP prices (HDX) → `model/train.py`, 30 s → `bands.json`, 21 KB.
- **Frame C (Tech, 0:15).** `docs/slides/backtest.png` (already made).

## After recording
1. Check each clip is **60 s or less**. Export MP4.
2. Portal: upload Team introduction, Product demo and Technical walkthrough. Fill in the project name, the challenge (World Bank, Agriculture), the GitHub link, the live URL and the team photo. Uploads stay open until **9:15 AM ET**.
3. Google Form: upload the same three clips, the repo link, the demo link and the team picture. **List every team member.** Agree to the T&C; the code is MIT-licensed (`LICENSE`). **No re-submissions**, so submit once.
4. Join the three clips (Demo → Tech → Team), upload the ~3-minute cut unlisted, check it opens in a private window, and put the link at the top of the README.

## If a take breaks
- **Wrong state:** stop the server, `rm -f data/service.db`, seed, start again.
- **A reply differs from this script:** the database wasn't fresh, or `models/bands.json` changed. Re-run step 1 of "Before recording".
- **No SMS reply in the simulator:** check `/health` shows `"sms_out": true`, and that the sandbox callback matches the *current* tunnel address plus `/sms`. If it still fails, record 0:08–0:37 on the local inbox instead (same messages, same replies) and keep the Wi-Fi-off shot.
- **The laptop run fails:** record on https://smallai-agri.vercel.app instead. The examples are on its front page. In that case, drop the Wi-Fi-off line.
- **Backup machine:** Omar's laptop can run the local parts (inbox, Wi-Fi off, dashboard) with the same commands. It has no Africa's Talking keys.

## Facts said on camera, and where they come from
| Claim | Source |
|---|---|
| Newest town prices 6–10 months old | `models/bands.json` `gap_months_h1`; WFP data ends Apr 2026 |
| Prices since 2008, 28 towns | `data/processed/monthly.csv`: Oct 2008 – Apr 2026; 28 markets in the bands |
| Spreadsheet band 69% a year out, ours ~80% | `docs/slides/backtest.csv` (12-month gap: 0.690 vs 0.795) |
| Bands file 21 KB | inbox footer (`models/bands.json`) |
| Reply in milliseconds | measured: median 2 ms, max 15 ms per reply on a laptop |
| Rebuild in 30 s | `model/train.py` full run |
| 400K farmers, $70M, P160418 | team's problem statement (`docs/CONCEPT.md`) |
