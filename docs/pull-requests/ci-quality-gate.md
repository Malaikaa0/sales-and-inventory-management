## What this adds

A CI quality gate, together with the work it checks: team unit tests, coverage scope, static analysis, control flow graphs and mutation testing.

Four checks: `Lint`, `Tests and coverage`, `SonarQube quality gate`, `Mutation testing`. Thresholds, suppressed findings and reasons are in `docs/ci.md`. No step uses `continue-on-error` or `|| true`.

## Expected result of the checks

All four are expected to pass. `Mutation testing` has no mutants to run, because this branch changes none of the mutated files.

## Checked before opening

- The Sonar job's script passed on a new SonarQube server from a clean clone. The same script failed a probe project with one added bug.
- The test and mutation steps were run on Linux in a `python:3.12` container.
- First run on GitHub (commit `3694124`): all four checks passed. Screenshots are in `reports/ci/`.
