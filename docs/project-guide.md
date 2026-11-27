# Project guide

SE3002 Software Quality Engineering final project. This guide covers setup on your own computer, how we work in Git, who does what, and what is done so far.

| | |
| --- | --- |
| Our repository | https://github.com/Malaikaa0/sales-and-inventory-management |
| Upstream | https://github.com/munuhee/sales-and-inventory-management |
| Licence | MIT ([LICENSE](../LICENSE)) |
| Baseline tag | `baseline-v0` |
| Baseline commit | `0733e7216e88168fe235cd29e3a37840be2ad3fe` |

## 1. Set up your computer

These steps are for Windows PowerShell.

### 1.1 Install first

- [Git](https://git-scm.com/downloads)
- [Python 3.12](https://www.python.org/downloads/)
- Only for PDF receipts and invoices: the GTK3 runtime, see the [WeasyPrint guide](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows)

You need write access to push. Ask Member 1 to add your GitHub account under **Settings > Collaborators**.

### 1.2 Clone

The project setup is on the `area1-malaika` branch, not yet on `main`.

```powershell
git clone https://github.com/Malaikaa0/sales-and-inventory-management.git
cd sales-and-inventory-management
git switch area1-malaika
git remote add upstream https://github.com/munuhee/sales-and-inventory-management.git
```

Set your own name and email, so your commits count as yours:

```powershell
git config user.name "Your Name"
git config user.email "you@example.com"
```

### 1.3 Install the dependencies

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install pytest==9.2.0 pytest-django==4.14.0 coverage==7.17.5
```

If PowerShell blocks the activation script, run this first, then activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

### 1.4 Seed and run

```powershell
$env:DEBUG="True"
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Open http://127.0.0.1:8000. `$env:DEBUG` and the activated environment last only in the current window.

| Username | Role |
| --- | --- |
| `admin` | Admin |
| `manager` | Executive |
| `cashier` | Operative |

All three use the password `demo-pass-123`. This is synthetic demo data for local use only.

### 1.5 Reset between runs

Stop the server, then:

```powershell
Remove-Item db.sqlite3
python manage.py migrate
python manage.py seed_demo
```

### 1.6 Run our tests

```powershell
$env:DEBUG="True"
python -m pytest
```

With branch coverage:

```powershell
python -m coverage run --branch -m pytest
python -m coverage report --include="transactions/services.py"
```

Our tests go in `tests/team/`. Upstream tests earn no marks.

## 2. How we work in Git

1. Work on your own branch, started from `area1-malaika`:

    ```powershell
    git switch area1-malaika
    git pull
    git switch -c area2-yourname     # or area3-yourname
    ```

2. Commit your own work from your own account. Commit history is checked in the viva.
3. Add files by name, then check what is staged:

    ```powershell
    git add tests/team/api
    git status
    git commit -m "Short description of the change"
    git push -u origin area2-yourname
    ```

4. Merge through pull requests. The current CI ([ci.yml](../.github/workflows/ci.yml)) runs only for `main`, and it does not yet include our team tests, SonarQube or mutation.
5. Do not change upstream application code, except for a documented fix made through a pull request.
6. Never commit `.venv/`, `db.sqlite3` or `.env`.

## 3. Folders

| Folder | Contents |
| --- | --- |
| `tests/team/unit` | Unit tests |
| `tests/team/api` | API and integration tests |
| `tests/team/e2e` | Playwright browser tests |
| `tests/team/security` | Access checks |
| `tests/team/perf` | k6 scripts and the recovery test |
| `tools/generator` | Test data generator |
| `openapi` | OpenAPI specification |
| `docs` | Test management documents |
| `reports` | Tool output and evidence |

## 4. Done so far

| Item | Status |
| --- | --- |
| `baseline-v0` tag and `upstream` remote | Done |
| Folder structure and `pytest.ini` | Done |
| Setup, seed and reset instructions | Done, checked on a fresh clone |
| Unit tests for `parse_lines` and the sale services | Pushed: 38 tests pass, `transactions/services.py` at 100% statement and branch coverage |
| Unit tests for models and permissions | Written by Member 1, not yet pushed |
| Test plan, risk register, traceability, AI-use record | Empty files only |
| `docs/scope.md` | Not written |

Unit testing is not finished: the rest of the server-side business logic still needs tests or a written justification.

## 5. Work division

Marks are the group marks from the rubric. The 20 viva marks are individual.

### Member 1 (Malaika): static analysis, white-box, mutation, CI (34 marks)

- [x] Baseline and project setup
- [ ] Scope document: two workflows, at least 8 requirements (3 or more per workflow), 4 business rules, 2 roles
- [ ] Unit tests: 100% statement and branch coverage of server-side business logic (partly done)
- [ ] MCC table and MC/DC pairs for the critical module
- [ ] SonarQube metrics, control flow graph and cyclomatic complexity
- [ ] Mutation testing: 2 custom operators, at least 15 surviving mutants analysed
- [ ] CI quality gate, one fix pull request, one blocked pull request

### Member 2: API testing and data generation (31 marks)

- [ ] OpenAPI specification for the workflow endpoints
- [ ] Generator for equivalence classes and 3-point boundary values
- [ ] Change two constraints, regenerate and show the effect
- [ ] API and integration tests: rejections, invalid transitions, repeated requests, record read-back
- [ ] Lead: test plan, three-point estimates, traceability matrix
- [ ] Lead: defects, root cause analysis for 2 major defects, Pareto chart

### Member 3: use cases, usability, security, performance (35 marks)

- [ ] Use case specifications and Playwright automation
- [ ] Two browser tests (one per workflow), including a rejected value and keyboard navigation
- [ ] Lighthouse and axe-core, fix one screen, before and after reports
- [ ] Access matrix, 4 or more automated access checks, ZAP passive scan, dependency audit
- [ ] k6 load runs and one failure-and-recovery test
- [ ] Lead: risk register (8 product and 2 project risks), exit criteria
- [ ] Lead: weekly progress reports, GQM metrics, test completion report

### Everyone

- Write and automate **two use cases each**, with at least 2 alternative and 2 exception flows per use case.
- Log defects as GitHub Issues with severity, priority, status and triage decision.
- Record estimated and actual effort.
- Record your use of AI tools in [ai-use-record.md](ai-use-record.md).
- Understand every component. The viva covers all of them.

## 6. Order of work

1. Agree the two workflows and register the repository in the shared sheet. The deadline is 5 days from the announcement.
2. Write `docs/scope.md`. Sale and void sale are the suggested pair, still to be agreed.
3. Write the risk register and estimates. Risk level decides test technique and depth.
4. Start each area: unit, API, browser tests.
5. Mutation and the CI gate, once the tests are stable.
6. Security, performance, completion report and final package.

## 7. Final submission

- One PDF report and a zip of the repository, including the `.git` folder.
- File names: `Project_RollNumber1_RollNumber2_RollNumber3_Section.zip` and `.pdf`.
- The PDF contains the scope, risk register, traceability table, all results, area ownership, AI-use record and evidence links.
- It ends with a release or hold decision, showing actual against target for three release criteria.

The assignment brief is the authority if this guide differs from it.
