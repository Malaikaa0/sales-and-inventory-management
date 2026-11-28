## Defect

DEF-01 (Minor): the dashboard's "Low stock" table has no column headers, so a screen reader cannot name the column a cell belongs to. Found by SonarQube rule `Web:S5256`.

## Root cause

The table in `store/templates/store/dashboard.html` was written with a body only. The card title names the table visually but is not linked to its cells, and no test checked the page structure.

## Test

`tests/team/unit/test_dashboard_tables.py::test_low_stock_table_has_column_headers` renders the dashboard with a low stock item and expects the column headers `Product` and `Stock`.

First commit (test only): the test fails with `assert [] == ['Product', 'Stock']`.

## Fix

Second commit: a `<thead>` with two `<th scope="col">` cells. The headers are visible on the card.

## Checks

- Locally, after the fix: 223 unit tests pass, in-scope coverage 100%.
- SonarQube on this template: 2 bugs before, 1 after. The remaining one is DEF-02, not part of this change.
- `SonarQube quality gate` stays red until the other 5 bugs and 13 vulnerabilities are dealt with.
- Not checked: how the new header row looks in a browser, and a screen reader.
