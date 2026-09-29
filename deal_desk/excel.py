"""Write analyzed properties to an Excel workbook with live formulas.

Inputs go in plain columns; every metric (GPR, EGI, NOI, cap rate, DSCR, cash
needed, cash-on-cash, yield on cost, equity created, verdict) is an Excel formula,
so changing an input in Excel recalculates the deal.
"""

from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

from .generator import Property
from .underwriting import Assumptions, underwrite

USD, PCT, MULT = '"$"#,##0', "0.00%", '0.00"x"'

# (header, getter(property, assumptions, result), number format)
INPUTS = [
    ("ID", lambda p, a, r: p.id, None),
    ("Property", lambda p, a, r: p.name, None),
    ("Address", lambda p, a, r: p.address, None),
    ("Neighborhood", lambda p, a, r: p.neighborhood, None),
    ("Units", lambda p, a, r: p.units, None),
    ("Year built", lambda p, a, r: p.year_built, None),
    ("Class", lambda p, a, r: p.cond, None),
    ("Price", lambda p, a, r: a.price, USD),
    ("Monthly rent roll", lambda p, a, r: r.gpr / 12, USD),
    ("Vacancy %", lambda p, a, r: a.vacancy, PCT),
    ("Other income /mo", lambda p, a, r: a.other_monthly, USD),
    ("Taxes /yr", lambda p, a, r: a.taxes, USD),
    ("Insurance /yr", lambda p, a, r: a.insurance, USD),
    ("Utilities /mo", lambda p, a, r: a.util_monthly, USD),
    ("Repairs /unit/yr", lambda p, a, r: a.repairs_per_unit, USD),
    ("Mgmt % EGI", lambda p, a, r: a.mgmt_pct, PCT),
    ("Payroll /unit/yr", lambda p, a, r: a.payroll_per_unit, USD),
    ("Reserves /unit/yr", lambda p, a, r: a.reserves_per_unit, USD),
    ("LTV", lambda p, a, r: a.ltv, PCT),
    ("Rate", lambda p, a, r: a.rate, PCT),
    ("Amort yrs", lambda p, a, r: a.amort_years, None),
    ("Closing %", lambda p, a, r: a.closing_pct, PCT),
    ("Loan fee %", lambda p, a, r: a.loan_fee_pct, PCT),
    ("Rehab /unit", lambda p, a, r: a.rehab_per_unit, USD),
    ("Cash reserves /unit", lambda p, a, r: a.reserves_cash, USD),
    ("Market cap", lambda p, a, r: a.market_cap, PCT),
    ("Stabilized NOI", lambda p, a, r: r.stab_noi, USD),
]

FORMULAS = [
    ("GPR", "{Monthly rent roll}*12", USD),
    ("EGI", "{GPR}*(1-{Vacancy %})+{Other income /mo}*12", USD),
    ("OpEx", "{Taxes /yr}+{Insurance /yr}+{Utilities /mo}*12+{Repairs /unit/yr}*{Units}"
             "+{Mgmt % EGI}*{EGI}+{Payroll /unit/yr}*{Units}+{Reserves /unit/yr}*{Units}", USD),
    ("NOI", "{EGI}-{OpEx}", USD),
    ("Cap rate", "{NOI}/{Price}", PCT),
    ("Loan", "{Price}*{LTV}", USD),
    ("Debt service", "-PMT({Rate}/12,{Amort yrs}*12,{Loan})*12", USD),
    ("DSCR", "{NOI}/{Debt service}", MULT),
    ("Cash needed", "{Price}-{Loan}+{Price}*{Closing %}+{Loan}*{Loan fee %}"
                    "+{Rehab /unit}*{Units}+{Cash reserves /unit}*{Units}", USD),
    ("Cash flow", "{NOI}-{Debt service}", USD),
    ("Cash-on-cash", "{Cash flow}/{Cash needed}", PCT),
    ("Price / unit", "{Price}/{Units}", USD),
    ("Value @ mkt cap", "{NOI}/{Market cap}", USD),
    ("All-in cost", "{Price}*(1+{Closing %})+{Rehab /unit}*{Units}", USD),
    ("Yield on cost", "{Stabilized NOI}/{All-in cost}", PCT),
    ("Stabilized value", "{Stabilized NOI}/{Market cap}", USD),
    ("Equity created", "{Stabilized value}-{All-in cost}", USD),
    ("Verdict",
     'IF(AND({DSCR}>=1.25,{Cash-on-cash}>=0.07),"Buy",'
     'IF(AND({Yield on cost}-{Market cap}>=0.01,{Stabilized NOI}/{Debt service}>=1.25,{Equity created}>0),"Value-add buy",'
     'IF(OR({DSCR}>=1.1,AND({Yield on cost}-{Market cap}>=0.005,{Equity created}>0)),"Watch","Pass")))', None),
]

HEADERS = [h for h, _, _ in INPUTS] + [h for h, _, _ in FORMULAS]
COL = {h: get_column_letter(i + 1) for i, h in enumerate(HEADERS)}

HEAD_FILL = PatternFill("solid", fgColor="0B7169")
HEAD_FONT = Font(bold=True, color="FFFFFF")


def _formula(template: str, row: int) -> str:
    out = template
    for h in sorted(COL, key=len, reverse=True):  # longest first so "NOI" doesn't clobber "Stabilized NOI"
        out = out.replace("{" + h + "}", f"{COL[h]}{row}")
    return "=" + out


def write_workbook(deals: list[tuple[Property, Assumptions]], path: str) -> str:
    wb = Workbook()
    summary = wb.active
    summary.title = "Summary"
    ws = wb.create_sheet("Deals")
    rr = wb.create_sheet("Rent Roll")

    # --- Deals
    ws.append(HEADERS)
    for i, (p, a) in enumerate(deals, start=2):
        r = underwrite(p, a)
        for c, (_, get, fmt) in enumerate(INPUTS, start=1):
            cell = ws.cell(row=i, column=c, value=get(p, a, r))
            if fmt:
                cell.number_format = fmt
        for c, (_, tmpl, fmt) in enumerate(FORMULAS, start=len(INPUTS) + 1):
            cell = ws.cell(row=i, column=c, value=_formula(tmpl, i))
            if fmt:
                cell.number_format = fmt
    last = max(len(deals) + 1, 2)
    for c in range(1, len(HEADERS) + 1):
        h = ws.cell(row=1, column=c)
        h.fill, h.font = HEAD_FILL, HEAD_FONT
        h.alignment = Alignment(wrap_text=True, vertical="center")
        ws.column_dimensions[get_column_letter(c)].width = 14
    ws.column_dimensions["B"].width = 26
    ws.column_dimensions["C"].width = 40
    ws.column_dimensions["D"].width = 16
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(HEADERS))}{last}"
    v = COL["Verdict"]
    rng = f"{v}2:{v}{last}"
    for text, color in (("Buy", "C6EFCE"), ("Value-add buy", "FCE4B6"), ("Watch", "FFF2CC"), ("Pass", "F8CBAD")):
        ws.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=[f'"{text}"'],
                                                      fill=PatternFill("solid", fgColor=color)))

    # --- Rent roll (one row per unit type)
    rr.append(["ID", "Property", "Unit type", "Units", "Current rent", "Market rent",
               "Loss to lease /mo", "Annual upside"])
    row = 2
    for p, a in deals:
        for g, cur, mkt in zip(p.mix, a.rents, a.market_rents):
            rr.append([p.id, p.name, g.type, g.count, cur, mkt,
                       f"=MAX(F{row}-E{row},0)*D{row}", f"=G{row}*12"])
            for col in "EFGH":
                rr[f"{col}{row}"].number_format = USD
            row += 1
    for c in range(1, 9):
        h = rr.cell(row=1, column=c)
        h.fill, h.font = HEAD_FILL, HEAD_FONT
        rr.column_dimensions[get_column_letter(c)].width = 16
    rr.column_dimensions["B"].width = 26
    rr.freeze_panes = "A2"
    if row > 2:
        t = Table(displayName="RentRoll", ref=f"A1:H{row - 1}")
        t.tableStyleInfo = TableStyleInfo(name="TableStyleLight9", showRowStripes=True)
        rr.add_table(t)

    # --- Summary (all formulas over the Deals sheet)
    def col(h):
        return f"Deals!{COL[h]}2:{COL[h]}{last}"

    rows = [
        ("Orlando Deal Desk: batch underwriting", None, None),
        ("Practice data. Every property is generated, not a real listing.", None, None),
        (None, None, None),
        ("Properties analyzed", f"=COUNTA({col('ID')})", None),
        ("Total units", f"=SUM({col('Units')})", None),
        ("Total asking volume", f"=SUM({col('Price')})", USD),
        ("Median price / unit", f"=MEDIAN({col('Price / unit')})", USD),
        ("Median cap rate", f"=MEDIAN({col('Cap rate')})", PCT),
        ("Average DSCR", f"=AVERAGE({col('DSCR')})", MULT),
        ("Buy", f'=COUNTIF({col("Verdict")},"Buy")', None),
        ("Value-add buy", f'=COUNTIF({col("Verdict")},"Value-add buy")', None),
        ("Watch", f'=COUNTIF({col("Verdict")},"Watch")', None),
        ("Pass", f'=COUNTIF({col("Verdict")},"Pass")', None),
        ("Equity created across value-add buys",
         f'=SUMIF({col("Verdict")},"Value-add buy",{col("Equity created")})', USD),
        ("Capital needed for all Buy + Value-add buy deals",
         f'=SUMIF({col("Verdict")},"Buy",{col("Cash needed")})+SUMIF({col("Verdict")},"Value-add buy",{col("Cash needed")})', USD),
        ("Annual loss-to-lease across portfolio", f"=SUM('Rent Roll'!H2:H{max(row - 1, 2)})", USD),
    ]
    for label, val, fmt in rows:
        summary.append([label, val])
        if fmt:
            summary.cell(row=summary.max_row, column=2).number_format = fmt
    summary["A1"].font = Font(bold=True, size=14)
    summary["A2"].font = Font(italic=True, color="666666")
    summary.column_dimensions["A"].width = 50
    summary.column_dimensions["B"].width = 20

    # --- Neighborhood breakdown with COUNTIFS / AVERAGEIFS
    start = summary.max_row + 2
    summary.cell(row=start, column=1, value="By neighborhood").font = Font(bold=True)
    hdr = ["Neighborhood", "Deals", "Median-ish cap (avg)", "Avg DSCR", "Value-add buys"]
    for c, h in enumerate(hdr, start=1):
        cell = summary.cell(row=start + 1, column=c, value=h)
        cell.fill, cell.font = HEAD_FILL, HEAD_FONT
    for j, nb in enumerate(sorted({p.neighborhood for p, _ in deals})):
        r = start + 2 + j
        summary.cell(row=r, column=1, value=nb)
        summary.cell(row=r, column=2, value=f'=COUNTIF({col("Neighborhood")},A{r})')
        summary.cell(row=r, column=3, value=f'=AVERAGEIF({col("Neighborhood")},A{r},{col("Cap rate")})').number_format = PCT
        summary.cell(row=r, column=4, value=f'=AVERAGEIF({col("Neighborhood")},A{r},{col("DSCR")})').number_format = MULT
        summary.cell(row=r, column=5, value=f'=COUNTIFS({col("Neighborhood")},A{r},{col("Verdict")},"Value-add buy")')
    for c in "CDE":
        summary.column_dimensions[c].width = 18

    wb.save(path)
    return path
