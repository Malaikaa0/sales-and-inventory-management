# Defect log (master table)

Lead: Member 2. This is the single list of all logged defects for the Sale and Void sale project.

- Every defect is a GitHub Issue with the labels `defect`, `severity:*`, `priority:*` and `status:*`.
- Detailed reports are in `docs/defects/N*.md` (Member 2) and [docs/defects.md](../defects.md) (DEF-01–DEF-07, Member 3 with Member 1).
- Requirement IDs are from [scope.md](../scope.md). Risk IDs are from the [risk register](../risk-register.md).

**Severity:** Major means wrong money or stock, or data at risk. Minor means the task still works but is wrong, unclear or harder for some users. No defect is Critical.

**Priority:**

- P1: fix before release.
- P2: fix in this release if possible.
- P3: can wait.

Updated 28 Nov 2026.

| ID | Issue | Summary | Severity | Priority | Status | Triage decision | Risk | Requirement | Found by |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N1 | [#1](https://github.com/Malaikaa0/sales-and-inventory-management/issues/1) | Quantity above 100000 gets the "at least 1" message | Minor | P3 | Open, fix in PR [#11](https://github.com/Malaikaa0/sales-and-inventory-management/pull/11) (M1, as "D1") | Fix: one message per limit | PR-04 | BR1 (A4) | M2 API, generated BVA |
| N2 | [#2](https://github.com/Malaikaa0/sales-and-inventory-management/issues/2) | Purchase quantity has no upper limit (2,147,483,648 accepted) | Major | P2 | Open | Fix: `MaxValueValidator(100000)`; RCA in [rca-N2.md](rca-N2.md) | PR-01, PR-04 | A1 (protects FR2/FR6 stock) | M2 API |
| N3 | [#3](https://github.com/Malaikaa0/sales-and-inventory-management/issues/3) | Purchase validation failure returns 200, not 4xx | Minor | P3 | Open | Deferred: HTML form pattern, no data risk | PR-04 | – (weakness) | M2 API |
| N4 | [#4](https://github.com/Malaikaa0/sales-and-inventory-management/issues/4) | The same sale sent twice is recorded twice | Major | P2 (was P1) | Open | Fix: idempotency key; UI already blocks double click; RCA in [rca-N4.md](rca-N4.md) | PR-01 | FR2 (A3) | M2 API |
| N5 | [#5](https://github.com/Malaikaa0/sales-and-inventory-management/issues/5) | Boolean `false` accepted as 0 for tax, amount paid and points | Minor | P3 | Open | Fix: default only `None`/`""`, reject `bool` | PR-04, PR-02 | BR3, BR2 (A5) | M2 API, generated EP |
| N6 | [#6](https://github.com/Malaikaa0/sales-and-inventory-management/issues/6) | Item id beyond 64 bits gives 500 instead of 400 | Minor | P3 | Open | Fix: bound ids in `_int` | PR-04 | FR3 | M2 API coverage |
| N7 | [#8](https://github.com/Malaikaa0/sales-and-inventory-management/issues/8) | Till accepts 150% tax and charges 100% without warning | Major | P2 | Open | Fix: show an error, do not clamp silently | PR-02, PR-08 | BR3 | M2 E2E |
| N8 | [#9](https://github.com/Malaikaa0/sales-and-inventory-management/issues/9) | Logged-out till shows "Unexpected server response." instead of a sign-in prompt | Minor | P3 | Open | Fix: detect login redirect in `pos.js` | PR-08 | Roles (scope §User roles) | M2 E2E |
| DEF-01 | [#12](https://github.com/Malaikaa0/sales-and-inventory-management/issues/12) | "Low stock" table has no column headers | Minor | P3 | **Fixed, closed** (`6052421`) | Fixed and verified (Lighthouse `td-has-header`) | PR-05 | – (accessibility) | M1 Sonar `Web:S5256`; fixed by M3 |
| DEF-02 | [#13](https://github.com/Malaikaa0/sales-and-inventory-management/issues/13) | "Recent sales" table has no column headers | Minor | P3 | **Fixed, closed** (`6052421`) | Fixed and verified (Lighthouse `td-has-header`) | PR-05 | – (accessibility) | M1 Sonar `Web:S5256`; fixed by M3 |
| DEF-03 | [#14](https://github.com/Malaikaa0/sales-and-inventory-management/issues/14) | Dashboard muted table text fails WCAG 2.1 AA contrast | Minor | P2 | **Fixed, closed** (`6052421`) | Fixed and verified (axe 0 violations, Lighthouse 100) | PR-05 | – (accessibility) | M3 axe/Lighthouse |
| DEF-04 | [#15](https://github.com/Malaikaa0/sales-and-inventory-management/issues/15) | Concurrent sale writes hit SQLite lock contention under 10-VU load | Minor | P3 | Accepted | Accepted for SQLite (dev/test); production uses PostgreSQL | PR-06 | – (performance) | M3 k6 |
| DEF-05 | [#16](https://github.com/Malaikaa0/sales-and-inventory-management/issues/16) | Login page has no `<main>` landmark | Minor | P3 | Open | Fix: add `<main>`; outside the fixed screen | PR-05 | – (accessibility) | M3 axe |
| DEF-06 | [#19](https://github.com/Malaikaa0/sales-and-inventory-management/issues/19) | Point of sale placeholders and secure note fail WCAG 2.1 AA contrast (3.16:1, 3.28:1) | Minor | P2 | Open | Fix: darken to ≥ 4.5:1, rerun axe/Lighthouse on the till | PR-05 | WCAG 2.1 AA 1.4.3 (team target) | M3 axe |

## Summary

| Measure | Value |
| --- | --- |
| Logged defects | 14 (8 N + 6 DEF) |
| By severity | Major 3 (N2, N4, N7), Minor 11, Critical 0 |
| By status | Open 10, Fixed and closed 3 (DEF-01–03), Accepted 1 (DEF-04) |
| Open with a fix in review | 1 (N1 in PR #11) |
| Reopened | 0 |

## Triage of the other candidates (28 Nov 2026)

Checked against the evidence in the repository. A candidate becomes an Issue only if it can be reproduced and breaks a requirement (scope.md FR/BR, an agreed assumption, or the team's WCAG 2.1 AA target in PR-05).

| ID | Source | Finding | Decision | Reason |
| --- | --- | --- | --- | --- |
| D1 | [test-plan.md](../test-plan.md) §11 (M1) | Wrong message above 100,000 | **Duplicate of N1 ([#1](https://github.com/Malaikaa0/sales-and-inventory-management/issues/1))**, no new Issue | Same input, same message. Noted on #1; PR #11 "Fix D1" fixes #1 |
| D2 | test-plan §11 (M1) | Two lines of 100,000 for the same item accepted (200,000 units, stock 300,000) | **Rejected: not a defect** | scope.md BR1 sets the limit **per line** ("Each line quantity is 1 to 100,000"). The merged total is still checked against stock (`services.py:63,103`; API test `test_merged_duplicate_lines_exceeding_stock_rejected`). If the group wants a per-item limit, BR1 must change first |
| D3 | test-plan §11 (M1) | Sales list search for a phone made only of digits (`0712345678`, `345`) finds no sale | **Not filed: outside the requirements** | Reproducible from the code: `transactions/views.py:129-131` treats any all-digit search as a receipt number and drops the phone search. But the sales list search is not part of FR1–FR10/BR1–BR4 or the two workflows. Recorded as an out-of-scope observation for upstream |
| D4 | test-plan §11 (M1) | Quantity `2.0` rejected | **Rejected: not a defect** | The agreed rule (spec `x-accepts-numeric-strings`, A5 discussion) is that integer fields reject every JSON float, because `_int` does `int(str(2.0))`. The current behaviour matches it. `test_whole_number_float_is_rejected_current_behaviour` stays as is |
| DEF-06 | [defects.md](../defects.md) (M3) | Till placeholders and secure note below 4.5:1 contrast | **Filed: [#19](https://github.com/Malaikaa0/sales-and-inventory-management/issues/19)** | axe `color-contrast` (serious) on 3 nodes in `axe-before.json` and `axe-after.json` (`/transactions/new-sale/`). Breaks WCAG 2.1 AA 1.4.3 on the key screen of the Sale workflow |
| DEF-07 | [defects.md](../defects.md) (M3) | `/transactions/sales/` has an empty action `<th>` | **Not filed: best practice, not a requirement** | Reproducible (`axe-after.json`, rule `empty-table-header`, 1 node, impact minor). It is an axe best-practice rule, not a WCAG A/AA success criterion, and the sales list is not a key use-case screen. Kept as an improvement note |

Note: DEF-05 (`landmark-one-main`) is also an axe best-practice rule. It was filed before this triage rule was set, and stays open as P3.

## Related

- Pareto: [pareto.md](pareto.md), [reports/api/pareto.png](../../reports/api/pareto.png)
- RCA: [rca-N2.md](rca-N2.md), [rca-N4.md](rca-N4.md)
- Endpoint weaknesses (including W1, the void endpoint never returning 4xx): [api-coverage.md](../api-coverage.md#endpoint-weaknesses)
