# Orlando Deal Desk

A practice tool for underwriting small multifamily properties (2–48 units) in the Orlando area. It generates realistic-looking listings, has you work out the numbers yourself, checks your answers, and logs every deal to an Excel workbook that keeps live formulas.

> All listings are generated for practice. None of them are real properties, and the market assumptions in `deal_desk/market.py` are illustrative, not live data.

## What's in here

| Part | What it does |
|---|---|
| `app/index.html` | The practice app. Open it in any browser; there's nothing to install. |
| `deal_desk/` | Python engine: listing generator, underwriting math, and an Excel writer with live formulas. |
| `python -m deal_desk` | Screens hundreds or thousands of listings and writes `orlando_deals.xlsx`. |
| `tests/` | Checks the math by hand, against Excel's `PMT`, and on the Excel export. |

## The app

Open `app/index.html` in Chrome, Edge, Safari or Firefox.

- **Desk.** A feed of generated listings. Each one has a rent roll with current and market rent per unit type, taxes, insurance, owner-paid utilities, repairs and other income.
- **Practice quiz.** Five levels, each unlocked after two perfect rounds in a row:
  1. Income: gross potential rent, vacancy loss, effective gross income
  2. Expenses and NOI
  3. Valuation: cap rate, value at the area cap rate, price per unit
  4. Financing: debt service, DSCR, cash needed to close, cash-on-cash
  5. Value-add: stabilized NOI, yield on cost, stabilized value, equity created

  Answers within 1% count. You can type shorthand like `450k` or `1.2m`. After you check, each question shows a worked solution.
- **Underwrite and value-add.** Change any rent, expense, loan term, rehab budget, renovation premium, RUBS recapture or exit cap. The pro forma, cash to close, value-add case and a Buy / Value-add buy / Watch / Pass verdict update as you type. It also shows the maximum price that still covers debt at 1.25x DSCR.
- **Deal Log.** Every property you quiz on or underwrite is added here automatically. **Export to Excel** writes a `Summary` sheet and a `Deals` sheet, and every metric in it is a live Excel formula.
- **Screener.** Runs the same underwriting over 1,000 or more generated listings, filters by neighborhood, DSCR and cash-on-cash, and exports the batch.
- **Formulas.** A reference for every metric.

## The Python batch tool

```bash
pip install -r requirements.txt
python -m deal_desk --count 1000                     # writes orlando_deals.xlsx
python -m deal_desk --count 5000 --rate 0.065 --ltv 0.70 --out deals_65.xlsx
pytest
```

The workbook has three sheets:

- **Summary:** deal count, units, median cap rate, average DSCR, verdict counts, total equity created, capital needed, total loss-to-lease, and a neighborhood breakdown. Every figure is built from `COUNTIF`, `AVERAGEIF`, `SUMIF` and `MEDIAN` over the Deals sheet.
- **Deals:** one row per property. Inputs sit in plain columns. GPR, EGI, OpEx, NOI, cap rate, debt service (`PMT`), DSCR, cash needed, cash-on-cash, yield on cost, stabilized value, equity created and the verdict are all formulas, with conditional formatting on the verdict.
- **Rent Roll:** one row per unit type, with loss-to-lease and annual upside.

## The model

| Metric | Formula |
|---|---|
| GPR | Σ units × monthly rent × 12 |
| EGI | GPR × (1 − vacancy) + other income |
| OpEx | taxes + insurance + owner-paid utilities + repairs + management (% of EGI) + payroll/admin + replacement reserves |
| NOI | EGI − OpEx |
| Cap rate | NOI ÷ price |
| Debt service | `-PMT(rate/12, years×12, loan) × 12` |
| DSCR | NOI ÷ debt service |
| Cash needed | down payment + closing costs + loan fee + rehab + cash reserves |
| Cash-on-cash | (NOI − debt service) ÷ cash needed |
| Stabilized NOI | renovated units at market rent + premium, plus RUBS bill-back, with repairs down 15% |
| Yield on cost | stabilized NOI ÷ (price + closing + rehab) |
| Equity created | stabilized NOI ÷ market cap − all-in cost |

**Verdict rules.** A deal is a **Buy** at DSCR ≥ 1.25 and cash-on-cash ≥ 7%. It's a **Value-add buy** when yield on cost beats the market cap by 1 point or more, stabilized DSCR is ≥ 1.25, and equity created is positive. It's a **Watch** at DSCR ≥ 1.10 or a thinner value-add spread. Everything else is a **Pass**.

**Default terms.** 75% LTV, 7.0% interest, 30-year amortization, 3% closing costs, 1% loan fee, $1,000 per unit cash reserves, 8% management, $400 per unit payroll/admin, and $300 per unit replacement reserves.

## Next steps toward real listings

1. Replace `generate_properties()` with a loader for a real feed, such as an MLS/CoStar/LoopNet CSV export or the Orange County Property Appraiser data for taxes and assessed values.
2. Map each listing into the same `Property` dataclass. The underwriting and Excel export stay the same.
3. Schedule the screen to run daily and append new rows to the workbook.
