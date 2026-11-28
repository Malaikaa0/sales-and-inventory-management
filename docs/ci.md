# CI quality gate

Workflow: [ci.yml](../.github/workflows/ci.yml). It runs on every pull request to `main`, on every push to `main`, every Monday, and by hand. No step uses `continue-on-error` or `|| true`, and no job depends on another, because GitHub treats a skipped required check as passed.

## What each job checks

| Job (check name) | Checks | Fails when |
| --- | --- | --- |
| `Lint` | `flake8` with [.flake8](../.flake8) | Any finding |
| `Tests and coverage` | Django checks, missing migrations, then `pytest tests/team` against a freshly seeded, running application | A test fails or is skipped; in-scope statements below 100% or branches below 99% |
| `SonarQube quality gate` | A new SonarQube server inside the job; project and gate created through the API | A gate condition is not met |
| `Mutation testing` | Cosmic Ray on the business rules | Kill rate below the minimum, or any mutant not properly tested |

The upstream tests are no longer run: they earn no marks.

## Thresholds and why

| Threshold | Value | Reason |
| --- | --- | --- |
| In-scope statement coverage | 100% | Measured 100%. The assignment asks for full statement coverage of business logic |
| In-scope branch coverage | 99% | Measured 100%. One branch of slack: 1 of 120 missed is 99.17% |
| Bugs, vulnerabilities (all code in the analysed folders) | 0 | A known bug or vulnerability should block a release until fixed or formally triaged |
| Sonar coverage | at least 90% | Floor for the same files; the stricter figure is checked by the test job |
| Duplicated lines | at most 3% | SonarQube's usual limit; measured 0% |
| Mutation kill rate, pull requests | at least 95% | Lowest per-file rate measured (95.2%, `permissions.py`), rounded down, so a change to any one file is judged fairly |
| Mutation kill rate, full run | at least 97% | Measured overall rate (97.2%), rounded down |

Coverage scope is in [scope.md](scope.md#unit-coverage-scope), mutation results in [mutation.md](mutation.md).

The gate no longer has a maintainability condition. SonarQube analyses `accounts`, `store` and `transactions` only.

## The gate fails today

The current code has **6 bugs and 13 vulnerabilities**, so `SonarQube quality gate` is red on every pull request until they are dealt with. Coverage (100%) and duplication (0%) pass.

| Rule | Location (lines) | Count | Triage | Ways to clear it |
| --- | --- | --- | --- | --- |
| `Web:S5256` table without headers | `store/templates/store/dashboard.html` (75, 94) | 2 bugs | Real, [DEF-01 and DEF-02](defects.md) | Add header cells |
| `Web:S5256` | `transactions/templates/documents/receipt.html` (20, 76) | 2 bugs | Accepted | Add row headers and adjust the print styles |
| `Web:S5256` | `transactions/templates/transactions/sale_create.html` (68), `saledetail.html` (55) | 2 bugs | Accepted | Add row headers and adjust the styles |
| `python:S2245` pseudorandom generator | `store/management/commands/seed_demo.py` (115 to 172) | 13 vulnerabilities | False positive | Suppress this rule for this one file in `sonar-project.properties`, with the reason |

Reasons are in [sonar-triage.md](sonar-triage.md). Nothing has been suppressed or fixed to make the gate pass: the team decides. A new server in each run means that marking an issue in the SonarQube web page has no effect on CI.

## Mutation on pull requests

Only the changed files among `transactions/services.py`, `transactions/loyalty.py`, `store/models.py` and `accounts/permissions.py` are mutated. If none changed, the job passes and says so. A pull request that only weakens tests is therefore not caught by this job until the full run on `main`; coverage still applies to it.

## API tests

After `area2-Rehan` merges, `Tests and coverage` also runs the API tests against the application started in the job. Expect it to be red until two things are settled:

- 6 API tests currently fail on real behaviour;
- `tools/generator/generate.py` has 3 `flake8` findings, which turn `Lint` red.

## Member 3 tests

Commits up to `e625373` on `origin/area1-malaika` add browser, security and performance tests. A trial merge with this branch had no conflicts, but CI would fail:

- `tests/team/e2e` imports Playwright, which the workflow does not install, so collection stops with an error;
- `flake8` reports 4 findings in `tests/team/perf/recovery_test.py`, `tools/run_accessibility_audit.py` and `tools/run_zap_passive.py`.

Those commits also add column headers to both dashboard tables (DEF-01 and DEF-02).

## How the gate blocks a merge

A red check only informs. The merge is blocked by branch protection on `main`, which must require the four checks.

In GitHub: **Settings > Branches > Add branch ruleset** (or classic protection rule) for `main`:

1. Require a pull request before merging.
2. Require status checks to pass, and add: `Lint`, `Tests and coverage`, `SonarQube quality gate`, `Mutation testing`.
3. Require branches to be up to date before merging.
4. Do not allow bypassing (classic rule: "Do not allow bypassing the above settings"; ruleset: leave the bypass list empty).
5. Block force pushes and deletion.

A check name appears in the list only after it has run once. Also enable workflows under the **Actions** tab, since this is a fork; scheduled runs on forks need enabling there too.

**Order matters.** Merge the CI pull request before turning protection on. It cannot pass the Sonar check while the issues above exist.

## Evidence from before the first run on GitHub

| What | Result | Where |
| --- | --- | --- |
| Gate on a clean probe project, then with one added bug | Passed, then failed with `bugs: 1` | [reports/sonar/gate-proof/](../reports/sonar/gate-proof/) |
| Gate on the current code | Failed: 6 bugs, 13 vulnerabilities | [current-code-gate.json](../reports/sonar/gate-proof/current-code-gate.json) |
| Test and mutation steps on Linux | Passed; `loyalty.py` 114 of 119 killed, as on Windows | Run in a `python:3.12` container |
| Mutation gate on the blocked change | Failed: 77.5% against 95% | [blocked-pr.summary.txt](../reports/mutation/blocked-pr.summary.txt) |

Pull request descriptions are in [pull-requests/](pull-requests/).

## Limits

- Mutation is slow: 426 mutants took 32 minutes here, and 119 took 16 minutes in a container. The job is allowed 180 minutes.
- The SonarQube images are not pinned to a version, so a new release can change results.
- Coverage counts the unit tests. API tests run against a separate server process and add no coverage.
