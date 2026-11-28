# Scope

**Status: draft.** Written from the source code and README. The team has not yet agreed it, and it is not recorded here as registered in the shared sheet.

## System under test

| | |
| --- | --- |
| System | Django Sales and Inventory Management System |
| Upstream | https://github.com/munuhee/sales-and-inventory-management |
| Team repository | https://github.com/Malaikaa0/sales-and-inventory-management |
| Licence | MIT |
| Baseline tag | `baseline-v0` |
| Baseline commit | `0733e7216e88168fe235cd29e3a37840be2ad3fe` |

Install, seed and reset commands are in the [README](../README.md#setup-seed-and-reset).

## Module and workflows

Module: sales (`transactions`).

| Workflow | Starting condition | User action | Expected outcome |
| --- | --- | --- | --- |
| W1 Make a sale | A signed-in Operative or higher, an existing customer, an item in stock | Choose the customer and items, enter tax, amount paid and optional points, submit | A Completed sale is saved, stock goes down, loyalty points change |
| W2 Void a sale | A signed-in Executive or higher, a Completed sale | Open the sale, enter a reason, confirm | The sale becomes Voided, stock and points are reversed |

## Shared records

| Record | W1 make sale | W2 void sale |
| --- | --- | --- |
| `Sale`, `SaleDetail` | Creates | Reads the lines, changes the status |
| `Item.quantity` | Reads and decreases | Increases |
| `Customer.loyalty_points` | Reads and changes | Reads and changes |
| `LoyaltyTransaction` | Adds earn and redeem rows | Adds a reversal row |

W1 creates the sale and its lines, and W2 uses them.

## Functional requirements

| ID | Workflow | Requirement |
| --- | --- | --- |
| FR1 | W1 | The server works out prices, totals, tax and change from its own data. |
| FR2 | W1 | A completed sale reduces the stock of each item by the quantity sold. |
| FR3 | W1 | A sale for more than the available stock is rejected and nothing is saved. |
| FR4 | W1 | A customer can redeem loyalty points as a discount before tax. |
| FR5 | W1 | A sale earns loyalty points on the amount after discount and before tax. |
| FR6 | W2 | Voiding a sale returns its items to stock. |
| FR7 | W2 | Voiding a sale reverses its loyalty points, without taking the balance below zero. |
| FR8 | W2 | A voided sale is kept, with the time, user and reason. |
| FR9 | W2 | A sale cannot be voided twice. |
| FR10 | W2 | Only an Executive or Admin can void a sale. |

## Business rules

| ID | Type | Rule |
| --- | --- | --- |
| BR1 | Boundary | A sale has 1 to 200 lines. Each line quantity is 1 to 100,000. The quantity of an item cannot exceed its stock. |
| BR2 | Decision | A redemption of R > 0 points is accepted only if loyalty is enabled, R is at least the minimum, R is within the balance and R is within the redeemable maximum. |
| BR3 | Boundary | Tax is 0 to 100 percent. The amount paid is not negative and is at least the grand total. |
| BR4 | State change | A sale goes from Completed to Voided only once. The request needs an Executive or Admin and a reason of 1 to 200 characters. |

Decision tables are in [mcc-mcdc.md](mcc-mcdc.md).

## User roles

| Role | Make a sale | Void a sale |
| --- | --- | --- |
| Operative | Allowed | Denied |
| Executive | Allowed | Allowed |

## Test basis

- [README](../README.md): features, roles and loyalty points.
- Source: `transactions/services.py`, `transactions/loyalty.py`, `transactions/views.py`, `accounts/permissions.py`.

Assumptions, to be confirmed by the team:

1. The limits of 200 lines and 100,000 units come from the code, not from user documentation.
2. The quantity limit is meant per submitted line. See candidate defect D2 in the [test plan](test-plan.md).
3. The role and reason checks of BR4 are enforced by the void view. The `void_sale` service does not check them itself.

## Open point

A sale has only two states, Completed and Voided. Voiding a voided sale is the disallowed change from Voided. The team still has to choose the disallowed change to test from Completed.
