# Sources, and where each one is used (final v20, 9 Oct 2026)

Section names follow the Seeking Alpha version (SA v19). "X" refers to the X version (v19). Every number traces to a source below, or to a script in `scripts/` whose output sits in `results/`. Where I don't have a stable link, the source is named with its date.

## Final v20: section map and new sources

Sections of the final Seeking Alpha text: Opening; The Customers Own The War; The Fee Depends On The Regime; The Wave, Plant By Plant; Testing The Model On 2015-2025; What The 2030s Need From New Plants; What Venture Global Can Lock In, And What A New Plant Needs; Valuation And Price Target; Scenarios And Risks; Earnings Aren't Cash; So. The tables below use the v19 section names; their content moved as follows: "Shortage Test" is now the second paragraph of The Fee Depends On The Regime; "What A New Plant Needs" is merged into What Venture Global Can Lock In; "Management's Number", "Balance Sheet, Governance" and "Risks To The Rating" are folded into Scenarios And Risks and Earnings Aren't Cash; CAPM, multiples, options, judgment audit and the trade are in full in FULL_REPORT_v20.md (appendix A4-A8).

| Source | What it supports | Where it goes |
|---|---|---|
| IGU World LNG Reports, 2016-2026 editions (capacity, trade, utilisation, approvals by year), e.g. 2020 edition https://aglaw.psu.edu/wp-content/uploads/2020/06/2020-World-LNG-Report.pdf, 2021 edition https://naturgas.com.co/wp-content/uploads/2021/07/IGU_WorldLNG_2021_compressed.pdf, 2024 edition https://safety4sea.com/wp-content/uploads/2024/06/IGU-2024-LNG-Report_Final_LR_2024_06.pdf, 2025 summary https://safety4sea.com/igu-world-lng-report-lng-trade-grew-by-2-4-in-2024/, 2017 release https://www.igu.org/news/igu-releases-2017-world-lng-report | 2015-2025 backtest; approvals 20.6/41.2 and year-by-year; fee curve | Opening; Testing The Model; What The 2030s Need; Charts 5 (A769V) and 6 (lHJ2r); data/lng_history_v20.csv |
| GIIGNL Annual Report 2015 (nameplate 298 Mtpa end-2014) | 2015 average capacity | Backtest; data/lng_history_v20.csv |
| EIA Today in Energy, 3 Mar 2026 https://www.eia.gov/todayinenergy/detail.php?id=67264 | US contract volumes 2021-25 (54 Mt in 2022, 40 Mt in 2025) | What The 2030s Need |
| IEA, LNG Market Trends and their implications (2015 approvals, ~25 bcm) | 2015 approvals | data/lng_history_v20.csv |
| Euronews, 9 Oct 2026 https://www.euronews.com/2026/10/09/qatarenergys-lng-expansion-targets-early-2027-production-amid-reports-of-3bn-loan | Hormuz transits ~75% below February in September; North Field East targeting early 2027 | Scenarios And Risks; X risks line |
| Egypt Oil & Gas / Reuters, 6 Oct 2026 https://egyptoil-gas.com/news/qatar-lng-cargoes-resume-strait-of-hormuz-transits/ ; QatarEnergy warning (21 Sep 2026) https://egyptoil-gas.com/news/qatarenergy-warns-hormuz-crisis-could-delay-lng-expansion-projects/ ; Bloomberg on force majeure into October https://www.bloomberg.com/news/articles/2026-08-28/qatar-extends-lng-force-majeure-as-hormuz-traffic-remains-halted | Hormuz status; expansion delay risk; force majeure | Scenarios And Risks; Hormuz scenario assumptions |
| scripts/model_v20_backtest.py, model_v20_supply.py, model_v20_addons.py | Fee curve, approvals rule, odds 35% (0/6/100%), mean fee $3.12 -> $9.39, break-even 22-33, Hormuz $13.61 / $19.13 | Opening; Testing; What The 2030s Need; Scenarios And Risks; Charts 4, 5, 6, 9 |

Final chart list (unpublished, Datawrapper folder 449514): 1 pCkRq glance, 2 gYAn7 Q3 split, 3 OPSnE regimes, 4 3HIh1 plant-by-plant supply, 5 A769V backtest (new), 6 lHJ2r approvals needed vs implied, 7 oYIPi contract fees, 8 LnQ27 replacement cost, 9 PKP7W scenarios incl. Hormuz (new copy of Uwgsm), 10 cu3SO earnings. Appendix only: tJdmX judgment audit, dkif7 trade.

## Market data (prices, curves, consensus)

| Source | What it supports | Where it goes |
|---|---|---|
| NYSE closes via StockAnalysis / S&P Global Market Intelligence, https://stockanalysis.com/stocks/vg/history/ | VG $13.05 (Oct 7), $13.29 (Oct 8) | Opening; Disclosures; Chart 1; X line 1 |
| CME settlements, Oct 7 2026: JKM https://www.cmegroup.com/markets/energy/natural-gas/lng-japan-korea-marker-platts-swap.settlements.html, Henry Hub https://www.cmegroup.com/markets/energy/natural-gas/natural-gas.settlements.html, TTF https://www.cmegroup.com/markets/energy/natural-gas/dutch-ttf-natural-gas-calendar-month.settlements.html | Implied fee 15.41 / 8.03 / 5.12 / 3.80 / 2.50; open interest | Fee Depends On The Regime (futures paragraph); Wave Plant By Plant (para 2); Earnings; Chart 3; X futures line |
| IMF primary commodity prices https://www.imf.org/en/Research/commodity-prices and FRED (https://fred.stlouisfed.org/series/PNGASEUUSDM, https://fred.stlouisfed.org/series/PNGASJPUSDA, https://fred.stlouisfed.org/series/MHHNGSP) | Fee by regime 2011-2026; shortage test (43%, 23%, $9.60, $16.60) | Opening; Fee Depends On The Regime; Shortage Test; Chart 3; X para 2 |
| ECB reference rate https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/eurofxref-graph-usd.en.html | EUR/USD for TTF conversion | Model only |
| S&P Global consensus via StockAnalysis https://stockanalysis.com/stocks/vg/forecast/ and Yahoo Finance | 18 analysts, average target $16.67, EPS consensus | Risks (Street paragraph); Earnings; Chart 10 |
| Yahoo Finance / Damodaran Online (Oct 1) | 10-year 5.28%, ERP, beta | Valuation (discount-rate paragraphs) |
| Options chain, Jan 2029 (Oct 8 quotes) | 45% / 24% / median $9.80; put spread | Scenarios; The Trade; Charts 8 and 11 |
| iBorrowDesk https://iborrowdesk.com/report/VG | Borrow 0.41% | The Trade |

## Venture Global primary sources

| Source | What it supports | Where it goes |
|---|---|---|
| Q3 cargo 8-K (Oct 7 2026) | 465.8 TBtu, $6.79 fee | The Customers Own The War; Chart 2; X Q3 line |
| Q2 2026 10-Q https://www.sec.gov/Archives/edgar/data/2007855/000200785526000062/vg-20260630.htm | Diluted shares 2.643bn, debt, cash $3.1bn, arbitration caps $425m, BP claim | Valuation; Balance Sheet; Risks |
| FY2025 10-K https://www.sec.gov/Archives/edgar/data/2007855/000200785526000013/vg-20251231.htm and prospectus https://www.sec.gov/Archives/edgar/data/2007855/000119312525012218/d146310d424b4.htm | "may be uncorrelated" quote; Plaquemines "$11.4 billion of costs" | Customers Own The War; Earnings |
| Investor decks Q4 2025, Q1 2026, Q2 2026 (https://s205.q4cdn.com/622838971/files/doc_financials/2026/q2/VG-Quarterly-Investor-Presentation_2Q2026_vF.pdf) | 47/6/32 MTPA split, contracted share, fee slide ($5.19 median), escalation convention, cost basis, CP2 timing | Customers Own The War; Fee Regime; Valuation; Chart 1 |
| Earnings call transcripts (Motley Fool): Q4 2025 https://www.fool.com/earnings/call-transcripts/2026/03/02/venture-global-vg-q4-2025-earnings-transcript/ and Q2 2026 https://www.fool.com/earnings/call-transcripts/2026/08/18/venture-global-vg-q2-2026-earnings-call-transcript/ | Sabel quotes ("make the math work", "$3.50 to $4.50 minimum", "about $11 billion") | Customers Own The War; What A New Plant Needs; Management's Number |
| VG / Business Wire releases, Sep 14 (China Gas) and Oct 1 (ConocoPhillips) 2026, https://www.businesswire.com/news/home/20261001098196/en/ | 1.5 MTPA of new 20-year SPAs from 2030 (+$0.03/share, model) | Customers Own The War (bolt-on paragraph); X para 4 |
| VG 8-K Oct 8 2026 (ICC partial final award, Oct 7), reported by Reuters https://www.reuters.com/business/venture-global-breached-lng-supply-deal-with-galp-tribunal-rules-2026-10-08/ | Galp liability finding; damages hearing 2027-28; $170m cap | Risks To The Rating; X risks line |
| Form 4s https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0002007855&type=4 (data/insider_form4_2026-06-15_to_2026-09-18.csv) | 9.0m shares, $124m, 7 insiders | Governance |
| Proxy / 10-K governance (data/governance_2026.csv) | Class B 1.97bn, 97.6% of vote, controlled company | Governance |
| Bloomberg via Reuters (Oct 6 2026) | Talks with more Chinese buyers | Customers Own The War |

## LNG supply, demand and costs

| Source | What it supports | Where it goes |
|---|---|---|
| IGU World LNG Report 2026 (summary: https://safety4sea.com/igu-world-lng-report-global-lng-trade-hits-record-437-million-tonnes-in-2025/) | 524.5 MTPA operating end-2025; 83.9% utilisation; 437 Mt trade; 234.3 MTPA under construction; 68.4 MTPA FID in 2025; 206 MTPA FID in 2021-25, "double" 2016-20; 1,105.4 MTPA pre-FID; mid-2030s rebalancing narrative | Wave Plant By Plant (all three paragraphs); Charts 4 and 5; X supply lines |
| Project developers and trade press, one row per project in `data/lng_projects_v19.csv` (Sempra, NextDecade, Woodside, QatarEnergy via Reuters/OGJ/NGI, Cheniere, LNG Canada/RBN, Woodfibre, Cedar, Sempra ECA, NLNG via Reuters, ADNOC via The National, TotalEnergies, Eni, Southern Energy/Golar, Caturus, Delfin, VG decks; S&P Global for Golden Pass) | Capacity and start/full-output year of 24 sanctioned projects (249 MTPA) | Wave Plant By Plant (para 1); Chart 4 |
| IEA Gas 2025 (Oct 2025) https://www.iea.org/news/coming-surge-in-lng-production-is-set-to-reshape-global-gas-markets | Legacy feed-gas losses ~20 bcm/yr by 2030; price-driven demand +65 bcm by 2030; Arctic LNG 2 excluded | Wave Plant By Plant (paras 1-2); model |
| IEA Gas Market Report Q3-2026 https://www.iea.org/reports/gas-market-report-q3-2026/executive-summary | War losses ~140 bcm 2026-30, 54 bcm in 2026 | Wave Plant By Plant (para 1); Chart 4 |
| S&P Global (Mar 19 2026) https://www.spglobal.com/energy/en/news-research/latest-news/electric-power/031926-qatarenergy-expects-3-5-years-to-repair-lng-facilities-after-strikes and LNG Prime / QatarEnergy (Sep 2026) | Ras Laffan repair: 3-5 years, later "three years" | Wave Plant By Plant; Risks |
| Shell LNG Outlook 2026 (via SAFETY4SEA) | Demand +65% 2025-2050 | Wave Plant By Plant (para 2); Charts 4 and 5 |
| GECF expert commentary (May 2026) | Demand ~700 Mt 2035, ~785 Mt 2040; North American next-tranche cost ~$3.80-4.00 | Wave Plant By Plant; What A New Plant Needs; Charts 4, 5, 7 |
| Developers' FID releases (Woodside, NextDecade, Sempra, Caturus) (data/lrmc_capex_comps_v14.csv) | Cost per tonne; replacement-cost fees $2.68-3.00, $3.76 | What A New Plant Needs; Chart 7 |
| Poten (2023, 2025), Reuters (Nov 2025), Argus (Dec 5 2025), S&P Global Platts (Mar 26 2026) https://www.spglobal.com/energy/en/news-research/latest-news/electric-power/032626-venture-global-vitol-lng-deal-targets-upside-in-2026-27-spot-prices (data/contract_fee_database_v15.csv) | Contract fees $2.30-3.15; Argus spot premium 2023-25; Vitol strip $8.71 | What VG Can Lock In; Fee Regime; Chart 6; X lock-in line |

## Valuation cross-checks

| Source | What it supports | Where it goes |
|---|---|---|
| Sempra Port Arthur FID figures; Cheniere Q2 2026 call https://www.fool.com/earnings/call-transcripts/2026/08/13/cheniere-energy-lng-q2-2026-earnings-call-transcript/ (data/deal_economics_v15.csv) | 7.6% unlevered after-tax; 8.5% EBITDA yield | Valuation (para 1) |
| Cheniere / CQP filings https://www.sec.gov/Archives/edgar/data/0001383650/000138365026000025/cqp-20260728.htm (data/peer_multiple_inputs_2026-10-08.csv) | Multiples 11.6x, 12.0x, 9.8x | Valuation (multiples paragraph) |
| J.P. Morgan rating via Insider Monkey https://www.insidermonkey.com/blog/venture-global-vg-upgraded-at-jp-morgan-here-is-why-1780162/ | Overweight, $17, "outsized" | Risks |
| NY court decision https://www.nycourts.gov/reporter/pdfs/2026/2026_30753.pdf and 10-Q | BP claim range, May 2027 hearing | Risks; Catalysts |

## Author calculations (scripts, results)

| Script | Output used | Where it goes |
|---|---|---|
| scripts/model_v10.py | $8.99 today, $11.27 end-2028, $4.49 needed, scenarios, CAPM case | Valuation; Scenarios; Charts 1, 8, 9 |
| scripts/model_v11_addons.py, model_v19_addons.py (section 1) | Shortage test, with and without 2011-14 | Opening; Shortage Test |
| scripts/model_v19_supply.py | Plant-by-plant balance; break-even approval pace; odds 6% / 32%; flat fees $2.36 / $3.00 | Wave Plant By Plant; Charts 4 and 5; X |
| scripts/model_v19_addons.py (sections 2-4) | CP2 overrun (-$0.97 today, -$1.11 end-2028); new SPAs (+$0.03); value at $3.90 ($13.25) | Customers Own The War; Scenarios; Wave Plant By Plant; X |
| scripts/model_v15_addons.py, model_v17_addons.py | Contract fees, options, multiples, Vitol strip, Argus | as listed above |

## Charts (all unpublished, Datawrapper folder 449514)

1 pCkRq glance · 2 gYAn7 Q3 split · 3 OPSnE regimes · 4 3HIh1 plant-by-plant supply (new) · 5 lHJ2r break-even approval pace (new) · 6 oYIPi contract fees · 7 LnQ27 replacement cost · 8 Uwgsm scenarios · 9 tJdmX judgment audit · 10 cu3SO earnings · 11 dkif7 trade. ZpuIy (v17 balance) is retired, not deleted.
