## Do not merge

This pull request exists to show the quality gate blocking a change.

## The change

A bulk discount for large baskets in `transactions/services.py`: a new rule with several limits, and no tests.

## Why the pipeline should reject it

The existing unit tests still pass, so passing tests alone would let it through.

| Check | Local result on this change | Minimum |
| --- | --- | --- |
| In-scope statement coverage | 99.81% (1039 of 1041) | 100% |
| In-scope branch coverage | 98.39% (122 of 124) | 99% |
| Mutation kill rate, `services.py` | 77.5% (330 of 426, 96 survived) | 95% |

Expected red checks: `Tests and coverage` and `Mutation testing`. `SonarQube quality gate` may pass, since it requires only 90% coverage.
