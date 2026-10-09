"""Builds vg_model_v7.xlsx: a formula-driven version of model_v7.py's central case
(inputs -> annual model 2027-2031 -> sum-of-the-parts today and at end-2028 -> fee the price
needs -> long-run fee x cost grid). Numbers in blue are inputs; everything else is a formula."""
import io, contextlib, os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.comments import Comment
with contextlib.redirect_stdout(io.StringIO()):
    import model_v7 as M, valuation as V, sotp as S
    from eps_path import DA as DAE

OUT = os.path.join(os.path.dirname(__file__), "..", "vg_model_v7.xlsx")
wb = Workbook()
blue = Font(name="Arial", color="0000FF"); black = Font(name="Arial"); bold = Font(name="Arial", bold=True)
green = Font(name="Arial", color="008000"); yellow = PatternFill("solid", fgColor="FFFF00")
def put(ws, cell, v, font=black, fmt=None, note=None, fill=None):
    ws[cell] = v; ws[cell].font = font
    if fmt: ws[cell].number_format = fmt
    if note: ws[cell].comment = Comment(note, "model")
    if fill: ws[cell].fill = fill

# ---------------- Inputs
I = wb.active; I.title = "Inputs"
I["A1"] = "Venture Global (VG) model v7 - inputs (blue = input, yellow = key assumption)"; I["A1"].font = bold
rows = [
 ("Share price, Oct 7 2026 close ($)", V.bs[M.PRICE_KEY], "0.00", "stockanalysis.com / Yahoo Finance close", False),
 ("Diluted shares (bn)", V.SHARES, "0.000", "Q2 2026 10-Q Note 16 (2,643m)", False),
 ("Tax rate", V.TAX, "0.0%", "close to the 19.2% Q2 2026 effective rate", False),
 ("Discount rate, contracted cash and capex", S.RC, "0.0%", "ASSUMPTION: a little above the 6.375%/6.625% VGLNG coupons issued in 2026", True),
 ("Discount rate, open cargoes", S.RO, "0.0%", "ASSUMPTION: above the 9.0% Series A preferred", True),
 ("Cost of net debt", V.DEBT_COST, "0.0%", "ASSUMPTION", False),
 ("Net debt end-2026 ($bn)", V.ND0, "0.00", "valuation.py estimate: 30 Jun net debt + H2 capex - H2 cash earnings", False),
 ("Series A preferred liquidation ($bn)", S.PREF_LIQ, "0.00", "Q2 2026 10-Q", False),
 ("Preferred dividend ($bn/yr)", V.PREF, "0.000", "4 x $67m quarterly, Q2 2026 10-Q", False),
 ("Minority share of EBITDA ($bn/yr)", V.NCI, "0.00", "2026 NCI guide midpoint, Q1 2026 deck", False),
 ("BP adjustment ($bn)", S.BP, "0.00", "ASSUMPTION: half of BP's $3.7bn low-end claim, after tax", False),
 ("Common dividend ($bn/yr)", M.DIV, "0.00", "$0.04/qtr on 2.498bn shares (Q2 2026 call)", False),
 ("2026 volume (TBtu)", V.vol[2026], "#,##0", "Aug 2026 cargo outlook x 3.7 TBtu", False),
 ("2026 open volume (TBtu)", V.open_tbtu[2026], "#,##0", "Q2 2026 deck $1 sensitivity midpoint", False),
 ("2026 contracted fee", 5.05, "0.00", "Aug 2026 release", False),
 ("2026 unsold fee assumption", 13.00, "0.00", "midpoint of $12.50-13.50, Aug 2026 release", False),
 ("2026 EBITDA guide midpoint ($bn)", 8.9, "0.00", "Aug 2026 release", False),
 ("Plaquemines basis cost 2026 ($bn)", M.BASIS26, "0.000", "Q4 2025 deck ($110m Q1) + Q1 2026 deck ($300-350m Q2-Q4)", False),
 ("CP2 contract fee premium over Calcasieu ($/MMBtu)", M.CP2X, "0.00", "ASSUMPTION: half of the lender-sizing back-solve (waterfall.py)", True),
 ("Long-run open fee from 2032 ($/MMBtu)", M.L_CENTRAL, "0.00", "ASSUMPTION: top of contract-market anchors, bottom of Sabel's $3.50-4.50", True),
 ("Contract fee in terminal ($/MMBtu)", 2.45, "0.00", "ASSUMPTION (Calcasieu-like)", False),
 ("Contracted volume threshold for CP2 premium (TBtu)", 1560, "#,##0", "Calcasieu 520 + Plaquemines 1,040", False),
 ("Maintenance capex in terminal ($bn/yr)", 1.0, "0.00", "ASSUMPTION", False),
 ("Terminal D&A tax shield base ($bn/yr)", 2.6, "0.00", "ASSUMPTION", False),
 ("Contract run-off year", 2049, "0", "ASSUMPTION: 20-year SPAs run off around 2049", False),
]
r0 = 3
names = {}
for i, (lab, v, fmt, note, key) in enumerate(rows):
    r = r0 + i
    I[f"A{r}"] = lab; I[f"A{r}"].font = black
    put(I, f"B{r}", v, blue, fmt, note, yellow if key else None)
    names[lab] = f"Inputs!$B${r}"
r = r0 + len(rows) + 1
I[f"A{r}"] = "2026 all-in cost per MMBtu (calibrated to guidance)"; put(I, f"B{r}", f"=({names['2026 volume (TBtu)']}-{names['2026 open volume (TBtu)']})*{names['2026 contracted fee']}/{names['2026 volume (TBtu)']}+{names['2026 open volume (TBtu)']}*{names['2026 unsold fee assumption']}/{names['2026 volume (TBtu)']}-{names['2026 EBITDA guide midpoint ($bn)']}*1000/{names['2026 volume (TBtu)']}", black, "0.000")
names["C26"] = f"Inputs!$B${r}"; r += 1
I[f"A{r}"] = "Underlying cost per MMBtu ex basis"; put(I, f"B{r}", f"={names['C26']}-{names['Plaquemines basis cost 2026 ($bn)']}*1000/{names['2026 volume (TBtu)']}", black, "0.000")
names["CEX"] = f"Inputs!$B${r}"; r += 2
# annual inputs
I[f"A{r}"] = "Annual inputs"; I[f"A{r}"].font = bold; r += 1
hdr = r
I[f"A{hdr}"] = "Item"
for j, y in enumerate(M.YEARS):
    c = chr(ord("B") + j); I[f"{c}{hdr}"] = str(y); I[f"{c}{hdr}"].font = bold
ann = [
 ("Volume (TBtu)", V.vol, "#,##0", "Aug 2026 outlook x 3.7 TBtu; 85 MTPA from 2030"),
 ("Open volume (TBtu)", V.open_tbtu, "#,##0", "$1 sensitivity midpoints (Aug deck); 2030-31 ASSUMPTION"),
 ("CME futures fee, JKM method ($/MMBtu)", M.FUT, "0.00", "CME settlements Oct 6 2026, JKM less 115% HH less $2"),
 ("Contract fee ($/MMBtu)", V.CONTRACT_FEE, "0.00", "ASSUMPTION"),
 ("Plaquemines basis cost ($bn)", M.BASIS, "0.000", "2027 as 2026, half in 2028, none after (company: declines in 2028)"),
 ("Committed capex ($bn)", V.CAPEX, "0.0", "ASSUMPTION"),
 ("D&A ($bn)", S.DA, "0.00", "ASSUMPTION"),
]
arow = {}
for k, (lab, d, fmt, note) in enumerate(ann):
    rr = hdr + 1 + k; I[f"A{rr}"] = lab
    for j, y in enumerate(M.YEARS):
        c = chr(ord("B") + j); put(I, f"{c}{rr}", float(d[y]), blue, fmt, note if j == 0 else None)
    arow[lab] = rr
I.column_dimensions["A"].width = 52
for c in "BCDEF": I.column_dimensions[c].width = 12

# ---------------- Model
Mo = wb.create_sheet("Model")
Mo["A1"] = "Annual model, central case ($bn unless stated)"; Mo["A1"].font = bold
Mo["A2"] = "Year"
for j, y in enumerate(M.YEARS):
    c = chr(ord("B") + j); Mo[f"{c}2"] = str(y); Mo[f"{c}2"].font = bold
def ref(lab, c): return f"Inputs!{c}${arow[lab]}"
lines = ["Volume (TBtu)", "Open volume (TBtu)", "Contracted volume (TBtu)", "Contracted margin before costs", "CP2 contract premium",
         "Open margin before costs", "Operating cost", "EBITDA", "Cost on contracted volume", "Cost on open volume",
         "Contracted EBITDA", "Open EBITDA", "D&A", "Interest on opening net debt", "Pre-tax income", "Tax", "Preferred and minority",
         "Net income to common", "EPS ($)", "Cash tax", "Capex", "Common dividend", "Free cash flow after dividends", "Closing net debt",
         "Net debt / EBITDA (x)", "Year index t", "Discount factor, contracted", "Discount factor, open", "Discount factor from end-2028, contracted", "Discount factor from end-2028, open"]
L = {lab: 3 + i for i, lab in enumerate(lines)}
for lab, rr in L.items(): Mo[f"A{rr}"] = lab
for j, y in enumerate(M.YEARS):
    c = chr(ord("B") + j); prev = chr(ord("B") + j - 1)
    f = {}
    f["Volume (TBtu)"] = f"={ref('Volume (TBtu)', c)}"
    f["Open volume (TBtu)"] = f"={ref('Open volume (TBtu)', c)}"
    f["Contracted volume (TBtu)"] = f"={c}{L['Volume (TBtu)']}-{c}{L['Open volume (TBtu)']}"
    f["Contracted margin before costs"] = f"={c}{L['Contracted volume (TBtu)']}*{ref('Contract fee ($/MMBtu)', c)}/1000"
    f["CP2 contract premium"] = f"=IF({y}>=2030,MAX(0,{c}{L['Contracted volume (TBtu)']}-{names['Contracted volume threshold for CP2 premium (TBtu)']})*{names['CP2 contract fee premium over Calcasieu ($/MMBtu)']}/1000,0)"
    f["Open margin before costs"] = f"={c}{L['Open volume (TBtu)']}*{ref('CME futures fee, JKM method ($/MMBtu)', c)}/1000"
    f["Operating cost"] = f"={names['CEX']}*{c}{L['Volume (TBtu)']}/1000+{ref('Plaquemines basis cost ($bn)', c)}"
    f["EBITDA"] = f"={c}{L['Contracted margin before costs']}+{c}{L['CP2 contract premium']}+{c}{L['Open margin before costs']}-{c}{L['Operating cost']}"
    f["Cost on contracted volume"] = f"={c}{L['Operating cost']}*{c}{L['Contracted volume (TBtu)']}/{c}{L['Volume (TBtu)']}"
    f["Cost on open volume"] = f"={c}{L['Operating cost']}*{c}{L['Open volume (TBtu)']}/{c}{L['Volume (TBtu)']}"
    f["Contracted EBITDA"] = f"={c}{L['Contracted margin before costs']}+{c}{L['CP2 contract premium']}-{c}{L['Cost on contracted volume']}"
    f["Open EBITDA"] = f"={c}{L['Open margin before costs']}-{c}{L['Cost on open volume']}"
    f["D&A"] = f"={ref('D&A ($bn)', c)}"
    opening = names["Net debt end-2026 ($bn)"] if j == 0 else f"{prev}{L['Closing net debt']}"
    f["Interest on opening net debt"] = f"={opening}*{names['Cost of net debt']}"
    f["Pre-tax income"] = f"={c}{L['EBITDA']}-{c}{L['D&A']}-{c}{L['Interest on opening net debt']}"
    f["Tax"] = f"={names['Tax rate']}*MAX(0,{c}{L['Pre-tax income']})"
    f["Preferred and minority"] = f"={names['Preferred dividend ($bn/yr)']}+{names['Minority share of EBITDA ($bn/yr)']}"
    f["Net income to common"] = f"={c}{L['Pre-tax income']}-{c}{L['Tax']}-{c}{L['Preferred and minority']}"
    f["EPS ($)"] = f"={c}{L['Net income to common']}/{names['Diluted shares (bn)']}"
    f["Cash tax"] = f"={names['Tax rate']}*MAX(0,{c}{L['EBITDA']}-{c}{L['Interest on opening net debt']}-(1+0.3*{j}))"
    f["Capex"] = f"={ref('Committed capex ($bn)', c)}"
    f["Common dividend"] = f"={names['Common dividend ($bn/yr)']}"
    f["Free cash flow after dividends"] = f"={c}{L['EBITDA']}-{c}{L['Interest on opening net debt']}-{c}{L['Cash tax']}-{c}{L['Capex']}-{c}{L['Preferred and minority']}-{c}{L['Common dividend']}"
    f["Closing net debt"] = f"={opening}-{c}{L['Free cash flow after dividends']}"
    f["Net debt / EBITDA (x)"] = f"={c}{L['Closing net debt']}/{c}{L['EBITDA']}"
    f["Year index t"] = f"={j + 1}"
    f["Discount factor, contracted"] = f"=1/(1+{names['Discount rate, contracted cash and capex']})^{c}{L['Year index t']}"
    f["Discount factor, open"] = f"=1/(1+{names['Discount rate, open cargoes']})^{c}{L['Year index t']}"
    f["Discount factor from end-2028, contracted"] = f"=IF({j + 1}>2,1/(1+{names['Discount rate, contracted cash and capex']})^({j + 1}-2),0)"
    f["Discount factor from end-2028, open"] = f"=IF({j + 1}>2,1/(1+{names['Discount rate, open cargoes']})^({j + 1}-2),0)"
    for lab, form in f.items():
        fmt = "0.00" if "EPS" in lab or "(x)" in lab or "factor" in lab else ("#,##0" if "TBtu" in lab else "0.00")
        put(Mo, f"{c}{L[lab]}", form, black, fmt)
Mo.column_dimensions["A"].width = 44

# ---------------- Valuation
Va = wb.create_sheet("Valuation")
Va["A1"] = "Sum of the parts ($bn unless stated)"; Va["A1"].font = bold
t, rc, ro, sh = names["Tax rate"], names["Discount rate, contracted cash and capex"], names["Discount rate, open cargoes"], names["Diluted shares (bn)"]
rng = lambda lab: f"Model!$B${L[lab]}:$F${L[lab]}"
yr = lambda lab: f"Model!$F${L[lab]}"
n = f"({names['Contract run-off year']}-2031)"
Lf = names["Long-run open fee from 2032 ($/MMBtu)"]; cex = names["CEX"]
term_ec = f"({yr('Contracted volume (TBtu)')}*({names['Contract fee in terminal ($/MMBtu)']}-{cex})/1000+MAX(0,{yr('Contracted volume (TBtu)')}-{names['Contracted volume threshold for CP2 premium (TBtu)']})*{names['CP2 contract fee premium over Calcasieu ($/MMBtu)']}/1000-{names['Maintenance capex in terminal ($bn/yr)']}*{yr('Contracted volume (TBtu)')}/{yr('Volume (TBtu)')})"
term_eo = f"({yr('Open volume (TBtu)')}*({Lf}-{cex})/1000-{names['Maintenance capex in terminal ($bn/yr)']}*(1-{yr('Contracted volume (TBtu)')}/{yr('Volume (TBtu)')}))"
term_conv = f"({yr('Contracted volume (TBtu)')}*({Lf}-{cex})/1000)"
items = [
 ("PV contracted cash 2027-31", f"=SUMPRODUCT(({rng('Contracted EBITDA')}*(1-{t})+{t}*{rng('D&A')})*{rng('Discount factor, contracted')})"),
 ("PV open cargoes 2027-31", f"=SUMPRODUCT({rng('Open EBITDA')}*(1-{t})*{rng('Discount factor, open')})"),
 ("PV committed capex", f"=-SUMPRODUCT({rng('Capex')}*{rng('Discount factor, contracted')})"),
 ("PV contracted annuity 2032-2049", f"=({term_ec}*(1-{t})+{t}*{names['Terminal D&A tax shield base ($bn/yr)']})*(1-(1+{rc})^-{n})/{rc}/(1+{rc})^5"),
 ("PV open cargoes from 2032", f"={term_eo}*(1-{t})/{ro}/(1+{ro})^5"),
 ("PV contracted volume turning open after 2049", f"={term_conv}*(1-{t})/{ro}/(1+{ro})^(5+{n})"),
 ("Less net debt end-2026", f"=-{names['Net debt end-2026 ($bn)']}"),
 ("Less preferred", f"=-{names['Series A preferred liquidation ($bn)']}"),
 ("Less Calcasieu minority", f"=-{names['Minority share of EBITDA ($bn/yr)']}*(1-{t})/{rc}"),
 ("Less BP adjustment", f"=-{names['BP adjustment ($bn)']}"),
]
for i, (lab, form) in enumerate(items):
    Va[f"A{3 + i}"] = lab; put(Va, f"B{3 + i}", form, black, "0.00")
e = 3 + len(items)
Va[f"A{e}"] = "Equity value today"; put(Va, f"B{e}", f"=SUM(B3:B{e - 1})", black, "0.00")
Va[f"A{e + 1}"] = "Value per share today ($)"; put(Va, f"B{e + 1}", f"=B{e}/{sh}", black, "0.00"); Va[f"A{e+1}"].font = bold
# end-2028 roll
r2 = e + 3
Va[f"A{r2 - 1}"] = "Value at end-2028"; Va[f"A{r2 - 1}"].font = bold
roll = [
 ("PV contracted cash 2029-31", f"=SUMPRODUCT(({rng('Contracted EBITDA')}*(1-{t})+{t}*{rng('D&A')})*{rng('Discount factor from end-2028, contracted')})"),
 ("PV open cargoes 2029-31", f"=SUMPRODUCT({rng('Open EBITDA')}*(1-{t})*{rng('Discount factor from end-2028, open')})"),
 ("PV capex 2029-31", f"=-SUMPRODUCT({rng('Capex')}*{rng('Discount factor from end-2028, contracted')})"),
 ("PV contracted annuity 2032-2049", f"=({term_ec}*(1-{t})+{t}*{names['Terminal D&A tax shield base ($bn/yr)']})*(1-(1+{rc})^-{n})/{rc}/(1+{rc})^3"),
 ("PV open cargoes from 2032", f"={term_eo}*(1-{t})/{ro}/(1+{ro})^3"),
 ("PV contracted volume turning open after 2049", f"={term_conv}*(1-{t})/{ro}/(1+{ro})^(3+{n})"),
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
Va[f"A{e2 + 3}"] = "Value per share per $1 of long-run fee"; put(Va, f"B{e2 + 3}", f"=(({yr('Open volume (TBtu)')}/1000)*(1-{t})/{ro}/(1+{ro})^5+({yr('Contracted volume (TBtu)')}/1000)*(1-{t})/{ro}/(1+{ro})^(5+{n}))/{sh}", black, "0.00")
Va[f"A{e2 + 4}"] = "Long-run fee the price needs ($/MMBtu)"; put(Va, f"B{e2 + 4}", f"={Lf}+(B{e2 + 2}-B{e + 1})/B{e2 + 3}", black, "0.00")
Va.column_dimensions["A"].width = 50

# ---------------- Grid (flat cost, no basis)
G = wb.create_sheet("Grid")
G["A1"] = "Value per share today: long-run fee from 2032 (rows) x flat cost per MMBtu (columns), no basis cost"; G["A1"].font = bold
costs = [1.15, 0.92, 0.75, 0.60]; fees = [2.5, 3.0, 3.5, 4.0, 4.5, 5.19, 6.0]
G["A3"] = "Long-run fee \\ cost"
for j, cst in enumerate(costs):
    put(G, f"{chr(66 + j)}3", cst, blue, "0.00")
for i, fv in enumerate(fees):
    rr = 4 + i; put(G, f"A{rr}", fv, blue, "0.00")
    for j in range(len(costs)):
        cc = chr(66 + j); c = f"{cc}$3"; Lc = f"$A{rr}"
        con = rng('Contracted volume (TBtu)'); op = rng('Open volume (TBtu)'); vo = rng('Volume (TBtu)')
        ecs = f"({rng('Contracted margin before costs')}+{rng('CP2 contract premium')}-{c}*{con}/1000)"
        eos = f"({op}*Inputs!$B${arow['CME futures fee, JKM method ($/MMBtu)']}:$F${arow['CME futures fee, JKM method ($/MMBtu)']}/1000-{c}*{op}/1000)"
        tec = f"({yr('Contracted volume (TBtu)')}*({names['Contract fee in terminal ($/MMBtu)']}-{c})/1000+MAX(0,{yr('Contracted volume (TBtu)')}-{names['Contracted volume threshold for CP2 premium (TBtu)']})*{names['CP2 contract fee premium over Calcasieu ($/MMBtu)']}/1000-{names['Maintenance capex in terminal ($bn/yr)']}*{yr('Contracted volume (TBtu)')}/{yr('Volume (TBtu)')})"
        teo = f"({yr('Open volume (TBtu)')}*({Lc}-{c})/1000-{names['Maintenance capex in terminal ($bn/yr)']}*(1-{yr('Contracted volume (TBtu)')}/{yr('Volume (TBtu)')}))"
        tcv = f"({yr('Contracted volume (TBtu)')}*({Lc}-{c})/1000)"
        form = (f"=(SUMPRODUCT(({ecs}*(1-{t})+{t}*{rng('D&A')})*{rng('Discount factor, contracted')})"
                f"+SUMPRODUCT({eos}*(1-{t})*{rng('Discount factor, open')})"
                f"-SUMPRODUCT({rng('Capex')}*{rng('Discount factor, contracted')})"
                f"+({tec}*(1-{t})+{t}*{names['Terminal D&A tax shield base ($bn/yr)']})*(1-(1+{rc})^-{n})/{rc}/(1+{rc})^5"
                f"+{teo}*(1-{t})/{ro}/(1+{ro})^5+{tcv}*(1-{t})/{ro}/(1+{ro})^(5+{n})"
                f"-{names['Net debt end-2026 ($bn)']}-{names['Series A preferred liquidation ($bn)']}-{names['Minority share of EBITDA ($bn/yr)']}*(1-{t})/{rc}-{names['BP adjustment ($bn)']})/{sh}")
        put(G, f"{cc}{rr}", form, black, "0.00")
G.column_dimensions["A"].width = 22
for ws in wb.worksheets:
    for row in ws.iter_rows():
        for cell in row:
            if cell.font is None or cell.font.name != "Arial":
                cell.font = Font(name="Arial", bold=cell.font.bold if cell.font else False, color=cell.font.color if cell.font else None)
wb.save(OUT)
print("saved", OUT)
