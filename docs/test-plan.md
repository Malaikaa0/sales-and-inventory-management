# Test plan

SE3002 Software Quality Engineering final project. Test plan lead: Member 2 (Rehan). It follows [project-guide.md](project-guide.md), which is the group authority.

## 1. Scope

**In scope: two workflows that share the stock record `Item.quantity`.**

| Workflow | Endpoint | Role | Requirements |
| --- | --- | --- | --- |
| Sale | `POST /transactions/new-sale/` | Operative (cashier) or higher | FR1–FR5, BR1–BR3 |
| Void sale | `POST /transactions/sale/{pk}/void/` | Executive (manager) or higher | FR6–FR10, BR4 |

Requirement and rule IDs come from [scope.md](scope.md) (Member 1), the group authority. The draft IDs in [member-2.md](member-2.md) §7 are replaced; the mapping is in [traceability.md](traceability.md#id-mapping-draft--scopemd). Agreed assumptions:

- **A1:** a purchase quantity is at most 100000.
- **A3:** a repeated identical sale request records one sale.
- **A4:** a quantity above the maximum gets a message naming the limit.
- **A5:** a boolean is the wrong type for number fields.

Purchases, products and customers are used only to set up test data. Setup screens, reports and exports are tested only for access.

**Out of scope:** PDF receipts and invoices, the Excel exports, staff management, bills, and deployment (Docker, Azure, Terraform).

## 2. Approach: risk-based

Risk level, likelihood × impact from the [risk register](risk-register.md) (Member 3), sets the technique and depth.

| Risk area | Level | Technique | Area |
| --- | --- | --- | --- |
| Stock corrupted by sale, void or repeats (shared record) | High | Integration tests with stock read back after every request; state transitions; repeated requests | API (M2) |
| Totals, tax, change and points wrong | High | Unit tests with 100% statement and branch coverage, MC/DC, mutation | Unit (M1) |
| Bad input accepted at the boundaries | High | EP + 3-point BVA generated from the OpenAPI spec | API (M2) |
| Unauthorised void or sale | High | Access matrix and automated access checks; ZAP passive scan | Security (M3), API (M2) |
| Cashier cannot complete or correct a sale | Medium | Use cases automated in Playwright, including a rejected value and keyboard navigation | E2E (M3, everyone) |
| Slow or failing under load | Medium | k6 load runs, one failure-and-recovery test | Performance (M3) |
| Hidden code defects | Medium | SonarQube metrics, cyclomatic complexity, CI quality gate | Static (M1) |

Expected results come from the requirements and agreed assumptions, never from the code. Where the code differs, the test fails and a defect is logged.

## 3. Areas and owners

| Area | Owner | Deliverables |
| --- | --- | --- |
| Static analysis, white-box, mutation, CI | Member 1 (Malaika) | Scope, unit tests (`tests/team/unit`), MCC/MC-DC, SonarQube, mutation analysis, CI gate |
| API testing, data generation, test management | Member 2 (Rehan) | OpenAPI spec, generator, API tests (`tests/team/api`), this plan, estimates, traceability, defects, RCA, Pareto |
| Use cases, usability, security, performance | Member 3 | Playwright, Lighthouse/axe, access checks, ZAP, k6, risk register, exit criteria, completion report |

Everyone writes and automates two use cases, logs defects in the agreed format, and records effort and AI use.

## 4. Environment

- Windows (PowerShell) and Linux, Python 3.12+ (3.14 also used), Django 5.2, SQLite.
- `DEBUG=True`, `LOGIN_MAX_ATTEMPTS=1000` for API runs, and a separate database per run (`SQLITE_PATH`).
- Tools:
  - pytest 9.2.0, pytest-django 4.14.0 and coverage 7.17.5.
  - `requests`, PyYAML and openapi-spec-validator, pinned in `tools/generator/requirements.txt`.
  - Playwright, Lighthouse, axe-core, k6, pip-audit, OWASP ZAP and SonarQube for the other areas.
- PostgreSQL is not used in tests. Production behaviour on PostgreSQL is reasoned from the code, as in N2.

## 5. Test data

- **Base data:** `python manage.py seed_demo`, which gives 21 products, 115 sales, and the users `admin`, `manager` and `cashier` with password `demo-pass-123`. All of it is synthetic.
- **Synthetic data per test:** the API fixtures create a fresh item (price 1.00, stock 100000) and a fresh customer (0 points) through the app's own forms. Tests therefore never depend on each other or on seed values.
- **Generated data:** `tools/generator/generate.py openapi/openapi.yaml` writes `tools/generator/out/cases.json`, 111 deterministic EP and BVA cases.
- **Reset:** delete the database, then `migrate` and `seed_demo`.

## 6. Schedule

| Date | Work |
| --- | --- |
| Fri 27 Nov | Baseline, folder structure, setup guide, unit tests for services, models and permissions (M1); defects N1–N3 first seen |
| Sat 28 Nov | OpenAPI spec, generator, API tests, baseline run, N1–N5, regeneration demo, API coverage, this plan (M2). Scope document, risk register, E2E, accessibility, security, and performance runs (M1, M3) |
| Sun 29 Nov | Traceability matrix, RCA for N2 and N4, Pareto chart, exit decision, final package |

## 7. Criteria

**Entry**
- The app installs from `requirements.txt`, migrates and seeds on a clean clone.
- The spec validates with openapi-spec-validator.
- The workflows and requirement IDs are agreed.

**Exit**
- Owned by Member 3; see the exit criteria in the [risk register](risk-register.md) and the [test completion report](test-completion-report.md).
- This plan expects at least these:
  - All planned API tests are run.
  - Every High risk has at least one passing or defect-linked test.
  - No open Critical defects.
  - All Major defects are triaged.

**Suspension**
- The server can't start, or the seed fails.
- More than 30% of a run fails for one cause that blocks further testing, such as login, CSRF or a fixture.
- A defect corrupts the test database.

**Resumption**
- The blocking cause is fixed or worked around.
- The database is reset.
- A smoke run passes: log in, one sale, one void.

## 8. Risks to the plan (project risks)

| Risk | Mitigation |
| --- | --- |
| Short timeline (deadline Sun 29 Nov) | Risk-based depth, generated test data, and a daily check of these estimates |
| Environment differences between members (Windows and Linux, Python versions) | Pinned tool versions, setup steps checked on a fresh clone, server URL set by environment variable |
| Requirement IDs differ between documents | All Member 2 documents re-mapped to the scope.md IDs on 28 Nov (mapping in the traceability matrix) |
| Tests passing because expectations copy the code | Expectations come from the requirements, and every difference is recorded as an assumption or defect |

Product risks are in the [risk register](risk-register.md) (Member 3).

## 9. Three-point estimates (Member 2)

Hours. E = (O + 4M + P) / 6. Actual is filled in on Sunday. (Member 3 estimates and actuals are in [weekly-progress.md](weekly-progress.md).)

| Task | O | M | P | E | Actual |
| --- | --- | --- | --- | --- | --- |
| OpenAPI specification | 1.5 | 3 | 5 | 3.08 | |
| Generator (EP + 3-point BVA) | 2 | 4 | 7 | 4.17 | |
| Regeneration demo (two constraints) | 0.5 | 1 | 2 | 1.08 | |
| API and integration tests | 4 | 7 | 12 | 7.33 | |
| Defects: rerun, log, triage | 1 | 2 | 4 | 2.17 | |
| RCA for 2 major defects + Pareto chart | 1.5 | 3 | 5 | 3.08 | |
| API coverage measurement | 0.5 | 1.5 | 3 | 1.58 | |
| Test plan | 1 | 2 | 3.5 | 2.08 | |
| Traceability matrix | 1 | 2 | 4 | 2.17 | |
| Two use cases + Playwright automation | 3 | 5 | 9 | 5.33 | |
| **Total** | **16** | **30.5** | **54.5** | **32.08** | |

## 10. Unit coverage (Member 1)

Settings are in [.coveragerc](../.coveragerc). The reason for the scope is in [scope.md](scope.md#unit-coverage-scope).

```powershell
$env:DEBUG="True"
coverage run -m pytest tests/team/unit -q
coverage report                              # in scope
coverage report --omit="*/migrations/*"      # whole project
```

Measured on 2026-11-28 with 162 tests passing:

| | In scope | Whole project |
| --- | --- | --- |
| Statements | 1031 of 1031 (100%) | 1566 of 2080 (75.3%) |
| Branches | 120 of 120 (100%) | 140 of 304 (46.1%) |
| Combined, as `coverage.py` reports it | 100% | 71.6% |

Whole project means `accounts`, `bills`, `invoice`, `store`, `transactions` and `InventoryMS`, without migrations and upstream tests. It includes files that no test imports.

### Uncovered code in scope

None. The last uncovered branch, `transactions/forms.py` 14->exit (a form with no `item` field), is covered by `test_bootstrap_mixin_without_item_field`.

Static analysis results are in [sonar-triage.md](sonar-triage.md).

## 11. Candidate defects (Member 1)

Found by reading the code and confirmed by running it. No test failed. See also `N1`–`N6` in [docs/defects](defects) and `DEF-01`–`DEF-07` in [defects.md](defects.md).

| ID | Input | Expected | Actual |
| --- | --- | --- | --- |
| D1 | A cart line with quantity 100001 | A message that states the maximum of 100,000 | "Quantities must be at least 1." |
| D2 | Two lines for the same item, 100000 each, stock 300000 | Rejected, if the limit applies per item | Accepted: 200000 units sold |
| D3 | Sales list search `0712345678`, the phone of a customer with one sale (also `345`) | That customer's sale | No sales. A search of only digits is treated as a receipt number |
| D4 | A cart line with quantity `2.0` | Accepted as 2, since the code allows whole floats | Rejected: "Quantity must be a whole number." |

D4 is currently asserted as present behaviour by `test_whole_number_float_is_rejected_current_behaviour`. If it is accepted as a defect and fixed, that test must change.

## 12. Known defects in CI (Member 2)

Agreed on 28 Nov 2026. Tests that fail because of an **open, logged** defect are marked `@pytest.mark.xfail(strict=True, reason="Known defect N# — issue #n, open")`:

| Test | Defect | Issue |
| --- | --- | --- |
| `tests/team/api/test_purchase.py::test_purchase_above_int32_rejected_N2` | N2 | [#2](https://github.com/Malaikaa0/sales-and-inventory-management/issues/2) |
| `tests/team/api/test_repeats.py::test_same_sale_posted_twice_records_one_sale` | N4 | [#4](https://github.com/Malaikaa0/sales-and-inventory-management/issues/4) |
| `tests/team/api/test_sale_generated.py::test_generated_sale_case[SALE-amount_paid-EP-wrong-type-bool-false]` | N5 | [#5](https://github.com/Malaikaa0/sales-and-inventory-management/issues/5) |
| `…[SALE-redeem_points-EP-wrong-type-bool-false]` | N5 | [#5](https://github.com/Malaikaa0/sales-and-inventory-management/issues/5) |
| `…[SALE-tax_percentage-EP-wrong-type-bool-false]` | N5 | [#5](https://github.com/Malaikaa0/sales-and-inventory-management/issues/5) |
| `tests/team/e2e/test_e2e_m2_use_cases.py::test_uc_m2_2_exc3_tax_out_of_range_rejected` | N7 | [#8](https://github.com/Malaikaa0/sales-and-inventory-management/issues/8) |
| `tests/team/e2e/test_e2e_m2_use_cases.py::test_uc_m2_2_exc5_session_expired` | N8 | [#9](https://github.com/Malaikaa0/sales-and-inventory-management/issues/9) |

N1 is **not** marked: its fix (PR #11) is merged before these tests reach `main`.

Why we use `xfail(strict=True)`:

- **The gate stays meaningful.** Any new failure still fails the pipeline. Known failures are visible in every run as `xfailed`, with the issue number, instead of hiding behind a red build that everyone ignores.
- **A fix forces the marker's removal.** With `strict=True`, a test that starts passing is reported as XPASS and fails the run. Whoever fixes the defect must remove the marker, so the test then guards the fix.
- **Expected results do not change.** The tests still assert the requirement (scope.md IDs and agreed assumptions), not the current behaviour.

The raw failing baseline, without markers, is [reports/api/run-baseline.txt](../reports/api/run-baseline.txt) for the API tests and [reports/e2e/run-m2.txt](../reports/e2e/run-m2.txt) for the E2E tests.
