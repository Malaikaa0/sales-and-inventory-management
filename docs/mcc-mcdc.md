# MCC, MC/DC and decision tables

## Critical decision: loyalty redemption (BR2)

Code: `create_sale` in [services.py](../transactions/services.py). It applies when the points to redeem, R, are greater than 0. The code checks the conditions one after another and stops at the first failure.

| Condition | Meaning |
| --- | --- |
| C1 | Loyalty is enabled |
| C2 | R >= `min_redeem` |
| C3 | R <= customer balance |
| C4 | R <= `max_redeemable(balance, sub_total)` |

`max_redeemable` is 0 when loyalty is disabled or the point value is not positive. Otherwise it is the smaller of the balance and the bill expressed in points.

### MCC table

Four conditions give 16 combinations. C4 true forces C1 true and C3 true, so 6 combinations are impossible and 10 remain. Each row is a case in [test_mcc_loyalty.py](../tests/team/unit/test_mcc_loyalty.py), with R = 50 and point value 1.00.

| Row | C1 | C2 | C3 | C4 | Enabled | Min | Balance | Bill | Expected result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R1 | T | T | T | T | Yes | 10 | 100 | 100 | Accepted |
| R2 | T | F | T | T | Yes | 60 | 100 | 100 | Rejected: below minimum |
| R3 | T | T | T | F | Yes | 10 | 100 | 20 | Rejected: exceeds the bill |
| R4 | T | T | F | F | Yes | 10 | 30 | 100 | Rejected: not enough points |
| R5 | T | F | T | F | Yes | 60 | 100 | 20 | Rejected: below minimum |
| R6 | T | F | F | F | Yes | 60 | 30 | 100 | Rejected: below minimum |
| R7 | F | T | T | F | No | 10 | 100 | 100 | Rejected: not enabled |
| R8 | F | T | F | F | No | 10 | 30 | 100 | Rejected: not enabled |
| R9 | F | F | T | F | No | 60 | 100 | 100 | Rejected: not enabled |
| R10 | F | F | F | F | No | 60 | 30 | 100 | Rejected: not enabled |

Impossible: TTFT, TFFT, FTTT, FTFT, FFTT, FFFT.

### MC/DC pairs

The outcome is "accepted" only when all four conditions are true.

| Condition | Pair | What changes | Outcome |
| --- | --- | --- | --- |
| C2 | R1 (TTTT) and R2 (TFTT) | Only C2 | Accepted to rejected |
| C4 | R1 (TTTT) and R3 (TTTF) | Only C4 | Accepted to rejected |
| C1 | None | | |
| C3 | None | | |

### Why C1 and C3 cannot be varied independently

An independence pair starts from the only accepting row, TTTT, and changes one condition.

- **C1:** the pair would need FTTT. When loyalty is disabled, `max_redeemable` returns 0, so R <= 0 is false and C4 becomes false too.
- **C3:** the pair would need TTFT. `max_redeemable` is never more than the balance, so R above the balance is also above the maximum and C4 becomes false too.

C4 depends on both, so unique-cause MC/DC is not achievable for C1 and C3. Their checks still show in the behaviour: R7 reports "not enabled" and R4 reports "only has", while R3 reports "cannot exceed the bill".

## Decision tables

"-" means the value does not matter. Test names are in `tests/team/unit/`.

### DT1: line quantity (BR1)

| Quantity >= 1 | Quantity <= 100,000 | Quantity <= stock | Result | Tests |
| --- | --- | --- | --- | --- |
| F | T | - | Rejected | `test_quantity_outside_limits_rejected` |
| T | F | - | Rejected | `test_quantity_outside_limits_rejected` |
| T | T | F | Rejected, not enough stock | `test_stock_boundary` |
| T | T | T | Accepted | `test_stock_boundary`, `test_quantity_inside_limits_accepted` |

### DT2: loyalty redemption (BR2)

| R > 0 | C1 | C2 | C3 | C4 | Result | MCC rows |
| --- | --- | --- | --- | --- | --- | --- |
| F (R = 0) | - | - | - | - | Sale without discount | Not part of the decision |
| T | F | - | - | F | Rejected: not enabled | R7 to R10 |
| T | T | F | - | - | Rejected: below minimum | R2, R5, R6 |
| T | T | T | F | F | Rejected: not enough points | R4 |
| T | T | T | T | F | Rejected: exceeds the bill | R3 |
| T | T | T | T | T | Accepted | R1 |

A negative R is rejected before this decision (`test_redeem_negative_rejected`).

### DT3: earning points (supports FR5)

| Enabled | `earn_per` > 0 | Amount > 0 | Points earned | Test |
| --- | --- | --- | --- | --- |
| F | - | - | 0 | `test_points_for_amount` |
| T | F | - | 0 | `test_points_for_amount` |
| T | T | F | 0 | `test_points_for_amount` |
| T | T | T | floor(amount / `earn_per`) | `test_points_for_amount` |

### DT4: tax and payment (BR3)

| 0 <= tax <= 100 | Paid >= 0 | Paid >= total | Result | Tests |
| --- | --- | --- | --- | --- |
| F | - | - | Rejected: tax | `test_tax_limits` |
| T | F | - | Rejected: negative amount | `test_amount_paid_limit` |
| T | T | F | Rejected: less than the total | `test_amount_paid_limit` |
| T | T | T | Accepted | `test_tax_limits`, `test_amount_paid_limit` |

### DT5: void request (BR4)

| Executive or Admin | Reason 1 to 200 characters | Sale is Completed | Result | Tests |
| --- | --- | --- | --- | --- |
| F | - | - | 403, sale unchanged | `test_void_forbidden_for_cashier` |
| T | F | - | Form shown again, sale unchanged | `test_void_requires_reason`, `test_void_reason_length_limit` |
| T | T | F | Error "already been voided" | `test_void_flow` |
| T | T | T | Voided, stock restored | `test_void_flow`, `test_void_reason_length_limit` |

### DT6: points reversal on void (BR4, FR7)

`net` is points redeemed minus points earned on the sale.

| `net` < 0 | Balance < -`net` | Balance change | Test |
| --- | --- | --- | --- |
| T | T | The whole remaining balance is removed | `test_void_when_earned_points_already_spent` |
| T | F | `net` is applied | `test_void_restores_stock_and_cannot_repeat` |
| F | - | `net` is applied (nothing if it is 0) | `test_void_gives_back_redeemed_points` |
