"""Sum of the parts. The contracted book is a take-or-pay annuity and gets discounted
like one; the open cargoes are a commodity spread and get a commodity discount rate.
Same volumes, fees, costs and capex as valuation.py, so the two can be compared.

ASSUMPTIONS (all mine, all shown with sensitivities):
- contracted cash at 7.0% unlevered: a little above the 6.375% and 6.625% coupons VG paid on the
  parent notes it issued in 2026 (Q2 2026 10-Q)
- open cash at 10.0%: above the 9.000% VG pays on its Series A preferred, which ranks ahead of the
  common, because open cash is junior and volatile. 12% shown as the sensitivity
- committed capex discounted at the contracted rate
- 20-year contracts run off around 2049; after that those volumes are treated as open at the terminal fee
- maintenance capex 1.0bn a year from 2032, split by volume
- D&A tax shield goes to the contracted bucket
- deductions at end-2026: net debt (valuation.py estimate), 3.0bn VGLNG Series A preferred at
  liquidation value, Stonepeak's 23% of Calcasieu at its share of EBITDA capitalised at 7%,
  and the same BP adjustment as valuation.py
"""
LEGACY_NOTE = "LEGACY cross-check from an earlier version (v4-v6). The v7 numbers used in the piece are in results/model_v7.txt, waterfall.txt and pair_v7.txt.\n"
import os
from common import annual_curve, fee_jkm, fee_ttf, RESULTS, PRICE_KEY
from valuation import vol, open_tbtu, COST, CONTRACT_FEE, CAPEX, TAX, NCI, SHARES, ND0, YEARS, bs

RC, RO = 0.07, 0.10
DA = {2027: 1.25, 2028: 1.6, 2029: 2.0, 2030: 2.4, 2031: 2.6}
PREF_LIQ = 3.0
BP = 3.7 * 0.5 * (1 - TAX)
curve = annual_curve()

def sotp(fee, terminal, rc=RC, ro=RO, detail=False):
    pv_c = pv_o_war = pv_o_late = pv_capex = 0.0
    for t, y in enumerate(YEARS, start=1):
        con = vol[y] - open_tbtu[y]
        ec = con * (CONTRACT_FEE[y] - COST) / 1000
        eo = open_tbtu[y] * (fee[y] - COST) / 1000
        cc = ec * (1 - TAX) + TAX * DA[y]
        co = eo * (1 - TAX)
        pv_c += cc / (1 + rc) ** t
        if y <= 2028:
            pv_o_war += co / (1 + ro) ** t
        else:
            pv_o_late += co / (1 + ro) ** t
        pv_capex += CAPEX[y] / (1 + rc) ** t
    con = vol[2031] - open_tbtu[2031]
    share_c = con / vol[2031]
    ec = con * (2.45 - COST) / 1000 - 1.0 * share_c
    cc = ec * (1 - TAX) + TAX * 2.6
    n = 2049 - 2031
    annuity = cc * (1 - (1 + rc) ** -n) / rc / (1 + rc) ** 5
    pv_c += annuity
    tail = con * (terminal - COST) / 1000 * (1 - TAX) / ro / (1 + ro) ** (5 + n)
    pv_o_late += tail
    eo = open_tbtu[2031] * (terminal - COST) / 1000 - 1.0 * (1 - share_c)
    pv_o_late += eo * (1 - TAX) / ro / (1 + ro) ** 5
    nci = NCI * (1 - TAX) / rc
    ev = pv_c + pv_o_war + pv_o_late - pv_capex
    eq = ev - ND0 - PREF_LIQ - nci - BP
    if detail:
        return {"contracted book": pv_c, "open cargoes 2027-28": pv_o_war, "open cargoes 2029 on": pv_o_late,
                "committed capex": -pv_capex, "net debt end-2026": -ND0, "preferred": -PREF_LIQ,
                "Calcasieu minority": -nci, "BP adjustment": -BP, "equity": eq}
    return eq / SHARES

jk = {y: fee_jkm(curve[y]) for y in YEARS}
cases = {
    "bear: futures to 2031, then 3.00": (jk, 3.00),
    "base: futures to 2029, then 5.19": ({**jk, 2030: 5.19, 2031: 5.19}, 5.19),
    "bull: futures to 2028, then 6.00": ({**jk, 2029: 6.0, 2030: 6.0, 2031: 6.0}, 6.0),
}
L = []
vals = {}
for k, (fe, te) in cases.items():
    vals[k] = sotp(fe, te)
    L.append(f"{k:<36} ${vals[k]:6.2f}/share")
w = 0.25 * vals["bear: futures to 2031, then 3.00"] + 0.5 * vals["base: futures to 2029, then 5.19"] + 0.25 * vals["bull: futures to 2028, then 6.00"]
L.append(f"weighted 25/50/25: ${w:.2f} vs price {bs[PRICE_KEY]} ({w / bs[PRICE_KEY] - 1:+.0%})")
L.append("base case, $bn and $/share:")
d = sotp(*cases["base: futures to 2029, then 5.19"], detail=True)
for k, v in d.items():
    L.append(f"  {k:<24} {v:7.1f}  {v / SHARES:6.2f}")
db = sotp(*cases["bear: futures to 2031, then 3.00"], detail=True)
L.append(f"bear case open cargoes 2029 on: {db['open cargoes 2029 on'] / SHARES:.2f}/share")
others = sum(v for k, v in d.items() if k not in ("open cargoes 2029 on", "equity")) / SHARES
L.append(f"what the price pays for open cargoes from 2029 on: {bs[PRICE_KEY] - others:.2f}/share (base gives {d['open cargoes 2029 on'] / SHARES:.2f}, bear {db['open cargoes 2029 on'] / SHARES:.2f})")
L.append("sensitivity of the base case ($/share):")
for rc in (0.06, 0.07, 0.08):
    L.append("  contracted " + f"{rc:.0%}: " + "  ".join(f"open {ro:.0%} -> {sotp(*cases['base: futures to 2029, then 5.19'], rc=rc, ro=ro):5.2f}" for ro in (0.09, 0.10, 0.12)))
# what the price pays for the open cargoes from 2029 on
base_fee, _ = cases["base: futures to 2029, then 5.19"]
def eq_flat(x):
    return sotp({**jk, 2029: x, 2030: x, 2031: x}, x)
lo, hi = 0.0, 20.0
for _ in range(60):
    mid = (lo + hi) / 2
    lo, hi = (mid, hi) if eq_flat(mid) < bs[PRICE_KEY] else (lo, mid)
L.append(f"flat open fee from 2029 that the price needs on this method: {mid:.2f} (futures kept for 2027-28)")
for ro in (0.09, 0.12):
    lo, hi = 0.0, 20.0
    for _ in range(60):
        mm = (lo + hi) / 2
        v = sotp({**jk, 2029: mm, 2030: mm, 2031: mm}, mm, ro=ro)
        lo, hi = (mm, hi) if v < bs[PRICE_KEY] else (lo, mm)
    L.append(f"  with open cash at {ro:.0%}: {mm:.2f}")

# --- v5: value at the end of 2028 (the 24-month view) -------------------------
# By then 2027-28 cash has been earned and spent (capex, interest, preferred, NCI). What is left
# is the 2029-on business, valued the same way, less net debt at end-2028 from eps_path.py and
# the BP award, assumed paid by then at the same 50%-of-low-end figure.
from eps_path import path
def sotp_2028(fee, terminal, rc=RC, ro=RO):
    pv = 0.0
    for t_, y in enumerate((2029, 2030, 2031), start=1):
        con = vol[y] - open_tbtu[y]
        cc = con * (CONTRACT_FEE[y] - COST) / 1000 * (1 - TAX) + TAX * DA[y]
        co = open_tbtu[y] * (fee[y] - COST) / 1000 * (1 - TAX)
        pv += cc / (1 + rc) ** t_ + co / (1 + ro) ** t_ - CAPEX[y] / (1 + rc) ** t_
    con = vol[2031] - open_tbtu[2031]
    share_c = con / vol[2031]
    cc = (con * (2.45 - COST) / 1000 - 1.0 * share_c) * (1 - TAX) + TAX * 2.6
    n = 2049 - 2031
    pv += cc * (1 - (1 + rc) ** -n) / rc / (1 + rc) ** 3
    pv += con * (terminal - COST) / 1000 * (1 - TAX) / ro / (1 + ro) ** (3 + n)
    eo = open_tbtu[2031] * (terminal - COST) / 1000 - 1.0 * (1 - share_c)
    pv += eo * (1 - TAX) / ro / (1 + ro) ** 3
    nd28 = path(fee)[2][4]
    nci = NCI * (1 - TAX) / rc
    return (pv - nd28 - PREF_LIQ - nci - BP) / SHARES, nd28
L.append("value at end-2028 ($/share), same cases:")
v28 = {}
for k, (fe, te) in cases.items():
    v28[k], nd28 = sotp_2028(fe, te)
    L.append(f"  {k:<36} ${v28[k]:6.2f}   (net debt end-2028 {nd28:.1f} bn)")
w28 = 0.25 * v28["bear: futures to 2031, then 3.00"] + 0.5 * v28["base: futures to 2029, then 5.19"] + 0.25 * v28["bull: futures to 2028, then 6.00"]
px = bs[PRICE_KEY]
L.append(f"  weighted end-2028: ${w28:.2f} vs price {px} ({w28 / px - 1:+.0%}); base alone {v28['base: futures to 2029, then 5.19'] / px - 1:+.0%}")
L.append(f"today: base alone {vals['base: futures to 2029, then 5.19'] / px - 1:+.0%}, weighted {w / px - 1:+.0%}")
fut = path(jk)
L.append(f"P/E at {px} on 2031 EPS: base {px / path({**jk, 2030: 5.19, 2031: 5.19})[5][2]:.1f}x, futures all the way {px / fut[5][2]:.0f}x")

out = LEGACY_NOTE + "\n".join(L); print(out)
open(os.path.join(RESULTS, "sotp.txt"), "w").write(out + "\n")
