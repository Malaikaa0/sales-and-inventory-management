# SonarQube results and triage

SonarQube Community Build 26.11.0.134175, latest scoped analysis 2026-11-28T10:36:27+0000. Settings: [sonar-project.properties](../sonar-project.properties). Raw API responses, with author fields removed: [reports/sonar/](../reports/sonar/).

The metric, rating and issue sections describe the **scoped** analysis of `accounts`, `store` and `transactions`, with tests in `tests/team`. A whole repository analysis is compared under [Two scopes](#two-scopes).

The triage below is a proposal for the team to confirm.

## Metrics in plain words

| Metric | Value | What it means | What it shows here |
| --- | --- | --- | --- |
| Lines of code | 4208 | Lines that are not blank or comments, all languages | The size the other figures refer to |
| Bugs | 6 | Code Sonar expects to behave wrongly | All are tables without headers in templates, not logic errors |
| Vulnerabilities | 13 | Code an attacker might exploit | All are the random generator in the demo data loader |
| Security hotspots | 0 | Sensitive code a person should review | None raised |
| Code smells | 1 | Code that is harder to maintain | Very few |
| Coverage | 100.0% | Lines and branches run by tests (1031 lines, 120 conditions) | Only for files in the [coverage scope](scope.md#unit-coverage-scope) |
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

The security rating comes entirely from findings triaged below as false positives.

## Quality gate

Gate **SQE-gate**, applied to `sales-and-inventory-management`. Result of the last analysis: **OK**. Saved: [definition](../reports/sonar/quality-gate-definition.json), [result](../reports/sonar/quality-gate.json).

| Condition | Rule | Actual | Status |
| --- | --- | --- | --- |
| New bugs | above 0 fails | 0 | OK |
| New vulnerabilities | above 0 fails | 0 | OK |
| Coverage | below 90 fails | 100.0 | OK |
| Duplicated lines | above 3 fails | 0.0 | OK |
| Maintainability rating | worse than A fails | A | OK |

The two "new" conditions look only at code changed in the new code period (since the previous version). No application code has changed between analyses, so they say nothing about the 6 existing bugs and 13 existing vulnerabilities, which the gate does not block. The gate has not yet been seen to fail; the blocked pull request still has to show that.

## Two scopes

| Metric | Scoped: `sales-and-inventory-management` | Whole: `sales-inventory-whole` |
| --- | --- | --- |
| Lines of code | 4208 | 8143 |
| Bugs | 6 | 14 |
| Vulnerabilities | 13 | 16 |
| Security hotspots | 0 | 0 |
| Code smells | 1 | 5 |
| Coverage % | 100.0 | 60.1 |
| Line coverage % | 100.0 | 61.8 |
| Branch coverage % | 100.0 | 46.1 |
| Duplicated lines % | 0.0 | 0.2 |
| Duplicated blocks | 0 | 2 |
| Technical debt (min) | 5 | 13 |
| Debt ratio % | 0.0 | 0.0 |
| Cyclomatic complexity | 446 | 890 |
| Cognitive complexity | 301 | 579 |
| Reliability rating | C | C |
| Security rating | C | E |
| Maintainability rating | A | A |
| Security review rating | A | A |

Whole repository raw results: [reports/sonar/whole/](../reports/sonar/whole/). Its gate is **Sonar way**, status OK, with 0 conditions evaluated.

### Why the scopes differ

| | Scoped | Whole |
| --- | --- | --- |
| Purpose | The code under test and what it depends on. Our gate applies here | The repository as a whole, since the brief asks for SonarQube on the project |
| Sources | `accounts`, `store`, `transactions` | `.`, which adds `bills`, `invoice`, `InventoryMS`, `static`, `terraform` and root files |
| Left out of analysis | Migrations, upstream tests | `.venv`, `reports`; our tests are analysed as tests |
| Coverage counted for | Files in the [coverage scope](scope.md#unit-coverage-scope) | Analysed code except migrations, upstream tests and `manage.py` |

The whole repository coverage differs from the `coverage.py` whole-project figure in the [test plan](test-plan.md#unit-coverage), because SonarQube also counts code that `coverage.py` does not measure, such as JavaScript, which has no tests here.

### Whole repository issues by folder

35 open issues. Only the 20 scoped issues below are triaged; any others still need triage.

The whole repository security rating of E comes from findings outside the application code, the most severe being a Blocker on a public IP address in `terraform/azure/main.tf`. The other issues not in the scoped list are in `static` JavaScript, `invoice` templates, `transactions/tests.py` (upstream), the `Dockerfile` and `terraform`.

| Folder or file | Bugs | Vulnerabilities | Code smells |
| --- | --- | --- | --- |
| `Dockerfile` | 0 | 1 | 0 |
| `accounts` | 0 | 0 | 1 |
| `invoice` | 3 | 0 | 0 |
| `static` | 4 | 0 | 4 |
| `store` | 2 | 13 | 0 |
| `terraform` | 0 | 2 | 0 |
| `transactions` | 5 | 0 | 0 |

## Issues in the scoped analysis

20 issues: 2 real defects, 13 false positives, 5 accepted. No issue has been changed inside SonarQube.

| # | Type | Location | Rule | Severity | Triage | Reason |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Bug | [store/templates/store/dashboard.html:75](../store/templates/store/dashboard.html#L75) | Web:S5256 | Major | Real defect | The "Low stock" table lists data with no column headers. Draft [DEF-01](defects.md). |
| 2 | Bug | [store/templates/store/dashboard.html:94](../store/templates/store/dashboard.html#L94) | Web:S5256 | Major | Real defect | The "Recent sales" table lists data with no column headers. Draft [DEF-02](defects.md). |
| 3 | Bug | [transactions/templates/documents/receipt.html:20](../transactions/templates/documents/receipt.html#L20) | Web:S5256 | Major | Accepted | Three label and value pairs (receipt number, date, status). This template is output only as a PDF, and `InventoryMS/pdf.py` calls `write_pdf()` with no tagging option, so we expect header cells not to reach a screen reader. Each label sits beside its value in the same row. |
| 4 | Bug | [transactions/templates/documents/receipt.html:76](../transactions/templates/documents/receipt.html#L76) | Web:S5256 | Major | Accepted | Receipt totals with the label in the first cell of each row. Same untagged PDF output, so we expect no gain from `<th>`, while the print styles in `document_base.html` target `td` and would need changing. |
| 5 | Bug | [transactions/templates/transactions/sale_create.html:68](../transactions/templates/transactions/sale_create.html#L68) | Web:S5256 | Major | Accepted | Four fixed rows (Subtotal, Loyalty discount, Tax, Total) in two columns, each value straight after its label. `style.css` styles `.totals td` and `.pos-totals td`, so changing the label cells also means CSS changes in upstream code. |
| 6 | Bug | [transactions/templates/transactions/saledetail.html:55](../transactions/templates/transactions/saledetail.html#L55) | Web:S5256 | Major | Accepted | A read-only payment summary of label and value rows, in reading order. `.totals td` rules in `style.css` set the layout, so the change would touch CSS too. `<th scope="row">` is the better markup and can follow if axe reports it. |
| 7 | Code Smell | [accounts/templates/accounts/login.html:39](../accounts/templates/accounts/login.html#L39) | Web:S9379 | Major | Accepted | The page has one task, and `autofocus` puts keyboard users at Username without tabbing. A failed sign-in message has `role="alert"`, so it should still be announced. Recheck in the keyboard and axe tests. |
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

None of the candidate defects D1 to D4 in the [test plan](test-plan.md#candidate-defects) appears among the scoped issues. They are errors in behaviour that were found by reading and running the code.

## Per-function complexity

SonarQube publishes complexity measures per file, not per function. The per-function values come from a separate analysis of `transactions/services.py`, with two rules set to a threshold of 0. See [cfg-complexity.md](cfg-complexity.md).

## Reproduce

These commands carry the settings used. The scans were run from Git Bash, so this PowerShell form has not been run as written.

```powershell
coverage run -m pytest tests/team/unit -q
coverage xml
docker network create sqe-sonar    # once
docker run -d --name sqe-sonarqube --network sqe-sonar -p 127.0.0.1:9000:9000 sonarqube:community
# Open http://localhost:9000, create a token, then:
$env:SONAR_TOKEN = Read-Host "Token"
$scan = "run","--rm","--network","sqe-sonar","-e","SONAR_TOKEN","-e","SONAR_HOST_URL=http://sqe-sonarqube:9000","-v","${PWD}:/usr/src","sonarsource/sonar-scanner-cli:latest"

# scoped
docker @scan

# whole repository
coverage xml --omit="*/migrations/*" -o coverage-whole.xml
docker @scan "-Dsonar.projectKey=sales-inventory-whole" "-Dsonar.sources=." "-Dsonar.exclusions=.venv/**,tests/**,reports/**" "-Dsonar.coverage.exclusions=**/migrations/**,**/tests.py,InventoryMS/test_utils.py,manage.py" "-Dsonar.python.coverage.reportPaths=coverage-whole.xml"
```

The quality gate is stored in the SonarQube server, not in the repository. A new server needs it created again from [quality-gate-definition.json](../reports/sonar/quality-gate-definition.json). Never write the token into a file.
