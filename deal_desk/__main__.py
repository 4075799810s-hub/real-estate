"""Screen a batch of generated Orlando multifamily listings and export to Excel.

    python -m deal_desk --count 1000 --out deals.xlsx
    python -m deal_desk --count 500 --rate 0.065 --ltv 0.7
"""

import argparse
from collections import Counter

from .generator import generate_properties
from .underwriting import assumptions_from, underwrite
from .excel import write_workbook


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--count", type=int, default=1000, help="number of listings to generate (default 1000)")
    ap.add_argument("--seed", type=int, default=42, help="random seed, same seed = same listings")
    ap.add_argument("--out", default="orlando_deals.xlsx", help="output workbook path")
    ap.add_argument("--rate", type=float, help="interest rate override, e.g. 0.065")
    ap.add_argument("--ltv", type=float, help="loan-to-value override, e.g. 0.70")
    ap.add_argument("--top", type=int, default=10, help="print the top N deals by yield on cost")
    args = ap.parse_args(argv)

    overrides = {k: v for k, v in (("rate", args.rate), ("ltv", args.ltv)) if v is not None}
    deals = []
    for p in generate_properties(args.count, args.seed):
        deals.append((p, assumptions_from(p).with_(**overrides)))

    results = [(p, underwrite(p, a)) for p, a in deals]
    counts = Counter(r.verdict for _, r in results)
    print(f"Screened {len(results):,} listings: " + ", ".join(f"{counts[v]} {v}" for v in ("Buy", "Value-add buy", "Watch", "Pass")))
    if args.top > 0:
        print(f"\nTop {args.top} by yield on cost:")
        print(f"{'ID':<10} {'Property':<26} {'Area':<15} {'Units':>5} {'Price':>12} {'Cap':>6} {'DSCR':>5} {'YoC':>6} {'Cash needed':>12}  Verdict")
    for p, r in sorted(results, key=lambda x: -x[1].yoc)[: max(args.top, 0)]:
        print(f"{p.id:<10} {p.name[:26]:<26} {p.neighborhood:<15} {p.units:>5} {p.asking_price:>12,.0f} "
              f"{r.cap_rate:>6.2%} {r.dscr:>5.2f} {r.yoc:>6.2%} {r.cash_needed:>12,.0f}  {r.verdict}")

    write_workbook(deals, args.out)
    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
