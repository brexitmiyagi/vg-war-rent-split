# What open-cargo fee does the $1.00 consensus for 2027 EPS assume? Same inputs as valuation.py.
LEGACY_NOTE = "LEGACY cross-check from an earlier version (v4-v6). The v7 numbers used in the piece are in results/model_v7.txt, waterfall.txt and pair_v7.txt.\n"
if __name__ == "__main__":
    print(LEGACY_NOTE, end="")
from common import annual_curve, fee_jkm
from valuation import vol, open_tbtu, COST, CONTRACT_FEE, ND0, DEBT_COST, TAX, PREF, NCI, SHARES

DA_2027 = 1.25   # ASSUMPTION, $bn: H1 2026 D&A was $0.511bn, Plaquemines fully in service adds more

def eps_2027(fee, contract_fee=CONTRACT_FEE[2027]):
    y = 2027
    ebitda = ((vol[y] - open_tbtu[y]) * contract_fee + open_tbtu[y] * fee - COST * vol[y]) / 1000
    pre = ebitda - DA_2027 - ND0 * DEBT_COST
    return ebitda, (pre * (1 - TAX) - PREF - NCI) / SHARES

f = fee_jkm(annual_curve()[2027])
e, p = eps_2027(f)
print(f"2027 at the futures fee {f:.2f}: EBITDA {e:.2f} $bn, EPS {p:.2f}")
for cf in (2.40, 3.00, 3.50):
    lo, hi = 0.0, 30.0
    for _ in range(60):
        m = (lo + hi) / 2
        lo, hi = (m, hi) if eps_2027(m, cf)[1] < 1.00 else (lo, m)
    print(f"  contracted fee {cf:.2f}: $1.00 of EPS needs an open fee of {m:.2f}")
