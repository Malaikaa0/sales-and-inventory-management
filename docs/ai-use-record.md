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

This record covers help from this tool in one working session. Add any other AI use, including any used for the earlier unit tests and view tests.
