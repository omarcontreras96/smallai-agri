# Concept: SMS price-band service for smallholder sellers

Status: consolidated from the team's chat session (Oct 3, ~2–5 PM ET). Items marked **PROPOSED** still need a team yes.

## One-sentence problem (brief's template)
Because of this tool, a smallholder farmer like Noor will know the fair price band for her crop *before* she accepts a broker's offer at the farm gate, which she would otherwise do blind; we know because the Côte d'Ivoire E-Agriculture project ($70M, P160418) broadcast prices to 400K farmers and never measured whether anyone received a better price.

## What it is
Noor texts a shortcode from her basic phone: crop, offered price, unit, market. The service replies with the expected price band for this week and the coming days, a verdict (low / fair / good), a suggested counter, and the co-op's own buying price and day as an outside option. When unsure it says so and points to a person.

## Why not a lookup / SMS broadcast / spreadsheet (the judges' trap)
- Public price series are weeks old and per kg; brokers quote per bag today. The tool projects a band through seasonality and converts local units.
- Each farmer-reported offer updates the band for that market (nowcasting), building the price-received indicator no project has.
- Messages arrive in Swahili, English, Sheng, with local units and buyer claims; regex does not survive that input.

## Rules compliance (brief section 06)
| Rule | How |
|---|---|
| Runs on a device she has | Basic phone, SMS |
| Core works offline | Models run on one box at the co-op (Android phone / Pi with SIM). Needs cell signal only, no internet. Store-and-forward when signal drops |
| Model files small | Parser sub-1B quantized (hundreds of MB); band model is kilobytes |
| Local language | Swahili replies from fixed templates; parser handles Swahili/English/Sheng input. Less-supported fallback answer: Kikuyu/Kalenjin via same templates |
| Human in the loop | Wide band or unknown market → "Sijui kwa uhakika. Uliza chama" (not sure, ask the co-op). Farmer decides; co-op shown as one option, not referee |
| No hallucination | Replies composed from a fixed answer list, never free generation to the farmer |

## Architecture (Small AI, three small models)
1. **Parser** (only LM): Gemma 3 270M or Qwen 2.5 0.5B, quantized, few-shot/fine-tuned on a few hundred synthetic messages → JSON {crop, price, unit, qty, market, claim}. Deterministic unit table (gunia, debe, gorogoro, kg); ambiguous bag size → one clarifying question.
2. **Band model**: per crop × market quantile regression on WFP history (month, market, last price, months since obs, trend) → P25–P75 band for this week and next two.
3. **Nowcaster**: Bayesian update of the band from farmer-reported offers; feeds a co-op dashboard and flags under-paying buyers/areas.
Reply composer: fixed Swahili/English templates.

Interface for demo: Africa's Talking SMS/USSD sandbox (free, has a phone simulator). Fallback: simulated SMS thread in a web UI on a phone, airplane mode on camera. Production story: GSM modem at the co-op.

## Country and crop — DECIDED (Oct 3, 8 PM ET): Uganda, maize + beans
See docs/DATA.md cross-country table and docs/BUILD_PLAN.md. The Kenya/potato analysis below is kept for the record.

### Earlier proposal (superseded)
- **Kenya.** WFP/HDX series live through Aug 2026, 28K rows: dry beans 40 markets, maize 35, Irish potatoes 37, tomatoes 22. Mexico's series stopped June 2022. Swahili well supported (Common Voice, FLEURS, MMS). Africa's Talking is Nairobi-based. Pepe has ground truth from sourcing from Kenyan farms.
- **Irish potatoes** as core, **beans** riding along on the same pipeline. Potatoes: ~800K smallholders, co-ops in Nyandarua/Meru/Nakuru, brokers at farm gate, and the "extended bag" asymmetry (110–150 kg bags priced as 50 kg; 2019 law poorly enforced). Avoid maize (NCPB floor + large farms). Tomatoes as stretch.
- Mexico (Chiapas, coyotes) kept for the "what localizing AI means to us" section.
- Precedent to position against: M-Farm (Kenya, 2010s) sent last known price; we send a negotiating band for a specific offer.

## Sample exchange (video)
```
Noor:  mahindi 900 beseni mbale
Tool:  Beseni ya kg ngapi? 1=15kg 2=20kg
Noor:  1
Tool:  900/15kg = 60/kg. Bei ya soko Mbale mwezi huu: 650-850/kg (rejareja).
       Ofa ni CHINI (~20%). Omba 11000 kwa beseni. Mwezi ujao: inapanda kidogo.
       Bei ya soko si bei ya shambani; uliza chama kabla ya kuuza.
```
Plus one exchange where the tool says it is not sure.

## Evidence plan (15% of score)
- Backtest band on held-out 2025–26 months: coverage share.
- Parser accuracy on ~200 synthetic test messages.
- Reply latency and model file sizes on the box, shown on a slide.
- Stated gaps: WFP is monthly retail, not farm gate; nowcaster closes it but is unvalidated; KAMIS daily prices unreachable at build time.

## Data sources (cite source, year, country, license, gaps)
WFP Food Prices Kenya (HDX) · LSMS-ISA · FAOSTAT · Common Voice / FLEURS / MMS (Swahili) · MASSIVE (intent template) · GSMA Mobile Gender Gap · P160418 ICR + IEG review (evidence the gap is real) · AgriConnect page.

## Milestones (ET)
- 7 PM: data pulled, band model trained, parser returning JSON on sample messages.
- 11 PM: full SMS flow in sandbox incl. clarifying question, fail-safe, logging.
- 2 AM: co-op dashboard on logged offers (synthetic, labeled), Swahili templates reviewed.
- 3 AM: freeze, record 2–5 min video. 8 AM: submit.
