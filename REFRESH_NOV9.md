# Refresh kit: Venture Global Q3 2026 results (expected 9 November 2026)

The v15 piece is written on data to October 7 (CME settlements of October 7; consensus checked October 8). The Q3 deck replaces two of its estimates with reported numbers and tests two calls. Work through the steps in order, then re-run `scripts/` and `build_excel_v14.py`.

## 1. Inputs to update

| What | Where it comes from | File to edit |
|---|---|---|
| Plaquemines Q3 2026 weighted average liquefaction fee | Q3 deck, Plaquemines appendix slide. Replaces my back-out of 8.65 (range 8.62–8.68). | `data/vg_fee_history.csv` (add `plaq_q3_2026_new`), then make `war_capture.py` use it in place of `plaq_q3_2026()` |
| Calcasieu Q3 2026 fee | Q3 deck, Calcasieu slide | `data/vg_fee_history.csv` |
| 2026 guidance (EBITDA range, unsold-cargo fee assumption, $1 sensitivity, contracted %) | Q3 release | `data/vg_balance_sheet_2026-06-30.csv` (guide rows), `data/vg_outlook_slide23.csv` (2026 row) |
| 2027–2029 cargo outlook, $1 sensitivities, contracted % | Q3 deck, production outlook slide | `data/vg_outlook_slide23.csv`, and append a row to `data/vg_outlook_vintages.csv` |
| Plaquemines basis cost commentary | Q3 deck and call | `data/cost_items_2026.csv`, `BASIS` in `model_v10.py` |
| Q3 balance sheet: debt by entity, cash, PP&E; interest table (total cost, capitalized) | Q3 10-Q (recalibrate `CASH_RATE`, `PL_RATE` and `CAPI` in `model_v8.py`, which `model_v10.py` imports) | `data/debt_by_entity_*.csv`, `data/debt_maturities_liquidity_*.csv`, `data/vg_balance_sheet_*.csv` |
| CME settlements | cmegroup.com settlements, trade date = the day before publication | new `data/cme_settlements_YYYY-MM-DD.csv`; point `CURVE_FILE` in `common.py` at it |
| September JKM from the IMF | IMF external-data.xlsx (October release) | replace my 26.6 estimate in `data/jkm_imf_monthly.csv` |
| Share prices | close before publication | `data/vg_balance_sheet_*.csv` (`PRICE_KEY` in `common.py`), `data/pair_2026-10-07.csv`, `data/prices_vg_lng_spy_daily.csv` |
| Commissioning accounting | Q3 10-Q: when CP2 assets are placed in service; whether Q3/Q4 Plaquemines cargoes were revenue or CIP credits | `CIP_TBTU` and the D&A additions in `model_v10.py` |
| Total contracted third-party revenue | Q3 deck | re-run the $138bn check in `model_v10.py` |
| Q3 2026 actuals vs my Q3E (EPS $0.54, EBITDA $2.63bn) | Q3 release | `scripts/model_v11_addons.py` |

## 2. Calls to score or check

| Call | Rule | Action |
|---|---|---|
| #233 | 2026 EBITDA guidance midpoint above $8.9bn | Resolves at the Q3 release. Score it. |
| #232 | Plaquemines Q4 fee below Q3 | Record the reported Q3 fee as the baseline. Resolves on the Q4 deck. |
| #236 | 2029 contracted share below 50% | Resolves on the Q4 deck. Note the Q3 deck reading. |
| #231 / #238 | pair and Sell (was Underweight) | Reset entry prices to the close before publication if not yet published. |

## 3. What would change the view

- **2029 contracted share jumps** (above about 50%) at disclosed or reported fees above $4.49: move toward Hold.
- **Management restates the 2029 framework with volumes and costs:** rebuild the reconciliation in `model_v10.py`.
- **Phase 1 COD slips:** Q4 call #232 weakens. The BP and arbitration exposure gets worse.

## 4. Publication timing

The piece can run now or after November 9.

- **Now:** the likely guidance raise lands on a fresh call.
- **After the 9th:** the Q3 deck replaces my back-out with a reported number, and the entry price includes the guidance reaction.

That is the author's call.


## Added in v14

- If the Q3 deck or call gives a weighted fee on contracted 2027 volume, replace `CONTRACT_FEE[2027]` ($3.00 assumed) in `valuation.py` and rerun `model_v14_addons.py`: each $1 is $0.47 of 2027 EPS and $0.90 of value.
- Update the peer multiple with Q3 balance sheets and any guidance change (`data/peer_multiple_inputs_2026-10-08.csv`); Cheniere reports October 29.


## Added in v15

- Add any new reported contract fee (Q3 call, Platts, Reuters) to `data/contract_fee_database_v15.csv` and rerun `model_v15_addons.py`; a fee at or above $4.49 on 2029-31 volume resolves call #237 as a loss.
- Re-pull the January 2029 option chain into `data/options_jan2029_chain_*.csv` and rerun the options-implied distribution.
- Update CQP and Cheniere trailing EBITDA after their October 29 results.


## Added in v17

- On publication day run `python refresh_to_close.py <close> <cme_file>` and update the price, the fee needed and the returns in the text.
- Re-pull Form 4s since 18 Sep 2026 and update `data/insider_form4_*.csv`.
- If Shell, IGU, IEA (Gas 2026, due in October) or GECF publish new supply or demand numbers, update `data/lng_balance_inputs_v17.csv` and rerun `model_v17_addons.py`.
