# vg-war-rent-split

This is the data and code behind my Venture Global piece, "Venture Global: Its Customers Own The War, Its Shareholders Own The Glut" (October 2026; final version v20). It asks three questions:

1. When the Strait of Hormuz closed and LNG prices rose, who ended up with the spread from Venture Global's plants?
2. How much of the spot price does Venture Global earn on the cargoes it sells itself?
3. What is the stock worth when the futures, the contract market and the coming supply wave all point to a lower fee in the 2030s?

Everything I took from a filing, an exchange or a data provider is in `data/`, with the source next to it. Everything I chose myself is marked ASSUMPTION in the scripts.

## Start here (v20)

- `FULL_REPORT_v20.md` is the full report: the published text plus an appendix with every section cut for length.
- `python scripts/replicate.py` reruns every model from a clean copy and checks the outputs byte for byte. GitHub Actions runs it on every push (`.github/workflows/replicate.yml`).
- `CALLS.md` is the scoreboard for the eight calls. `SOURCES.md` maps every source to the section and chart it supports.
- New in v20: `scripts/model_v20_backtest.py` (2015-2025 backtest, fee curve, approvals response), `scripts/model_v20_supply.py` (forward model with price-responsive approvals, shocks and a prolonged-Hormuz scenario), `scripts/model_v20_addons.py` (valuation of those cases), `data/lng_history_v20.csv`.

## Earlier start-here notes (v17)

Every number in the v17 piece comes from these scripts and from the spreadsheet `vg_model_v10.xlsx`, which uses formulas only and reproduces `model_v10.py` exactly: the annual model, D&A built from the balance sheet, the 2032-2049 tail, the valuation, the grid, the four weighted scenarios and the replacement-cost sheet (20-year and 35-year life). The regime history, CAPM, CP2 delay and judgment audit are in `model_v10.py`; the credit check is in `bond_check.py`. You need Python 3 and nothing else (plus `openpyxl` to rebuild the spreadsheet).

```
cd scripts
python model_v10.py       # valuation, regimes, CAPM, scenarios, sensitivities, CP2 delay, LRMC, judgment audit, EPS readings
python bond_check.py      # implied yield on VG's fixed-rate notes and 2026 new-issue spreads
python model_v11_addons.py # through-cycle shortage share, free cash flow, quarterly estimates Q3 2026E-Q4 2027E
python model_v12_addons.py # share-count consistency, TTF-bias sensitivity, pair payoff by scenario
python model_v13_addons.py # scenarios at CAPM-consistent rates, pair edge decomposition, put spread vs live quotes
python model_v14_addons.py # corrected replacement-cost comps, 2027-28 contracted-fee sensitivity, peer EV/EBITDA, Cheniere exposure range
python model_v17_addons.py # LNG supply-demand balance 2025-40, balance-implied fee paths, Vitol vs strip, Argus merchant premium, fee needed at a new close
python refresh_to_close.py 13.29 # publication-day check: fee needed and returns at a new close (pass a newer CME file once published)
python model_v15_addons.py # contract-fee database, deal-implied returns, options-implied distribution, CQP multiple, merchant exposure, coupon and beta corrections
python waterfall.py       # where the open-cargo cash sits, CP2 restricted payments, parent maturity wall and liquidity
python pair_v7.py         # VG/LNG volatility, correlation, beta, hedge ratio, carry
python war_capture.py     # Q3 split and capture test on the JKM basis (BASIS=ttf for the TTF cross-check)
python last_wave.py       # the fee after the last supply wave, and the size of the next one
python curve_fees.py      # CME settlements -> implied fee by year
python war_rent_split.py  # 2027 split between contract buyers and Venture Global
python option_value.py    # the 20-year contract as an option, with historical and market-implied vol (repo only)
python build_excel_v10.py # rebuilds vg_model_v10.xlsx
python build_excel_v14.py # rebuilds vg_model_v14.xlsx (same model, corrected LRMC comps; current spreadsheet)
```

Other files at the top level:

- `PAIR_TRADE_NOTE.md`: the trade, sized, with carry and the things that would end it.
- `REFRESH_Q3.md`: what to update when Venture Global reports Q3 (expected mid-November 2026). `REFRESH_NOV9.md` is the earlier version.

The prices used are the October 7, 2026 closes: VG 13.05, LNG 272.20.

## What v20 adds (valuation core and target unchanged)

- **Backtest, 2015-2025** (`model_v20_backtest.py`, `results/backtest_v20.txt`): IGU capacity at 84% against trend demand vs the fee paid. Utilisation doesn't separate regimes (correlation +0.22; 2019, a glut, had the highest utilisation). The three-state classifier scores 4/11, so it is replaced by a fitted line: fee = 3.00 - 46.3 x surplus (R^2 0.46 without the 2021-22 shock). A balanced market pays about $3.00, close to developers' $2.68-3.00.
- **Approvals respond to price**: 24.5 Mtpa + 1.28 x last year's fee (IGU approvals 2016-25: ~25/yr after cheap years, ~41 after expensive ones); EIA US contract volumes 2021-25 lead US approvals.
- **Forward model** (`model_v20_supply.py`): fitted fee curve calibrated to the 2028-31 CME strip (surplus offset 8.7%), IEA price response, price-responsive approvals, two-year shocks at a 3/16 annual rate. 2,000 paths per case. Odds the 2032-49 fee clears $4.49: 35% (Shell 0%, midpoint 6%, GECF 100%). Mean fee $3.12 (end-2028 value $9.39). Break-even approvals with shocks: midpoint 22-33 Mtpa/yr (28 at 1% decline), GECF 39-50, Shell 6-17. History-only (no market calibration): mean $1.82, odds 15%.
- **Prolonged Hormuz** (`model_v20_addons.py`): Gulf exports 25% of normal in 2027, 50% in 2028, Ras Laffan repairs to 2030, North Field two years late: end-2028 value $13.61 (+$2.34); severe variant $19.13.
- **Text**: the Seeking Alpha version is cut to ~2,400 words, leads with the approval-pace test and treats the odds as a range driven by demand; CAPM, multiples, options, judgment audit and the trade move to the appendix in `FULL_REPORT_v20.md`.
- **Charts** (unpublished, Datawrapper folder 449514): A769V backtest (new), 3HIh1 supply with price-responsive approvals, lHJ2r approvals needed vs implied, PKP7W scenarios incl. Hormuz, CP2 overrun and new contracts (copy of Uwgsm).

## What v19 adds (valuation and target unchanged)

- **Plant-by-plant supply** (`data/lng_projects_v19.csv`, `scripts/model_v19_supply.py`): 524.5 Mtpa operating at end-2025 (IGU) plus 24 sanctioned projects (249 Mtpa), each with a sourced capacity and start/full-output year; 84% utilisation (IGU 2025); IEA war losses (140 bcm 2026-30) and legacy feed-gas losses; 0-2%/yr legacy decline after 2030; Shell, GECF and midpoint demand rebased to IGU's 437 Mt. Under-construction rows reconcile to IGU's 234.3 Mtpa within 0.3.
- **The test turned around**: the constant pace of new FIDs from 2027 at which the 2032-49 open-cargo fee averages $4.49 (`results/fid_breakeven_v19.csv`). Midpoint demand: ~15 Mtpa/yr (10-20); GECF 19-28; Shell 0-7. History (IGU): 20.6/yr in 2016-20, 41.2/yr in 2021-25.
- **Odds**: across 3 demand paths x 3 decline rates x FID pace uniform on 20.6-41.2, the fee clears $4.49 in ~6% of cases; ~32% with 2011-26-rate shocks on top (an upper bound). Mean flat fee $2.36 ($3.00 with shocks), below the $3.50 used; the base fee is kept because the regime model is blunt (step to a $1 glut fee, no price feedback to FIDs). Robustness under other FID rules in `results/model_v19_supply.txt` section E.
- **Fixes** (`scripts/model_v19_addons.py`): shortage defined (every month of 2011-14, 2021-22, 2026); test without 2011-14 (23% history vs 25% needed, or 14% with 2015-25-like in-between years); CP2 cost overrun +10% = -$0.97 today, -$1.11 end-2028 (+20% about -$2); new China Gas + ConocoPhillips SPAs (1.5 MTPA from 2030) +$0.03.
- **News**: Galp ICC partial award (7 Oct 2026) on liability, damages capped at $170m (`data/arbitration_ledger.csv`). Q3 results date not announced (estimates Nov 9-16).
- **SOURCES.md** maps every source to the section and chart it supports. **CALLS.md** is the scoreboard for the eight calls.
- Charts: 3HIh1 (plant-by-plant supply) replaces ZpuIy; lHJ2r (break-even FID pace) is new.

## What v18 changes

- Final verification fixes to the text only: the demand-path claim now starts in 2028 (supply is below GECF's path in 2026-27); 'no fee reported' instead of 'no buyer has committed'; 1.5 MTPA of new 20-year SPAs since the August deck (China Gas 14 Sep, ConocoPhillips 1 Oct; fees undisclosed) cut the open share to ~36% (43% after medium-term roll-off); Q3 results 'expected around November 9' (not yet announced). Model unchanged.

## What v17 adds (valuation unchanged; SA text cut to ~3,300 words, full-length v16 kept as FULL_REPORT_v16.md)

- **Supply-demand balance** (`data/lng_balance_inputs_v17.csv`, `results/lng_balance_v17.csv`): committed supply (IGU 524.5 MTPA end-2025, Shell ~180 Mt new by 2030, less IEA war losses) reaches ~615 Mt by 2030 against ~480 Mt (Shell path) and ~565 Mt (GECF path) of demand: surplus 8-29%. GECF's path catches committed supply around 2032-33; Shell's not before 2040 (before retirements).
- **Balance-implied fee paths**: glut lasts ($2.75 to 2034, $3.25 after) = flat $3.10, value $7.34 / end-2028 $9.27; GECF ($3.00, then $4.00) = flat $3.70, $9.80 / $12.24. Average $3.40 vs my $3.50.
- **Contract fees reframed**: they show what VG can hedge, not forecasts of spot. Vitol's five-year (~$3) vs a 2027 strip fee of ~$8.71 at signing (Platts: Cal27 JKM 15.125, HH 3.838).
- **Argus merchant premium**: Gulf Coast spot over a 115% HH + $3 contract was +5.37 (2023), +4.63 (2024), +4.11 (2025): a spot fee of ~$7-8, in line with my 2023-25 regime table; the bull's best evidence, from rebalancing years rather than a wave.
- **Governance and insiders** (`data/governance_2026.csv`, `data/insider_form4_2026-06-15_to_2026-09-18.csv`): VG Partners (founders) ~97.6% of the vote, NYSE controlled company. Seven insiders sold 8.97m shares for $124.3m from 15 Jun to 18 Sep 2026, all after option exercises, $96.3m with the Form 4 10b5-1 box checked; founders did not sell.
- **Publication-day refresh** (`scripts/refresh_to_close.py`): at the 8 Oct close of $13.29 the fee needed is $4.55. CME 8 Oct settlements were not yet published when v17 was built.
- **Replication** (`REPLICATION.md`): clean-copy run, 15 outputs match byte for byte.

## What v16 changes

- Rating label only: Seeking Alpha offers Strong Buy / Buy / Hold / Sell / Strong Sell, so the relative call ("Underweight": total return trails the S&P 500 over 24 months) is published as **Sell, moderate conviction**. Target, terms and every number unchanged. Where earlier notes say Underweight, read Sell; where they say Neutral, read Hold.

## What v15 adds (valuation unchanged; evidence that does not rest on my own assumptions)

- **Contract-fee database** (`data/contract_fee_database_v15.csv`): every fee reported on new US LNG contracts since late 2023 (Poten, Reuters, Argus, Platts, VG's own call and deck). On a 115%-of-Henry-Hub basis the highest is about $3.15 (Vitol five-year, signed March 2026, three weeks into the war). None is within $1.30 of the $4.49 the price needs.
- **Deal-implied returns** (`data/deal_economics_v15.csv`): Sempra's Port Arthur FID figures ($1.64bn EBITDA on $13bn, long-term capacity fully contracted) imply a 7.6% unlevered after-tax return over 20 years (8.9% pre-tax). Cheniere trades at ~8.5% EBITDA yield on its CFO's $8bn+ run rate; CQP at ~10.2% on trailing EBITDA. Stonepeak's Louisiana LNG stake is a tolling stream with cost overruns left to Woodside; its return terms are not public.
- **Options-implied distribution** (`data/options_jan2029_chain_2026-10-08.csv`, `results/options_implied_v15.csv`): risk-neutral probabilities from the January 2029 call chain. P(below $8.75) ~45% vs 25% on my weights; P(above $18.75) ~24% vs 10%; median ~$9.80 vs my $11.27 base. Option prices carry a protection premium and the chain is thin (the $12.50 put has 22 contracts open).
- **Peers**: trailing EV/EBITDA (S&P) VG 10.7x, Cheniere 12.0x, Cheniere Partners 9.8x, next to 2026-guidance 8.9x vs 11.6x.
- **Merchant exposure**: Q2 deck, 85 MTPA = 47 long-term / 6 medium-term / 32 available: 38% open today, 45% after medium-term roll-off; the deck expects "a greater proportion of new bolt-on infrastructure to be contracted on a medium-term basis".
- **GECF counterpoint**: levelized cost of proposed North American projects ~$3.8-4.0 vs ~$2.66 for those under construction (May 2026). Added to the LRMC chart and the risks.
- **Corrections** (see below): Sabel's August "make the math work" quote, Street target $16.67, parent-note coupon 8.9%, BP damages hearing, CME open interest disclosure, beta label.

## What v14 adds (valuation unchanged; primary-source pass 8 Oct 2026)

- **Replacement-cost comps corrected** (`data/lrmc_capex_comps_v14.csv`, `results/lrmc_v14.csv`): Rio Grande Phase 1 is $14.9bn ex-financing ($847/t), not the $18.0bn headline; Commonwealth is $13bn ($1,368/t); Corpus Christi Trains 8-9 dropped because Cheniere's FID release gives no cost. Three greenfield comps now need $2.68-3.00 over a 35-year life at 8% ($3.01-3.39 on 20 years); Commonwealth $3.76. The old file `lrmc_capex_comps.csv` is kept for the record and feeds only the v10 outputs.
- **2027-28 contracted fee** (undisclosed; $3.00 / $2.60 assumed): each $1 moves 2027 EPS $0.47, 2028 EPS $0.56 and value today $0.90. Versus $2.45 it adds $0.31. Added to the judgment audit.
- **Peer multiple from primary inputs** (`data/peer_multiple_inputs_2026-10-08.csv`): EV / 2026 guided Adjusted EBITDA, VG 8.85x (diluted cap $34.5bn + net debt $37.8bn + preferred $3.0bn + NCI at book $3.5bn, over $8.9bn) vs Cheniere 11.56x (cap $56.2bn + net debt $22.5bn + CQP units held by others at market $15.5bn, over $8.15bn). VG at Cheniere's multiple: ~$22. Today's VG EV on my 2031 EBITDA ($7.43bn): 10.6x.
- **Cheniere exposure**: its 10-Q says "90% or more" contracted through the mid-2030s (contracts of 10+ years), so $1 of long-run margin is $5.3-10.6 a share (2-4% of price). Pair payoffs barely move (+24.7% vs +24.9% weighted).
- **Spreadsheet**: `vg_model_v14.xlsx` (530 formulas, 0 errors after recalculation) reproduces $8.99 / $4.49 with the corrected LRMC sheet.

## What v13 adds (valuation unchanged; full rerun 8 Oct 2026 matches v12 outputs and the spreadsheet)

- **Rating dependence:** at CAPM-consistent rates (6%/9%) the scenarios are worth $9.01 / $14.92 / $20.83 / $26.02 at end-2028, weighted $15.74 (+23% over 24 months), i.e. roughly fair. The Underweight rests on the 10% open-cargo rate and on the supply wave.
- **Trade edge:** pair weighted +24.9% = VG-specific +5.3 + 1.51x Cheniere expected +20.4 - borrow 0.8 points; two-year volatility ~85%.
- **Put spread vs live quotes** (Yahoo, ~10:40 ET 8 Oct; `data/vg_options_last_2026-10-07.csv`): Jan-2029 $12.50/$10 costs ~$1.20 at mid, $1.55 at the offer; expected payoff on my weights $1.18.
- **Intraday:** VG ~$13.45 on 8 Oct (+3%); the fee the price needs would be ~$4.58. All published numbers stay on 7 Oct closes and settlements, the latest complete data.

## What v12 adds (valuation unchanged)

- **Share count:** per-share values use 2.643bn diluted shares (10-Q Note 16: basic 2,489m + 154m dilutive options). Market value for free-cash-flow yields now uses the same count ($34.5bn): 2027-31 FCF to common $6.6bn = 19%. Without option dilution: $9.51 today, $11.92 end-2028.
- **Headline consistency:** the $4.49 the price needs is 28% above the $3.50 base (replacement cost plus a merchant premium), and needs a 44% shortage share after 2032 vs 43% in 2011-26.
- **TTF-basis bias:** each $1 the 2011-14 shortage fee is understated cuts the required share by ~2.5 points (41% at +$1, 37% at +$3, 33% at +$5).
- **Pair payoff** (`results/pair_payoff_v12.csv`): per $1 short over 24 months, +66% / +31% / -4% / -47% (bear/base/bull/management), weighted +25%; ~21 points of that is 1.51x Cheniere's CAPM expected return; break-even VG +20%.

## What v11 adds (valuation unchanged)

- **Through-cycle test** (`results/model_v11_addons.txt`): shortage months were 43% of 2011-Sep 2026 at an average fee of ~$9.60; the 2015-20 wave averaged $0.45 (TTF basis). The $4.49 the price needs requires shortages 44% of the time if the other years look like 2015-20 (28% if they look like 2015-25). The base case's $3.50 implies about a third. Q3 2026 capture: company fee $6.79 vs spot-equivalent $17.43 (39%).
- **Free cash flow** (`results/fcf_v11.csv`): 2027-31 net income $24.5bn vs free cash flow to common before dividends $6.6bn; yields -8.6%, 1.7%, 8.7%, 10.2%, 8.2% on a $32.6bn market value (2.498bn Class A+B shares).
- **Quarterly estimates** (`results/quarterly_v11.csv`): Q3 2026E EPS $0.54, Q4 $0.47 (consensus $0.53 / $0.48); 2027 by quarter $0.60 / $0.42 / $0.77 / $0.94, summing to the annual $2.73.

## What v10 adds

- **Regimes, not medians:** the fee by market regime (`results/regimes_v10.csv`): 2015-20 supply wave $0.45 (TTF basis) / $1.62 (JKM basis, 2017-20); 2021-22 shortage ~$18.8; 2023-25 ~$6.7-7.3; 2026 ~$10.8-11.9. World trade grew 45% in 2015-19 (IGU); the IEA wave to 2030 is ~42%.
- **Accounting precedent:** the FY2024 10-K says Plaquemines placed $11.4bn of assets in service the month of first LNG, so CP2 cargoes are central-case revenue. The construction-cost reading stays as a sensitivity (2027 EPS $2.73 vs $1.91).
- **CAPM:** beta 0.92 since IPO (daily returns; corrected in v15: weekly is 0.40 and the daily fit explains ~3% of moves), 10-year 5.28%, Damodaran implied ERP 4.20% -> 9.1%, below the 12.1% the base case implies.
- **Discount rates at today's rates:** Calcasieu's April 2036 notes ~1.7 points and VGLNG's June notes ~1.9-2.2 points over the 10-year -> ~7.0% project, ~7.3% parent at 5.28% (`results/bond_check_v10.txt`).
- **Replacement cost over the full life:** 35 years (20 contracted + 15 at the same fee): $2.92-3.05; Commonwealth $3.65. (Corrected in v14 to $2.68-3.00 and $3.76; see above.)
- **CP2 delay:** 6 months $7.44, 12 months $5.90 today.
- **Four weighted scenarios:** bear/base/bull/management at 25/45/20/10; weighted end-2028 $12.04.
- **Judgment audit:** `results/audit_v10.csv`.

**v10 results:** value today 8.99; end-2028 11.27 (target 11.25); the price needs 4.49.

## What v9 added (record)

- **D&A from the balance sheet:** $1.0bn a year on $37.7bn of in-service plant at 30 June 2026 (10-Q Note 5), 2.68% a year, applied to each phase as it enters service (`data/depreciation_inputs_2026-06-30.csv`).
- **Reported vs cash EBITDA:** the 10-Q credits commissioning-cargo proceeds to construction in progress until assets are placed in service, and Consolidated Adjusted EBITDA starts from GAAP net income. CP2's and the bolt-ons' pre-in-service margin is cash but not EBITDA. That's the main step in the 2027 EPS bridge ($2.71 cash basis, $1.91 on the company's definition, consensus $1.00).
- **Discount rates against the market:** VGLNG's new secured notes priced at par at 6.375% (2034) and 6.625% (2036) in June 2026.
- **Replacement cost (LRMC):** the flat 20-year fee a new US project needs at 8% after tax, from announced FID costs (`data/lrmc_capex_comps.csv`): $3.30-3.44, and $4.17 for Commonwealth.
- **Scenarios:** long-run fee $2.50 / $3.50 / $4.50 weighted 30/50/20 (judgement).
- **Symmetric inflation:** fee and costs both rising 2.5% a year, next to the one-sided case.
- **$138bn check:** VG's total contracted third-party revenue implies an average base fixed fee of $2.09-2.67.
- **Pair and options:** Cheniere's exposure per $1 of long-run fee (`data/cheniere_exposure_2026-10-08.csv`) and a January 2029 put spread from last trades (`data/vg_options_last_2026-10-07.csv`).

**v9 results:** value today 8.77; end-2028 11.46 (target 11.50); the price needs 4.54; each $1 of long-run fee is worth 4.11 a share. Scenarios at end-2028: 6.49 / 11.46 / 16.44, weighted 10.97. Sensitivities are in `results/model_v9.txt`.

`model_v8.py` and `vg_model_v8.xlsx` are kept as the v8 record.

## The v8 central case (superseded by v9, kept for the record)

- **Fees:** the CME futures for every year they exist (settlements of October 7, 2026), using Venture Global's own formula (JKM less 115% of Henry Hub less $2): 15.41 for 2027, 8.03 for 2028, 5.12 for 2029, 3.80 for 2030, 2.50 for 2031. Then a long-run fee of 3.50 from 2032, held flat in dollars.
- **Contract escalation:** Venture Global's own convention from the IPO prospectus (424B4, 24 January 2025): 17.5% of the fixed facility charge rises 2.5% a year from the first full year after COD. First escalation year by plant: Calcasieu 2027, Plaquemines Phase 1 2028, Phase 2 2029, CP2 2031/2032. This is the company's illustrative assumption, not a disclosed contract term. The 2032-2049 contracted cash is summed year by year.
- **Costs:** the 2026 calibration is split into an underlying 0.92 per MMBtu plus the Plaquemines basis cost. The company sized that basis cost at 110 million for Q1 and 300 to 350 million for Q2 to Q4, and says it declines in 2028. I keep it for 2027, halve it for 2028 and drop it after that. Costs are held flat in dollars.
- **Interest:** calibrated to the Q2 2026 10-Q. Cash interest 7.52% of net debt ((691 + 46 - 26) x 4 / 37,796); P&L interest cost before capitalization 8.23% ((804 - 26) x 4 / 37,796). Capitalized interest (ASSUMPTION, anchored on Q2's 315m): 1.4bn in 2027, 1.1bn in 2028, 0.6bn in 2029, 0.2bn in 2030, none in 2031. It affects EPS and cash tax only.
- **CP2 contract fees:** 0.40 above Calcasieu's.
- **Discount rates:** 7% for contracted cash and committed capex, 10% for open cargoes.

**Results:**

- Value today: 9.20 a share.
- Value at the end of 2028: 11.49. The 24-month target is 11.50, and it implies about a 12% a year equity return.
- The long-run fee the price needs: 4.44.
- Each $1 of long-run fee is worth 4.11 a share.
- EPS: 1.66 (2026), 2.71 (2027; 2.28 without capitalized interest), 2.94 (2028), 2.34 (2029), 1.12 (2030), 0.34 (2031).

**Sensitivities:**

- Without escalation (the v7 basis on today's curve): 8.33.
- Costs rising 2.5% a year with the long-run fee flat: 4.85.
- With the uncut 2026 cost: 6.01.
- Without the bolt-ons: 7.13.
- CP2 contract premium at 0: 7.91. At the full lender-implied 0.85: 10.65.
- If management's 2029 framework is right: 18.13, and the price would need only 2.26.

`model_v7.py` and `vg_model_v7.xlsx` are kept so the v7 numbers can be reproduced (set `CURVE_FILE` back to `cme_settlements_2026-10-06.csv` and `EURUSD` to 1.1269 in `common.py`). Run on today's curve, `model_v7.py` now writes `results/model_v7_on_current_curve.txt`.

## Legacy scripts (earlier versions, kept as cross-checks)

`sotp.py`, `valuation.py`, `valuation_v6.py`, `eps_path.py`, `three_statement.py`, `pair.py`, `estimates_vs_consensus.py` and `consensus_2027.py` produced the v4 to v6 numbers: the 25/50/25 weights, the $10.79 and $14.48 values, the flat-$3.85 central case and the dollar-neutral pair.

Their output now starts with a LEGACY line. None of their numbers is used in v8. `model_v8.py` imports some of their inputs (volumes, contract fees, capex, net debt), which are unchanged.

`tieout.py`, `q2_decomposition.py`, `firm_start_vitol.py`, `ipo_promise.py` and `peers.py` are unchanged and still current.

## Data added for v7

- `jkm_imf_monthly.csv`: IMF Asia LNG spot series to August 2026, plus my September estimate from JOGMEC's weekly assessments.
- `jkm_proxy_validation.csv`: four checks against the IEA's published JKM figures. Three match closely; the first half of 2025 does not.
- `cost_items_2026.csv`: the Plaquemines basis cost.
- `debt_maturities_liquidity_2026-06-30.csv`: maturities, blended VGLNG coupon, revolvers and cash.
- `cp2_restricted_payment_terms.csv`: the CP2 loan agreement's payout tests.
- `management_2029_framework.csv`: Sabel's March numbers next to the May and August decks.
- `vg_outlook_vintages.csv`: the May and August cargo outlooks side by side.
- `prices_vg_lng_spy_daily.csv`: Yahoo Finance adjusted closes since VG's IPO.
- `pair_stats_inputs.csv`: borrow, dividends and buybacks for the pair.
- `cme_ttf_options_atm_2026-10-06.csv`: TTF option prices used for implied volatility.

## Data and checks added for v8

- `cme_settlements_2026-10-07.csv`: CME settlements for trade date October 7, 2026 (TTF, Henry Hub, JKM, with open interest). `common.py` now points at it, with the ECB EUR/USD rate of October 7 (1.1177).
- Escalation convention: IPO prospectus (424B4, 24 January 2025), definition of "total contracted revenue": https://www.sec.gov/Archives/edgar/data/2007855/000119312525012218/d146310d424b4.htm
- Interest and capitalized interest: Q2 2026 10-Q, Note 8 interest table (total interest cost 804m, capitalized 315m, expense 489m for the quarter): https://www.sec.gov/Archives/edgar/data/2007855/000200785526000062/vg-20260630.htm
- The $3 billion 364-day facility and its lenders: 8-K and Exhibit 99.1 of September 2, 2026 (accession 0002007855-26-000066).
- Re-checked on October 8, 2026: VG and LNG closes (Yahoo Finance), dividends (LNG $0.555 a quarter, VG $0.04), borrow 0.41% with 10 million shares (IBorrowDesk, October 7, 4:43 PM), short interest 43.63 million, 8.36% of float (S&P Global via StockAnalysis), analyst targets (VG $16.78 from 18; LNG $310.57 from 22), consensus EPS (2026 $1.69, 2027 $1.00; Yahoo 2027 $0.997 from 9, $0.908 ninety days earlier), J.P. Morgan's rating (Overweight, $17, June 4, 2026, still its latest action) and the IPO bookrunners (Goldman Sachs, J.P. Morgan and BofA Securities as leads; RBC also a bookrunner).
- `results/eps_path_v8.csv`, `payoff_v8.csv`, `grid_v8.csv`, `model_v8.txt`: the v8 outputs.

## Sources

- Venture Global Q2 2026 10-Q: https://www.sec.gov/Archives/edgar/data/2007855/000200785526000062/vg-20260630.htm
- Venture Global FY2025 10-K: https://www.sec.gov/Archives/edgar/data/2007855/000200785526000013/vg-20251231.htm
- Q3 2026 cargo 8-K (7 October 2026) and Q1 and Q2 2026 cargo 8-Ks: https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0002007855&type=8-K
- Q2 2026 results release: https://investors.ventureglobal.com/news/news-details/2026/Venture-Global-Reports-Second-Quarter-2026-Results/default.aspx
- Q2 2026 investor presentation: https://s205.q4cdn.com/622838971/files/doc_financials/2026/q2/VG-Quarterly-Investor-Presentation_2Q2026_vF.pdf
- Q4 2025 investor deck (69% of 2026 contracted as of 25 Feb 2026): https://s205.q4cdn.com/622838971/files/doc_financials/2025/q4/VG-Quarterly-Investor-Presentation_4Q2025_vF.pdf
- Q1 2026 results release (84% at 4.51; unsold at 9.50 to 10.50): https://www.sec.gov/Archives/edgar/data/2007855/000200785526000042/vgincq12026earningsrelease.htm
- Q4 2025 results release: https://www.sec.gov/Archives/edgar/data/2007855/000200785526000015/vgincq42025earningsrelease.htm
- Q2 2026 earnings call, as transcribed by The Motley Fool: https://www.fool.com/earnings/call-transcripts/2026/08/18/venture-global-vg-q2-2026-earnings-call-transcript/
- Venture Global S-1, December 2024: https://www.sec.gov/Archives/edgar/data/2007855/000119312524282957/d146310ds1.htm
- Insider sales, Forms 4: https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0002007855&type=4
- CME settlements, trade dates October 2, October 6 and October 7, 2026. TTF: https://www.cmegroup.com/markets/energy/natural-gas/dutch-ttf-natural-gas-calendar-month.settlements.html, Henry Hub: https://www.cmegroup.com/markets/energy/natural-gas/natural-gas.settlements.html, JKM: https://www.cmegroup.com/markets/energy/natural-gas/lng-japan-korea-marker-platts-swap.settlements.html
- ECB euro reference rates: https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/eurofxref-graph-usd.en.html
- TTF (IMF, EU natural gas) on FRED: https://fred.stlouisfed.org/series/PNGASEUUSDM
- Henry Hub (EIA) on FRED: https://fred.stlouisfed.org/series/MHHNGSP
- World Bank Pink Sheet (August and September 2026 TTF, September Henry Hub, and a second source for the quarterly averages): https://www.worldbank.org/en/research/commodity-markets
- IMF Asia LNG price via FRED: https://fred.stlouisfed.org/series/PNGASJPUSDA
- Plaquemines Phase 1 customers at FID: https://lngprime.com/americas/venture-global-takes-fid-on-13-2-billion-plaquemines-lng-export-project/52556/
- Share price, consensus, ratings, short interest and peer multiples (S&P Global data): https://stockanalysis.com/stocks/vg/forecast/ and https://stockanalysis.com/stocks/vg/statistics/
- Vitol deal pricing as reported by traders, S&P Global Platts, 26 March 2026: https://www.spglobal.com/energy/en/news-research/latest-news/electric-power/032626-venture-global-vitol-lng-deal-targets-upside-in-2026-27-spot-prices
- Cheniere Q2 2026 call, as transcribed by The Motley Fool: https://www.fool.com/earnings/call-transcripts/2026/08/13/cheniere-energy-lng-q2-2026-earnings-call-transcript/
- CP2 Amended and Restated Common Terms Agreement (Exhibit 10.6 to the Q1 2026 10-Q): https://www.sec.gov/Archives/edgar/data/2007855/000200785526000040/exhibit106-q12026.htm
- Shell NA LNG v Venture Global Calcasieu Pass, NY Sup Ct, 2 March 2026: https://www.nycourts.gov/reporter/pdfs/2026/2026_30753.pdf
- Edison settlement (8-K, 26 March 2026): https://www.sec.gov/Archives/edgar/data/2007855/000200785526000021/pr_finalvgedison.htm
- IEA Gas 2025 press release, 27 October 2025: https://www.iea.org/news/coming-surge-in-lng-production-is-set-to-reshape-global-gas-markets
- IEA Gas Market Report Q3-2026, executive summary: https://www.iea.org/reports/gas-market-report-q3-2026/executive-summary
- IGU 2026 World LNG Report (2025 trade 436.98 Mt), as reported: https://safety4sea.com/igu-world-lng-report-global-lng-trade-hits-record-437-million-tonnes-in-2025/
- IMF Primary Commodity Prices, external-data.xlsx (September 2026 release): https://www.imf.org/en/Research/commodity-prices
- JOGMEC weekly JKM assessments as republished by Global LNG Hub (August to October 2026): https://globallnghub.com/natural-gas-prices-weekly-update-jkm-ttf-and-henry-hub-14-september-2026/
- CME TTF options settlements (product 8694), 6 October 2026: https://www.cmegroup.com/markets/energy/natural-gas/dutch-ttf-natural-gas-calendar-month.settlements.options.html
- Q1 2026 investor presentation (2029 contracted 48%; 'industry low long-term pricing'; CP2 SPAs 18.5 MTPA): https://s205.q4cdn.com/622838971/files/doc_financials/2026/q1/VG-Quarterly-Investor-Presentation_1Q2026_vF.pdf
- Q4 2025 earnings call, as transcribed by The Motley Fool (2029 EBITDA framework; mid-term contract 'north of a $3 net spread'): https://www.fool.com/earnings/call-transcripts/2026/03/02/venture-global-vg-q4-2025-earnings-transcript/
- J.P. Morgan upgrade to Overweight, $17 (4 June 2026), as reported: https://www.insidermonkey.com/blog/venture-global-vg-upgraded-at-jp-morgan-here-is-why-1780162/
- Venture Global Q4 2025 investor deck (2030 cargo target; Q1 2026 basis bridge): https://s205.q4cdn.com/622838971/files/doc_financials/2025/q4/VG-Quarterly-Investor-Presentation_4Q2025_vF.pdf
- Venture Global FY2025 10-K (VGLNG notes 8.716% weighted; restricted net assets; VG Commodities excess-capacity SPAs): https://www.sec.gov/Archives/edgar/data/2007855/000200785526000013/vg-20251231.htm
- Yahoo Finance daily adjusted closes for VG, LNG and SPY (query1.finance.yahoo.com chart API, 7 Oct 2026)
- IBorrowDesk (Interactive Brokers borrow data), VG, 7 Oct 2026: https://iborrowdesk.com/report/VG
- Cheniere Partners Q2 2026 distribution: https://www.sec.gov/Archives/edgar/data/0001383650/000138365026000025/cqp-20260728.htm
- IEA Gas Market Report Q1-2026 executive summary (H1 and H2 2025 Asian spot changes): https://www.iea.org/reports/gas-market-report-q1-2026/executive-summary
- QatarEnergy repair timeline, S&P Global, 19 March 2026: https://www.spglobal.com/energy/en/news-research/latest-news/electric-power/031926-qatarenergy-expects-3-5-years-to-repair-lng-facilities-after-strikes

## Things to be careful with

The long end of the curve is thin. On October 7, CME showed TTF open interest of 10 lots a month in 2028 and none from 2029. JKM has 175 to 215 lots a month through 2029 and none after. Henry Hub is deep. Those later prices are settlement marks, which is why v7 uses a stated long-run fee from 2032 (3.50) after the 2031 mark, shows the whole range on the payoff line and grid, and checks the curve against the Vitol deal and Cheniere.

The Q3 2026 Plaquemines fee is my back-out, not a published number. The capture test has five quarters. Venture Global changed how it measures plant-level fees during 2025, so I only compare numbers on the same basis; Q3 and Q4 2025 are printed for reference and left out of the statistics.

The spot fee in `war_capture.py` and `option_value.py` uses TTF because JKM monthly averages aren't free. Venture Global's deck says JKM rose 56% year on year in Q2 2026, so a JKM version would show it keeping less of the spot price, not more.

The option values assume a normal model with flat volatility taken from annual averages. They show how much the contract is worth to a holder who waits until delivery. They are not a forecast.

I convert TTF at one EURUSD rate for every year. A forward rate would move the TTF fee a little.

The discount rates in `sotp.py` (7% contracted, 10% open, 7% capex), the contracted fee for 2027 (3.00) and 2028 (2.60), the capex path after 2026, D&A for 2027 and the rough tax depreciation are my judgement calls. The script prints what happens when the big ones move.

The all-in cost of 1.147 dollars per MMBtu is calibrated so that 2026 lands on the guidance midpoint. It probably falls as the company gets bigger.

The BP adjustment (half the low end of BP's claim, after tax) is a judgement, not a forecast of the award.

I give no value to CP3 or anything else that isn't on Venture Global's production slide.

The end-2028 value assumes the BP award is paid by then at the same 50%-of-low-end figure, and that the 2029-on business is valued on the same rates. It is a model value, not a forecast of where the stock trades.

The central case and the $11 target are a model value, not a forecast of where the stock trades. Equity values below zero on the payoff line are floored at zero in the chart.

Management's 2029 framework (about 11 billion of EBITDA at a $3 fee) can't be reconciled from the filings: with my volumes it leaves a gap of about 3.1 billion at central costs, of which about 1.1 billion is explained by the larger open volume the March framework implies (its 3 billion per $1 against 1.8-1.9 in the May deck and 2.45-2.5 in August). I show it as a separate line rather than using it.

The waterfall's split between ring-fenced and free volume, the entity interest rates and the timing of CP2's completion are my assumptions. The restricted-payment terms are CP2's; I assume the other projects work similarly, which the 10-K supports only in general terms.

The September 2026 JKM figure is an estimate from week-end assessments described as 'mid-25s' and so on. The same method on TTF lands within 0.16 of the World Bank's September average.

Consensus for 2028 and later isn't public on the free pages, so I don't compare it.

## Corrections

- 9 Oct 2026 (before publication, v15): (1) Sabel's August quote that 20-year contracts are "a requirement to make the math work" was presented as VG's own reason for selling forward; in context he said it of the industry's slow-build model and that VG's bolt-ons will carry more midterm contracts. Rewritten. (2) Street average target $16.67, not $16.78. (3) VGLNG notes due 2029-32 carry a blended 8.87%, not 8.4% (8.38% is all 11.0bn); the $13.4bn window is 2028-32 because the CP2 bridge is due 2028. (4) BP: May 2027 is the damages hearing, not a payment date. (5) CME JKM open interest is zero for 2030-31; disclosed. (6) model_v10.py labelled the 0.92 beta "weekly"; it is the daily figure (weekly 0.40, daily R^2 ~3%). (7) Sabel's $3.50-4.50 refers to long-term contract prices. (8) BofA was a third IPO lead; Morgan Stanley, Citi, UBS and Bernstein are not in the September facility.
- 8 Oct 2026 (before publication): replacement-cost comps corrected in v14 (Rio Grande ex-financing, Commonwealth $13bn, Corpus Christi 8-9 removed) and Cheniere's contracted share restated from "about 95%" to its own "90% or more".
