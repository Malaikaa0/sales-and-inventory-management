"""
Fail when in-scope statement or branch coverage is below its own threshold.

    coverage json -o coverage.json
    python tools/ci/check_coverage.py coverage.json --statements 100 --branches 99

coverage.py's fail_under only checks the two combined, so they are checked here.
"""
import argparse
import json
import sys

parser = argparse.ArgumentParser()
parser.add_argument('report')
parser.add_argument('--statements', type=float, required=True)
parser.add_argument('--branches', type=float, required=True)
args = parser.parse_args()

with open(args.report, encoding='utf-8') as handle:
    totals = json.load(handle)['totals']

failed = False
for label, covered, total, minimum in (
    ('statements', totals['covered_lines'], totals['num_statements'], args.statements),
    ('branches', totals['covered_branches'], totals['num_branches'], args.branches),
):
    if not total:
        print(f'{label}: nothing measured')
        failed = True
        continue
    percent = 100 * covered / total
    ok = percent >= minimum
    failed = failed or not ok
    print(f'{label}: {covered}/{total} = {percent:.2f}% (minimum {minimum}%) {"ok" if ok else "FAILED"}')

sys.exit(1 if failed else 0)
