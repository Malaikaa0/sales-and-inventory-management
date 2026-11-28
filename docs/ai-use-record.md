# AI use record

Tool: Claude Code (Anthropic), model Claude Sonnet 5.5.

"Checks run in the session" are what the tool ran. "Checked by me" is for the team member to fill in.

| Date | Purpose | Output | Checks run in the session | Checked by me |
| --- | --- | --- | --- | --- |
| 2026-11-27 | Baseline and project structure | Folders, empty documents; confirmed the existing `baseline-v0` tag and `upstream` remote | Compared tag, HEAD and `upstream/main` | |
| 2026-11-27 | Setup instructions | README section "Setup, seed and reset" | Not run at the time; run on a fresh clone later that day | |
| 2026-11-27 | Git history | Removed an AI co-author line from one commit message, force-pushed the branch, deleted the local backup ref | Searched all refs and files for the line | |
| 2026-11-27 | Progress summary and work division | Summary in chat; [project-guide.md](project-guide.md) | Ran the team tests; ran the setup steps on a fresh clone | |
| 2026-11-27 | Publishing existing work | Committed and pushed two test files; updated the guide | Ran the team tests | |
| 2026-11-28 | Coverage run and failure triage | No failures at the start: 121 tests passed | Ran line and branch coverage | |
| 2026-11-28 | MCC tests | `test_mcc_loyalty.py`, 10 cases. The file named in the request was not found, so it was written from the code | Ran the tests; each case asserts its own condition values | |
| 2026-11-28 | Tests for uncovered code and rule rows | `test_store_and_admin.py`, `test_void_rules.py` | Ran all unit tests: 147 passed | |
| 2026-11-28 | Candidate defects | D1 to D4 in [test-plan.md](test-plan.md) | D1 to D3 reproduced with a temporary test; D4 is shown by an existing team test | |
| 2026-11-28 | Scope draft | [scope.md](scope.md): workflows, requirements, business rules, roles | Compared with the source; not agreed by the team | |
| 2026-11-28 | Coverage justification | "Unit coverage" in [test-plan.md](test-plan.md) | Branch coverage report | |
| 2026-11-28 | MCC, MC/DC and decision tables | [mcc-mcdc.md](mcc-mcdc.md) | MCC rows match the test cases | |
| 2026-11-28 | This record | [ai-use-record.md](ai-use-record.md) | | |
| 2026-11-28 | Coverage scope | `.coveragerc`, scope reasons, both coverage figures | Ran all unit tests with both reports | |
| 2026-11-28 | Account model and form branch tests | `test_account_models.py` | 162 tests passed; in-scope coverage 100% | |
| 2026-11-28 | SonarQube analysis and triage | `sonar-project.properties`, `reports/sonar/`, [sonar-triage.md](sonar-triage.md) | Values read from the saved JSON; flagged lines read in the source | |
| 2026-11-28 | Control flow graphs and complexity | [cfg-complexity.md](cfg-complexity.md) | Script checked counts and path independence; Sonar counting tested with a probe; diagrams not rendered | |
| 2026-11-28 | Removing personal fields | Author and email fields removed from `reports/sonar/`, including from unpushed commits | Searched the saved JSON for email addresses | |
| 2026-11-28 | Quality gate and two scans | `SQE-gate` on the server, scoped and whole repository results in `reports/sonar/`, [sonar-triage.md](sonar-triage.md) | Read gate conditions and results back from the API | |
| 2026-11-28 | Accepted issue reasons and defect drafts | [sonar-triage.md](sonar-triage.md), [defects.md](defects.md) (DEF-01, DEF-02) | Read the flagged templates and styles; rendered the dashboard to confirm both defects; no screen reader check | |

### Member 3 session rows (Antigravity / Gemini)

| Date | Purpose | Output | Checks run in the session | Checked by me |
| --- | --- | --- | --- | --- |
| 2026-11-28 | Risk register, exit criteria & Member 3 use cases | [risk-register.md](risk-register.md), [UC-M3-1](use-cases/UC-M3-1-make-sale-pos.md), [UC-M3-2](use-cases/UC-M3-2-void-sale-recovery.md) | Cross-checked against [scope.md](scope.md), `transactions/views.py`, `transactions/services.py`, and `pos.js` | |
| 2026-11-28 | Playwright E2E workflow automation | [tests/team/e2e/test_e2e_workflows.py](../tests/team/e2e/test_e2e_workflows.py), [reports/e2e/e2e-run.txt](../reports/e2e/e2e-run.txt) | Ran `pytest tests/team/e2e -v` against seeded isolated server: 2/2 passed (keyboard nav, rejected values, stock read-back) | |
| 2026-11-28 | Lighthouse & axe-core audits + Dashboard fix | [tools/run_accessibility_audit.py](../tools/run_accessibility_audit.py), [dashboard.html](../store/templates/store/dashboard.html), [style.css](../static/css/style.css), [accessibility-report.md](accessibility-report.md) | Executed before & after Lighthouse + `axe-core`; Dashboard Lighthouse Accessibility 95 -> 100, `axe-core` 1 (20 nodes) -> 0 | |
| 2026-11-28 | Access matrix, RBAC checks, `pip-audit`, OWASP ZAP passive scan | [access-matrix.md](access-matrix.md), [tests/team/security/test_access_matrix.py](../tests/team/security/test_access_matrix.py), [tools/run_zap_passive.py](../tools/run_zap_passive.py), [security-report.md](security-report.md) | Ran `pytest tests/team/security -v` (35/35 pass), `pip-audit --local` (0 CVEs), ZAP 2.17.0 passive scan (0 High) | |
| 2026-11-28 | k6 load test & crash failure-and-recovery test | [tests/team/perf/load_test.js](../tests/team/perf/load_test.js), [tools/run_k6_load.py](../tools/run_k6_load.py), [tests/team/perf/recovery_test.py](../tests/team/perf/recovery_test.py), [performance-report.md](performance-report.md) | Ran `k6` (898 reqs, p95 228.6ms, 1.00% err) & recovery test (2.49s recovery, 0 orphan sales, `consistency_verified=true`) | |
| 2026-11-28 | Lead reports: weekly progress, GQM metrics & test completion report | [weekly-progress.md](weekly-progress.md), [test-completion-report.md](test-completion-report.md), [member-3.md](member-3.md) | Verified all cited counts, timings, and paths against saved JSON/text reports and full `pytest` run | |

This record covers help from this tool in our working sessions. Add any other AI use, including any used for the earlier unit tests and view tests.
