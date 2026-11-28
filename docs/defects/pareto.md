# Pareto analysis — defects by category

The chart covers the eight defects confirmed for Sale and Void sale on 28 Nov 2026:

- N1–N6 were found by the API tests.
- N7 and N8 were found by the Playwright E2E tests.

The chart is [`reports/api/pareto.png`](../../reports/api/pareto.png). To regenerate it, run `python reports/api/make_pareto.py`; it needs matplotlib 3.11.2 (`tools/generator/requirements.txt`).

![Pareto chart of defects by category](../../reports/api/pareto.png)

## Categories

| Defect | Category | Severity / priority | Why this category |
| --- | --- | --- | --- |
| N2 | Input validation | Major / P2 | No upper bound on purchase quantity |
| N7 | Input validation | Major / P2 | Out-of-range tax silently clamped by the till instead of rejected |
| N5 | Input validation | Minor / P3 | `false` accepted as 0 (wrong type not rejected) |
| N6 | Input validation | Minor / P3 | No upper bound on item ids, leading to a 500 |
| N1 | Error reporting | Minor / P3 | Correct rejection, wrong message |
| N3 | Error reporting | Minor / P3 | Correct rejection, but 200 instead of 4xx |
| N8 | Error reporting | Minor / P3 | Ended session shown as "Unexpected server response." |
| N4 | Idempotency / repeats | Major / P1 (P2 proposed) | Repeated request creates a second sale |

## Counts, sorted

| Category | Defects | % | Cumulative % |
| --- | --- | --- | --- |
| Input validation | 4 | 50.0 | 50.0 |
| Error reporting | 3 | 37.5 | 87.5 |
| Idempotency / repeats | 1 | 12.5 | 100.0 |
| **Total** | **8** | **100** | |

## Reading

- **Input validation and error reporting** together hold 87.5% of the defects. That passes the 80% line, so these two categories are the "vital few".
- **Input validation** is still the largest category, and it now includes a defect in the browser (N7) as well as on the server (N2, N5, N6).
  - The shared rule, "every numeric input has a type check, a minimum and a maximum", must apply on both sides.
  - The client must show an error for an invalid value, not change it silently.
  - This is preventive action 1 in [rca-N2.md](rca-N2.md), widened to the UI.
- **Error reporting** defects do not corrupt data. Each one gives the user the wrong message or status (N1, N3, N8), so one review of error paths and messages would fix all three.
- **Fix order** is set by priority, not by count:
  1. N4 (double charge, stock wrong).
  2. The input validation rule (N2 and N7 are Major).
  3. The error-reporting review.
- **Not counted:** W1 (void never returns 4xx) is an accepted endpoint weakness. Defects in other members' areas, such as the dashboard accessibility defects, are tracked by their owners.
