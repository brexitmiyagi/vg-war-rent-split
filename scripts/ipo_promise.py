"""The IPO said commissioning cash 'can potentially surpass the total costs of the
projects prior to COD'. Did it?

Calcasieu: net commissioning proceeds (S-1 figure, to Sep 2024) against the S-1 cost.
Plaquemines: segment revenue less cost of sales from first LNG to June 2026, plus
the test LNG proceeds booked against construction cost, against the S-1 cost range.
The Q3 line is my estimate, not a filed number: it scales Q2's segment margin by
fee times volume from the Q3 2026 8-K.
Segment margin excludes whatever the sales and shipping arm adds on resale.
"""
import os
from common import read, RESULTS

d = {r["item"]: float(r["value_musd"]) for r in read("commissioning_cash_vs_cost.csv")}
L = []
c = d["calcasieu_net_commissioning_proceeds_to_2024_09_30"] / d["calcasieu_total_project_cost"]
L.append(f"Calcasieu: {d['calcasieu_net_commissioning_proceeds_to_2024_09_30']/1000:.1f}bn net commissioning cash vs {d['calcasieu_total_project_cost']/1000:.1f}bn cost = {c:.0%}")
m24 = d["plaquemines_revenue_2024"] - d["plaquemines_cost_of_sales_2024"]
m25 = d["plaquemines_revenue_2025"] - d["plaquemines_cost_of_sales_2025"]
mh1 = d["plaquemines_revenue_h1_2026"] - d["plaquemines_cost_of_sales_h1_2026"]
mq2 = d["plaquemines_revenue_q2_2026"] - d["plaquemines_cost_of_sales_q2_2026"]
todate = m24 + m25 + d["plaquemines_test_lng_to_cip_2025"] + mh1
L.append(f"Plaquemines margin: 2024 {m24:.0f}m, 2025 {m25:.0f}m, test LNG {d['plaquemines_test_lng_to_cip_2025']:.0f}m, H1 2026 {mh1:.0f}m (Q2 {mq2:.0f}m) -> to June 2026 {todate/1000:.2f}bn")
lo, hi = d["plaquemines_cost_low_s1"], d["plaquemines_cost_high_s1"]
L.append(f"  vs S-1 cost {lo/1000:.0f}-{hi/1000:.0f}bn: {todate/hi:.0%} to {todate/lo:.0%}")
# Q3 2026: no segment data yet. Scale the Q2 margin by fee x volume from the Q3 8-K back-out.
q3 = mq2 * (d["plaquemines_fee_q3_2026_est"] * d["plaquemines_tbtu_q3_2026"]) / (d["plaquemines_fee_q2_2026"] * d["plaquemines_tbtu_q2_2026"])
sep = todate + q3
L.append(f"  my estimate for Q3 2026: {q3:.0f}m, so about {sep/1000:.1f}bn to the end of September, {sep/hi:.0%} to {sep/lo:.0%} of the S-1 cost")
L.append("  Phase 1 reaches COD on 31 October (reported); Phase 2 (6.7 MTPA) keeps commissioning to mid-2027 and excess capacity stays merchant after that, so this is not the final number")
L.append(f"CP2 cost estimate: S-1 {d['cp2_cost_low_s1']/1000:.0f}-{d['cp2_cost_high_s1']/1000:.0f}bn -> 10-K {d['cp2_cost_low_10k']/1000:.1f}-{d['cp2_cost_high_10k']/1000:.1f}bn, up {(d['cp2_cost_low_10k']+d['cp2_cost_high_10k'])/(d['cp2_cost_low_s1']+d['cp2_cost_high_s1'])-1:.0%} at the midpoint")
out = "\n".join(L); print(out)
open(os.path.join(RESULTS, "ipo_promise.txt"), "w").write(out + "\n")
