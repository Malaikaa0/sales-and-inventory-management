## What this adds

A CI quality gate, together with the Member 1 work it checks: team unit tests, coverage scope, static analysis, control flow graphs and mutation testing.

Four checks: `Lint`, `Tests and coverage`, `SonarQube quality gate`, `Mutation testing`. Thresholds and reasons are in [docs/ci.md](https://github.com/Malaikaa0/sales-and-inventory-management/blob/ci-quality-gate/docs/ci.md). No step uses `continue-on-error` or `|| true`.

## Expected result of the checks

- `Lint`, `Tests and coverage`: expected to pass.
- `Mutation testing`: expected to pass; this branch changes none of the mutated files.
- `SonarQube quality gate`: **expected to fail** on 6 existing bugs and 13 vulnerabilities, listed in docs/ci.md. Nothing has been suppressed to hide them.

## Checked before opening

The test and mutation steps were run on Linux in a `python:3.12` container. The Sonar gate was run locally: a clean probe project passed, the same project with one added bug failed. The workflow itself has not yet run on GitHub.
