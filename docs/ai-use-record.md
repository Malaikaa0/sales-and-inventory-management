# AI-use record

Every use of an AI tool for project work. Each member adds their own rows and fills in "What I checked" themselves.

## Member 1 (Malaika)

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

## Member 2 (Rehan)

All rows: Claude Code (Anthropic, CLI in VS Code), one working session on Sat 28 Nov 2026 on branch `area2-Rehan`. Claude Code read the repository, ran commands and wrote files. I reviewed each step and made the decisions.

| # | Task | Purpose | Prompt summary | Output used | What I checked |
| --- | --- | --- | --- | --- | --- |
| 1 | Code reading | Learn the endpoints, limits and status codes before writing tests | Read the project guide, my notes and the sale/void code, then report the endpoints, limits and differences from my notes | Endpoint table with code line references; 13 differences between `member-2.md` and the code | _to fill in_ |
| 2 | OpenAPI spec | `openapi/openapi.yaml` for sale, void and supporting endpoints | Write OpenAPI 3.0.3 matching the code, with `x-` extensions for the code's quirks; validate with openapi-spec-validator | Spec (validates OK); later fixes: floats rejected on integer fields, requirement-based messages (A4, A5), void weakness note | _to fill in_ |
| 3 | Generator | EP + 3-point BVA test data from the spec | Build `tools/generator/generate.py`: read the spec and extensions, deterministic output, expected status from the rules | Generator and `cases.json` (111 cases); pinned `tools/generator/requirements.txt` | _to fill in_ |
| 4 | API and integration tests | Tests in `tests/team/api/` with stock read back | conftest with login/CSRF/stock helpers and fixtures; generated, void, rules, repeats, flow, access and purchase tests; run on a fresh server | 143 tests; `reports/api/run-baseline.txt` and `results-baseline.xml` | _to fill in_ |
| 5 | Expectations review | Expected results from requirements, not copied from code | Fix N1 expectation (A4), check every other expectation for the same problem | Changed expectations for quantity max message and booleans (A5); "" kept as default after my decision | _to fill in_ |
| 6 | Regeneration demo | Show the effect of changing two constraints | Quantity max 500, tax max 50 on a separate branch; regenerate, diff, run | `area2-Rehan-regen`: `reports/api/regen-diff.txt`, `run-regen.txt` | _to fill in_ |
| 7 | Defects | Defect reports and GitHub Issues | Write N1–N6 with steps, expected/actual, evidence lines, severity, priority, triage; create Issues with labels via gh | `docs/defects/N1.md`–`N6.md`; Issues #1–#6 | _to fill in_ |
| 8 | API coverage | Measure and raise API coverage | Compute coverage from the spec and tests; add tests for untested status codes and properties; explain unreachable codes | `docs/api-coverage.md`; `test_api_coverage.py` (13 tests); N6 found | _to fill in_ |
| 9 | Test plan and estimates | Lead document | Scope, risk-based approach, owners, environment, data, schedule, criteria, risks; three-point estimates | `docs/test-plan.md` | _to fill in_ |
| 10 | Traceability | Lead document | FR/BR → M1 unit tests → my API tests → E2E → result → defect; requirements coverage % | `docs/traceability.md` (100% covered, 75% passing with no open defect) | _to fill in_ |
| 11 | RCA | Root cause analysis for the 2 major defects | 5 Whys + fishbone + corrective and preventive actions for N2 and N4 | `docs/defects/rca-N2.md`, `rca-N4.md` | _to fill in_ |
| 12 | Pareto | Defects by category | Categorise N1–N6, matplotlib chart with cumulative % | `docs/defects/pareto.md`, `reports/api/pareto.png`, `make_pareto.py` | _to fill in_ |
| 13 | Git and project docs | Commits, issue links, guide progress, use cases | Logical commits, link Issues into docs, tick done items in the guide, write my two use cases | Commits on `area2-Rehan`; `docs/use-cases/UC-M2-*.md` | _to fill in_ |

AI output I did not accept as given:

- Claude Code first copied the code's messages as expected results. I made expectations follow the requirements (A4, A5).
- I decided that `""` keeps the default and that only booleans are rejected.
- I decided that void's 302 and 200 responses pass FR7 and are reported as a weakness.

## Member 3

Tool: Antigravity (Google DeepMind, Gemini).

| Date | Purpose | Output | Checks run in the session | Checked by me |
| --- | --- | --- | --- | --- |
| 2026-11-28 | Risk register, exit criteria & Member 3 use cases | [risk-register.md](risk-register.md), [UC-M3-1](use-cases/UC-M3-1-make-sale-pos.md), [UC-M3-2](use-cases/UC-M3-2-void-sale-recovery.md) | Cross-checked against [scope.md](scope.md), `transactions/views.py`, `transactions/services.py`, and `pos.js` | |
| 2026-11-28 | Playwright E2E workflow automation | [tests/team/e2e/test_e2e_workflows.py](../tests/team/e2e/test_e2e_workflows.py), [reports/e2e/e2e-run.txt](../reports/e2e/e2e-run.txt) | Ran `pytest tests/team/e2e -v` against seeded isolated server: 2/2 passed (keyboard nav, rejected values, stock read-back) | |
| 2026-11-28 | Lighthouse & axe-core audits + Dashboard fix | [tools/run_accessibility_audit.py](../tools/run_accessibility_audit.py), [dashboard.html](../store/templates/store/dashboard.html), [style.css](../static/css/style.css), [accessibility-report.md](accessibility-report.md) | Executed before & after Lighthouse + `axe-core`; Dashboard Lighthouse Accessibility 95 -> 100, `axe-core` 1 (20 nodes) -> 0 | |
| 2026-11-28 | Access matrix, RBAC checks, `pip-audit`, OWASP ZAP passive scan | [access-matrix.md](access-matrix.md), [tests/team/security/test_access_matrix.py](../tests/team/security/test_access_matrix.py), [tools/run_zap_passive.py](../tools/run_zap_passive.py), [security-report.md](security-report.md) | Ran `pytest tests/team/security -v` (35/35 pass), `pip-audit --local` (0 CVEs), ZAP 2.17.0 passive scan (0 High) | |
| 2026-11-28 | k6 load test & crash failure-and-recovery test | [tests/team/perf/load_test.js](../tests/team/perf/load_test.js), [tools/run_k6_load.py](../tools/run_k6_load.py), [tests/team/perf/recovery_test.py](../tests/team/perf/recovery_test.py), [performance-report.md](performance-report.md) | Ran `k6` (898 reqs, p95 228.6ms, 1.00% err) & recovery test (2.49s recovery, 0 orphan sales, `consistency_verified=true`) | |
| 2026-11-28 | Lead reports: weekly progress, GQM metrics & test completion report | [weekly-progress.md](weekly-progress.md), [test-completion-report.md](test-completion-report.md), [member-3.md](member-3.md) | Verified all cited counts, timings, and paths against saved JSON/text reports and full `pytest` run | |

This record covers help from AI tools in our working sessions. Add any other AI use, including any used for the earlier unit tests and view tests.
