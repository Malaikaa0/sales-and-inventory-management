# Pareto analysis — defects by category

The chart covers the six defects confirmed by the API tests for Sale and Void sale (N1–N6, 28 Nov 2026). The chart is [`reports/api/pareto.png`](../../reports/api/pareto.png). To regenerate it, run `python reports/api/make_pareto.py`; it needs matplotlib, which is installed in `.venv` (3.11.2).

![Pareto chart of defects by category](../../reports/api/pareto.png)

## Categories

| Defect | Category | Severity | Why this category |
| --- | --- | --- | --- |
| N2 | Input validation | Major | No upper bound on purchase quantity |
| N5 | Input validation | Minor | `false` accepted as 0 (wrong type not rejected) |
| N6 | Input validation | Minor | No upper bound on item ids, leading to a 500 |
| N1 | Error reporting | Minor | Correct rejection, wrong message |
| N3 | Error reporting | Minor | Correct rejection, but 200 instead of 4xx |
| N4 | Idempotency / repeats | Major | Repeated request creates a second sale |

## Counts, sorted

| Category | Defects | % | Cumulative % |
| --- | --- | --- | --- |
| Input validation | 3 | 50.0 | 50.0 |
| Error reporting | 2 | 33.3 | 83.3 |
| Idempotency / repeats | 1 | 16.7 | 100.0 |
| **Total** | **6** | **100** | |

## Reading

- **Input validation** and **error reporting** together hold 83% of the defects. That passes the 80% line, so these two categories are the "vital few" to fix first.
- **Input validation** is where most defects are found. The improvement with the biggest effect is one shared rule that every numeric input has a type check, a minimum and a maximum. That rule covers N2, N5 and N6, and is preventive action 1 in [rca-N2.md](rca-N2.md).
- **Idempotency** has only one defect, but it is the highest-priority one (P1: double charge, stock wrong). Count alone does not set the fix order: N4 is fixed first, then the input validation rule.
- **Not counted:** W1 (void never returns 4xx) is an accepted endpoint weakness, not a defect. Member 1's failing unit test is a test problem, not an app defect.
