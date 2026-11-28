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
| Status | Draft, not triaged |

**Steps**

1. Seed the demo data (`python manage.py seed_demo`) and start the server.
2. Sign in as `cashier`.
3. Open the dashboard (`/`).
4. In the browser's developer tools, inspect the table in the "Low stock" card.

**Expected:** the table has header cells naming its columns, for example Product and Stock. The headers may be visually hidden.

**Actual:** the table has only a body. Every cell is a `<td>`.

**Likely impact:** a screen reader cannot announce which column a cell belongs to. The card title "Low stock" is not linked to the table.

**Suggested fix:** add a `<thead>` with `<th scope="col">` cells.

## DEF-02: "Recent sales" table has no column headers

| Field | Value |
| --- | --- |
| File and line | [store/templates/store/dashboard.html:94](../store/templates/store/dashboard.html#L94) |
| Severity | Minor |
| Priority | Low |
| Category | Accessibility |
| Status | Draft, not triaged |

**Steps**

1. Seed the demo data and start the server.
2. Sign in as `cashier`.
3. Open the dashboard (`/`).
4. Inspect the table in the "Recent sales" card.

**Expected:** header cells naming the three columns, for example Receipt, When and Amount.

**Actual:** the table has only a body. Every cell is a `<td>`.

**Likely impact:** a screen reader cannot announce which column a cell belongs to. The time and the amount are read without a label.

**Suggested fix:** add a `<thead>` with `<th scope="col">` cells.
