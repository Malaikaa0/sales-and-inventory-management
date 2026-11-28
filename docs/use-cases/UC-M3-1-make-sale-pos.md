# UC-M3-1 — Make a sale at Point of Sale (POS)

| Field | Value |
| --- | --- |
| Owner | Member 3 |
| Primary actor | Cashier (`Operative` role) or Manager (`Executive` role) |
| Secondary actors | Customer (pays, redeems/earns loyalty points) |
| Linked requirements | FR1, FR2, FR3, FR4, FR5, BR1, BR2, BR3 |
| Shared records | `Item.quantity` (decreases), `Customer.loyalty_points` (redeemed/earned), `Sale`, `SaleDetail`, `LoyaltyTransaction` |
| Automation | Automated in Playwright: `tests/team/e2e/test_e2e_workflows.py` (including keyboard navigation and rejected-value verification) |

## Preconditions

1. The user is authenticated with an active profile of role `Operative` or higher (`cashier` or `manager`).
2. At least one customer exists in the system.
3. At least one product exists with stock quantity > 0.

## Trigger

A customer brings one or more products to the point-of-sale counter for purchase.

## Main success flow

1. The cashier navigates to **New sale** (`/transactions/new-sale/`).
2. Using the keyboard (`/` shortcut or Tab navigation), the cashier focuses the **Find a product** search box, types a product name, and selects an in-stock item.
3. The system adds the item to the **Current sale** cart table with quantity `1` and recalculates Subtotal, Tax, and Total.
4. The cashier adjusts the line quantity (within `1..stock` and `<= 100,000`) if more than one unit is purchased.
5. The cashier selects an existing **Customer** from the customer search dropdown.
6. The cashier enters the **Tax rate (%)** (`0..100`) and clicks **Exact** (or enters **Amount paid** >= Total).
7. The cashier clicks **Complete sale** (`#submit-btn`).
8. The server validates inputs inside an atomic transaction, computes prices, discount, tax, change, and loyalty points from database values, deducts `Item.quantity`, updates `Customer.loyalty_points`, and returns JSON `{status: "success", receipt_number, grand_total, change, points_earned}`.
9. The system displays the **Sale completed** modal (`#done-modal`) showing the receipt number, sale total, and change returned, with links to **Print receipt** and **View sale**.

## Alternative flows

- **A1. Keyboard-only navigation and `/` quick-search shortcut.** At step 2, when focus is outside an input/select/textarea, pressing `/` opens the `#item-search` Select2 box automatically (`pos.js`). The cashier uses arrow keys and `Enter` to add the product, `Tab` to move through quantity, customer, tax, **Exact**, and **Complete sale**, and completes the sale without mouse clicks on the cart controls.
- **A2. Customer redeems loyalty points (`FR4`, `BR2`).** At step 5, when the selected customer has `loyalty_points > 0` and loyalty is enabled, `#loyalty-box` becomes visible. The cashier enters a valid point count (or clicks **Use max**). The system applies the pre-tax discount, updates the taxable amount and grand total, and deducts the redeemed points on completion.
- **A3. Duplicate product selection merges cart line.** At step 2, if the cashier selects an item already present in the cart, the UI increments the existing row's quantity instead of adding a duplicate row (capped at available stock).

## Exception flows

- **E1. Rejected value — insufficient payment (`BR3`).** At step 6, the cashier enters an **Amount paid** less than the grand total (e.g., `1.00` on a larger total) and submits. Client validation shows `#form-error` ("Amount paid must cover the sale total.") and focuses `#paid`; if bypassed via API/DOM, the server rejects with HTTP `400` ("Amount paid (...) is less than the total (...)"). No sale is created and stock/points remain unchanged.
- **E2. Rejected value — invalid boundary / oversell on server (`FR3`, `BR1`).** If a cart quantity exceeds available stock, exceeds `100,000`, or tax is outside `0..100`, the server rejects the `POST /transactions/new-sale/` request with HTTP `400`, displays `#form-error` in the UI, and rolls back the atomic transaction so `Item.quantity` and `Sale` records are untouched.
- **E3. Missing customer or empty cart.** At step 7, if the cashier submits with no customer selected or an empty cart, the system blocks submission, shows an inline alert in `#form-error`, and focuses the missing control.
- **E4. Unauthenticated / inactive user (`BR4`).** An anonymous user or deactivated staff member attempting to open `/transactions/new-sale/` is redirected (`302`) to `/accounts/login/` and cannot create a sale.

## Postconditions

- **Success:** A `Sale` (`Completed`) and matching `SaleDetail` rows exist; `Item.quantity` decreases by sold quantities; `Customer.loyalty_points` reflects `earned - redeemed` with matching `LoyaltyTransaction` audit entries.
- **Failure (E1–E4):** No `Sale` is saved; stock and loyalty points remain unchanged.
