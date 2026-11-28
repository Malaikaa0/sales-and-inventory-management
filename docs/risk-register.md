# Risk register and exit criteria

**Owner:** Member 3 (Use cases, usability, security, performance).  
**Scope:** Two workflows sharing `Item.quantity` and `Customer.loyalty_points` — **W1 Make a sale** (`FR1`–`FR5`, `BR1`–`BR3`) and **W2 Void a sale** (`FR6`–`FR10`, `BR4`) as defined in [scope.md](scope.md).  
**Scale:** Likelihood (1 = Low, 2 = Medium, 3 = High) × Impact (1 = Low, 2 = Medium, 3 = High).  
- **High (6–9):** Mandatory automated negative/boundary testing + targeted verification on every change.  
- **Medium (3–4):** Automated happy/alternative flow + focused audit or load verification.  
- **Low (1–2):** Baseline smoke check or monitoring.

---

## 1. Product risks (8)

| ID | Risk | Area / Workflow | L | I | Score | Level | Test technique & mitigation | Linked IDs / Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **PR-01** | **Stock corruption across shared workflows or retries:** Concurrent sales, overselling, voiding a sale twice, or double-posting a sale leaves `Item.quantity` inaccurate. | W1, W2 (`Item.quantity`) | 2 | 3 | 6 | **High** | Atomic transactions with `select_for_update()`, unit branch tests (100% in-scope), API stock read-back after every valid/invalid call, E2E flow checks, k6 concurrency/contention run. | FR2, FR3, FR6, FR9, BR1, BR4; `tests/team/unit/`, `tests/team/e2e/`, `tests/team/perf/` |
| **PR-02** | **Server-side pricing, tax, or loyalty point miscalculation:** Rounding errors, negative balances on void, or accepting client-tampered totals corrupt financial or ledger records. | W1, W2 (`Customer.loyalty_points`) | 2 | 3 | 6 | **High** | 100% statement/branch unit coverage on `transactions/services.py` and `loyalty.py`, MCC/MC-DC test pairs, mutation analysis (M1), API/E2E verification of server-computed totals and point reversals. | FR1, FR4, FR5, FR7, BR2, BR3; `docs/mcc-mcdc.md` |
| **PR-03** | **Unauthorised access to void, exports, or admin actions:** Operatives (`cashier`), inactive users, or anonymous callers reach manager/admin views (`void`, `purchases`, `staff`, Excel exports) via direct URL or CSRF/session bypass. | W2 & RBAC (`accounts/permissions.py`) | 2 | 3 | 6 | **High** | Full role-by-endpoint access matrix; automated security tests (`tests/team/security/`) covering anonymous (`302`), Operative (`403`), inactive profile logout, and Executive/Admin access; OWASP ZAP passive scan. | FR10, BR4; `tests/team/security/`, `reports/security/` |
| **PR-04** | **Invalid boundary or malformed input accepted or misreported:** Quantities outside `1..100000`, line counts > 200, tax outside `0..100`, or non-numeric inputs cause misleading error messages or 500 errors. | W1, W2 | 3 | 2 | 6 | **High** | OpenAPI 3-point BVA & EP test generation (M2), E2E rejected-value flow in POS and Void forms, unit boundary tests, candidate defect logging (`D1`–`D4`). | FR3, BR1, BR3, BR4; `tests/team/e2e/` |
| **PR-05** | **Keyboard and screen-reader accessibility barriers on core screens:** Missing table headers (`<th>`), unlabeled controls, or focus traps block keyboard-only cashiers or assistive technology users. | UI / Usability (`dashboard`, `sale_create`, `saledelete`) | 3 | 2 | 6 | **High** | Lighthouse + `axe-core` audits across core screens; Playwright keyboard-only navigation test on POS; remediate dashboard table accessibility defects (`DEF-01`, `DEF-02`) and capture before/after reports. | `docs/defects.md`; `reports/accessibility/`, `tests/team/e2e/` |
| **PR-06** | **Performance degradation or failure under peak checkout load:** Slow queries (`select_related`, stock locks) or SQLite lock contention under multi-cashier traffic push p95 latency past acceptable till response times. | W1, Dashboard, Catalog search | 2 | 2 | 4 | **Medium** | k6 load tests (`tests/team/perf/`) measuring p95/p99 latency and error rate across read + checkout endpoints, plus failure-and-recovery test confirming database consistency after mid-run server interruption. | `tests/team/perf/`, `reports/perf/` |
| **PR-07** | **Security misconfiguration or vulnerable third-party packages:** Missing HTTP security headers (`CSP`, `X-Frame-Options`, `HttpOnly` cookies), stack traces in `DEBUG`, or known CVEs in `requirements.txt` expose the deployment. | Platform / Dependencies | 2 | 2 | 4 | **Medium** | OWASP ZAP passive scan against running app (`reports/security/`), automated header/cookie checks, and `pip-audit` dependency vulnerability scan against installed packages. | `InventoryMS/middleware.py`, `requirements.txt`; `reports/security/` |
| **PR-08** | **UI/UX friction or silent errors during checkout or void cancellation:** Missing inline feedback, unclear confirmation dialogs, or stale cart state causes cashiers to double-submit or abandon sales. | W1, W2 UI | 2 | 2 | 4 | **Medium** | End-to-end Playwright walkthroughs of both workflows (including rejected values, cancellation, and post-void status checks) and Lighthouse usability/best-practice checks. | `docs/use-cases/`, `tests/team/e2e/` |

---

## 2. Project risks (2)

| ID | Risk | L | I | Score | Level | Mitigation & contingency |
| --- | --- | --- | --- | --- | --- | --- |
| **PJ-01** | **Cross-member integration & merge drift across parallel branches:** Work proceeds concurrently on `area1-malaika` (M1 & M3) and `area2-Rehan` (M2) with `docs/scope.md` still in draft, risking mismatched requirement IDs or file conflicts. | 3 | 2 | 6 | **High** | Keep Member 3 deliverables in dedicated namespaces (`docs/use-cases/UC-M3-*`, `tests/team/e2e/`, `tests/team/security/`, `tests/team/perf/`, `reports/{accessibility,security,perf,e2e}/`), align all IDs to [scope.md](scope.md) (`FR1`–`FR10`, `BR1`–`BR4`), and cross-reference M2's traceability matrix cleanly. |
| **PJ-02** | **Environment & tool availability differences (Windows/PowerShell, WSL, Docker, SQLite vs PostgreSQL):** Missing native binaries (`k6`, `node`, `zap`), browser dependencies, or PostgreSQL-only overflow behaviour (`N2`) could delay or skew test execution. | 2 | 2 | 4 | **Medium** | Pin Python dependencies in `.venv`, record exact tool versions and run commands in each report, use SQLite isolation (`SQLITE_PATH`) per test run, and document PostgreSQL-specific risks explicitly in defect reports and the completion report. |

---

## 3. Exit criteria (release gate)

Owned by **Member 3** and referenced by [test-plan.md](test-plan.md). Release readiness is evaluated against these mandatory exit criteria in the [Test Completion Report](test-completion-report.md):

1. **Test execution completeness:**
   - 100% of planned unit tests (`tests/team/unit/`), API tests (`tests/team/api/`), E2E Playwright tests (`tests/team/e2e/`), and automated security access checks (`tests/team/security/`) are executed on the release candidate.
   - All **High** product risks (`PR-01`–`PR-05`) have passing automated test evidence or a triaged, documented defect.
2. **Coverage & requirement traceability:**
   - In-scope unit statement and branch coverage = **100%** (measured via `coverage.py`).
   - 100% of agreed functional requirements (`FR1`–`FR10`) and business rules (`BR1`–`BR4`) are mapped in the traceability matrix with executed test evidence.
3. **Defect & quality thresholds:**
   - **Zero** open **Critical** defects without an approved fix or documented release-blocking hold.
   - **100%** of **Major** and **Minor** defects discovered during testing are logged, triaged, and assigned a status/disposition (`Fixed`, `Accepted/Known Issue`, or `Hold`).
   - Accessibility (`axe-core` / Lighthouse), security (`pip-audit`, ZAP passive scan, access matrix), and performance (`k6` load + failure/recovery) runs have recorded reports with no unresolved critical violations.
4. **Release / Hold decision rule:**
   - **GO (Release)** only if Criteria 1–3 all meet target.
   - **NO-GO (Hold)** if any Critical defect remains open, any High-risk security/access check fails, or a mandatory exit criterion fails its target.
