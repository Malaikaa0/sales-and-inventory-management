# UC-M3-2 — Void a completed sale

| Field | Value |
| --- | --- |
| Owner | Member 3 |
| Primary actor | Manager (`Executive` role) or `Admin` |
| Secondary actors | Cashier (`Operative` role, denied in E1); Customer (loyalty points reversed) |
| Linked requirements | FR6, FR7, FR8, FR9, FR10, BR4 |
| Shared records | `Sale` (status -> `Voided`), `Item.quantity` (increases), `Customer.loyalty_points` & `LoyaltyTransaction` (reversed) |
| Automation | Automated in Playwright: `tests/team/e2e/test_e2e_workflows.py` |

## Preconditions

1. A `Completed` sale exists in the database (`Sale.status == 'C'`).
2. The actor is signed in with an active `Executive` (`manager`) or `Admin` (`admin`) profile.

## Trigger

A customer returns an order or a manager identifies an erroneously recorded sale that must be cancelled with full audit trail.

## Main success flow

1. The manager opens the sale detail page (`/transactions/sale/{pk}/`) from **Sales** or directly after checkout.
2. The page shows status **Completed** and displays the **Void** action button (`a[href$='/void/']`).
3. The manager activates **Void** (mouse or keyboard `Tab` + `Enter`).
4. The system renders the confirmation page (`/transactions/sale/{pk}/void/`) showing the receipt number, total, customer, a required **Reason** field (`#id_reason`), **Void sale**, and **Cancel**.
5. The manager enters a valid void reason (1–200 characters) and activates **Void sale**.
6. Inside one atomic transaction, the server restores `Item.quantity` for every `SaleDetail` line, reverses net loyalty points (clamped so customer points never drop below `0`), marks `Sale.status = 'V'`, records `voided_at`, `voided_by`, and `void_reason`, and redirects (`302`) back to `/transactions/sale/{pk}/`.
7. The sale detail page displays the flash message `"Sale IMS... voided. Stock restored."`, updates the badge to **Voided**, shows the audit banner with timestamp, user, and reason, and hides the **Void** button.

## Alternative flows

- **A1. Manager cancels on confirmation page.** At step 4 or 5, the manager clicks/activates **Cancel** (`a[href$='/sale/{pk}/']`). No database mutation occurs; the sale remains **Completed** and stock/points remain unchanged.
- **A2. Earned loyalty points already spent before void (`FR7`).** At step 6, if the customer's current `loyalty_points` balance is smaller than the points earned on the sale being voided, the reversal is clamped to `-customer.loyalty_points` so the customer balance stops at `0` instead of becoming negative or blocking the void.
- **A3. Keyboard-only void confirmation.** From the sale detail page, the manager navigates to the **Void** button with `Tab`, presses `Enter`, types the reason into `#id_reason`, tabs to **Void sale**, and presses `Enter` to confirm.

## Exception flows

- **E1. Unauthorized role (`FR10`, `BR4`).** An `Operative` (`cashier`) views the sale detail page (the **Void** button is hidden) and if they navigate directly to `/transactions/sale/{pk}/void/` via GET or POST, the server responds with HTTP `403 Forbidden` and leaves the sale, stock, and points untouched.
- **E2. Rejected value — blank or whitespace-only reason (`BR4`).** At step 5, the manager submits an empty or whitespace-only reason (or > 200 characters). `VoidSaleForm` rejects the submission, re-renders `/transactions/sale/{pk}/void/` (HTTP `200`) with a validation error, and keeps the sale **Completed**.
- **E3. Already voided sale (`FR9`, `BR4`).** If a manager submits a second POST to `/transactions/sale/{pk}/void/` for an already-voided sale, `void_sale()` raises `ValidationError("This sale has already been voided.")`, redirects back to `/transactions/sale/{pk}/` with an error banner, and does not restore stock or reverse points a second time.

## Postconditions

- **Success:** `Sale.status` is `Voided` (`V`) with `voided_at`, `voided_by`, and `void_reason` saved; `Item.quantity` is restored; loyalty points are reversed safely (`>= 0`).
- **Failure (E1–E3):** Sale state, stock quantities, and loyalty balance remain unchanged.
