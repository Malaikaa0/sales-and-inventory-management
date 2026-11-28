# UC-M1-1: Redeem loyalty points on a sale

Owner: Member 1. Workflow W1. Requirements FR4, FR5, FR2. Rules BR2, BR3.

| | |
| --- | --- |
| Actor | Cashier (Operative) |
| Preconditions | Signed in; loyalty enabled with a minimum of 10 points and 1 point worth Ksh 1; an item in stock priced Ksh 100; a customer with a points balance |
| Success postconditions | A Completed sale records the points redeemed; stock goes down; the balance is reduced by the points redeemed and increased by any earned |
| Failure postconditions | No sale; stock and balance unchanged |

## Main flow

1. The cashier opens **New sale**, adds the item and chooses the customer.
2. The cashier enters 40 points. The total shows Ksh 60.00.
3. The cashier presses **Exact**, then **Complete sale**.
4. The system shows "Sale completed" with total Ksh 60.00.

## Alternative flows

- **A1, use the maximum (at step 2):** the cashier presses **Use max**; all usable points are filled in. The flow continues at step 3.
- **A2, more than the balance (at step 2):** the cashier types 500 with a balance of 30. The total shows Ksh 70.00 and only 30 points are redeemed. The field still shows what was typed and no message says it was reduced.

## Exception flows

- **E1, below the minimum (at step 3):** with 9 points the system shows "Redeem at least 10 points." and saves nothing. The cashier changes it to 10 and the sale completes.
- **E2, amount paid too low (at step 3):** with Ksh 59.99 against Ksh 60.00 the system shows "Amount paid must cover the sale total." and saves nothing.

## Automation

[test_m1_use_cases.py](../../tests/team/e2e/test_m1_use_cases.py)

| Flow | Test |
| --- | --- |
| Main | `test_uc1_main_redeem_part_of_balance` |
| A1 | `test_uc1_alternative_use_max` |
| A2 | `test_uc1_alternative_more_than_balance_is_reduced` |
| E1 | `test_uc1_exception_below_minimum_then_corrected` |
| E2 | `test_uc1_exception_amount_paid_too_low` |
