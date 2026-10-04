# Demo and video script

Target length **about 4:00** (the brief allows 2–5 min). The five sections follow the brief's order. Every reply below was produced by the current `main` on a fresh database, so a clean recording shows exactly these messages.

Links for the form: demo https://smallai-agri.vercel.app · repo https://github.com/omarcontreras96/smallai-agri

## Before recording
1. `git pull` and `uv sync` on `main`.
2. Fresh state: `rm -f data/service.db`. **Do not seed yet**; the seeding happens on camera in scene 3f.
3. Start the service: `uv run uvicorn service.main:app`
4. Browser, zoom 125%, two tabs:
   - `http://localhost:8000/inbox?phone=%2B256700000001` (Noor's phone)
   - `http://localhost:8000/coop`
5. A terminal next to the browser, for the seeding in 3f.
6. Slides 1, 2, 4 and 5 open (see "Slides" below).
7. **Turn Wi-Fi off before section 3** and keep it off for the whole demo, with the icon visible in the menu bar. Everything in section 3 runs offline.
8. Optional: Pepe's Africa's Talking simulator take (scene 3g), recorded separately because it needs internet.

Swahili replies get English subtitles; the subtitle text is given under each reply.

## Section 1. The problem (0:00–0:25), slide 1
On screen: the one-sentence problem, and Noor.

> Because of this tool, a smallholder farmer like Noor will know the fair price band for her maize or beans *before* she accepts a buyer's offer, which she would otherwise do blind; we know because the Côte d'Ivoire E-Agriculture project ($70M, P160418) broadcast prices to 400K farmers and never measured whether anyone received a better price.

Voice-over: "This is Noor. She grows coffee, maize and beans on two hectares in Uganda and carries a basic phone. At harvest a buyer names a price. She has no independent way to know if it's fair."

## Section 2. What the AI does, and why simpler tools fall short (0:25–1:05), slide 2 with `docs/slides/backtest.png`
Voice-over:
- "Three small models, all on a laptop at the co-op. A parser reads messy SMS in Swahili, English and Luganda. A band model forecasts this month's fair price range for each market. A nowcaster updates that range from what farmers report."
- "Why not just text out the latest price list? Because the newest public prices for Ugandan towns are six to ten months old. A spreadsheet that adds historical swings to the last price catches the real price 82% of the time one month out, and only 69% a year out. Our band stays at about 80% at every gap: it widens honestly as the data ages."
- "And a web search gives no per-basin price for maize in Arua, on a basic phone, today."

## Section 3. The tool, end to end (1:05–2:55)
Wi-Fi is off. Noor's phone is the inbox tab.

**3a. A low offer, in Swahili (1:05–1:35).** Type:
```
mahindi 20000 beseni arua
```
Reply: `Beseni ni kilo ngapi? Jibu 1=15kg 2=20kg`. Subtitle: *How many kg is the basin? Reply 1=15kg 2=20kg*

Type `1`. Reply:
```
Mahindi Arua: 20,000/beseni (15kg) = 1,330/kg.
Bei ya soko mwezi huu: 1,590-2,590/kg.
Ofa ni CHINI (~34% chini ya wastani). Omba 30,500 kwa beseni.
Miezi 2 ijayo: bei inashuka.
Bei ya rejareja mjini, si ya shambani. Uamuzi ni wako.
```
Subtitle: *Maize, Arua: 20,000 per 15 kg basin = 1,330/kg. Market price this month: 1,590–2,590/kg. The offer is LOW (~34% below average). Ask for 30,500 per basin. Next 2 months: prices falling. Town retail price, not farm-gate. Your decision.*

Voice-over: "It converts her unit, compares the offer with this month's band, says what to ask for, and where prices are heading. It reminds her the reference is the town market price and that the decision is hers."

**3b. English, per kg (1:35–1:45).** Type `beans 4000 kg jinja`:
```
Beans Jinja: 4,000/kg.
Market price this month: 3,740-4,920/kg.
Offer is FAIR. You can ask 4,250 per kg.
Next 2 months: prices steady.
Town retail price, not farm-gate. You decide.
```

**3c. A Luganda word (1:45–1:55).** Type `kasooli 1500 kilo arua` (kasooli = maize in Luganda):
```
Mahindi Arua: 1,500/kg.
Bei ya soko mwezi huu: 1,590-2,590/kg.
Ofa ni CHINI (~26% chini ya wastani). Omba 2,050 kwa kilo.
Miezi 2 ijayo: bei inashuka.
Bei ya rejareja mjini, si ya shambani. Uamuzi ni wako.
```
Voice-over: "It understands Luganda crop and unit words. It replies in Swahili, because we wouldn't ship Luganda replies we couldn't have checked by a native speaker."

**3d. "Not sure, ask a person" (1:55–2:15).** This is the pass/fail criterion; make it visible.
- Type `maize 1200 kg wakiso`:
  ```
  Not sure: last Wakiso market data is 18 months old. Ask your co-op or extension officer.
  ```
- Type `mahindi 1000 kilo kitgum`:
  ```
  Sijui kwa uhakika: soko 'kitgum' halipo kwenye orodha yetu. Uliza chama au afisa kilimo.
  ```
  Subtitle: *Not sure: the market 'kitgum' is not on our list. Ask your co-op or extension officer.*

Voice-over: "When the data is too old, the band too wide, the market unknown or the message unclear, it says so and points her to a person. It never guesses."

**3e. Offline and small (2:15–2:30).** Point at the Wi-Fi icon (off), then scroll to the inbox footer with the file sizes.

Voice-over: "All of this ran with Wi-Fi off, on a laptop. The price bands are a 21-kilobyte file. A reply takes about two milliseconds. In the field, the same box sits at the co-op with an SMS gateway: no internet, no cloud model."

**3f. The co-op dashboard (2:30–2:55).** In the terminal, run:
```bash
uv run python -m service.seed_demo
```
Voice-over: "Now other farmers report their offers. These are synthetic and labelled 'demo'."

Switch to the `/coop` tab (it opens on maize). Expected tiles: 24 offers logged, 22 farmers reporting, 7 markets with reports, 5 bands updated by reports, 3 offers below P10. The beans tab shows 12 offers, 4 markets, 1 below P10.

Point at three things:
1. **Mbale maize:** its last market data is 17 months old (the "not sure" case), but the band is now refreshed by four farmers' reports.
2. **Red dots:** offers below the band's low end, i.e. buyers the co-op should look at.
3. **Gulu maize:** the band after reports sits well below the model band. Say it plainly: "Farmers report farm-gate offers, and the model knows town retail prices, so reports pull the band down. That gap is real, and the dashboard makes it visible."

(Scripted reply not recommended here: after the reports, `mahindi 1500 kilo mbale` now gets a verdict based on four farmers' reports. Whether two to four reports should reopen a stale market is still an open decision. The dashboard shows the same thing without endorsing it.)

**3g. Optional: the real SMS path (Pepe's take, ~10 s).** Africa's Talking simulator: the same `mahindi 20000 beseni arua` → `1` exchange arriving as SMS. Voice-over: "And through a real SMS gateway, here in Africa's Talking's sandbox."

## Section 4. Where it sits in Noor's day, and the stack (2:55–3:25), slide 4
Voice-over: "Noor uses it at the moment of sale: the buyer is at her gate or she is at the market, and she texts before she agrees. Behind the shortcode, one small box at the co-op runs everything: the parser, the bands and the nowcaster. Once a month someone rebuilds the bands from the WFP price data on a laptop in thirty seconds and copies a 21-kilobyte file over."

Slide 4 layout:
- **Day:** harvest → buyer names a price → SMS → reply in seconds → she decides.
- **Stack:** basic phone → SMS shortcode → Africa's Talking → co-op laptop or Raspberry Pi (FastAPI service: parser, `bands.json`, nowcaster, Swahili/English templates, SQLite log) → co-op dashboard.
- **Monthly:** WFP prices (HDX) → `model/train.py` → `bands.json`.

## Section 5. What localizing AI means to us (3:25–4:00), slide 5
Draft voice-over (team to edit, in your own words):

> "For us, localizing AI is not translating an app. It means:
> - the units people actually sell in (a basin, a tin, a bag), and asking when one is unclear;
> - the words people actually type, in Swahili, English and Luganda, typos included;
> - local reference prices with their holes stated: retail, not farm-gate, and months old. When the data is old, the honest answer is a wider band, not false precision;
> - local people as the fallback: the co-op and the extension officer, not a chatbot;
> - running where the farmer is: a basic phone and a box at the co-op, no cloud.
>
> **[Omar: one or two sentences on the Chiapas coyotes, the buyers who set the price because farmers can't check it, in your own words.]**"

## Slides
| # | Slide | Status |
|---|---|---|
| 1 | The problem sentence + Noor | to make |
| 2 | Why AI: `docs/slides/backtest.png` + three one-liners (stale data, spreadsheet 69% vs ours ~80%, no search answer) | chart done |
| 3 | Data gaps: the table in `docs/EVIDENCE.md` ("What the data does NOT cover"), condensed to five rows | to make |
| 4 | Noor's day + the stack (layout above) | to make |
| 5 | What localizing AI means to us | to make |
| 6 | Moonshot | to make. Draft idea for the team: every co-op runs a price box, and farmers' reports become the first public record of prices *received* at the farm gate, the indicator broadcast projects never measured. |

Slide 3 can replace part of section 2 or follow 3f if time allows; keep the total under 5:00.

## If something breaks while recording
- **Wrong state:** stop the server, `rm -f data/service.db`, start again.
- **A reply differs from this script:** the database wasn't fresh, or `models/bands.json` changed. Re-run from a clean database.
- **The laptop run fails:** record the same messages on https://smallai-agri.vercel.app instead. Each visitor gets a random number there, and the examples are on its front page. In that case, say it's the hosted copy and skip the Wi-Fi-off claim.

## Facts we say on camera, and where they come from
| Claim | Source |
|---|---|
| Newest town prices 6–10 months old | `models/bands.json` `gap_months_h1`; WFP data ends Apr 2026 |
| Spreadsheet band 82% → 69%, ours 79–83% | `docs/slides/backtest.csv` |
| Bands file 21 KB | inbox footer (`models/bands.json`) |
| Reply ~2 ms on a laptop | measured on this script: median 2 ms, max 15 ms |
| Rebuild in ~30 s | `model/train.py` full run |
| 400K farmers, $70M, P160418 | team's problem statement (`docs/CONCEPT.md`) |
