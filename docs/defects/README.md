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

## Summary

| Measure | Value |
| --- | --- |
| Logged defects | 13 (8 N + 5 DEF) |
| By severity | Major 3 (N2, N4, N7), Minor 10, Critical 0 |
| By status | Open 9, Fixed and closed 3 (DEF-01–03), Accepted 1 (DEF-04) |
| Open with a fix in review | 1 (N1 in PR #11) |
| Reopened | 0 |

## Candidates not yet logged (need triage)

| ID | Source | Finding | Proposed decision |
| --- | --- | --- | --- |
| DEF-06 | [defects.md](../defects.md) (M3) | `/transactions/new-sale/` Select2 placeholder and `.pos-secure-note` contrast below 4.5:1 | Log as Minor/P3 (PR-05) |
| DEF-07 | [defects.md](../defects.md) (M3) | `/transactions/sales/` table has an empty action `<th>` | Log as Minor/P3 (PR-05) |
| D1 | [test-plan.md](../test-plan.md) §11 (M1) | Wrong message above 100,000 | **Duplicate of N1 (#1)**; fixed in PR #11 |
| D2 | test-plan §11 (M1) | Two lines of 100,000 for the same item accepted (200,000 units) | Decide whether the limit is per line (as coded and as scope BR1 says) or per item. If per line, not a defect |
| D3 | test-plan §11 (M1) | Sales search for a phone number made only of digits finds no sale | Log as Minor/P3 (outside the two workflows' requirements) |
| D4 | test-plan §11 (M1) | Quantity `2.0` rejected | Not a defect under A5 and the spec: integer fields reject all floats (`_int`), as agreed. Close |

## Related

- Pareto: [pareto.md](pareto.md), [reports/api/pareto.png](../../reports/api/pareto.png)
- RCA: [rca-N2.md](rca-N2.md), [rca-N4.md](rca-N4.md)
- Endpoint weaknesses (including W1, the void endpoint never returning 4xx): [api-coverage.md](../api-coverage.md#endpoint-weaknesses)
