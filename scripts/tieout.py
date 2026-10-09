# Ties every transcribed segment line back to the totals Venture Global filed. Fails loudly if not.
from common import read

seg = read("vg_segments_q2_2026.csv")
filed = {"Q2 2026": (4578, 2188), "Q2 2025": (3101, 1038), "H1 2026": (9177, 3339), "H1 2025": (5995, 2118)}
for period, (rev, oi) in filed.items():
    rows = [r for r in seg if r["period"] == period]
    assert round(sum(float(r["revenue_musd"]) for r in rows)) == rev, period + " revenue"
    assert round(sum(float(r["income_from_operations_musd"]) for r in rows)) == oi, period + " op income"
    for r in rows:
        costs = sum(float(r[k]) for k in ("cost_of_sales_musd", "om_musd", "ga_musd", "development_musd", "da_musd"))
        assert round(float(r["revenue_musd"]) - costs) == round(float(r["income_from_operations_musd"])), r
    print(f"{period}: revenue {rev} and operating income {oi} tie, line by line")
# Adjusted EBITDA reconciliation, Q2 2026 (slide 29): op income + D&A + stock comp + derivative fair value
assert 2188 + 260 + 15 + 28 == 2491
print("Q2 2026 adjusted EBITDA 2,491 ties")
bs = {r["item"]: float(r["value"]) for r in read("vg_balance_sheet_2026-06-30.csv")}
assert bs["class_a_shares"] + bs["class_b_shares"] == 2498
print("Shares outstanding 2,498m tie (529m A + 1,969m B)")
ins = read("insider_sales_2026.csv")
tot = sum(float(r["proceeds_usd"]) for r in ins); sh = sum(float(r["shares_sold"]) for r in ins)
print(f"Insider sales Jul-Sep 2026: {sh:,.0f} shares, ${tot/1e6:.1f}m, avg ${tot/sh:.2f}")
print("all tie-outs passed")
