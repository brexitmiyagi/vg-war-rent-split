"""Builds vg_model_v9.xlsx: a formula-driven version of model_v9.py's central case
(inputs -> annual model 2027-2031 -> contracted and open cash 2032-2049 year by year -> sum of the
parts today and at end-2028 -> fee the price needs -> long-run fee x cost grid).
Blue = input, black = formula, yellow = key assumption. v8 adds fee escalation (company convention,
424B4), interest calibrated to the Q2 2026 10-Q, capitalized interest for EPS, and a cost-inflation
switch (0 in the central case)."""
import io, contextlib, os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.comments import Comment
with contextlib.redirect_stdout(io.StringIO()):
    import model_v8 as M, model_v9 as M9, valuation as V, sotp as S
    from eps_path import DA as DAE

OUT = os.path.join(os.path.dirname(__file__), "..", "vg_model_v9.xlsx")
wb = Workbook()
blue = Font(name="Arial", color="0000FF"); black = Font(name="Arial"); bold = Font(name="Arial", bold=True)
green = Font(name="Arial", color="008000"); yellow = PatternFill("solid", fgColor="FFFF00")
def put(ws, cell, v, font=black, fmt=None, note=None, fill=None):
    ws[cell] = v; ws[cell].font = font
    if fmt: ws[cell].number_format = fmt
    if note: ws[cell].comment = Comment(note, "model")
    if fill: ws[cell].fill = fill

I = wb.active; I.title = "Inputs"
I["A1"] = "Venture Global (VG) model v9 - inputs (blue = input, yellow = key assumption)"; I["A1"].font = bold
rows = [
 ("Share price, Oct 7 2026 close ($)", V.bs[M.PRICE_KEY], "0.00", "stockanalysis.com / Yahoo Finance close, 7 Oct 2026", False),
 ("Diluted shares (bn)", V.SHARES, "0.000", "Q2 2026 10-Q Note 16 (2,643m)", False),
 ("Tax rate", V.TAX, "0.0%", "close to the 19.2% Q2 2026 effective rate", False),
 ("Discount rate, contracted cash and capex", S.RC, "0.0%", "ASSUMPTION: a little above the 6.375%/6.625% VGLNG coupons issued in 2026", True),
 ("Discount rate, open cargoes", S.RO, "0.0%", "ASSUMPTION: above the 9.0% Series A preferred", True),
 ("Cash interest rate on net debt", M.CASH_RATE, "0.00%", "Q2 2026 10-Q: (stated 691 + other 46 - interest income 26) x 4 / 30 Jun net debt 37,796", False),
 ("P&L interest cost rate before capitalization", M.PL_RATE, "0.00%", "Q2 2026 10-Q: (total interest cost 804 - interest income 26) x 4 / 37,796", False),
 ("Net debt end-2026 ($bn)", M.ND0, "0.00", "30 Jun net debt + H2 capex - (H2 EBITDA - H2 cash interest - 0.4)", False),
 ("Series A preferred liquidation ($bn)", S.PREF_LIQ, "0.00", "Q2 2026 10-Q", False),
 ("Preferred dividend ($bn/yr)", V.PREF, "0.000", "4 x $67m quarterly, Q2 2026 10-Q", False),
 ("Minority share of EBITDA ($bn/yr)", V.NCI, "0.00", "2026 NCI guide midpoint, Q1 2026 deck", False),
 ("BP adjustment ($bn)", S.BP, "0.00", "ASSUMPTION: half of BP's $3.7bn low-end claim, after tax", False),
 ("Common dividend ($bn/yr)", M.DIV, "0.00", "$0.04/qtr on 2.498bn shares", False),
 ("2026 volume (TBtu)", V.vol[2026], "#,##0", "Aug 2026 cargo outlook x 3.7 TBtu", False),
 ("2026 open volume (TBtu)", V.open_tbtu[2026], "#,##0", "Q2 2026 deck $1 sensitivity midpoint", False),
 ("2026 contracted fee", 5.05, "0.00", "Aug 2026 release", False),
 ("2026 unsold fee assumption", 13.00, "0.00", "midpoint of $12.50-13.50, Aug 2026 release", False),
 ("2026 EBITDA guide midpoint ($bn)", 8.9, "0.00", "Aug 2026 release", False),
 ("Plaquemines basis cost 2026 ($bn)", M.BASIS26, "0.000", "Q4 2025 deck ($110m Q1) + Q1 2026 deck ($300-350m Q2-Q4)", False),
 ("CP2 contract fee premium over Calcasieu ($/MMBtu)", M.CP2X, "0.00", "ASSUMPTION: half of the lender-sizing back-solve (waterfall.py)", True),
 ("Long-run open fee from 2032 ($/MMBtu)", M.L_CENTRAL, "0.00", "ASSUMPTION: top of contract-market anchors, bottom of Sabel's $3.50-4.50", True),
 ("Contract fee in terminal, before escalation ($/MMBtu)", 2.45, "0.00", "ASSUMPTION (Calcasieu-like)", False),
 ("Long-term base book (TBtu): Calcasieu + Plaquemines SPAs", M.BASE_BOOK, "#,##0", "10 + 20 MTPA x 52", False),
 ("Escalating share of the fixed fee", M.ESC_SHARE, "0.0%", "Company convention, IPO prospectus 424B4 (24 Jan 2025): 17.5% of the fixed facility charge rises 2.5% a year after the first full year post-COD", False),
 ("Escalation rate a year", M.ESC_RATE, "0.0%", "Company convention, 424B4", False),
 ("Cost inflation a year (central case 0)", 0.0, "0.0%", "Sensitivity: 2.5% takes value to about 4.85 (model_v8.txt)", True),
 ("Maintenance capex in terminal ($bn/yr)", 1.0, "0.00", "ASSUMPTION", False),
 ("Contract run-off year", 2049, "0", "ASSUMPTION: 20-year SPAs run off around 2049", False),
]
r0 = 3; names = {}
for i, (lab, v, fmt, note, key) in enumerate(rows):
    r = r0 + i; I[f"A{r}"] = lab
    put(I, f"B{r}", v, blue, fmt, note, yellow if key else None); names[lab] = f"Inputs!$B${r}"
r = r0 + len(rows) + 1
I[f"A{r}"] = "2026 all-in cost per MMBtu (calibrated to guidance)"
put(I, f"B{r}", f"=({names['2026 volume (TBtu)']}-{names['2026 open volume (TBtu)']})*{names['2026 contracted fee']}/{names['2026 volume (TBtu)']}+{names['2026 open volume (TBtu)']}*{names['2026 unsold fee assumption']}/{names['2026 volume (TBtu)']}-{names['2026 EBITDA guide midpoint ($bn)']}*1000/{names['2026 volume (TBtu)']}", black, "0.000")
names["C26"] = f"Inputs!$B${r}"; r += 1
I[f"A{r}"] = "Underlying cost per MMBtu ex basis"; put(I, f"B{r}", f"={names['C26']}-{names['Plaquemines basis cost 2026 ($bn)']}*1000/{names['2026 volume (TBtu)']}", black, "0.000")
names["CEX"] = f"Inputs!$B${r}"; r += 2
# escalation tranches
I[f"A{r}"] = "Escalation tranches (weight, first escalation year)"; I[f"A{r}"].font = bold; r += 1
tr = {}
for lab, w, f, note in (("Calcasieu (MTPA)", 10.0, 2027, "COD Apr 2025"), ("Plaquemines Phase 1 (MTPA)", 13.3, 2028, "COD Q4 2026"),
                        ("Plaquemines Phase 2 (MTPA)", 6.7, 2029, "COD mid-2027"), ("CP2 Phase 1 (weight)", 0.5, 2031, "COD 2029, ASSUMPTION 50/50"),
                        ("CP2 Phase 2 (weight)", 0.5, 2032, "COD 2030")):
    I[f"A{r}"] = lab; put(I, f"B{r}", w, blue, "0.0", note); put(I, f"C{r}", f, blue, "0"); tr[lab] = r; r += 1
def mb(y):   # base-book multiplier for year y (y may be a cell ref)
    s, g = names["Escalating share of the fixed fee"], names["Escalation rate a year"]
    parts = [f"Inputs!$B${tr[k]}*(1+{s}*((1+{g})^MAX(0,{y}-Inputs!$C${tr[k]}+1)-1))" for k in ("Calcasieu (MTPA)", "Plaquemines Phase 1 (MTPA)", "Plaquemines Phase 2 (MTPA)")]
    den = "+".join(f"Inputs!$B${tr[k]}" for k in ("Calcasieu (MTPA)", "Plaquemines Phase 1 (MTPA)", "Plaquemines Phase 2 (MTPA)"))
    return f"(({'+'.join(parts)})/({den}))"
def mc(y):
    s, g = names["Escalating share of the fixed fee"], names["Escalation rate a year"]
    return "(" + "+".join(f"Inputs!$B${tr[k]}*(1+{s}*((1+{g})^MAX(0,{y}-Inputs!$C${tr[k]}+1)-1))" for k in ("CP2 Phase 1 (weight)", "CP2 Phase 2 (weight)")) + ")"
r += 1
I[f"A{r}"] = "Annual inputs"; I[f"A{r}"].font = bold; r += 1
hdr = r; I[f"A{hdr}"] = "Item"
for j, y in enumerate(M.YEARS):
    c = chr(ord("B") + j); I[f"{c}{hdr}"] = y; I[f"{c}{hdr}"].font = bold
ann = [
 ("Volume (TBtu)", V.vol, "#,##0", "Aug 2026 outlook x 3.7 TBtu; 85 MTPA from 2030"),
 ("Open volume (TBtu)", V.open_tbtu, "#,##0", "$1 sensitivity midpoints (Aug deck); 2030-31 ASSUMPTION"),
 ("CME futures fee, JKM method ($/MMBtu)", M.FUT, "0.00", "CME settlements 7 Oct 2026, JKM less 115% HH less $2"),
 ("Contract fee before escalation ($/MMBtu)", V.CONTRACT_FEE, "0.00", "ASSUMPTION"),
 ("Plaquemines basis cost ($bn)", M.BASIS, "0.000", "2027 as 2026, half in 2028, none after (company: declines in 2028)"),
 ("Committed capex ($bn)", V.CAPEX, "0.0", "ASSUMPTION"),
 ("CIP-credited commissioning volume (TBtu)", M9.CIP_TBTU, "#,##0", "ASSUMPTION: CP2 and bolt-on output before each phase is placed in service (10-Q policy: proceeds reduce construction in progress)"),
 ("Capitalized interest ($bn)", M.CAPI, "0.00", "ASSUMPTION anchored on Q2 2026 (315m, 1.26bn a year), falling as CP2 phases are placed in service"),
]
arow = {}
for k, (lab, d, fmt, note) in enumerate(ann):
    rr = hdr + 1 + k; I[f"A{rr}"] = lab
    for j, y in enumerate(M.YEARS):
        c = chr(ord("B") + j); put(I, f"{c}{rr}", float(d[y]), blue, fmt, note if j == 0 else None)
    arow[lab] = rr
I.column_dimensions["A"].width = 58
for c in "BCDEF": I.column_dimensions[c].width = 12

Mo = wb.create_sheet("Model")
Mo["A1"] = "Annual model, central case ($bn unless stated)"; Mo["A1"].font = bold
Mo["A2"] = "Year"
for j, y in enumerate(M.YEARS):
    c = chr(ord("B") + j); Mo[f"{c}2"] = y; Mo[f"{c}2"].font = bold
def ref(lab, c): return f"Inputs!{c}${arow[lab]}"
lines = ["Volume (TBtu)", "Open volume (TBtu)", "Contracted volume (TBtu)", "Escalation multiplier, base book", "Escalation multiplier, CP2",
         "Contracted margin before costs", "CP2 contract premium", "Open margin before costs", "Unit cost ($/MMBtu)", "Operating cost", "EBITDA", "CIP-credited commissioning margin", "Reported EBITDA (company definition)",
         "Cost on contracted volume", "Cost on open volume", "Contracted EBITDA", "Open EBITDA", "D&A",
         "Cash interest on opening net debt", "Capitalized interest", "P&L interest after capitalization", "Pre-tax income", "Tax",
         "Preferred and minority", "Net income to common", "EPS ($)", "Cash tax", "Capex", "Common dividend", "Free cash flow after dividends",
         "Closing net debt", "Net debt / EBITDA (x)", "Discount factor, contracted", "Discount factor, open",
         "Discount factor from end-2028, contracted", "Discount factor from end-2028, open"]
L = {lab: 3 + i for i, lab in enumerate(lines)}
for lab, rr in L.items(): Mo[f"A{rr}"] = lab
base = names["Long-term base book (TBtu): Calcasieu + Plaquemines SPAs"]
for j, y in enumerate(M.YEARS):
    c = chr(ord("B") + j); prev = chr(ord("B") + j - 1); yc = f"{c}$2"
    f = {}
    f["Volume (TBtu)"] = f"={ref('Volume (TBtu)', c)}"
    f["Open volume (TBtu)"] = f"={ref('Open volume (TBtu)', c)}"
    f["Contracted volume (TBtu)"] = f"={c}{L['Volume (TBtu)']}-{c}{L['Open volume (TBtu)']}"
    f["Escalation multiplier, base book"] = "=" + mb(yc)
    f["Escalation multiplier, CP2"] = "=" + mc(yc)
    con = f"{c}{L['Contracted volume (TBtu)']}"; fee = ref('Contract fee before escalation ($/MMBtu)', c)
    f["Contracted margin before costs"] = f"=(MIN({con},{base})*{fee}*{c}{L['Escalation multiplier, base book']}+MAX(0,{con}-{base})*{fee}*IF({yc}>=2030,{c}{L['Escalation multiplier, CP2']},1))/1000"
    f["CP2 contract premium"] = f"=IF({yc}>=2030,MAX(0,{con}-{base})*{names['CP2 contract fee premium over Calcasieu ($/MMBtu)']}*{c}{L['Escalation multiplier, CP2']}/1000,0)"
    f["Open margin before costs"] = f"={c}{L['Open volume (TBtu)']}*{ref('CME futures fee, JKM method ($/MMBtu)', c)}/1000"
    f["Unit cost ($/MMBtu)"] = f"={names['CEX']}*(1+{names['Cost inflation a year (central case 0)']})^({yc}-2026)"
    f["Operating cost"] = f"={c}{L['Unit cost ($/MMBtu)']}*{c}{L['Volume (TBtu)']}/1000+{ref('Plaquemines basis cost ($bn)', c)}"
    f["EBITDA"] = f"={c}{L['Contracted margin before costs']}+{c}{L['CP2 contract premium']}+{c}{L['Open margin before costs']}-{c}{L['Operating cost']}"
    f["Cost on contracted volume"] = f"={c}{L['Operating cost']}*{con}/{c}{L['Volume (TBtu)']}"
    f["Cost on open volume"] = f"={c}{L['Operating cost']}*{c}{L['Open volume (TBtu)']}/{c}{L['Volume (TBtu)']}"
    f["Contracted EBITDA"] = f"={c}{L['Contracted margin before costs']}+{c}{L['CP2 contract premium']}-{c}{L['Cost on contracted volume']}"
    f["Open EBITDA"] = f"={c}{L['Open margin before costs']}-{c}{L['Cost on open volume']}"
    f["CIP-credited commissioning margin"] = f"={ref('CIP-credited commissioning volume (TBtu)', c)}*({ref('CME futures fee, JKM method ($/MMBtu)', c)}-{c}{L['Unit cost ($/MMBtu)']})/1000"
    f["Reported EBITDA (company definition)"] = f"={c}{L['EBITDA']}-{c}{L['CIP-credited commissioning margin']}"
    f["D&A"] = "=0"
    opening = names["Net debt end-2026 ($bn)"] if j == 0 else f"{prev}{L['Closing net debt']}"
    f["Cash interest on opening net debt"] = f"={opening}*{names['Cash interest rate on net debt']}"
    f["Capitalized interest"] = f"={ref('Capitalized interest ($bn)', c)}"
    f["P&L interest after capitalization"] = f"={opening}*{names['P&L interest cost rate before capitalization']}-{c}{L['Capitalized interest']}"
    f["Pre-tax income"] = f"={c}{L['Reported EBITDA (company definition)']}-{c}{L['D&A']}-{c}{L['P&L interest after capitalization']}"
    f["Tax"] = f"={names['Tax rate']}*MAX(0,{c}{L['Pre-tax income']})"
    f["Preferred and minority"] = f"={names['Preferred dividend ($bn/yr)']}+{names['Minority share of EBITDA ($bn/yr)']}"
    f["Net income to common"] = f"={c}{L['Pre-tax income']}-{c}{L['Tax']}-{c}{L['Preferred and minority']}"
    f["EPS ($)"] = f"={c}{L['Net income to common']}/{names['Diluted shares (bn)']}"
    f["Cash tax"] = f"={names['Tax rate']}*MAX(0,{c}{L['Reported EBITDA (company definition)']}-({c}{L['Cash interest on opening net debt']}-{c}{L['Capitalized interest']})-(1+0.3*{j}))"
    f["Capex"] = f"={ref('Committed capex ($bn)', c)}"
    f["Common dividend"] = f"={names['Common dividend ($bn/yr)']}"
    f["Free cash flow after dividends"] = f"={c}{L['EBITDA']}-{c}{L['Cash interest on opening net debt']}-{c}{L['Cash tax']}-{c}{L['Capex']}-{c}{L['Preferred and minority']}-{c}{L['Common dividend']}"
    f["Closing net debt"] = f"={opening}-{c}{L['Free cash flow after dividends']}"
    f["Net debt / EBITDA (x)"] = f"={c}{L['Closing net debt']}/{c}{L['EBITDA']}"
    f["Discount factor, contracted"] = f"=1/(1+{names['Discount rate, contracted cash and capex']})^({yc}-2026)"
    f["Discount factor, open"] = f"=1/(1+{names['Discount rate, open cargoes']})^({yc}-2026)"
    f["Discount factor from end-2028, contracted"] = f"=IF({yc}>2028,1/(1+{names['Discount rate, contracted cash and capex']})^({yc}-2028),0)"
    f["Discount factor from end-2028, open"] = f"=IF({yc}>2028,1/(1+{names['Discount rate, open cargoes']})^({yc}-2028),0)"
    for lab, form in f.items():
        fmt = "0.000" if "multiplier" in lab or "factor" in lab else ("0.00" if "EPS" in lab or "(x)" in lab else ("#,##0" if "TBtu" in lab else "0.00"))
        put(Mo, f"{c}{L[lab]}", form, black, fmt)
Mo.column_dimensions["A"].width = 46

# ---------------- D&A built from the balance sheet
D = wb.create_sheet("D&A")
D["A1"] = "Book D&A from in-service plant (Q2 2026 10-Q Note 5), mid-year convention ($bn)"; D["A1"].font = bold
dins = [("Terminal and pipeline facilities, gross, 30 Jun 2026", 34.943), ("LNG tankers, gross", 2.038), ("Other PP&E, gross", 0.724),
        ("Depreciation expense H1 2026", 0.506), ("D&A H1 2026", 0.511), ("CP2 total cost basis before commissioning credits (ASSUMPTION)", M9.CP2_COST),
        ("CP2 Phase 1 share of cost", 0.55)]
dn = {}
for i, (lab, v) in enumerate(dins):
    rr = 3 + i; D[f"A{rr}"] = lab; put(D, f"B{rr}", v, blue, "0.000"); dn[lab] = f"'D&A'!$B${rr}"
rr = 3 + len(dins)
D[f"A{rr}"] = "In-service gross, 30 Jun 2026"; put(D, f"B{rr}", f"={dn['Terminal and pipeline facilities, gross, 30 Jun 2026']}+{dn['LNG tankers, gross']}+{dn['Other PP&E, gross']}", black, "0.000"); g0 = f"'D&A'!$B${rr}"; rr += 1
D[f"A{rr}"] = "Depreciation rate a year"; put(D, f"B{rr}", f"={dn['Depreciation expense H1 2026']}*2/{g0}", black, "0.0000"); rate = f"'D&A'!$B${rr}"; rr += 1
D[f"A{rr}"] = "Amortization a year"; put(D, f"B{rr}", f"=({dn['D&A H1 2026']}-{dn['Depreciation expense H1 2026']})*2", black, "0.000"); amort = f"'D&A'!$B${rr}"; rr += 1
D[f"A{rr}"] = "Commissioning margin credited to CP2 cost, 2027-2031"; put(D, f"B{rr}", f"=SUM(Model!$B${L['CIP-credited commissioning margin']}:$F${L['CIP-credited commissioning margin']})", black, "0.00"); cred = f"'D&A'!$B${rr}"; rr += 1
D[f"A{rr}"] = "CP2 net cost basis"; put(D, f"B{rr}", f"={dn['CP2 total cost basis before commissioning credits (ASSUMPTION)']}-{cred}", black, "0.00"); cp2n = f"'D&A'!$B${rr}"; rr += 2
D[f"A{rr}"] = "Additions placed in service"; D[f"B{rr}"] = "Timing (year + 0.5 = mid-year)"; D[f"C{rr}"] = "Amount"
for k, y in enumerate([2026] + list(M.YEARS)): D.cell(row=rr, column=5 + k, value=y).font = bold
hdr_add = rr; rr += 1
adds = [("Two LNG tankers", 2026.5, "0.5"), ("Rest of Plaquemines and other non-CP2 construction", 2027.5, "3.25"),
        ("CP2 Phase 1", 2028.5, f"{dn['CP2 Phase 1 share of cost']}*{cp2n}"), ("CP2 bolt-on expansion", 2029.5, "6.5"),
        ("CP2 Phase 2 and Plaquemines bolt-on", 2030.5, f"(1-{dn['CP2 Phase 1 share of cost']})*{cp2n}+4.2")]
a0 = rr
for lab, tm, amt in adds:
    D[f"A{rr}"] = lab; put(D, f"B{rr}", tm, blue, "0.0"); put(D, f"C{rr}", "=" + amt, blue if amt[0].isdigit() else black, "0.00")
    for k in range(6):
        col = chr(ord("E") + k)
        put(D, f"{col}{rr}", f"=IF($B{rr}<{col}${hdr_add},1,IF(INT($B{rr})={col}${hdr_add},0.5,0))", black, "0.0")
    rr += 1
a1 = rr - 1; rr += 1
D[f"A{rr}"] = "Book D&A"; D[f"A{rr}"].font = bold
for k in range(6):
    col = chr(ord("E") + k)
    put(D, f"{col}{rr}", f"={rate}*({g0}+SUMPRODUCT($C${a0}:$C${a1},{col}${a0}:{col}${a1}))+{amort}", black, "0.00")
darow = rr; rr += 1
D[f"A{rr}"] = "Run-rate D&A from 2032 (all additions in service; terminal tax shield)"; put(D, f"B{rr}", f"={rate}*({g0}+SUM($C${a0}:$C${a1}))+{amort}", black, "0.00")
names["Terminal D&A tax shield base ($bn/yr)"] = f"'D&A'!$B${rr}"
D.column_dimensions["A"].width = 58
# Model D&A columns B..F map to D&A sheet columns F..J (2027..2031)
for j in range(5):
    c = chr(ord("B") + j)
    Mo[f"{c}{L['D&A']}"] = f"='D&A'!{chr(ord('F') + j)}{darow}"

# ---------------- Tail 2032-2049
T = wb.create_sheet("Tail 2032-2049")
T["A1"] = "Contracted and open cash, 2032 to contract run-off, at 2031 volumes ($bn)"; T["A1"].font = bold
th = ["Year", "Escalation, base book", "Escalation, CP2", "Unit cost", "Contracted revenue", "Contracted EBITDA after maintenance",
      "Open EBITDA after maintenance", "DF contracted today", "DF open today", "DF contracted from end-2028", "DF open from end-2028"]
for k, h in enumerate(th):
    T.cell(row=2, column=k + 1, value=h).font = bold
con31, op31, vol31 = f"Model!$F${L['Contracted volume (TBtu)']}", f"Model!$F${L['Open volume (TBtu)']}", f"Model!$F${L['Volume (TBtu)']}"
Lf = names["Long-run open fee from 2032 ($/MMBtu)"]; t = names["Tax rate"]; rc = names["Discount rate, contracted cash and capex"]; ro = names["Discount rate, open cargoes"]
mnt = names["Maintenance capex in terminal ($bn/yr)"]; tf = names["Contract fee in terminal, before escalation ($/MMBtu)"]; cp2x = names["CP2 contract fee premium over Calcasieu ($/MMBtu)"]
years_tail = list(range(2032, 2050))
for i, y in enumerate(years_tail):
    rr = 3 + i
    put(T, f"A{rr}", y, blue, "0")
    put(T, f"B{rr}", "=" + mb(f"$A{rr}"), black, "0.000")
    put(T, f"C{rr}", "=" + mc(f"$A{rr}"), black, "0.000")
    put(T, f"D{rr}", f"={names['CEX']}*(1+{names['Cost inflation a year (central case 0)']})^($A{rr}-2026)", black, "0.000")
    put(T, f"E{rr}", f"=(MIN({con31},{base})*{tf}*B{rr}+MAX(0,{con31}-{base})*({tf}+{cp2x})*C{rr})/1000", black, "0.00")
    put(T, f"F{rr}", f"=E{rr}-D{rr}*{con31}/1000-{mnt}*{con31}/{vol31}", black, "0.00")
    put(T, f"G{rr}", f"={op31}*({Lf}-D{rr})/1000-{mnt}*(1-{con31}/{vol31})", black, "0.00")
    put(T, f"H{rr}", f"=1/(1+{rc})^($A{rr}-2026)", black, "0.0000")
    put(T, f"I{rr}", f"=1/(1+{ro})^($A{rr}-2026)", black, "0.0000")
    put(T, f"J{rr}", f"=1/(1+{rc})^($A{rr}-2028)", black, "0.0000")
    put(T, f"K{rr}", f"=1/(1+{ro})^($A{rr}-2028)", black, "0.0000")
last = 3 + len(years_tail) - 1
TR = lambda col: f"'Tail 2032-2049'!${col}$3:${col}${last}"
uc49 = f"'Tail 2032-2049'!$D${last}"
for k in range(1, 12): T.column_dimensions[chr(64 + k)].width = 16

Va = wb.create_sheet("Valuation")
Va["A1"] = "Sum of the parts ($bn unless stated)"; Va["A1"].font = bold
sh = names["Diluted shares (bn)"]
rng = lambda lab: f"Model!$B${L[lab]}:$F${L[lab]}"
shield = names["Terminal D&A tax shield base ($bn/yr)"]
perp = f"(({op31}*({Lf}-{uc49})/1000-{mnt}*(1-{con31}/{vol31}))+{con31}*({Lf}-{uc49})/1000)*(1-{t})/{ro}"
items = [
 ("PV contracted cash 2027-31", f"=SUMPRODUCT(({rng('Contracted EBITDA')}*(1-{t})+{t}*{rng('D&A')})*{rng('Discount factor, contracted')})"),
 ("PV open cargoes 2027-31", f"=SUMPRODUCT({rng('Open EBITDA')}*(1-{t})*{rng('Discount factor, open')})"),
 ("PV committed capex", f"=-SUMPRODUCT({rng('Capex')}*{rng('Discount factor, contracted')})"),
 ("PV contracted cash 2032-2049 (escalating)", f"=SUMPRODUCT(({TR('F')}*(1-{t})+{t}*{shield})*{TR('H')})"),
 ("PV open cargoes 2032-2049", f"=SUMPRODUCT({TR('G')}*(1-{t})*{TR('I')})"),
 ("PV all volume as open after 2049", f"={perp}/(1+{ro})^({names['Contract run-off year']}-2026)"),
 ("Less net debt end-2026", f"=-{names['Net debt end-2026 ($bn)']}"),
 ("Less preferred", f"=-{names['Series A preferred liquidation ($bn)']}"),
 ("Less Calcasieu minority", f"=-{names['Minority share of EBITDA ($bn/yr)']}*(1-{t})/{rc}"),
 ("Less BP adjustment", f"=-{names['BP adjustment ($bn)']}"),
]
for i, (lab, form) in enumerate(items):
    Va[f"A{3 + i}"] = lab; put(Va, f"B{3 + i}", form, black, "0.00")
e = 3 + len(items)
Va[f"A{e}"] = "Equity value today"; put(Va, f"B{e}", f"=SUM(B3:B{e - 1})", black, "0.00")
Va[f"A{e + 1}"] = "Value per share today ($)"; put(Va, f"B{e + 1}", f"=B{e}/{sh}", black, "0.00"); Va[f"A{e + 1}"].font = bold
r2 = e + 3
Va[f"A{r2 - 1}"] = "Value at end-2028"; Va[f"A{r2 - 1}"].font = bold
roll = [
 ("PV contracted cash 2029-31", f"=SUMPRODUCT(({rng('Contracted EBITDA')}*(1-{t})+{t}*{rng('D&A')})*{rng('Discount factor from end-2028, contracted')})"),
 ("PV open cargoes 2029-31", f"=SUMPRODUCT({rng('Open EBITDA')}*(1-{t})*{rng('Discount factor from end-2028, open')})"),
 ("PV capex 2029-31", f"=-SUMPRODUCT({rng('Capex')}*{rng('Discount factor from end-2028, contracted')})"),
 ("PV contracted cash 2032-2049", f"=SUMPRODUCT(({TR('F')}*(1-{t})+{t}*{shield})*{TR('J')})"),
 ("PV open cargoes 2032-2049", f"=SUMPRODUCT({TR('G')}*(1-{t})*{TR('K')})"),
 ("PV all volume as open after 2049", f"={perp}/(1+{ro})^({names['Contract run-off year']}-2028)"),
 ("Less net debt end-2028", f"=-Model!$C${L['Closing net debt']}"),
 ("Less preferred", f"=-{names['Series A preferred liquidation ($bn)']}"),
 ("Less Calcasieu minority", f"=-{names['Minority share of EBITDA ($bn/yr)']}*(1-{t})/{rc}"),
 ("Less BP adjustment", f"=-{names['BP adjustment ($bn)']}"),
]
for i, (lab, form) in enumerate(roll):
    Va[f"A{r2 + i}"] = lab; put(Va, f"B{r2 + i}", form, black, "0.00")
e2 = r2 + len(roll)
Va[f"A{e2}"] = "Value per share at end-2028 ($) = 24-month target"; put(Va, f"B{e2}", f"=SUM(B{r2}:B{e2 - 1})/{sh}", black, "0.00"); Va[f"A{e2}"].font = bold
Va[f"A{e2 + 1}"] = "Implied equity return a year, incl. dividends"; put(Va, f"B{e2 + 1}", f"=((B{e2}+2*0.16)/B{e + 1})^(1/2.23)-1", black, "0.0%")
Va[f"A{e2 + 2}"] = "Share price ($)"; put(Va, f"B{e2 + 2}", f"={names['Share price, Oct 7 2026 close ($)']}", green, "0.00")
Va[f"A{e2 + 3}"] = "Value per share per $1 of long-run fee"
put(Va, f"B{e2 + 3}", f"=(({op31}/1000)*(1-{t})*SUM({TR('I')})+(({op31}+{con31})/1000)*(1-{t})/{ro}/(1+{ro})^({names['Contract run-off year']}-2026))/{sh}", black, "0.00")
Va[f"A{e2 + 4}"] = "Long-run fee the price needs ($/MMBtu)"; put(Va, f"B{e2 + 4}", f"={Lf}+(B{e2 + 2}-B{e + 1})/B{e2 + 3}", black, "0.00")
Va.column_dimensions["A"].width = 50

G = wb.create_sheet("Grid")
G["A1"] = "Value per share today: long-run fee from 2032 (rows) x flat cost per MMBtu (columns), no basis cost, escalation on"; G["A1"].font = bold
costs = [1.15, 0.92, 0.75, 0.60]; fees = [2.5, 3.0, 3.5, 4.0, 4.5, 5.19, 6.0]
G["A3"] = "Long-run fee \\ cost"
for j, cst in enumerate(costs): put(G, f"{chr(66 + j)}3", cst, blue, "0.00")
for i, fv in enumerate(fees):
    rr = 4 + i; put(G, f"A{rr}", fv, blue, "0.00")
    for j in range(len(costs)):
        cc = chr(66 + j); c = f"{cc}$3"; Lc = f"$A{rr}"
        con = rng('Contracted volume (TBtu)'); op = rng('Open volume (TBtu)')
        ecs = f"({rng('Contracted margin before costs')}+{rng('CP2 contract premium')}-{c}*{con}/1000)"
        eos = f"({op}*Inputs!$B${arow['CME futures fee, JKM method ($/MMBtu)']}:$F${arow['CME futures fee, JKM method ($/MMBtu)']}/1000-{c}*{op}/1000)"
        tail_c = f"SUMPRODUCT((({TR('E')}-{c}*{con31}/1000-{mnt}*{con31}/{vol31})*(1-{t})+{t}*{shield})*{TR('H')})"
        tail_o = f"({op31}*({Lc}-{c})/1000-{mnt}*(1-{con31}/{vol31}))*(1-{t})*SUM({TR('I')})"
        pp = f"(({op31}*({Lc}-{c})/1000-{mnt}*(1-{con31}/{vol31}))+{con31}*({Lc}-{c})/1000)*(1-{t})/{ro}/(1+{ro})^({names['Contract run-off year']}-2026)"
        form = (f"=(SUMPRODUCT(({ecs}*(1-{t})+{t}*{rng('D&A')})*{rng('Discount factor, contracted')})"
                f"+SUMPRODUCT({eos}*(1-{t})*{rng('Discount factor, open')})"
                f"-SUMPRODUCT({rng('Capex')}*{rng('Discount factor, contracted')})"
                f"+{tail_c}+{tail_o}+{pp}"
                f"-{names['Net debt end-2026 ($bn)']}-{names['Series A preferred liquidation ($bn)']}-{names['Minority share of EBITDA ($bn/yr)']}*(1-{t})/{rc}-{names['BP adjustment ($bn)']})/{sh}")
        put(G, f"{cc}{rr}", form, black, "0.00")
G.column_dimensions["A"].width = 22

# ---------------- Scenarios (value is linear in the long-run fee)
Sc = wb.create_sheet("Scenarios")
Sc["A1"] = "Scenarios on the long-run fee from 2032; weights are the author's judgement"; Sc["A1"].font = bold
Sc["A2"] = "Value per $1 of long-run fee at end-2028"
put(Sc, "B2", f"=(({op31}/1000)*(1-{t})*SUM({TR('K')})+(({op31}+{con31})/1000)*(1-{t})/{ro}/(1+{ro})^({names['Contract run-off year']}-2028))/{sh}", black, "0.00")
for k, h in enumerate(["Scenario", "Long-run fee", "Weight", "Value today", "Value end-2028", "VG 24-month total return"]):
    Sc.cell(row=4, column=k + 1, value=h).font = bold
for i, (lab, l, w) in enumerate((("Bear: the wave lands", 2.5, 0.3), ("Base", 3.5, 0.5), ("Bull: replacement cost holds", 4.5, 0.2))):
    r = 5 + i; Sc[f"A{r}"] = lab; put(Sc, f"B{r}", l, blue, "0.00"); put(Sc, f"C{r}", w, blue, "0%")
    put(Sc, f"D{r}", f"=Valuation!$B${e + 1}+(B{r}-{Lf})*Valuation!$B${e2 + 3}", black, "0.00")
    put(Sc, f"E{r}", f"=Valuation!$B${e2}+(B{r}-{Lf})*$B$2", black, "0.00")
    put(Sc, f"F{r}", f"=(E{r}+0.32)/{names['Share price, Oct 7 2026 close ($)']}-1", black, "0%")
Sc["A9"] = "Probability-weighted"; put(Sc, "D9", "=SUMPRODUCT(C5:C7,D5:D7)", black, "0.00"); put(Sc, "E9", "=SUMPRODUCT(C5:C7,E5:E7)", black, "0.00")
Sc.column_dimensions["A"].width = 34

# ---------------- LRMC of a new US project
Lr = wb.create_sheet("LRMC")
Lr["A1"] = "Flat 20-year fee a new US export project needs: after-tax unlevered hurdle, 4-year build (15/30/35/20%), 21% tax, 100% bonus depreciation at COD"; Lr["A1"].font = bold
for k, h in enumerate(["Project", "Type", "$ per tonne", "Hurdle", "Opex $/MMBtu", "Capex per MMBtu-yr", "PV of capex at COD", "Tax shield", "Annuity factor", "Fee needed"]):
    Lr.cell(row=3, column=k + 1, value=h).font = bold
import csv as _csv
comps = list(_csv.DictReader(open(os.path.join(os.path.dirname(__file__), "..", "data", "lrmc_capex_comps.csv"))))
for i, cpx in enumerate(comps):
    r = 4 + i
    Lr[f"A{r}"] = cpx["project"]; Lr[f"B{r}"] = cpx["type"]
    put(Lr, f"C{r}", float(cpx["usd_per_tonne"]), blue, "#,##0"); put(Lr, f"D{r}", 0.08, blue, "0.0%"); put(Lr, f"E{r}", f"={names['CEX']}", black, "0.00")
    put(Lr, f"F{r}", f"=C{r}/52", black, "0.00")
    put(Lr, f"G{r}", f"=F{r}*(0.15*(1+D{r})^4+0.30*(1+D{r})^3+0.35*(1+D{r})^2+0.20*(1+D{r}))", black, "0.00")
    put(Lr, f"H{r}", f"=0.21*F{r}", black, "0.00")
    put(Lr, f"I{r}", f"=(1-(1+D{r})^-20)/D{r}", black, "0.000")
    put(Lr, f"J{r}", f"=E{r}+(G{r}-H{r})/((1-0.21)*I{r})", black, "0.00")
Lr.column_dimensions["A"].width = 40
wb.save(OUT)
print("saved", OUT)
