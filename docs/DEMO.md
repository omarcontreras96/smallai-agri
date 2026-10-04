# Video scripts: three 60-second clips

Hack-Nation wants **three videos of at most 60 seconds each**: Demo, Tech and Team. Each goes to the portal (MP4 or MOV, at most 1 GB) **and** to the Google Form. The World Bank brief wants **one video of 2 to 5 minutes** covering five points, and says entries without it will not be shortlisted.

The plan covers both:
- record the three clips so that, played back to back, they cover all five World Bank points;
- join them into one ~3-minute cut, upload it unlisted (YouTube or Drive), and link it at the top of the README.

| World Bank point | Where it is covered |
|---|---|
| 1. One-sentence problem statement | Combined cut: Frame A before the Demo clip (the Demo clip itself opens with the dramatized problem) |
| 2. AI capabilities, why a simpler tool would not do, guardrails | Tech clip, 0:00–0:40 |
| 3. Tool demo, end to end | Demo clip, 0:11–0:51 (real SMS through Africa's Talking) |
| 4. Where it sits in the user's day, tech stack | Demo clip, 0:00 and 0:51 (Noor at the moment of sale) and Tech clip, 0:00 (stack frame) |
| 5. What localizing AI means to us | Team clip, 0:25–0:60 |

Each script is about 55 seconds of voice-over at a calm pace (2.4 words per second), leaving a margin under the 60-second limit. Time a read-through before recording. Every reply below comes from the current `main` on a fresh database, recorded in this order.

Links for both forms: demo https://smallai-agri.vercel.app · repo https://github.com/omarcontreras96/smallai-agri

## Before recording (Pepe's PC: Africa's Talking is set up there)
1. Latest code and a fresh state. **Demo clip: empty database, no seeding** (the replies below were produced that way; the 200 synthetic offers are streamed in on camera, see the dashboard shot):
   ```bash
   git pull && uv sync
   rm -f data/service.db
   uv run uvicorn service.main:app
   ```
   **Tech clip** (dashboard shots): after the Demo take, stop the server, `rm -f data/service.db && uv run python -m service.seed_demo`, start it again.
   Being on the latest `main` matters: the bands and the example markets changed tonight, and the captions below assume them.
2. The SMS path, with **internet on**:
   - start the tunnel: `cloudflared tunnel --url http://localhost:8000`;
   - in the Africa's Talking sandbox, set the shortcode's incoming-SMS callback to the tunnel address plus `/sms` (the address changes on every tunnel restart);
   - check `http://localhost:8000/health` shows `"sms_out": true`;
   - open the Africa's Talking phone simulator with a test number. This is Noor's phone.
3. Browser at 125% zoom, two more tabs: `http://localhost:8000/inbox?phone=%2B256700000002` (the offline shot) and `http://localhost:8000/coop`.
4. Rehearse once, then **reset** (step 1) so the recording starts clean. Don't send anything else from the simulator number between the rehearsal and the take.
5. Three still frames ready (see "Still frames" at the end).
6. Recording: macOS `Cmd+Shift+5`; Windows: Snipping Tool video (`Win+Shift+R`), edit in Clipchamp (cut waits, captions, join clips). Or record the screen and the voice separately. Paste messages instead of typing them, and **cut the few seconds of waiting** for each SMS reply in the edit. Add captions for the Swahili replies.

---

## Clip 1. Demo: SourceSpot (60 s)
Form fields: portal "Product demo", Google Form "Demo video".

Story: a buyer lowballs Noor, SourceSpot shows what it can do (three English messages), then Noor uses it in Swahili on the same offer and sells for more. All SMS from **one simulator number** (`+256700000001`): one phone is one vote, so her own offers don't move the Gulu band between Swahili 1 and 2.

| Time | On screen | Voice-over |
|---|---|---|
| 0:00–0:09 | **Scene 1, video, labelled "Dramatization".** Gulu market. A buyer weighs Noor's maize and names his price: *"Eleven hundred a kilo. Take it or leave it."* Noor hesitates; close-up of her basic phone. | "This is Noor, a smallholder maize farmer in Uganda. A buyer offers her eleven hundred shillings a kilo, and she has no price to check it against." |
| 0:09–0:10 | **Frame D:** *Is this offer fair?* (`docs/slides/frame_d_question.png`) | "Is it fair?" |
| 0:10–0:11 | **Frame F:** *No* (`docs/slides/frame_f_no.png`) | "No." |
| 0:11–0:13 | **Frame E:** *This is SourceSpot* + logo (`docs/slides/frame_e_sourcespot.png`) | "That's why we built SourceSpot." |
| 0:13–0:24 | **English 1**, Africa's Talking simulator: send `A buyer in Arua is offering me 20,000 shillings for a basin of maize. Is that fair?` → size question → send `1` → LOW verdict | "Farmers text the offer in their own words. It asks the basin size, converts to a price per kilo and checks this month's market band: low, ask for thirty thousand five hundred." |
| 0:24–0:27 | **English 2:** send `What is the price of beans in Lira?` → band | "They can check a market before selling." |
| 0:27–0:32 | **English 3:** send `maize 1200 kg wakiso` → "Not sure… Ask your co-op or extension officer." | "When the data is too old, it never guesses: not sure, ask your co-op." |
| 0:32–0:38 | **Swahili 1 and 2**, English captions: send `mahindi 1100 kwa kilo gulu` → CHINI, ask 1,750; then `mahindi 1800 kwa kilo gulu` → SAWA | "And it's built for Noor: she can use it in her own language, Swahili." |
| 0:38–0:47 | **Dashboard** `/coop?crop=maize&refresh=2`: first only these messages (4 offers, 1 farmer, Noor's 1,100 in Gulu flagged red). Then 200 synthetic reports stream in (speed up 2–3× in the edit): tiles climb, dots and blue "after reports" bands fill the markets. On-screen label: *"Simulated: 200 synthetic farmer reports"*. | "Every offer also reaches her co-op's dashboard. With two hundred simulated reports, each market's price band updates from what farmers are actually offered." |
| 0:47–0:54 | **Scene 2, video, labelled "Dramatization".** Same market. Noor shows the buyer her phone and counters; he agrees; handshake; she counts the money. | "Now Noor can negotiate a better price, by SMS on the phone she already has. No internet needed. She decides." |
| 0:54–0:59 | **Frame G:** logo, SourceSpot, tagline (`docs/slides/frame_g_end.png`) | "SourceSpot: AI crop-price predictions by SMS, empowering smallholder farmers across developing countries." |

Voice-over: about 150 words, about 59 s at a natural pace (~2.6 words/s), so there is almost no slack under 60 s. If the cut runs long, drop "They can check a market before selling." (~3 s). Record the voice first (Windows Sound Recorder), then fit the video to it in Clipchamp. Paste the messages, and cut the SMS waits in the edit.

**Dashboard shot (0:42–0:51):**
1. Before the take, open `http://localhost:8000/coop?crop=maize&refresh=2` in a second browser window (reloads every 2 s), and a terminal in the repo with this command typed but not run:
   ```bash
   uv run python -m service.seed_demo --n 200 --seconds 15
   ```
2. After Swahili 2, switch to the dashboard. Hold 2–3 s on the "only Noor's messages" state: 4 offers logged, 1 farmer reporting, 3 markets, 1 offer below P10 (Gulu row, red dot).
3. Run the command. In ~15 s the maize tab climbs to about 104 offers, 101 farmers, 26 markets, 20 bands updated, 15 below P10 (the other ~96 offers are beans). The dashboard header says "Includes synthetic demo offers".
4. After the take: `uv run python -m service.seed_demo --reset` removes only the synthetic offers.

Replies on screen (real output, empty database, this order), with captions for Swahili:

English 1
```
How many kg is the basin? Reply 1=15kg 2=20kg
```
```
Maize Arua: 20,000/basin (15kg) = 1,330/kg.
Market price this month: 1,590-2,590/kg.
Offer is LOW (~34% below average). Ask 30,500 per basin.
Next 2 months: prices falling.
Town retail price, not farm-gate. You decide.
```
English 2
```
Beans Lira this month: 2,920-4,480/kg (average 3,730).
Next 2 months: prices steady.
Town retail price.
```
English 3
```
Not sure: last Wakiso market data is 18 months old. Ask your co-op or extension officer.
```
Swahili 1 (`mahindi 1100 kwa kilo gulu`)
```
Mahindi Gulu: 1,100/kg.
Bei ya soko mwezi huu: 1,410-2,190/kg.
Ofa ni CHINI (~38% chini ya wastani). Omba 1,750 kwa kilo.
Miezi 2 ijayo: bei haibadiliki sana.
Bei ya rejareja mjini, si ya shambani. Uamuzi ni wako.
```
*Maize, Gulu: 1,100/kg. Market price this month: 1,410–2,190/kg. The offer is LOW (~38% below average). Ask for 1,750 per kg. Next 2 months: prices steady. Town retail price, not farm-gate. Your decision.*

Swahili 2 (`mahindi 1800 kwa kilo gulu`)
```
Mahindi Gulu: 1,800/kg.
Bei ya soko mwezi huu: 1,410-2,190/kg.
Ofa ni SAWA.
Miezi 2 ijayo: bei haibadiliki sana.
Bei ya rejareja mjini, si ya shambani. Uamuzi ni wako.
```
*Maize, Gulu: 1,800/kg. Market price this month: 1,410–2,190/kg. The offer is FAIR. Next 2 months: prices steady. Town retail price, not farm-gate. Your decision.*

Verdicts are 167–218 characters, so they arrive as **two SMS parts**; the simulator may show one bubble or two. The captions cover the whole text.

**Moved out of the Demo clip (to place in the Tech clip):** the Wi-Fi-off shot (core works offline: `beans 4000 kg jinja` in the local inbox answers FAIR, ask 4,250).

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
| A, the problem | `docs/slides/frame_a_problem.png` | Combined cut, before the Demo clip |
| D, the question | `docs/slides/frame_d_question.png` | Demo 0:09–0:10 |
| E, This is SourceSpot + logo | `docs/slides/frame_e_sourcespot.png` (logo: `docs/slides/logo/sourcespot-mark.svg`) | Demo 0:11–0:13 |
| F, No | `docs/slides/frame_f_no.png` | Demo 0:10–0:11 |
| G, end card: logo, SourceSpot, tagline | `docs/slides/frame_g_end.png` | Demo 0:54–0:59 |
| B, Noor's day + stack | `docs/slides/frame_b_stack.png` | Tech 0:00–0:15 |
| C, backtest | `docs/slides/backtest.png` | Tech 0:15–0:33 |

Frames A, B, D, E, F and G are HTML in `docs/slides/frames/` (D–G use `frame_warm.css`; `render.sh` also works on Windows with Edge). To change the text, edit the HTML and re-render with `bash docs/slides/frames/render.sh` (headless Chrome, throwaway profile). Contents:

- **Frame A (combined cut).** The problem sentence:
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
- **Wrong state:** stop the server, `rm -f data/service.db`, start again (seed only for the Tech clip's dashboard shots).
- **A reply differs from this script:** the database wasn't fresh, or `models/bands.json` changed. Re-run step 1 of "Before recording".
- **No SMS reply in the simulator:** check `/health` shows `"sms_out": true`, and that the sandbox callback matches the *current* tunnel address plus `/sms`. If it still fails, record 0:11–0:51 on the local inbox instead (same messages, same replies).
- **The laptop run fails:** record on https://smallai-agri.vercel.app instead. The examples are on its front page. In that case, drop the Wi-Fi-off line.
- **Backup machine:** Omar's laptop can run the local parts (inbox, Wi-Fi off, dashboard) with the same commands. It has no Africa's Talking keys.

## Facts said on camera, and where they come from
| Claim | Source |
|---|---|
| Newest town prices 6–10 months old | `models/bands.json` `gap_months_h1`; WFP data ends Apr 2026 |
| Prices since 2008, 28 towns | `data/processed/monthly.csv`: Oct 2008 – Apr 2026; 28 markets in the bands |
| Spreadsheet band 69% a year out, ours ~80% | `docs/slides/backtest.csv` (12-month gap: 0.690 vs 0.795) |
| Bands file ~23 KB | inbox footer shows `bands.json` 22.6 KB (Frame B says 21 KB: update) |
| Reply in milliseconds | measured: median 2 ms, max 15 ms per reply on a laptop |
| Rebuild in 30 s | `model/train.py` full run |
| 400K farmers, $70M, P160418 | team's problem statement (`docs/CONCEPT.md`) |
| 200 simulated reports | `service.seed_demo --n 200` (synthetic, tagged `demo` on the dashboard; requires #18) |
