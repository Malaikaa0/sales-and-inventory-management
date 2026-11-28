# Root cause analysis — N2: purchase quantity has no upper limit

Defect: [N2](N2.md), Major / P2. A purchase of 2,147,483,648 units is accepted and stock becomes 2,147,483,694. On PostgreSQL, the production database, the same request would overflow the 32-bit `quantity` column and fail with a server error.

## 5 Whys

1. **Why did stock become 2,147,483,694?** The purchase form accepted quantity 2,147,483,648 and a successful purchase adds its quantity to `Item.quantity`.
2. **Why was the quantity accepted?** `Purchase.quantity` and `PurchaseForm` only check the lower bound (`MinValueValidator(1)`). Nothing checks the upper bound.
3. **Why is there no upper bound?** The sale side got explicit limits (`MAX_QTY_PER_LINE = 100000` in `services.py`) when it was hardened. The purchase side kept the default Django model field and was not reviewed for limits.
4. **Why was the purchase side not reviewed?** Limits were treated as a sale (cashier) concern. Purchases are entered by trusted managers, so the input was assumed safe. No written requirement gave a maximum for purchases. A1 only came from this project's test analysis.
5. **Why did tests not catch it earlier?** The existing tests checked valid purchases and the lower bound only. They ran on SQLite, which stores the large value without error, so the PostgreSQL overflow could not show up in testing.

**Root cause:** no requirement-level limit for purchase quantity, and validation that relies on the database column instead of a business limit. Development and test used SQLite, which hid the column limit of the production database.

## Fishbone (cause and effect)

```
 People                     Process                    Requirements
   │ trusted-manager           │ limits reviewed only      │ no max purchase
   │ assumption                │ for the sale path         │ quantity stated (A1
   │                           │                           │ added by testing)
   └──────────────┬────────────┴──────────────┬────────────┘
                  │                           │
                  ▼                           ▼
 ───────────────────────────────────────────────────────────►  N2: 2,147,483,648
                  ▲                           ▲                 units accepted;
                  │                           │                 stock corrupted /
   ┌──────────────┴────────────┬──────────────┴────────────┐    overflow on PostgreSQL
   │ only MinValueValidator(1) │ no BVA at the upper end    │ SQLite in dev/test,
   │ on Purchase.quantity      │ of purchase quantity;      │ PostgreSQL (32-bit
   │ (no MaxValueValidator)    │ no DB-parity test          │ integer) in production
 Code                        Tools                      Environment
```

| Category | Cause |
| --- | --- |
| People | Managers are trusted, so their input was not treated as untrusted |
| Process | Input limits were reviewed for the sale workflow only; no checklist item for "every numeric input has a min and a max" |
| Code | `Purchase.quantity` only has `MinValueValidator(1)`; the form widget sets `min` but not `max` |
| Tools | No boundary tests at the upper end; static analysis does not flag a missing maximum |
| Environment | SQLite (unbounded integer storage) in development and test; PostgreSQL `integer` (max 2,147,483,647) in production |
| Requirements | No stated maximum purchase quantity; A1 was added during this project |

## Corrective actions (fix this defect)

1. Add `MaxValueValidator(100000)` to `Purchase.quantity` and `max: 100000` to the form widget, with a clear message (owner: dev; through a fix pull request).
2. Add the upper-bound BVA cases 99999, 100000 and 100001 for purchase quantity to the generator and API tests. `test_purchase_above_int32_rejected_N2` must then pass.
3. Check existing data for stock values above the agreed maximum before deploying the fix.

## Preventive actions (stop it happening again)

1. Make "min and max for every numeric input" part of the requirements template and the code review checklist.
2. Generate boundary cases from the OpenAPI spec for every numeric input, not only for the sale endpoint.
3. Run the API suite once against PostgreSQL in CI (a service container), so database-specific limits fail in testing.
4. Treat input from every role as untrusted in validation, whatever the role's level of trust.
