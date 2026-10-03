# Data audit — Kenya (verified Oct 3, 2026, ~7 PM ET)

Sources are the ones named on pages 8–10 and 17 of the World Bank brief, plus what we found behind them.

## Price series (what the band model can learn from)

| Source | What it really is | Freshness | Usable for us? |
|---|---|---|---|
| **WFP Food Prices Kenya** (HDX, CC BY-IGO) `data/raw/wfp_food_prices_ken.csv` | 28,336 rows, 2006-01 → 2026-08, 279 markets, retail + wholesale, units 50 KG / 90 KG / 64 KG / KG | **2024–26 rows are almost all retail in 12 refugee-camp markets** (Dadaab, Kakuma, Kalobeyei). Producing-area wholesale series: Eldoret 20 yrs to 2025-06; Nairobi/Kisumu/Mombasa/Nakuru/Kitui to 2020; Kangemi & Wakulima Nairobi to mid/late 2025; Wakulima Nakuru to 2024-06; Kibuye Kisumu & Kathonzweni Makueni to mid-2026 | **Yes, for seasonality per market.** Weak as a "this week" reference upcountry. State this gap. |
| World Bank Real Time Prices Kenya (HDX, CC BY) | 55K rows, 234 markets, to 2026-08, partly ML-imputed | Only `beans`, `maize_fao`, goat have values; **potatoes/tomatoes/maize columns are empty** | Beans only, and mostly camps. Marginal. |
| FAOSTAT producer prices (HDX mirror `ken-faostat-food-prices`, CC BY-IGO) | Annual national farm-gate, 1991–2025, 71 items with 2024 values | 2024: potatoes 32.1 KES/kg, dry beans 94.1, tomatoes 40.9, maize 62.8, bananas 15.7, avocado 30.9 | Annual anchor and farm-gate vs wholesale spread. |
| KAMIS (kamis.kilimo.go.ke) | Gov't daily wholesale/retail/farm-gate, 5 markets × 47 counties, 150+ products | **Down tonight** (timeouts from two networks; last Wayback 2025-06). amis.co.ke domain lapsed | Cite as the production feed; cannot depend on it. |
| Mkulima Online "Bei za Soko" soko.mkulimaonline.org | Retail + wholesale, 53 markets, web UI only | Up | Possible manual spot-check for the video; no API. |
| FEWS NET Kenya (HDX) | Public JSON = Nairobi only, 6 processed items | to 2026-08 | No. |
| KNBS legacy (HDX) | Gross prices to farmers 2013–17, retail beans/maize 2017–19 (XLSX) | Old | Farm-gate/wholesale spread evidence only. |

### Per-crop depth in WFP (non-camp wholesale, producing-area markets)
| Crop | Best series | Recent (2023+) obs | Verdict |
|---|---|---|---|
| **Potatoes (Irish), 50 KG** | Eldoret 224 obs 2006–2025; Kibuye 47 (→2026-07); Kangemi 44 (→2025-10); Wakulima Nairobi 41 (→2025-06); Kathonzweni 39 (→2026-05); Nakuru 62 (2015–20) | ~120 | Enough for seasonality; no Nyandarua/Meru series |
| **Beans, 90 KG** | Eldoret 257 obs 2006–2025; Kangemi 107 (→2026-07); Wakulima Nakuru 102 (→2024-06); Nairobi/Mombasa/Kisumu 160–170 each to 2020 | ~150 | Richest and most recent; variety mix blurs one band |
| Tomatoes, 64 KG | 2021+ only, ~40 obs per market, 1–2 markets/month in 2026 | ~130 | Too thin and too volatile for a monthly band |
| Maize, 90 KG | Deep (Eldoret 212, Nairobi 170…) | ~60 | NCPB anchoring, large farms. Skip |
| Kale / cabbage / onions | 2021+, 2–4 markets/month | ~100 each | Possible later; no story |

## Smallholder / co-op / price-setting (facts from subagent scan, with sources in the hand-back)
- **Irish potato:** ~800K growers, 2nd crop after maize, Nyandarua 33% of ware potatoes; Crops (Irish Potato) Regulations 2019 cap packaging at 50 kg; brokers' "extended bag" (>110–150 kg at flat price) documented through 2021; High Court upheld the 50 kg rule. Free-market broker pricing at farm gate. Co-ops and NPCK exist.
- **Dry beans:** ~1.5M smallholders, 1.22 Mha, KES 113bn (2023); 94% sell before identifying a buyer, 6% group marketing. Free market, spot sales to brokers.
- **Tomatoes:** mostly smallholders, 70% via informal aggregators, extreme volatility (crate KES 300 → 5,000–10,000).
- **Avoid:** maize (NCPB buying price anchors market), tea/coffee/dairy (auction, co-op or processor pricing, no farm-gate negotiation).
- Kenya is **not** an LSMS-ISA country; closest microdata is KIHBS 2015/16 (KNBS NADA, "public").

## Plant-health image data (for the alternative concept)
- No open image dataset collected in Kenya was found.
- Strongest Kenya-adjacent field set: Tanzania Southern Highlands potato blight, 58,709 smartphone field images, healthy/early/late blight, CC BY (zenodo 8286529).
- PlantVillage (CC0 via Mendeley): potato early/late blight/healthy; tomato ×10; maize ×4. Lab backgrounds; domain shift documented.
- PlantDoc (CC BY 4.0): 2,598 field-ish images incl. potato and tomato classes.
- Makerere iBean (MIT): 1,296 Ugandan field bean images, 3 classes. iCassava: Kaggle.

## Language and SMS
- Swahili: Common Voice (CC0, ~700+ h), FLEURS `sw_ke`, MMS ASR + TTS (`facebook/mms-tts-swh`), MASSIVE `sw-KE` intent data (CC BY 4.0).
- Africa's Talking sandbox: free, simulator at simulator.africastalking.com:1517, SMS + USSD, npm/pip SDKs. Real handsets cannot be used in sandbox.

## Cross-country check of WFP price panels (verified Oct 3, ~7:45 PM ET)
Question raised by another session: is Kenya too sparse, and is Uganda better? Same density analysis run on the WFP/HDX files for Uganda, Ethiopia, Rwanda and Kenya.

| Country | Farmer crops with monthly panels | Town (non-camp) markets reporting | Current to | Price type / unit | Caveat |
|---|---|---|---|---|---|
| **Rwanda** | Potatoes (Irish) 2008–, beans (dry) 2008–, maize 2000–, bananas 2008–, cabbage | 27 towns, ~22 per month through Jul 2026 | 2026-08 (Aug partial) | Retail, KG | Best panel. Gov't has intervened in potato/maize prices at times; verify current regime. e-Soko (gov SMS prices) exists as precedent |
| **Uganda** | Maize (white) 2011–, beans 2006–, sorghum | 28 towns, 35–41 markets/month in 2025 incl. ~25 towns | Towns stop ~Apr 2026; **May–Aug 2026 only 13 refugee settlements** | Retail, KG (wholesale series ended 2022) | Strong 2015–2025 backtest; 2026 reference 4–6 months stale |
| Ethiopia | Maize (white) 85 markets, potatoes 38, fava beans 45, coffee 21 (retail KG) | 56–71 markets/month | 2026-07 | Retail, 100 KG | Dense, but no Africa's Talking, Amharic/Oromo, no team link |
| Kenya | Potatoes, beans, maize (wholesale 50/90 KG bags) | Deep to 2020; 2021–25 sparse; **2024+ almost only 12 camps** | 2026-08 (camps) | Wholesale bags + camp retail | Weakest recent panel; strongest story (50 kg law) and team link |

Implication: for the "evidence it works" backtest and a credible current band, Rwanda > Uganda > Ethiopia > Kenya. For team knowledge and Swahili, Kenya > Uganda > Rwanda.
