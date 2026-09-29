"""Underwriting math: NOI, cap rate, debt, cash needed, and the value-add case.

Same formulas as the browser app (app/index.html) and the Excel export.
"""

from dataclasses import dataclass, field, replace

from .generator import Property


@dataclass
class Assumptions:
    price: float
    taxes: float
    insurance: float
    util_monthly: float  # all owner-paid utilities
    util_rubs_base: float  # water/sewer + trash, the part you can bill back
    other_monthly: float
    repairs_per_unit: float
    vacancy: float
    rents: list[float]
    market_rents: list[float]
    rehab_per_unit: float
    market_cap: float
    mgmt_pct: float = 0.08
    payroll_per_unit: float = 400
    reserves_per_unit: float = 300
    ltv: float = 0.75
    rate: float = 0.07
    amort_years: int = 30
    closing_pct: float = 0.03
    loan_fee_pct: float = 0.01
    reserves_cash: float = 1000  # per unit, held at closing
    reno_premium: float = 0.05
    rubs_pct: float = 0.6

    def with_(self, **kw) -> "Assumptions":
        return replace(self, **kw)


def assumptions_from(p: Property) -> Assumptions:
    return Assumptions(
        price=p.asking_price, taxes=p.taxes, insurance=p.insurance,
        util_monthly=p.util_water + p.util_trash + p.util_elec,
        util_rubs_base=p.util_water + p.util_trash, other_monthly=p.other_monthly,
        repairs_per_unit=p.repairs_per_unit, vacancy=p.vacancy,
        rents=[g.rent for g in p.mix], market_rents=[g.market for g in p.mix],
        rehab_per_unit=p.rehab_per_unit, market_cap=p.market_cap,
    )


def annual_debt_service(loan: float, rate: float, years: int) -> float:
    if loan <= 0:
        return 0.0
    r, n = rate / 12, years * 12
    if r == 0:
        return loan / years
    return 12 * loan * r / (1 - (1 + r) ** -n)


@dataclass
class Result:
    gpr: float
    vac_loss: float
    egi: float
    opex: float
    noi: float
    cap_rate: float
    loan: float
    debt_service: float
    dscr: float
    cash_needed: float
    cash_flow: float
    coc: float
    price_per_unit: float
    value_at_market_cap: float
    stab_noi: float
    all_in: float
    yoc: float
    stab_value: float
    equity_created: float
    stab_dscr: float
    verdict: str
    reasons: list[str] = field(default_factory=list)


def underwrite(p: Property, a: Assumptions) -> Result:
    u = p.units
    gpr = sum(g.count * r * 12 for g, r in zip(p.mix, a.rents))
    vac_loss = gpr * a.vacancy
    other = a.other_monthly * 12
    egi = gpr - vac_loss + other
    utilities = a.util_monthly * 12
    repairs = a.repairs_per_unit * u
    payroll = a.payroll_per_unit * u
    reserves = a.reserves_per_unit * u
    opex = a.taxes + a.insurance + utilities + repairs + egi * a.mgmt_pct + payroll + reserves
    noi = egi - opex

    loan = a.price * a.ltv
    ds = annual_debt_service(loan, a.rate, a.amort_years)
    dscr = noi / ds if ds else float("inf")
    closing = a.price * a.closing_pct
    rehab = a.rehab_per_unit * u
    cash_needed = (a.price - loan) + closing + loan * a.loan_fee_pct + rehab + a.reserves_cash * u
    cash_flow = noi - ds
    coc = cash_flow / cash_needed

    # value-add: renovated units rent at market x (1 + premium); RUBS on water/sewer/trash; repairs drop 15%
    bump = 1 + a.reno_premium if a.rehab_per_unit > 0 else 1
    stab_rents = [max(r, m * bump) for r, m in zip(a.rents, a.market_rents)]
    stab_gpr = sum(g.count * r * 12 for g, r in zip(p.mix, stab_rents))
    stab_egi = stab_gpr * (1 - a.vacancy) + other + a.util_rubs_base * 12 * a.rubs_pct
    stab_opex = (a.taxes + a.insurance + utilities + repairs * 0.85 + stab_egi * a.mgmt_pct + payroll + reserves)
    stab_noi = stab_egi - stab_opex
    all_in = a.price + closing + rehab
    yoc = stab_noi / all_in
    stab_value = stab_noi / a.market_cap
    equity = stab_value - all_in
    stab_dscr = stab_noi / ds if ds else float("inf")

    reasons = []
    if dscr >= 1.25 and coc >= 0.07:
        verdict = "Buy"
        reasons.append("Cash flows well on day one.")
    elif yoc - a.market_cap >= 0.01 and stab_dscr >= 1.25 and equity > 0:
        verdict = "Value-add buy"
        reasons.append(f"Yield on cost {yoc:.2%} beats the {a.market_cap:.2%} market cap by 1+ point.")
    elif dscr >= 1.1 or (yoc - a.market_cap >= 0.005 and equity > 0):
        verdict = "Watch"
        reasons.append("Close. It could work at a lower price.")
    else:
        verdict = "Pass"
        reasons.append("Income doesn't support this price.")

    return Result(gpr, vac_loss, egi, opex, noi, noi / a.price, loan, ds, dscr, cash_needed, cash_flow, coc,
                  a.price / u, noi / a.market_cap, stab_noi, all_in, yoc, stab_value, equity, stab_dscr,
                  verdict, reasons)
