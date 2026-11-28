# Test plan

SE3002 Software Quality Engineering final project. Test plan lead: Member 2 (Rehan). It follows [project-guide.md](project-guide.md), which is the group authority.

## 1. Scope

**In scope: two workflows that share the stock record `Item.quantity`.**

| Workflow | Endpoint | Role | Requirements |
| --- | --- | --- | --- |
| Sale | `POST /transactions/new-sale/` | Operative (cashier) or higher | FR1–FR5, BR1, BR2, BR4 |
| Void sale | `POST /transactions/sale/{pk}/void/` | Executive (manager) or higher | FR6–FR8, BR3, BR4 |

Requirement and rule IDs come from the draft scope in [member-2.md](member-2.md) §7 until `docs/scope.md` is written by Member 1. Agreed assumptions:

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
  - Playwright, k6, OWASP ZAP and SonarQube for the other areas.
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
| Sat 28 Nov | OpenAPI spec, generator, API tests, baseline run, N1–N5, regeneration demo, API coverage, this plan (M2). Scope document and risk register (M1, M3) |
| Sun 29 Nov | Traceability matrix, RCA for N2 and N4, Pareto chart, E2E and security runs, exit decision, final package |

## 7. Criteria

**Entry**
- The app installs from `requirements.txt`, migrates and seeds on a clean clone.
- The spec validates with openapi-spec-validator.
- The workflows and requirement IDs are agreed.

**Exit**
- Owned by Member 3; see the exit criteria in the [risk register](risk-register.md) and the test completion report.
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
| `scope.md` not yet written | Use the draft IDs; rename in the traceability matrix when scope is agreed |
| Tests passing because expectations copy the code | Expectations come from the requirements, and every difference is recorded as an assumption or defect |

Product risks are in the [risk register](risk-register.md) (Member 3).

## 9. Three-point estimates (Member 2)

Hours. E = (O + 4M + P) / 6. Actual is filled in on Sunday.

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
