# UC-M2-2 — Complete a sale, with rejections

| Field | Value |
| --- | --- |
| Owner | Member 2 (Rehan) |
| Primary actor | Cashier (Operative role) |
| Secondary actors | Customer (pays, earns or redeems loyalty points) |
| Linked requirements | FR1, FR2, FR3, FR4, FR5, BR1, BR2, BR4 |
| Shared record | `Item.quantity` (stock), `Customer.loyalty_points` |
| Automation | Not automated yet. Planned: Playwright (`tests/team/e2e`), including a rejected value and keyboard navigation; API side in `tests/team/api/test_sale_rules.py` and `test_sale_generated.py` |

## Preconditions

1. The cashier is logged in with an active profile (Operative role or higher).
2. The customer exists, and the items exist with stock above 0.
3. Loyalty is enabled with the default settings (1 point per 100.00, 1 point = 1.00, minimum redemption 0).

## Trigger

A customer brings items to the till to pay.

## Main success flow

1. The cashier opens **New sale** (`/transactions/new-sale/`).
2. The cashier selects the customer. The system shows their points balance.
3. The cashier searches for items and adds them with quantities (1–100000 per line, at most 200 lines).
4. The cashier enters the tax percentage (0–100) and the amount paid.
5. The cashier completes the sale.
6. The system, in one transaction:
   - checks stock for every line;
   - prices the lines from the database and computes subtotal, tax, grand total, change and points earned;
   - saves the sale, reduces stock by each line's quantity and adds the earned points.
7. The system shows "Sale IMS… completed." with the grand total and change, and offers the receipt.

## Alternative flows

- **A1. Customer redeems points (FR5).** At step 4, the cashier enters points to redeem. The number must be no more than the customer's balance and no more than the bill. The system applies the discount before tax, deducts the points, and continues at step 6.
- **A2. Same item added twice.** At step 3, the cashier adds the same item on two lines. The system merges them into one quantity before the stock check. The sale continues if the total is within stock.
- **A3. Exact payment.** At step 4, the amount paid equals the grand total. The sale completes with change 0.00.

## Exception flows

- **E1. Not enough stock (FR3, BR2).** At step 6, a line's merged quantity is greater than the stock (for example stock 4, quantity 5). The system rejects the sale with "Not enough stock for <item>: N available." Nothing is saved and stock is unchanged. The cashier returns to step 3.
- **E2. Amount paid below the total (FR4, BR2).** At step 6, the amount paid is less than the grand total, even by 0.01. The system rejects the sale with "Amount paid (…) is less than the total (…)". Nothing is saved. The cashier returns to step 4.
- **E3. Value outside its limits (BR1).** At step 3 or 4, the cashier enters:
  - a quantity below 1 or above 100000;
  - more than 200 lines;
  - tax below 0 or above 100;
  - a negative amount;
  - a non-number.

  The system rejects the sale (400) with a field message and nothing is saved. The cashier returns to step 3 or 4. Open defects in this flow: N1 (wrong message above 100000), N5 (`false` accepted as 0) and N6 (a very large item id gives 500).
- **E4. Invalid redemption (FR5).** At step 6, the points are more than the balance or more than the bill, or loyalty is disabled. The system rejects the sale with the matching message. Nothing is saved, and points and stock are unchanged.
- **E5. Session expired or not logged in (BR4).** At step 5, the user is not logged in. The system redirects to the login page (302) and no sale is saved.
- **E6. Repeated submission.** At step 5, the request is sent twice (double click or retry). Required by A3: one sale is recorded. Actual: two sales are recorded and stock is reduced twice (defect N4, GitHub Issue #4).

## Postconditions

- **Success:** one sale with status **Completed** is saved. Stock of each item is reduced by its quantity. The customer's points change by earned − redeemed. Totals, tax and change are computed by the server.
- **Failure (E1–E5):** no sale is saved, and stock and points are unchanged.
