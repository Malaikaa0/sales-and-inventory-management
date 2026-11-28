# Test Completion Report

**Lead:** Member 3  
**Date:** 2026-11-28  
**System under test:** Sales and Inventory Management System (`InventoryMS`, baseline `baseline-v0`, working branch `area1-malaika` + integration with `area2-Rehan`)  
**Scope:** Workflows **W1 Make a sale** (`FR1`–`FR5`, `BR1`–`BR3`) and **W2 Void a sale** (`FR6`–`FR10`, `BR4`) sharing `Item.quantity` and `Customer.loyalty_points` ([scope.md](scope.md)).

---

## 1. Executive Summary of Test Execution

| Test Suite / Activity | Owner | Executed | Passed | Failed | Evidence |
| --- | --- | --- | --- | --- | --- |
| Unit & white-box tests (`tests/team/unit`) | M1 | 162 | 162 | 0 | [test-plan.md](test-plan.md), [mcc-mcdc.md](mcc-mcdc.md) |
| Static analysis (`SonarQube`) | M1 | 2 scans | Quality Gate `OK` (scoped) | 0 | [sonar-triage.md](sonar-triage.md) |
| API & generated BVA/EP tests (`tests/team/api`, `area2-Rehan`) | M2 | 143 | 137 | 6* | `reports/api/run-baseline.txt` (`area2-Rehan`) |
| Playwright E2E workflows (`tests/team/e2e`) | **M3** | 2 | 2 | 0 | [reports/e2e/e2e-run.txt](../reports/e2e/e2e-run.txt) |
| Accessibility audits (Lighthouse + `axe-core`) | **M3** | 2 phases | Dashboard **100 / 0** (after) | 0 (Dashboard) | [accessibility-report.md](accessibility-report.md) |
| Security RBAC & hardening (`tests/team/security`) | **M3** | 35 | 35 | 0 | [security-report.md](security-report.md) |
| Dependency audit (`pip-audit`) + ZAP 2.17.0 passive | **M3** | 2 scans | 0 CVEs / 0 High | 0 | [reports/security/](../reports/security/) |
| Performance (`k6` load + crash recovery) | **M3** | 2 runs | Thresholds & recovery PASS | 9/898 HTTP 500† | [performance-report.md](performance-report.md) |

*\*API baseline failures expose logged defects (`N1`, `N4`, `N5`, `N6`) on `area2-Rehan`.*  
*†k6 read checks 100% passed; 9/67 concurrent SQLite `POST /transactions/new-sale/` writes hit file-lock contention (1.00% overall HTTP failure rate, within `< 2%` threshold).*

---

## 2. GQM (Goal–Question–Metric) Measurement Framework

| Goal | Question | Metric | Target | Actual | Status |
| --- | --- | --- | --- | --- | --- |
| **G1: Correctness of shared stock & financial logic** | Are all in-scope workflow branches and requirements verified? | In-scope unit statement & branch coverage; requirement coverage | 100% stmt/branch; 100% FR/BR mapped | **100%** stmt (1031/1031) & **100%** branch (120/120); **100%** FR/BR covered (unit + API + E2E) | **Met** |
| **G2: End-to-end usability & WCAG accessibility** | Can users complete and void sales via keyboard, and does the Dashboard meet WCAG 2.1 AA? | Lighthouse Accessibility score; `axe-core` serious/critical violations on Dashboard | Lighthouse ≥ 95; 0 `axe-core` violations on fixed screen | Dashboard improved **95 → 100**; `axe-core` violations **1 (20 nodes) → 0**; E2E keyboard + rejected-value tests **2/2 pass** | **Met** |
| **G3: Security & access-control assurance** | Are role boundaries, CSRF/headers, dependencies, and passive scan surfaces secure? | RBAC check pass rate; Critical/High CVEs; ZAP High alerts | 100% RBAC pass; 0 Critical/High CVEs; 0 ZAP High alerts | **35/35 (100%)** security tests pass; **0** `pip-audit` CVEs; **0** ZAP High alerts | **Met** |
| **G4: Performance & crash resilience** | Does the POS handle concurrent load and recover atomically after a crash? | `k6` p95 latency & error rate; post-crash orphan sales & stock accuracy | p95 < 1500ms, error < 2%; 0 orphan sales, 100% stock match | **p95 = 228.60ms**, error = **1.00%**; crash recovery **2.49s**, **0** orphan sales, **100%** stock match (`consistency_verified=true`) | **Met** |
| **G5: Defect transparency & resolution** | Are all discovered defects triaged with no unresolved Critical bugs? | Critical open defects; Major/Minor triage rate | 0 open Critical; 100% Major triaged | **0** open Critical in M1/M3 scope; **2 Major API defects (`N2`, `N4`) open** in M2 scope (unfixed) | **Partial / Hold trigger** |


### 2.1 Brief GQM metrics: defect density, requirements coverage, reopen rate

> Computed by Member 2 (Rehan) on 28 Nov 2026 for Member 3's GQM framework, from repository and GitHub data only. Section 2 above is unchanged.

**Goal G6:** know how defect-prone and how completely verified the two workflows are, and whether fixes stay fixed, so the release/hold decision rests on measured data.

| Question | Metric | How it is measured | Value | Interpretation |
| --- | --- | --- | --- | --- |
| **Q1.** How defect-prone is the in-scope server-side logic? | **Defect density** | Confirmed defects located in in-scope server-side code ÷ KLOC of that code | **6 / 1.502 KLOC = 4.0 defects/KLOC** | All six (N1–N6) are input-validation or error-reporting problems at the API boundary, not calculation errors. The pricing, stock and points logic (100% statement/branch, mutation-tested by M1) had none. The density is driven by `services.py`, `views.py` and `models.py`, where N1, N4, N5 and N6 sit in the sale entry point. |
| **Q2.** How completely are the requirements verified? | **Requirements coverage** | From [traceability.md](traceability.md), over scope.md FR1–FR10 and BR1–BR4 (14 items) | Tested: **14 / 14 = 100%**. Passing with no open defect: **9 / 14 = 64.3%** | Every requirement has unit, API and E2E evidence, so the gap is in quality, not in testing. FR2 (N4), BR1 (N1), BR2 (N5) and BR3 (N5, N7) fail, and FR3 passes with N6 open. |
| **Q3.** Do fixed defects stay fixed? | **Reopen rate** | Issues with a `reopened` event ÷ closed defect issues, from GitHub issue events (#1–#19) | **0 / 4 = 0%** | No defect has been reopened. The 4 closed defects are #1 (N1, closed by PR #11) and #12–#14 (DEF-01–03, fixed in `6052421`). All were closed on 28 Nov, so the observation window is short. Recheck before submission. |

**Supporting counts** (GitHub Issues labelled `defect`, 28 Nov 2026):

| Measure | Value |
| --- | --- |
| Logged defects | 14 (N1–N8, DEF-01–DEF-06) |
| By severity | Critical 0 · Major 3 (N2, N4, N7) · Minor 11 |
| Open vs closed | Open 10 (including DEF-04 accepted) · Closed 4 (N1, DEF-01, DEF-02, DEF-03) |
| Reopened | 0 |

**How defect density was computed**

- **Numerator:** defects whose root cause is in the in-scope Python files.
  - N1: `services.py:61-62`.
  - N2: `Purchase.quantity` in `transactions/models.py`.
  - N3: the purchase `CreateView` in `transactions/views.py`.
  - N4: `sale_create_view` and `create_sale`.
  - N5: `services.py:74,77,80`.
  - N6: `_int` and the `pk__in` query in `services.py`.
- **Left out of the numerator:**
  - N7 and N8 are in client JavaScript (`static/js/pos.js`).
  - DEF-01–03, DEF-05 and DEF-06 are in templates and CSS.
  - DEF-04 is SQLite locking, an environment limit.
  - For reference only: all 14 logged defects over the same code would give 9.3/KLOC, but that mixes defects from outside the measured code.
- **Denominator:** non-blank, non-comment, non-docstring Python lines in the in-scope files from `.coveragerc` (`transactions`, `store`, `accounts/permissions.py`, `accounts/models.py`, minus the omitted files). Counted with Python's `tokenize` and `ast`, not by hand.
- **Not used:** SonarQube's scoped `ncloc` (4,208, `reports/sonar/measures.json`) also counts templates, CSS, JavaScript and tests, so it is not the server-side logic base.

| File | Lines of code |
| --- | --- |
| `store/__init__.py` | 0 |
| `store/admin.py` | 24 |
| `store/apps.py` | 4 |
| `store/forms.py` | 99 |
| `store/mixins.py` | 44 |
| `store/models.py` | 88 |
| `store/tables.py` | 10 |
| `store/urls.py` | 22 |
| `store/views.py` | 195 |
| `transactions/__init__.py` | 0 |
| `transactions/admin.py` | 50 |
| `transactions/apps.py` | 4 |
| `transactions/forms.py` | 39 |
| `transactions/loyalty.py` | 50 |
| `transactions/models.py` | 173 |
| `transactions/services.py` | 154 |
| `transactions/urls.py` | 16 |
| `transactions/views.py` | 253 |
| `accounts/permissions.py` | 105 |
| `accounts/models.py` | 172 |
| **Total (20 files)** | **1502** |

**Notes**

- **N1:** issue #1 is closed because PR #11 was merged into `main` (Member 1). The fix is not yet on `area1-malaika`, so the traceability figure (64.3%) still counts BR1 as failing there. Once the fix reaches `area1-malaika`, the expected value is 10/14 = 71.4%. That is a projection until it is measured.
- **Label mismatch:** issue #1 still carries the label `status:open` although it is closed. The lifecycle labels should be updated when an issue closes.

---

## 3. Exit Criteria Evaluation ([risk-register.md](risk-register.md))

| Exit Criterion | Target | Actual | Met? |
| --- | --- | --- | --- |
| 1. All planned tests executed across unit, E2E, security, perf, and API | 100% areas executed | Unit (162), E2E (2), Security (35 + ZAP + pip-audit), Perf (k6 + recovery), API (143 on `area2-Rehan`) executed | **Yes** (M1 mutation & CI gate still pending on M1) |
| 2. All High product risks (`PR-01`–`PR-05`) have verified automated evidence | 5 / 5 High risks covered | `PR-01`–`PR-05` all covered by passing unit/E2E/security/a11y tests + open defects documented | **Yes** |
| 3. Zero open Critical defects & all Major defects resolved or accepted for release | 0 Critical; 0 unaccepted Major blockers | `DEF-01`–`DEF-03` fixed on `area1-malaika`; however **Major functional defects `N4` (duplicate sale on repeated POST, no idempotency) and `N2` (purchase `int32` overflow risk) remain open** | **No** |

---

## 4. Release / Hold Decision

### Decision: **HOLD (NO-GO for Production Release)**

Evaluation against the three mandatory release criteria:

| Release Criterion | Target | Actual | Result |
| --- | --- | --- | --- |
| **RC-1: Automated Test & Coverage Gate** | In-scope unit coverage = 100%; E2E & Security suites = 100% pass | Unit = **100%** (162/162); E2E = **100%** (2/2); Security = **100%** (35/35); Accessibility = **100** Lighthouse | **PASS** |
| **RC-2: Security & Resilience Gate** | 0 High ZAP alerts; 0 `pip-audit` CVEs; `k6` p95 < 1500ms & 0 orphan sales on crash | ZAP High = **0**; CVEs = **0**; `k6` p95 = **228.60ms** (1.00% fail rate); Crash recovery = **2.49s**, **0** orphan sales | **PASS** |
| **RC-3: Open Major/Critical Defect & Completion Gate** | 0 open unmitigated Major defects in core workflows; M1 mutation & CI gate complete | Open unfixed defects on `area2-Rehan` include **N4** (duplicate sale/double stock deduction on retry/double-submit) and **N2** (purchase quantity `2,147,483,648` accepted -> PostgreSQL overflow), plus M1 mutation & CI gate pending | **FAIL (HOLD)** |

### Rationale & Conditions to Lift Hold
Core sale/void calculations, RBAC access controls, crash recovery atomicity, and Dashboard WCAG 2.1 AA accessibility all meet or exceed targets. However, releasing while **N4** (lack of idempotency allowing duplicate sales/stock deduction on retry) and **N2** (unbounded purchase quantity risking PostgreSQL integer overflow in production) remain unfixed poses a direct **PR-01** stock-integrity risk.

**Required before shifting to GO:**
1. Fix or enforce idempotency / upper quantity validation for `N4` and `N2` (and verify with M2's `test_repeats.py` and `test_purchase.py`).
2. Complete M1's mutation testing and CI quality gate checks and merge `area1-malaika` and `area2-Rehan` into `main`.
