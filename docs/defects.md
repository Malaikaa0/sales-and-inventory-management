# Defects

**Drafts.** None of these is logged as a GitHub Issue yet. Severity and priority are proposals for the team's triage.

Severity scale: Critical (data or money is wrong, or access control fails), Major (a task cannot be completed), Minor (the task works but is harder for some users).

Found by SonarQube rule `Web:S5256` and confirmed on 2026-11-28 by rendering the dashboard in a test: each table had no `<th>` cell, no caption and no `aria-label`. Not yet checked with a screen reader.

The other candidate defects, D1 to D4, are in the [test plan](test-plan.md#candidate-defects) and are not repeated here.

## DEF-01: "Low stock" table has no column headers

| Field | Value |
| --- | --- |
| File and line | [store/templates/store/dashboard.html:75](../store/templates/store/dashboard.html#L75) |
| Severity | Minor |
| Priority | Low |
| Category | Accessibility |
| Status | Fixed on `area1-malaika` (Member 3) |

**Steps**

1. Seed the demo data (`python manage.py seed_demo`) and start the server.
2. Sign in as `cashier`.
3. Open the dashboard (`/`).
4. In the browser's developer tools, inspect the table in the "Low stock" card.

**Expected:** the table has header cells naming its columns, for example Product and Stock. The headers may be visually hidden.

**Actual:** the table has only a body. Every cell is a `<td>`.

**Likely impact:** a screen reader cannot announce which column a cell belongs to. The card title "Low stock" is not linked to the table.

**Suggested fix / Resolution:** added `<thead class="visually-hidden">` with `<th scope="col">Product</th><th scope="col">Stock</th>` and `aria-label="Low stock products"`. Verified by Lighthouse `td-has-header` audit (Before: Fail -> After: Pass).

## DEF-02: "Recent sales" table has no column headers

| Field | Value |
| --- | --- |
| File and line | [store/templates/store/dashboard.html:94](../store/templates/store/dashboard.html#L94) |
| Severity | Minor |
| Priority | Low |
| Category | Accessibility |
| Status | Fixed on `area1-malaika` (Member 3) |

**Steps**

1. Seed the demo data and start the server.
2. Sign in as `cashier`.
3. Open the dashboard (`/`).
4. Inspect the table in the "Recent sales" card.

**Expected:** header cells naming the three columns, for example Receipt, When and Amount.

**Actual:** the table has only a body. Every cell is a `<td>`.

**Likely impact:** a screen reader cannot announce which column a cell belongs to. The time and the amount are read without a label.

**Suggested fix / Resolution:** added `<thead class="visually-hidden">` with `<th scope="col">Receipt</th><th scope="col">When</th><th scope="col">Amount</th>` and `aria-label="Recent sales"`. Verified by Lighthouse `td-has-header` audit (Before: Fail -> After: Pass).

## DEF-03: Dashboard table muted metadata fails WCAG 2.1 AA contrast ratio

| Field | Value |
| --- | --- |
| File and line | [static/css/style.css:763](../static/css/style.css#L763) |
| Severity | Minor |
| Priority | Medium |
| Category | Accessibility (WCAG 2.1 AA) |
| Status | Fixed on `area1-malaika` (Member 3) |

**Steps**

1. Open the dashboard (`/`) as `cashier`.
2. Run `axe-core` or Lighthouse accessibility audit.

**Expected:** secondary text inside dashboard tables meets minimum `4.5:1` contrast against `#ffffff`.

**Actual (before fix):** `.table .text-muted, .table small.text-muted` used `#77867d` (`3.82:1` contrast ratio), failing `color-contrast` across 20 nodes (`axe-core`) and Lighthouse (`95`).

**Resolution:** updated `#77867d` to `#59665e` (`5.89:1` contrast ratio). Verified in `after` audits (`axe-core`: 0 violations on Dashboard; Lighthouse Accessibility: `100`).

## DEF-04: Concurrent POS sale writes encounter SQLite lock contention under 10-VU load

| Field | Value |
| --- | --- |
| File and line | [transactions/services.py:84](../transactions/services.py#L84) |
| Severity | Minor (SQLite dev/test only) |
| Priority | Low |
| Category | Performance / Concurrency |
| Status | Open (accepted for SQLite; mitigated by PostgreSQL in production) |

**Steps**

1. Run `python tools/run_k6_load.py` (10 virtual users ramping over 25s, mixing reads and `POST /transactions/new-sale/`).

**Expected:** all valid concurrent sale submissions succeed cleanly.

**Actual:** 9 of 67 concurrent sale POSTs failed (1.00% overall HTTP failure rate across 898 requests) with `database is locked` under SQLite's file-level write lock; `sale_post_duration` p95 reached `1157.6ms`.

**Likely impact:** affects multi-cashier concurrency if deployed on SQLite; production configuration (`InventoryMS/settings.py`) uses PostgreSQL row-level locks.

## Remaining Accessibility Findings on Unmodified Screens (Out of Fixed-Screen Scope)

- **DEF-05 (Minor):** `/accounts/login/` lacks a `<main>` landmark (`axe-core`: `landmark-one-main`, `region`).
- **DEF-06 (Minor):** `/transactions/new-sale/` Select2 placeholders (`#87948c`, `3.16:1`) and `.pos-secure-note` (`#849188`, `3.28:1`) fall below `4.5:1` contrast.
- **DEF-07 (Minor):** `/transactions/sales/` table has an empty action `<th></th>` (`axe-core`: `empty-table-header`).
