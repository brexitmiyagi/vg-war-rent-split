"""A summary three-statement model, 2026-2031, on the central case (market-implied open fee:
CME futures for 2027-28, then the 2029-31 futures average flat; CP2 contract fees +0.40 from 2030).

Income statement: EBITDA -> D&A -> interest -> tax -> preferred and minority -> net income to common.
Cash flow: EBITDA - interest - cash tax - capex - preferred - minority - common dividend = change in net debt.
Balance sheet (summary): net PP&E rolls with capex less D&A; net debt rolls with free cash flow;
book equity rolls with net income less common dividends. 2026 opening balances from the Q2 2026 10-Q
are approximate: the model starts from my end-2026 net debt estimate (valuation.py), not a reported number.
ASSUMPTIONS as in valuation.py and eps_path.py; dividends at $0.04 a quarter on 2.498bn shares.
"""
LEGACY_NOTE = "LEGACY cross-check from an earlier version (v4-v6). The v7 numbers used in the piece are in results/model_v7.txt, waterfall.txt and pair_v7.txt.\n"
import os, io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    import valuation as V
    import sotp as S
    from eps_path import DA, INTEREST_2026
from common import RESULTS

fut_avg = sum(S.jk[y] for y in (2029, 2030, 2031)) / 3
fee = {**S.jk, 2029: fut_avg, 2030: fut_avg, 2031: fut_avg}
DIV = 0.04 * 4 * 2.498
# net PP&E: 30 Jun 2026 (10-Q) plus H2 capex (13.0 guide less 6.9 spent) less H2 D&A (half of 1.05)
PPE0 = V.bs["ppe_net_2026-06-30"] / 1000 + (V.bs["capex_2026_guide"] - V.bs["capex_h1_2026"]) / 1000 - DA[2026] / 2
EQ0 = 0.0       # book equity shown as the cumulative change from end-2026 (30 Jun 2026 total equity was 12.08bn incl. NCI)
rows = []
nd, ppe, eq = V.ND0, PPE0, EQ0
for i, y in enumerate(V.YEARS):
    con = V.vol[y] - V.open_tbtu[y]
    ebitda = (con * V.CONTRACT_FEE[y] + V.open_tbtu[y] * fee[y] - V.COST * V.vol[y]) / 1000
    if y >= 2030:
        ebitda += max(0.0, con - 1560) * 0.40 / 1000
    interest = nd * V.DEBT_COST
    ebt = ebitda - DA[y] - interest
    tax = V.TAX * max(0.0, ebt)
    ni = ebt - tax - V.PREF - V.NCI
    eps = ni / V.SHARES
    cash_tax = V.TAX * max(0.0, ebitda - interest - (1.0 + 0.3 * i))
    fcf = ebitda - interest - cash_tax - V.CAPEX[y] - V.PREF - V.NCI - DIV
    nd -= fcf; ppe += V.CAPEX[y] - DA[y]; eq += ni - DIV
    rows.append((y, ebitda, DA[y], interest, tax, ni, eps, V.CAPEX[y], fcf, nd, ppe, eq, nd / ebitda))
L = [f"central case: futures 2027-28, then {fut_avg:.2f} flat; CP2 contract fees +0.40 from 2030",
     "year  EBITDA  D&A  interest  tax  NI common  EPS  capex  FCF after div  net debt  net PP&E  equity change since end-2026  ND/EBITDA"]
for r in rows:
    L.append("{}  {:6.2f} {:4.2f} {:8.2f} {:4.2f} {:9.2f} {:5.2f} {:6.1f} {:13.2f} {:9.1f} {:9.1f} {:12.1f} {:9.1f}x".format(*r))
nci_val = V.NCI * (1 - V.TAX) / S.RC
for r in rows[-2:]:
    y, e, ndy = r[0], r[1], r[9]
    for mult, lab in ((8.1, "VG today"), (10.3, "Cheniere today")):
        eq = (mult * e - ndy - S.PREF_LIQ - nci_val - S.BP) / V.SHARES
        L.append(f"multiple check {y}: EBITDA {e:.2f} x {mult} ({lab}) -> {eq:.2f}/share in {y}, {eq / 1.12 ** (y - 2026.8):.2f} discounted at 12% a year to today (ASSUMPTION rate)")
L.append(f"P/E at {V.bs['share_price_2026-10-07']} on central EPS: " + ", ".join(f"{r[0]} {V.bs['share_price_2026-10-07'] / r[6]:.1f}x" for r in rows))
out = LEGACY_NOTE + "\n".join(L); print(out)
open(os.path.join(RESULTS, "three_statement.txt"), "w").write(out + "\n")
