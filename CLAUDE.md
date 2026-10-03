# CLAUDE.md — shared context for every Claude session on this repo

## What we are building
**Decided (Oct 3, 8 PM ET): Uganda, maize + beans. SMS price-band assistant for the moment of sale.** Read docs/BUILD_PLAN.md (workstreams A/B and the interface contract), docs/CONCEPT.md, docs/DATA.md. Owner A (model/evidence) = Omar; owner B (service/parser/dashboard) = Pepe.

A Small AI tool for the World Bank "Small AI for Development" hackathon challenge, Agriculture sector (Annex B). Persona: Noor, 38, 2 ha, coffee + maize + beans, Ondera highlands, member of a coffee cooperative, basic phone + occasional smartphone, 3G bundles, no Wi-Fi. Problem we attack: at harvest a buyer names a price she has no independent reference for (information asymmetry at point of sale).

## Hard rules from the brief (every design decision must respect these)
- Runs on a device the user already has (basic phone / low-end Android).
- Core feature works offline. Model small enough to side-load or send over a weak link.
- At least one interaction in a named local language (voice or text). Expect "how would it fare in a less-supported language?"
- Human makes the final call; tool informs and flags uncertainty. "Not sure, ask a person" fallback is mandatory (pass/fail criterion).
- Cite every dataset: source, license, size, and what it does NOT cover.
- Answer the judges' trap: why would SMS, a spreadsheet or a Google search not do the same job?

## Judging weights
Build works end to end 25% · Development relevance 20% · Data grounding 15% · Evidence it works 15% · Clarity/design/AI value prop 15% · Scalability 10% · Responsible AI pass/fail.

## Submission (by 9 AM ET Oct 4)
1. Prototype (code or link). 2. Video 2–5 min with: one-sentence problem statement in the brief's template, AI capabilities and why simpler tools fall short, end-to-end tool demo, where it sits in the user's day + tech stack, "what localizing AI means to us".

## Conventions
- Time-boxed hackathon: prefer the simplest thing that demos end to end. No speculative abstractions.
- Commit small and often to short-lived branches; squash-merge to main.
- Put decisions in `docs/DECISIONS.md` (one line each) so teammates' sessions stay in sync.
- Never commit secrets; `.env.example` lists required vars.

## Commands
```
uv sync                                   # install
uv run python model/prepare.py            # WFP Uganda -> data/processed/monthly.csv
uv run python model/train.py              # -> models/bands.json, models/metrics.json
uv run uvicorn service.main:app --reload  # SMS service: POST /sms, GET /inbox, GET /coop
uv run pytest                             # parser + nowcast tests
```
Data: `data/raw/wfp_food_prices_uga.csv` (WFP via HDX, CC BY-IGO). Currency UGX, retail prices per KG at town markets. Exclude markets containing "refugee settlement".
