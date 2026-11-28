# Weekly Progress Report

**Lead:** Member 3  
**Reporting period:** Week ending 2026-11-28 (Sprint / Project Delivery Week)  
**Repository:** https://github.com/Malaikaa0/sales-and-inventory-management (`area1-malaika`, `area2-Rehan`)

---

## 1. Status Summary by Area

| Area | Owner | Status | Key Outputs Completed | Open / Next Actions |
| --- | --- | --- | --- | --- |
| **Area 1: White-box, Static Analysis, Mutation, CI** | Member 1 (Malaika) | On track (core done) | `baseline-v0`, [scope.md](scope.md), 162 unit tests (**100%** in-scope statement/branch coverage), [mcc-mcdc.md](mcc-mcdc.md), [cfg-complexity.md](cfg-complexity.md), [sonar-triage.md](sonar-triage.md), draft `DEF-01` & `DEF-02`. | Mutation testing (2 operators, ≥15 mutants), CI quality gate PRs, SonarQube screenshots. |
| **Area 2: API Testing, Data Generation, Test Management** | Member 2 (Rehan) | On track (`area2-Rehan`) | OpenAPI 3.0.3 spec, deterministic EP + 3-point BVA generator (`cases.json`), 143 API tests (137 pass / 6 fail exposing defects), 2-constraint regeneration demo, [test-plan.md](test-plan.md), [traceability.md](traceability.md), N1–N6 defects + RCA + Pareto. | Merge `area2-Rehan` with `area1-malaika`; add Member 3's E2E test names into `traceability.md` and finalize actual hours. |
| **Area 3: Use Cases, Usability, Security, Performance & Lead Reports** | **Member 3** | **Complete** | [risk-register.md](risk-register.md) (8 product + 2 project risks + exit criteria), 2 use cases ([UC-M3-1](use-cases/UC-M3-1-make-sale-pos.md), [UC-M3-2](use-cases/UC-M3-2-void-sale-recovery.md)), Playwright E2E suite (2/2 pass), Lighthouse + `axe-core` before/after + Dashboard fix (`95 -> 100`), [access-matrix.md](access-matrix.md) + 35/35 security tests, `pip-audit` (`0` CVEs), OWASP ZAP 2.17.0 passive scan (`0` High), k6 load test (`898` reqs, `p95=228.6ms`) + crash recovery (`2.49s`, `consistency_verified=true`), GQM & [test-completion-report.md](test-completion-report.md). | Merge branch PRs into `main`; team sign-off on `scope.md` and GitHub Issues for final submission ZIP + PDF. |

---

## 2. Key Milestones & Metrics This Period

- **Unit testing (`tests/team/unit`):** 162 / 162 passing; 100% statement & branch coverage in scope (71.6% whole-project).
- **E2E testing (`tests/team/e2e`):** 2 / 2 passing (`test_e2e_make_sale_keyboard_and_rejected_values`, `test_e2e_void_sale_permissions_rejection_and_recovery`).
- **Accessibility:** Dashboard improved from Lighthouse **95** (`td-has-header`, `color-contrast` failing; `axe-core`: 20 failing nodes) to Lighthouse **100** and `axe-core`: **0** violations.
- **Security:** 35 / 35 RBAC/CSRF/header/lockout tests passing; `pip-audit` = 0 known CVEs; OWASP ZAP 2.17.0 = 0 High, 1 Medium (`DEBUG=True` 404 CSP skip only).
- **Performance:** `k6` 10-VU load test completed 898 requests (`p95 = 228.6ms`, `1.00%` error rate due to SQLite concurrent write lock contention on `POST /transactions/new-sale/`); crash recovery completed in `2.49s` with `0` orphan sales and `100%` stock consistency.

---

## 3. Effort Tracking (Member 3 — Hours)

Three-point estimate formula: `E = (O + 4M + P) / 6`.

| Task | O | M | P | E (hrs) | Actual (hrs) | Variance |
| --- | --- | --- | --- | --- | --- | --- |
| Risk register (8 product + 2 project) & exit criteria | 1.0 | 1.5 | 3.0 | 1.67 | 1.5 | -0.17 |
| Two use cases (W1, W2) + Playwright E2E automation | 2.5 | 4.0 | 7.0 | 4.25 | 3.5 | -0.75 |
| Lighthouse + axe-core audits & Dashboard fix (before/after) | 1.5 | 2.5 | 4.5 | 2.67 | 2.5 | -0.17 |
| Access matrix + 35 automated checks + ZAP + `pip-audit` | 2.0 | 3.5 | 6.0 | 3.67 | 3.5 | -0.17 |
| k6 load test + crash failure-and-recovery test | 1.5 | 3.0 | 5.0 | 3.08 | 2.5 | -0.58 |
| Weekly progress, GQM metrics & test completion report | 1.0 | 2.0 | 3.5 | 2.08 | 1.75 | -0.33 |
| **Total (Member 3)** | **9.5** | **16.5** | **29.0** | **17.42** | **15.25** | **-2.17** |
