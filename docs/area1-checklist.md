# Member 1 checklist: CI evidence

Checked on 2026-11-28. **Proven** means a file or URL shows it. **Missing** means there is no proof yet. This list covers the CI items only.

## CI gate

| Item | Status | Proof |
| --- | --- | --- |
| Workflow with lint, tests and coverage, SonarQube gate and mutation | Proven | [ci.yml](../.github/workflows/ci.yml) |
| Thresholds and reasons | Proven | [ci.md](ci.md#thresholds-and-why) |
| All four checks pass on a pull request | Proven | [46159501791](https://github.com/Malaikaa0/sales-and-inventory-management/actions/runs/46159501791) |
| Full mutation run on `main` passes | Proven | [46160834242](https://github.com/Malaikaa0/sales-and-inventory-management/actions/runs/46160834242) (591 of 608) |
| Gate fails on an added bug | Proven locally | [probe-with-bug-gate.json](../reports/sonar/gate-proof/probe-with-bug-gate.json) |
| Blocks deployment on failure | **Missing** | The workflow has no deployment step |

## Fix pull request (#11)

| Item | Status | Proof |
| --- | --- | --- |
| Pull request with defect, root cause, test and fix | Proven | https://github.com/Malaikaa0/sales-and-inventory-management/pull/11 |
| Red before the fix (`e2d1f1d`) | Proven | [46158578375](https://github.com/Malaikaa0/sales-and-inventory-management/actions/runs/46158578375) |
| Green after the fix (`bccb9fe`) | Proven | [46158779876](https://github.com/Malaikaa0/sales-and-inventory-management/actions/runs/46158779876) |
| Merged | Proven | [203950](../reports/ci/Screenshot%202026-11-28%20203950.png) |
| Own screenshot of the red and green run pages | **Missing** | Only [automated captures](ci.md#automated-captures) |

## Blocked pull request (#17)

| Item | Status | Proof |
| --- | --- | --- |
| Opened and not merged | Proven | https://github.com/Malaikaa0/sales-and-inventory-management/pull/17 |
| Checks fail for a real reason | Proven | [46158780829](https://github.com/Malaikaa0/sales-and-inventory-management/actions/runs/46158780829); [203856](../reports/ci/Screenshot%202026-11-28%20203856.png) |
| Screenshot showing that merging is blocked | Proven | [blocked-merge.png](../reports/ci/blocked-merge.png) and [pr17-blocked-full.png](../reports/ci/pr17-blocked-full.png) (the same image); run [46162699895](https://github.com/Malaikaa0/sales-and-inventory-management/actions/runs/46162699895) |

## Branch protection on `main`

Read through the GitHub API on 2026-11-28: required checks `Lint`, `Mutation testing`, `SonarQube quality gate`, `Tests and coverage`; pull request required; branches must be up to date; no approvals required; no bypass, including for administrators; force pushes and deletions off.

| Item | Status | Proof |
| --- | --- | --- |
| Pull request required, four checks required, branch up to date | Proven | [204711](../reports/ci/Screenshot%202026-11-28%20204711.png), taken while 1 approval was still set |
| No approvals required (current rule) | **Missing** | No screenshot of the rule after the change; so far only the API reading above. [rule-with-approvals-earlier.png](../reports/ci/rule-with-approvals-earlier.png) still shows 1 approval |
| No bypass, force push or deletion | Proven | [204305](../reports/ci/Screenshot%202026-11-28%20204305.png) |
| Rule exists for `main` | Proven | [204547](../reports/ci/Screenshot%202026-11-28%20204547.png) |
| Merge refused because of a failing check | Proven | [blocked-merge.png](../reports/ci/blocked-merge.png): failing required checks and a disabled merge button |
