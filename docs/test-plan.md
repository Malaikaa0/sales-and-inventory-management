# Test plan

**Status: incomplete.** Only unit coverage and candidate defects are recorded so far. Scope is in [scope.md](scope.md).

Still to write: approach by risk level, roles, environment, test data, schedule, entry, exit, suspension and resumption criteria, risks and estimates.

## Unit coverage

Settings are in [.coveragerc](../.coveragerc). The reason for the scope is in [scope.md](scope.md#unit-coverage-scope).

```powershell
$env:DEBUG="True"
coverage run -m pytest tests/team/unit -q
coverage report                              # in scope
coverage report --omit="*/migrations/*"      # whole project
```

Measured on 2026-11-28 with 147 tests passing:

| | In scope | Whole project |
| --- | --- | --- |
| Statements | 929 of 929 (100%) | 1554 of 2080 (74.7%) |
| Branches | 117 of 118 (99.2%) | 138 of 304 (45.4%) |
| Combined, as `coverage.py` reports it | 99.9% | 71.0% |

Whole project means `accounts`, `bills`, `invoice`, `store`, `transactions` and `InventoryMS`, without migrations and upstream tests. It includes files that no test imports.

### Uncovered code in scope

| File and branch | Justification |
| --- | --- |
| `transactions/forms.py` 14->exit | `BootstrapMixin` skips item setup only for a form without an `item` field, and its only subclass, `PurchaseForm`, has one. |

## Candidate defects

Found by reading the code and confirmed by running it. No test failed. They are not yet logged as GitHub Issues, and severity and triage are not decided. The expected results are our reading of reasonable behaviour.

| ID | Input | Expected | Actual |
| --- | --- | --- | --- |
| D1 | A cart line with quantity 100001 | A message that states the maximum of 100,000 | "Quantities must be at least 1." |
| D2 | Two lines for the same item, 100000 each, stock 300000 | Rejected, if the limit applies per item | Accepted: 200000 units sold |
| D3 | Sales list search `0712345678`, the phone of a customer with one sale (also `345`) | That customer's sale | No sales. A search of only digits is treated as a receipt number |
| D4 | A cart line with quantity `2.0` | Accepted as 2, since the code allows whole floats | Rejected: "Quantity must be a whole number." |

D4 is currently asserted as present behaviour by `test_whole_number_float_is_rejected_current_behaviour`. If it is accepted as a defect and fixed, that test must change.
