## Do not merge

This pull request exists to show the quality gate blocking a change.

## The change

A bulk discount for large baskets in `transactions/services.py`: a new rule with several limits, and no tests.

## Why the pipeline should reject it

The existing 222 unit tests still pass, so tests alone would let it through.

| Check | Local result on this branch | Minimum |
| --- | --- | --- |
| In-scope statement coverage | 99.81% (1039 of 1041) | 100% |
| In-scope branch coverage | 98.39% (122 of 124) | 99% |
| Mutation kill rate, `services.py` | 77.5% (330 of 426, 96 survived) | 95% |

`SonarQube quality gate` is also red, but it is red on `main` too, so it is not evidence about this change.
