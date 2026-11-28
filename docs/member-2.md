# Member 2 — API testing · Test data generation · Test management lead

Follows `docs/project-guide.md` (Member 1's guide). **That guide is the authority for the group.** This file is only Member 2's working notes.
Workflows: **Sale** + **Void sale** (confirm with Member 1). Shared record: `Item.quantity` (stock), plus `Customer.loyalty_points`.

## What I own (from the project guide)

- [ ] OpenAPI spec for the workflow endpoints → `openapi/openapi.yaml`
- [ ] Generator for equivalence classes + 3-point boundary values → `tools/generator/`
- [ ] Change two constraints, regenerate, show the effect
- [ ] API & integration tests → `tests/team/api/`: rejections, invalid transitions, repeated requests, record read-back
- [ ] Lead: test plan, three-point estimates, traceability matrix (`docs/test-plan.md`, `docs/traceability.md`)
- [ ] Lead: defects (GitHub Issues), RCA for 2 major defects, Pareto chart
- [ ] My 2 use cases (≥ 2 alternative + ≥ 2 exception flows each), automated in Playwright
- [ ] My rows in `docs/ai-use-record.md` + estimated/actual effort

## Must stay the same for the whole group
Workflows · requirement and rule IDs (from `docs/scope.md`, written by Member 1) · repo, branches, folders · defect format (GitHub Issue labels).
If `scope.md` isn't written yet, use the draft in §7 and agree it with Member 1.

## 0. Setup (Windows PowerShell)

```powershell
git switch area1-malaika; git pull
git switch -c area2-<yourname>
py -3.12 -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install pytest==9.2.0 pytest-django==4.14.0 coverage==7.17.5 requests pyyaml
pip install -r tools/generator/requirements.txt   # pinned generator + spec validator tools
$env:DEBUG="True"; $env:LOGIN_MAX_ATTEMPTS="1000"
python manage.py migrate; python manage.py seed_demo
python manage.py runserver        # leave it running in this window
```
Run the API tests in a second window (activate `.venv`, set `$env:DEBUG="True"`). Reset: stop the server, `Remove-Item db.sqlite3`, migrate, seed_demo.
Note: `pytest.ini` has `testpaths = tests/team`, so plain `python -m pytest` also runs the API tests, and they need the server. Run them with
`python -m pytest tests/team/api`, and mark them `@pytest.mark.api`, so Member 1 can skip them with `-m "not api"` (agree this with her).

## 1. Endpoints under test

| Method & path | Body | Success | Failure | Role |
|---|---|---|---|---|
| `GET/POST /accounts/login/` | form `username`, `password`, `csrfmiddlewaretoken` | 302 → `/` | 200 + error; locked after 5 failures | anyone |
| `GET /get-items/?term=` | – | 200 JSON `[{id,name,price,stock,...}]` (max 20) | 302 to login | Operative+ |
| `GET /accounts/get_customers/?term=` | – | 200 `{results:[{id,label,loyalty_points}]}` | | Operative+ |
| **`POST /transactions/new-sale/`** | JSON `{customer, items:[{id,quantity}], tax_percentage, amount_paid, redeem_points}` + header `X-CSRFToken` + `Referer` | 200 `{status:"success", sale_id, receipt_number, grand_total, change, points_earned}` | 400 `{status:"error", message}` · 500 unexpected | Operative+ |
| **`POST /transactions/sale/{pk}/void/`** | form `reason`, `csrfmiddlewaretoken` | 302 → sale detail | error if already voided · 403 for Operative | Executive+ |
| `GET /transactions/sale/{pk}/` | – | 200 HTML (status Completed/Voided) | 404 | Operative+ |
| `POST /transactions/new-purchase/` | form (used only as **setup** to add stock) | 302 | 200 + errors | Executive+ |

Login with `requests`: GET `/accounts/login/` → regex the `name="csrfmiddlewaretoken" value="..."` → POST the form with a `Referer` header → keep the `Session`.
For the sale POST, take a fresh token from GET `/transactions/new-sale/` and send it as `X-CSRFToken`.
Users: `cashier` (Operative), `manager` (Executive), `admin`. Password `demo-pass-123`.

## 2. OpenAPI spec (`openapi/openapi.yaml`, 3.0.3)

`SaleRequest`: `customer` integer ≥ 1 · `items` array `minItems: 1, maxItems: 200` of `{id: integer ≥ 1, quantity: integer, minimum: 1, maximum: 100000}` ·
`tax_percentage` number `0..100` · `amount_paid` number `≥ 0` · `redeem_points` integer `≥ 0`.
`VoidForm`: `reason` string `maxLength: 200`. Responses: `SaleSuccess`, `Error {status, message}`, 302, 403, 404.
Security: `cookieAuth` (`sessionid`) + `X-CSRFToken` header. Validate with `npx @redocly/cli lint openapi/openapi.yaml`.
These limits come from `transactions/services.py` (`MAX_LINES = 200`, `MAX_QTY_PER_LINE = 100000`). Check them in the code yourself.

## 3. Generator (`tools/generator/generate.py`)

`python tools/generator/generate.py openapi/openapi.yaml` → `tools/generator/out/cases.json`. Deterministic: no unseeded randomness.
- numbers/integers with min/max → `min−δ, min, min+δ, max−δ, max, max+δ` + one nominal value (δ = 1 for integers, 0.01 for money)
- arrays → lengths 0, 1, 2, 199, 200, 201
- strings with maxLength → `max−1, max, max+1`
- EP invalid classes, one at a time: missing, `null`, wrong type (`"abc"`, `2.5` for an integer), empty
- each case: `{id, field, technique (BVA/EP), partition, value, valid, expected_status, rule}`. The expected status is set by the generator (200 valid / 400 invalid).

**Regeneration demo:** change `items[].quantity.maximum 100000 → 500` and `tax_percentage.maximum 100 → 50` → regenerate → commit before/after `cases.json` + `git diff --stat` + the test run, then explain which cases appeared, disappeared or changed, and which now fail against the unchanged app.

## 4. API tests (`tests/team/api/`, pytest + requests)

- `conftest.py`: `BASE = http://127.0.0.1:8000`, `login(user)`, `csrf(session, path)`, `stock(session, name)` (from `/get-items/?term=`), `points(session, name)`, and a fixture that makes a fresh item with enough stock (via `new-purchase` as manager, status `S`).
- `test_sale_generated.py`: parametrize over `cases.json` → assert the status + `status` field + **stock read back** (unchanged when rejected, −q when accepted).
- `test_sale_rules.py`: oversell (stock = q accepted / q − 1 rejected) · under-payment by 0.01 · exact payment (change 0) · each redemption rule (disabled, below min, above balance, above the bill, valid) · tax out of range · unknown customer/item.
- `test_void.py`: void → stock +q and points reversed · **void again → rejected, stock not added twice** (invalid transition) · cashier void → 403, stock unchanged · void a missing sale → 404.
- `test_repeats.py`: POST the same sale JSON twice → count sales and stock movement (expected one per assumption; baseline likely two → defect). Void twice in quick succession.
- `test_flow.py` (the brief's scenario): stock 10 → sell 4 → 6 → sell 7 rejected → still 6 → void the first sale → 10.
- `test_access_api.py`: anonymous POST `new-sale` → 302, no sale.
- **API coverage criteria** table: paths, operations, parameters, enum values, status codes per operation, content types, response properties asserted (achieved / total).

## 5. Defects already confirmed on this repo (open them as GitHub Issues)

| # | Behaviour | Evidence |
|---|---|---|
| N1 | Sale line q = 100001 → 400 "Quantities must be at least 1." (wrong message for the upper bound) | `requests` run on `seed_demo` data, 27 Nov |
| N2 | Purchase q = 2,147,483,648 accepted; stock became 2,147,483,694 (no upper limit; PostgreSQL would overflow) | same |
| N3 | Purchase form validation failure returns 200, not 4xx | same |
| N4 | Repeated sale POST → likely a duplicate sale (no idempotency) | **to verify in `test_repeats.py`** |

Rerun each one yourself before logging it. Issue labels: `severity:critical/major/minor`, `priority:P1/P2/P3`, `status:*`, plus a triage decision in the body.

## 6. Lead documents

- **Test plan** (`docs/test-plan.md`): scope (the 2 workflows), approach (risk-based; technique per risk), roles (the 3 areas), environment (Windows, Python 3.12, SQLite, DEBUG), test data (seed_demo + synthetic), schedule, entry/exit/suspension/resumption criteria, risks. Member 3 owns the exit criteria and the risk register, so link to them.
- **Three-point estimates:** E = (O + 4M + P) / 6 per area, then actual hours on Sunday.
- **Traceability** (`docs/traceability.md`): FR/BR ID → unit test (M1) → API test (me) → E2E test (M3) → result → defect ID. Requirements coverage % = covered / total. Ask M1 and M3 for their test names.
- **Defects + RCA + Pareto:** all members log Issues; I run triage. RCA (5 Whys + fishbone) on 2 major defects (likely N2 and N4). Pareto chart by category.

## 7. Draft scope (only if `docs/scope.md` is still empty; agree it with Member 1)

- FR1 Cashier completes a sale; stock decreases by each line's quantity · FR2 the server computes totals, tax, change and points · FR3 a sale is rejected if any line exceeds stock, and nothing is saved · FR4 payment below the total is rejected · FR5 loyalty points earned/redeemed within limits
- FR6 Manager voids a sale; stock and points are restored · FR7 voiding an already voided sale is rejected · FR8 a cashier cannot void (403)
- BR1 (boundaries) q 1..100000, 1..200 lines, tax 0..100 · BR2 (decision) stock ≥ q AND paid ≥ total AND redemption valid · BR3 (state) Completed → Voided only, no second void · BR4 (access) active member AND role level ≥ required
- Roles: Operative (cashier) and Executive (manager)

## Viva prep
Rerun one generated BVA case (e.g. quantity 100001) and explain where it came from in the spec, why it's invalid, what's asserted and why stock is read back.
Be ready for a live "here's an updated spec": regenerate and predict the changes.
