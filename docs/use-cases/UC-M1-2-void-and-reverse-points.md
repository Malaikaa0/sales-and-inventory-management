# UC-M1-2: Void a sale and reverse its loyalty points

Owner: Member 1. Workflow W2. Requirements FR6 to FR10. Rule BR4.

| | |
| --- | --- |
| Actor | Manager (Executive) |
| Preconditions | Signed in; a Completed sale for a customer; 1 point earned per Ksh 100 |
| Success postconditions | The sale is Voided with the reason and user; stock is restored; points redeemed are given back and points earned are taken back, never below zero |
| Failure postconditions | The sale, stock and balance are unchanged |

## Main flow

1. The manager opens the sale and presses **Void**.
2. The manager enters a reason and presses **Void sale**.
3. The system shows "Sale ... voided. Stock restored." and the status Voided. The earned points are taken back.

## Alternative flows

- **A1, the sale redeemed points:** the redeemed points are given back and the earned point is taken back.
- **A2, the earned points were already spent:** the balance is lower than the points to take back. The system takes what is left, and the sale is still voided.

## Exception flows

- **E1, blank reason (at step 2):** a reason of only spaces shows "This field is required." The sale stays Completed.
- **E2, cashier not allowed (at step 1):** a cashier sees no **Void** button, and opening the void address gives 403.
- **E3, already voided:** opening the void address again and submitting shows "already been voided". The first reason is kept and nothing changes twice.

## Automation

[test_m1_use_cases.py](../../tests/team/e2e/test_m1_use_cases.py)

| Flow | Test |
| --- | --- |
| Main | `test_uc2_main_earned_points_taken_back` |
| A1 | `test_uc2_alternative_redeemed_points_given_back` |
| A2 | `test_uc2_alternative_earned_points_already_spent` |
| E1 | `test_uc2_exception_blank_reason` |
| E2 | `test_uc2_exception_cashier_not_allowed` |
| E3 | `test_uc2_exception_already_voided` |
