# AI-use record

Every use of an AI tool for project work. Each member adds their own rows and fills in "What I checked" themselves.

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
