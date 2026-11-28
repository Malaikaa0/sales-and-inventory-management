# SonarQube results and triage

SonarQube Community Build 26.11.0.134175, analysis of 2026-11-28T10:12:59+0000. Settings: [sonar-project.properties](../sonar-project.properties). Raw API responses: [reports/sonar/](../reports/sonar/).

Analysed: `accounts`, `store`, `transactions`, with tests in `tests/team`. **Not analysed:** `bills`, `invoice`, `InventoryMS` and `static` (including the point of sale JavaScript), so these figures do not describe the whole project.

The triage below is a proposal for the team to confirm.

## Metrics in plain words

| Metric | Value | What it means | What it shows here |
| --- | --- | --- | --- |
| Lines of code | 4208 | Lines that are not blank or comments, all languages | The size the other figures refer to |
| Bugs | 6 | Code Sonar expects to behave wrongly | All are tables without headers in templates, not logic errors |
| Vulnerabilities | 13 | Code an attacker might exploit | All are the random generator in the demo data loader |
| Security hotspots | 0 | Sensitive code a person should review | None raised |
| Code smells | 1 | Code that is harder to maintain | Very few |
| Coverage | 100.0% | Lines and branches run by tests (1031 lines, 120 conditions) | Only for files in the [coverage scope](scope.md#unit-coverage-scope); whole-project coverage is lower, see the [test plan](test-plan.md#unit-coverage) |
| Duplicated lines | 0.0% (0 blocks) | Share of lines repeated elsewhere | No duplicated blocks detected |
| Technical debt | 5 min | Estimated time to fix the code smells only | Bug fixes (12 min) and vulnerability fixes (130 min) are not part of it |
| Debt ratio | 0.0% | Debt compared with the estimated cost of writing the code | Negligible |
| Cyclomatic complexity | 446 | Number of independent paths, added up over the analysed code | A rough count of the test cases the logic needs |
| Cognitive complexity | 301 | How hard the code is to follow; nesting costs more | Compare functions rather than the total |

## Ratings

A is best, E is worst.

| Rating | Value | What decides it |
| --- | --- | --- |
| Reliability | C | The most severe bug: at least one Major |
| Security | C | The most severe vulnerability: at least one Major |
| Maintainability | A | The debt ratio |
| Security review | A | Share of hotspots reviewed; there are none to review |

The security rating of C comes entirely from findings triaged below as false positives.

SonarQube also counts issues by the quality they affect, where one issue can affect more than one: reliability 7, security 13, maintainability 1. These differ from the bug, vulnerability and smell counts above.

## Quality gate

Status: **OK**, with **0 conditions evaluated**. A pass with no conditions says nothing about quality. The CI gate needs thresholds on overall code.

## Issues

20 issues: 2 real defects, 13 false positives, 5 accepted. No issue has been changed inside SonarQube.

| # | Type | Location | Rule | Severity | Triage | Reason |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Bug | [store/templates/store/dashboard.html:75](../store/templates/store/dashboard.html#L75) | Web:S5256 | Major | Real defect | The "Low stock" table lists data with no column headers, so a screen reader cannot name the columns. |
| 2 | Bug | [store/templates/store/dashboard.html:94](../store/templates/store/dashboard.html#L94) | Web:S5256 | Major | Real defect | The "Recent sales" table lists data with no column headers, so a screen reader cannot name the columns. |
| 3 | Bug | [transactions/templates/documents/receipt.html:20](../transactions/templates/documents/receipt.html#L20) | Web:S5256 | Major | Accepted | Label and value table: the first cell of each row is its visible label. `<th scope="row">` would be better; low impact. |
| 4 | Bug | [transactions/templates/documents/receipt.html:76](../transactions/templates/documents/receipt.html#L76) | Web:S5256 | Major | Accepted | Label and value table: the first cell of each row is its visible label. `<th scope="row">` would be better; low impact. |
| 5 | Bug | [transactions/templates/transactions/sale_create.html:68](../transactions/templates/transactions/sale_create.html#L68) | Web:S5256 | Major | Accepted | Label and value table: the first cell of each row is its visible label. `<th scope="row">` would be better; low impact. |
| 6 | Bug | [transactions/templates/transactions/saledetail.html:55](../transactions/templates/transactions/saledetail.html#L55) | Web:S5256 | Major | Accepted | Label and value table: the first cell of each row is its visible label. `<th scope="row">` would be better; low impact. |
| 7 | Code Smell | [accounts/templates/accounts/login.html:39](../accounts/templates/accounts/login.html#L39) | Web:S9379 | Major | Accepted | Autofocus on the first field of a page whose only task is signing in. Revisit after the axe and Lighthouse checks. |
| 8 | Vulnerability | [store/management/commands/seed_demo.py:115](../store/management/commands/seed_demo.py#L115) | python:S2245 | Major | False positive | Seeded generator (`random.Random(42)`) that builds repeatable demo data. Nothing secret or security related depends on it. |
| 9 | Vulnerability | [store/management/commands/seed_demo.py:120](../store/management/commands/seed_demo.py#L120) | python:S2245 | Major | False positive | Seeded generator (`random.Random(42)`) that builds repeatable demo data. Nothing secret or security related depends on it. |
| 10 | Vulnerability | [store/management/commands/seed_demo.py:122](../store/management/commands/seed_demo.py#L122) | python:S2245 | Major | False positive | Seeded generator (`random.Random(42)`) that builds repeatable demo data. Nothing secret or security related depends on it. |
| 11 | Vulnerability | [store/management/commands/seed_demo.py:124](../store/management/commands/seed_demo.py#L124) | python:S2245 | Major | False positive | Seeded generator (`random.Random(42)`) that builds repeatable demo data. Nothing secret or security related depends on it. |
| 12 | Vulnerability | [store/management/commands/seed_demo.py:135](../store/management/commands/seed_demo.py#L135) | python:S2245 | Major | False positive | Seeded generator (`random.Random(42)`) that builds repeatable demo data. Nothing secret or security related depends on it. |
| 13 | Vulnerability | [store/management/commands/seed_demo.py:137](../store/management/commands/seed_demo.py#L137) | python:S2245 | Major | False positive | Seeded generator (`random.Random(42)`) that builds repeatable demo data. Nothing secret or security related depends on it. |
| 14 | Vulnerability | [store/management/commands/seed_demo.py:139](../store/management/commands/seed_demo.py#L139) | python:S2245 | Major | False positive | Seeded generator (`random.Random(42)`) that builds repeatable demo data. Nothing secret or security related depends on it. |
| 15 | Vulnerability | [store/management/commands/seed_demo.py:139](../store/management/commands/seed_demo.py#L139) | python:S2245 | Major | False positive | Seeded generator (`random.Random(42)`) that builds repeatable demo data. Nothing secret or security related depends on it. |
| 16 | Vulnerability | [store/management/commands/seed_demo.py:144](../store/management/commands/seed_demo.py#L144) | python:S2245 | Major | False positive | Seeded generator (`random.Random(42)`) that builds repeatable demo data. Nothing secret or security related depends on it. |
| 17 | Vulnerability | [store/management/commands/seed_demo.py:147](../store/management/commands/seed_demo.py#L147) | python:S2245 | Major | False positive | Seeded generator (`random.Random(42)`) that builds repeatable demo data. Nothing secret or security related depends on it. |
| 18 | Vulnerability | [store/management/commands/seed_demo.py:149](../store/management/commands/seed_demo.py#L149) | python:S2245 | Major | False positive | Seeded generator (`random.Random(42)`) that builds repeatable demo data. Nothing secret or security related depends on it. |
| 19 | Vulnerability | [store/management/commands/seed_demo.py:152](../store/management/commands/seed_demo.py#L152) | python:S2245 | Major | False positive | Seeded generator (`random.Random(42)`) that builds repeatable demo data. Nothing secret or security related depends on it. |
| 20 | Vulnerability | [store/management/commands/seed_demo.py:172](../store/management/commands/seed_demo.py#L172) | python:S2245 | Major | False positive | Seeded generator (`random.Random(42)`) that builds repeatable demo data. Nothing secret or security related depends on it. |

## What SonarQube did not report

None of the candidate defects D1 to D4 in the [test plan](test-plan.md#candidate-defects) appears among these issues. They are errors in behaviour that were found by reading and running the code.

## Per-function complexity

SonarQube publishes complexity measures per file, not per function. The per-function values come from a second analysis of `transactions/services.py` in a separate project, with two rules set to a threshold of 0. See [cfg-complexity.md](cfg-complexity.md).

## Reproduce

```powershell
coverage run -m pytest tests/team/unit -q
coverage xml
docker network create sqe-sonar    # once
docker run -d --name sqe-sonarqube --network sqe-sonar -p 127.0.0.1:9000:9000 sonarqube:community
# Open http://localhost:9000, create a token, then:
$env:SONAR_TOKEN = Read-Host "Token"
docker run --rm --network sqe-sonar -e SONAR_TOKEN -e SONAR_HOST_URL=http://sqe-sonarqube:9000 -v "${PWD}:/usr/src" sonarsource/sonar-scanner-cli:latest
```

Never write the token into a file.
