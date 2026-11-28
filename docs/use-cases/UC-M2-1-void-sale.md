# UC-M2-1 — Void a sale

| Field | Value |
| --- | --- |
| Owner | Member 2 (Rehan) |
| Primary actor | Manager (Executive role) |
| Secondary actors | Cashier (Operative role, attempts in E2); Customer (points are reversed) |
| Linked requirements (scope.md) | FR6, FR7, FR8, FR9, FR10, BR4 |
| Shared record | `Item.quantity` (stock), `Customer.loyalty_points` |
| Automation | Not automated yet. Planned: Playwright (`tests/team/e2e`), plus the existing API tests in `tests/team/api/test_void.py` |

## Preconditions

1. The manager is logged in with an active profile and the Executive role or higher.
2. A sale exists with status **Completed**.
3. The stock of each item on the sale and the customer's points balance are known (read back after the void).

## Trigger

A customer returns all items, or the manager finds that a sale was recorded by mistake.

## Main success flow

1. The manager opens **Sales** and selects the sale (`/transactions/sale/{pk}/`).
2. The system shows the sale with status **Completed** and a **Void** action.
3. The manager chooses **Void**.
4. The system shows the confirmation page with a required **Reason** field (`/transactions/sale/{pk}/void/`).
5. The manager enters a reason (1–200 characters) and confirms.
6. The system, in one transaction:
   - adds each line's quantity back to stock;
   - gives back the redeemed points and takes back the earned points;
   - sets the status to **Voided**, with the time, user and reason.
7. The system returns to the sale page with the message "Sale IMS… voided. Stock restored." The status shows **Voided**.

## Alternative flows

- **A1. Customer has already spent the earned points.** At step 6, the customer's balance is lower than the points earned on this sale. The system takes back only what is left, so the balance becomes 0, and still voids the sale. Stock is restored in full. The flow continues at step 7.
- **A2. Sale used points redemption.** At step 6, the sale redeemed points as well as earning them. The system applies the net reversal (redeemed − earned), so the balance returns to its value before the sale. Example: 10 → 7 after the sale → 10 after the void. The flow continues at step 7.
- **A3. Manager cancels.** At step 4 or 5, the manager leaves the confirmation page without confirming. Nothing changes and the sale stays **Completed**.

## Exception flows

- **E1. Sale already voided (FR9, BR4).** At step 5, the sale is already **Voided**, for example because of a second click or a second manager. The system does not change stock or points. It returns to the sale page (302) with the message "This sale has already been voided." The use case ends. Weakness W1: no 4xx status is returned.
- **E2. User is not a manager (FR10, BR4).** A cashier opens or posts the void URL. The system answers 403 and nothing changes. An anonymous user is sent to the login page (302).
- **E3. Reason missing, blank or too long.** At step 5, the reason is empty, only spaces, or longer than 200 characters. The system shows the form again (200) with the error. Nothing changes and the manager returns to step 5.
- **E4. Sale does not exist.** At step 1 or 4, the sale id is unknown. The system answers 404.

## Postconditions

- **Success:** the sale status is **Voided**. Stock for each line is increased by its quantity. The points are reversed as in step 6 (A1, A2). The sale row is kept for the audit trail.
- **Failure (E1–E4):** stock, points and sale status are unchanged.
