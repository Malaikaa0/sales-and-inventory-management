# CI quality gate

Workflow: [ci.yml](../.github/workflows/ci.yml). It runs on every pull request to `main`, on every push to `main`, every Monday, and by hand. No step uses `continue-on-error` or `|| true`, and no job depends on another, because GitHub treats a skipped required check as passed.

## What each job checks

| Job (check name) | Checks | Fails when |
| --- | --- | --- |
| `Lint` | `flake8` with [.flake8](../.flake8) | Any finding |
| `Tests and coverage` | Installs Chromium for Playwright; Django checks and missing migrations; seeds a fresh database and starts the application; then `pytest tests/team` | A test fails or is skipped; in-scope statements below 100% or branches below 99% |
| `SonarQube quality gate` | A new SonarQube server inside the job; project and gate created through the API | A gate condition is not met |
| `Mutation testing` | Cosmic Ray on the business rules | Kill rate below the minimum, or any mutant not properly tested |

The upstream tests are no longer run: they earn no marks.

## Thresholds and why

| Threshold | Value | Reason |
| --- | --- | --- |
| In-scope statement coverage | 100% | Measured 100%. The assignment asks for full statement coverage of business logic |
| In-scope branch coverage | 99% | Measured 100%. One branch of slack: 1 of 120 missed is 99.17% |
| Bugs, vulnerabilities (analysed folders, after the suppressions below) | 0 | A known bug or vulnerability should block a release until fixed or formally triaged |
| Sonar coverage | at least 90% | Floor for the same files; the stricter figure is checked by the test job |
| Duplicated lines | at most 3% | SonarQube's usual limit; measured 0% |
| Mutation kill rate, pull requests | at least 95% | Lowest per-file rate measured (95.2%, `permissions.py`), rounded down, so a change to any one file is judged fairly |
| Mutation kill rate, full run | at least 97% | Measured overall rate (97.2%), rounded down |

Coverage scope is in [scope.md](scope.md#unit-coverage-scope), mutation results in [mutation.md](mutation.md).

The gate no longer has a maintainability condition. SonarQube analyses `accounts`, `store` and `transactions` only.

## Findings fixed or suppressed

The first scan had 6 bugs and 13 vulnerabilities. Everything needed to pass is in the repository, since each CI run starts a new SonarQube server and nothing set in its web page survives.

### The 6 bugs (`Web:S5256`, table without header cells)

| # | Location | State | How, or why |
| --- | --- | --- | --- |
| 1 | `store/templates/store/dashboard.html:75` | Fixed; already fixed on `area2-Rehan` | Member 3's header cells (`e625373`), the same change applied here ([DEF-01](defects.md)) |
| 2 | `store/templates/store/dashboard.html:94` | Fixed; already fixed on `area2-Rehan` | Same ([DEF-02](defects.md)) |
| 3 | `transactions/templates/documents/receipt.html:20` | Excluded | Label and value pairs. Output only as an untagged PDF, so header cells are not expected to reach a screen reader |
| 4 | `transactions/templates/documents/receipt.html:76` | Excluded | Receipt totals, label in the first cell. Same untagged PDF; the print styles target `td` |
| 5 | `transactions/templates/transactions/sale_create.html:68` | Excluded | Four fixed label and value rows; the styles target `td` |
| 6 | `transactions/templates/transactions/saledetail.html:55` | Excluded | Read-only label and value rows; the styles target `td` |

Bugs 3 to 6 are not fixed on any branch.

### The 13 vulnerabilities

All are `python:S2245` in `store/management/commands/seed_demo.py`: a generator with a fixed seed, `random.Random(42)`, that builds repeatable demo data. No security use. Excluded for that file.

The exclusions are `sonar.issue.ignore.multicriteria` entries in [sonar-project.properties](../sonar-project.properties). Each covers one rule in one file, so a new finding of the same rule in that file would also be hidden. The measures in [sonar-triage.md](sonar-triage.md) were taken before the exclusions.

## Mutation on pull requests

Only the changed files among `transactions/services.py`, `transactions/loyalty.py`, `store/models.py` and `accounts/permissions.py` are mutated. If none changed, the job passes and says so. A pull request that only weakens tests is therefore not caught by this job until the full run on `main`; coverage still applies to it.

## When `area2-Rehan` merges

That branch (open pull request #7) holds the API, browser, security and performance tests. A trial merge with this branch, run on Linux with the steps of the test job on 2026-11-28, gave:

- one merge conflict, in `docs/project-guide.md`;
- **396 tests passed, 6 failed, none skipped**, in-scope coverage 100%;
- the 6 failures are API tests on real behaviour, `N2`, `N4`, three `N5` cases and `N1`. The D1 pull request fixes `N1`;
- `Lint` fails on 7 findings:

| File and line | Code | Finding | Area |
| --- | --- | --- | --- |
| `tests/team/perf/recovery_test.py:175` | F841 | `crash_time` assigned but never used | Member 3 |
| `tools/run_accessibility_audit.py:210` | E501 | Line of 145 characters, limit 127 | Member 3 |
| `tools/run_zap_passive.py:211` | E501 | Line of 149 characters | Member 3 |
| `tools/run_zap_passive.py:214` | E501 | Line of 129 characters | Member 3 |
| `tools/generator/generate.py:138` | E741 | Ambiguous variable name `l` | Member 2 |
| `tools/generator/generate.py:219` | E731 | Lambda assigned to a name | Member 2 |
| `tools/generator/generate.py:234` | E731 | Lambda assigned to a name | Member 2 |

## How the gate blocks a merge

A red check only informs. The merge is blocked by the branch protection rule on `main`, which requires the four checks.

The rule as read through the GitHub API on 2026-11-28: pull request required; the four checks required; branch must be up to date; no bypass, including for administrators; no force pushes or deletion; **no approvals required**. An approval requirement of 1 was set first and then removed.

To set it up: **Settings > Branches > Add branch ruleset** (or classic protection rule) for `main`:

1. Require a pull request before merging. Leave **Require approvals** off.
2. Require status checks to pass, and add: `Lint`, `Tests and coverage`, `SonarQube quality gate`, `Mutation testing`.
3. Require branches to be up to date before merging.
4. Do not allow bypassing (classic rule: "Do not allow bypassing the above settings"; ruleset: leave the bypass list empty).
5. Block force pushes and deletion.

A check name appears in the list only after it has run once. Also enable workflows under the **Actions** tab, since this is a fork; scheduled runs on forks need enabling there too.

Turn protection on after the first pull request has run, so that the check names can be selected.

## Evidence

### Runs on GitHub

As reported by `gh` on 2026-11-28.

| What | Commit | Conclusion | Run |
| --- | --- | --- | --- |
| #11, test only: the red run | `e2d1f1d` | failure. Tests and coverage, SonarQube failed; Lint, Mutation passed | [46158578375](https://github.com/Malaikaa0/sales-and-inventory-management/actions/runs/46158578375) |
| #11, with the fix: the green run | `bccb9fe` | success, all four | [46158779876](https://github.com/Malaikaa0/sales-and-inventory-management/actions/runs/46158779876) |
| #17, blocked change | `c482ada` | failure. Tests and coverage, Mutation failed; Lint, SonarQube passed | [46158780829](https://github.com/Malaikaa0/sales-and-inventory-management/actions/runs/46158780829) |
| #17 after **Update branch** onto the new `main` | `343adbd` | failure. Tests and coverage (99.81% statements, 98.41% branches), Mutation (330 of 426, 77.5%) failed; Lint, SonarQube passed | [46162699895](https://github.com/Malaikaa0/sales-and-inventory-management/actions/runs/46162699895) |
| #10, last head before merging | `acbfefc` | success, all four | [46159501791](https://github.com/Malaikaa0/sales-and-inventory-management/actions/runs/46159501791) |
| #18, last head before merging | `78ea31a` | success, all four | [46159730536](https://github.com/Malaikaa0/sales-and-inventory-management/actions/runs/46159730536) |
| `main` after merging #10 | `49128aa` | success; full mutation 591 of 608 (97.2%) | [46160780007](https://github.com/Malaikaa0/sales-and-inventory-management/actions/runs/46160780007) |
| `main` after merging #11 | `6755743` | success; full mutation 591 of 608 | [46160805452](https://github.com/Malaikaa0/sales-and-inventory-management/actions/runs/46160805452) |
| `main` after merging #18 | `086d916` | success; full mutation 591 of 608 | [46160834242](https://github.com/Malaikaa0/sales-and-inventory-management/actions/runs/46160834242) |

The SonarQube failure on `e2d1f1d` comes from the unit tests that job runs before the analysis, not from the quality gate.

### Screenshots taken by Member 1

Files in `reports/ci/`, copied unchanged. Those listed by time are named `Screenshot 2026-11-28 <time>.png`.

| File | What it shows | Matching run |
| --- | --- | --- |
| [203600](../reports/ci/Screenshot%202026-11-28%20203600.png) | Open pull requests: #10, #11 and #18 with 4 of 4 checks, #17 with 2 of 4. Also #20 from another member | #11 [46158779876](https://github.com/Malaikaa0/sales-and-inventory-management/actions/runs/46158779876), #17 [46158780829](https://github.com/Malaikaa0/sales-and-inventory-management/actions/runs/46158780829), #18 [46159730536](https://github.com/Malaikaa0/sales-and-inventory-management/actions/runs/46159730536). #10: its head at that moment was `acbfefc`, [46159501791](https://github.com/Malaikaa0/sales-and-inventory-management/actions/runs/46159501791) |
| [203856](../reports/ci/Screenshot%202026-11-28%20203856.png) | Open pull requests after the merges: #17 still open with 2 of 4 checks, and #20 | #17 [46158780829](https://github.com/Malaikaa0/sales-and-inventory-management/actions/runs/46158780829) |
| [203950](../reports/ci/Screenshot%202026-11-28%20203950.png) | Closed pull requests: #10, #11 and #18 merged with 4 of 4 checks; #7 merged; #21 closed | #10 [46159501791](https://github.com/Malaikaa0/sales-and-inventory-management/actions/runs/46159501791), #11 [46158779876](https://github.com/Malaikaa0/sales-and-inventory-management/actions/runs/46158779876), #18 [46159730536](https://github.com/Malaikaa0/sales-and-inventory-management/actions/runs/46159730536) |
| [204305](../reports/ci/Screenshot%202026-11-28%20204305.png) | Branch rule form: bypassing not allowed; force pushes and deletions not allowed | None: a settings page |
| [204547](../reports/ci/Screenshot%202026-11-28%20204547.png) | Branch protection rules list with one rule, `main` | None: a settings page |
| [204711](../reports/ci/Screenshot%202026-11-28%20204711.png) | Rule for `main` as first set: pull request with 1 approval; branches up to date; four required checks. The approval requirement was removed afterwards | None: a settings page |

None of the files above shows a run page.

| File | What it shows | Matching run |
| --- | --- | --- |
| [blocked-merge.png](../reports/ci/blocked-merge.png) | Merge box of a pull request: Mutation testing and Tests and coverage failing, Lint and SonarQube passing, all four marked **Required**, and the **Merge pull request** button disabled. The image itself shows no pull request number; the results match [#17](https://github.com/Malaikaa0/sales-and-inventory-management/pull/17), which GitHub reported as `BLOCKED` at head `343adbd` | [46162699895](https://github.com/Malaikaa0/sales-and-inventory-management/actions/runs/46162699895) |
| [pr17-blocked-full.png](../reports/ci/pr17-blocked-full.png) | The same image as `blocked-merge.png`, byte for byte. Despite its name, it shows no pull request title | [46162699895](https://github.com/Malaikaa0/sales-and-inventory-management/actions/runs/46162699895) |
| [rule-with-approvals-earlier.png](../reports/ci/rule-with-approvals-earlier.png) | The rule with **Require approvals ticked** (1 approval), as it was before the change. It is not evidence of the current rule | None: a settings page |

### Automated captures

The `pr*.png` files in `reports/ci/` were taken by an automated browser script during AI-assisted work, not by a team member. They show the run pages: [red](../reports/ci/pr11-red-failing-test.png), [green](../reports/ci/pr11-green-after-fix.png), [blocked](../reports/ci/pr17-blocked.png).

### Earlier local checks

| What | Result | Where |
| --- | --- | --- |
| Gate on a clean probe project, then with one added bug | Passed, then failed with `bugs: 1` | [reports/sonar/gate-proof/](../reports/sonar/gate-proof/) |
| Gate on the code before fixes and exclusions | Failed: 6 bugs, 13 vulnerabilities | [current-code-gate.json](../reports/sonar/gate-proof/current-code-gate.json) |
| Gate on a new server, clean clone, after them | Passed: 0 bugs, 0 vulnerabilities, coverage 100% | [fresh-server-gate.json](../reports/sonar/gate-proof/fresh-server-gate.json) |
| Test and mutation steps on Linux | Passed; `loyalty.py` 114 of 119 killed, as on Windows | Run in a `python:3.12` container |
| Mutation gate on the blocked change | Failed: 77.5% against 95% | [blocked-pr.summary.txt](../reports/mutation/blocked-pr.summary.txt) |
| Mutation gate on the D1 fix | Passed: 97.8% (313 of 320) | [fix-D1.summary.txt](../reports/mutation/fix-D1.summary.txt) |
| First run on GitHub, [pull request #10](https://github.com/Malaikaa0/sales-and-inventory-management/pull/10), commit `3694124` | All four checks passed | [reports/ci/](../reports/ci/) |
| Fix [pull request #11](https://github.com/Malaikaa0/sales-and-inventory-management/pull/11): failing test only (`e2d1f1d`) | Red: 1 test failed, 223 passed | [red](../reports/ci/pr11-red-failing-test.png) |
| Fix pull request #11: with the fix (`bccb9fe`) | All four passed; mutation 313 of 320 (97.8%) | [green](../reports/ci/pr11-green-after-fix.png) |
| Blocked [pull request #17](https://github.com/Malaikaa0/sales-and-inventory-management/pull/17), not to be merged | Red: coverage 99.81% / 98.39%, mutation 77.5% | [blocked](../reports/ci/pr17-blocked.png) |
| Use cases [pull request #18](https://github.com/Malaikaa0/sales-and-inventory-management/pull/18) | All four passed; 233 tests | [use cases](../reports/ci/pr18-use-cases.png) |

Pull request descriptions are in [pull-requests/](pull-requests/).

## Limits

- Mutation time varies with the machine: 426 mutants took 32 minutes locally and about 6 minutes on GitHub. The job is allowed 180 minutes.
- The SonarQube images are not pinned to a version, so a new release can change results.
- Coverage counts the unit tests. API tests run against a separate server process and add no coverage.
