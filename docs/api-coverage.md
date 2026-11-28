# API coverage — Sale and Void sale

Member 2. Measured on 28 Nov 2026 against `openapi/openapi.yaml` (spec version 1.0.0) and the tests in `tests/team/api/` (baseline run: 130 tests, `reports/api/run-baseline.txt`). Each item was counted from the spec and the test code, not estimated.

Counting rules:

- **Exercised** means a test sends that request or receives that response.
- **Asserted** means a test checks it with `assert`.
- Pages used only as setup, such as `/new-product/`, `/product/{slug}/`, `/accounts/customers/create/` and `/transactions/new-purchase/`, are not in the spec. They are not counted.

## Summary

| Criterion | Achieved / total | % |
| --- | --- | --- |
| Paths | 6 / 6 | 100% |
| Operations | 7 / 8 | 88% |
| Parameters (path and query) | 4 / 5 | 80% |
| Request body fields sent | 12 / 12 | 100% |
| Request body fields partitioned (EP/BVA) | 8 / 12 | 67% |
| Parameter values: generated EP/BVA cases run | 111 / 111 | 100% |
| Enum values asserted | 2 / 3 | 67% |
| Status codes per operation, exercised | 12 / 27 | 44% |
| Status codes per operation, asserted | 8 / 27 | 30% |
| Request content types | 3 / 3 | 100% |
| Response content types parsed | 5 / 8 | 63% |
| Response properties asserted or used | 11 / 25 | 44% |

The two workflow operations, `POST new-sale` and `POST void`, account for most of the status-code total that is covered. `POST void` has all 4 of its codes asserted, and `POST new-sale` has 3 of 5.

## Operations

| Operation | Exercised | By |
| --- | --- | --- |
| `POST /transactions/new-sale/` | Yes | every sale test |
| `POST /transactions/sale/{pk}/void/` | Yes | `test_void.py`, `test_flow.py` |
| `GET /transactions/sale/{pk}/void/` | **No** | the tests take the CSRF token from the new-sale page instead |
| `GET /transactions/sale/{pk}/` | Yes | `sale_status()` |
| `GET /get-items/` | Yes | `create_item()` |
| `GET /accounts/get_customers/` | Yes | `create_customer()`, `points()` |
| `GET /accounts/login/` | Yes | `login()`, `test_access_api.py` |
| `POST /accounts/login/` | Yes | `login()` |

## Parameters and body fields

Parameters: `pk` on void POST ✔, sale detail ✔ and void GET ✘. `term` on get-items ✔ and get_customers ✔.

Body fields:

| Body | Fields sent | Fields partitioned |
| --- | --- | --- |
| new-sale | 7 / 7 | 7 / 7: `customer`, `items`, `items[].id`, `items[].quantity`, `tax_percentage`, `amount_paid`, `redeem_points` |
| void form | 2 / 2 | 1 / 2: `reason` (`csrfmiddlewaretoken` is only sent valid) |
| login form | 3 / 3 | 0 / 3: valid credentials only |

## Status codes per operation

| Operation | Spec codes | Exercised | Asserted |
| --- | --- | --- | --- |
| POST new-sale | 200, 302, 400, 403, 500 | 200, 302, 400 | 200, 302, 400 |
| POST void | 200, 302, 403, 404 | all 4 | all 4 |
| GET void | 200, 302, 403, 404 | – | – |
| GET sale detail | 200, 302, 404 | 200 | – |
| GET get-items | 200, 302, 403, 405 | 200 | – |
| GET get_customers | 200, 302, 403, 405 | 200 | – |
| GET login | 200 | 200 | – |
| POST login | 200, 302 | 302 | 302 |
| **Total** | **27** | **12** | **8** |

## Content types

- **Request:** `application/json` (new-sale) and `application/x-www-form-urlencoded` (void, login): 3 / 3.
- **Response:** 5 of 8 are parsed:
  - JSON from new-sale, get-items and get_customers.
  - HTML from sale detail and the login page.
- **Not parsed:** the void POST 200 page, the void GET page and the login POST 200 page.

## Response properties

| Schema | Asserted or used | Not covered |
| --- | --- | --- |
| `SaleSuccess` (9) | 4: `status`, `sale_id`, `grand_total`, `change` | `message`, `receipt_number`, `points_earned`, `redirect`, `receipt_url` |
| `Error` (2) | 2: `status`, `message` | – |
| `ItemSearchResult` (8) | 2: `id`, `name` | `text`, `category`, `price`, `stock`, `quantity`, `total_item` |
| `CustomerSearchResult` (6) | 3: `id`, `label`, `loyalty_points` | `text`, `value`, `phone` |

Enum values asserted: `status: success` ✔ and `status: error` ✔. `ItemSearchResult.quantity: 1` ✘.

## Gaps to close next

1. The three request-level 400 classes in the spec are not tested yet: wrong Content-Type, invalid JSON, and a body that is not an object. The `post_sale(raw=..., content_type=...)` helper already supports them.
2. The 403 on new-sale needs a logged-in user below Operative, such as an inactive or pending profile. The 500 response needs a fault injected, so it is out of scope for black-box tests.
3. The supporting GET endpoints need their 302, 403 and 405 responses asserted. That overlaps with Member 3's access checks, so coordinate with them before adding tests.
4. Assert `points_earned`, `receipt_number` and `redirect` in the accepted generated cases.

## Endpoint weaknesses

| # | Weakness | Root cause | Severity | Fix |
| --- | --- | --- | --- | --- |
| N1 | Quantity above 100000 gets the "at least 1" message | Two bounds share one condition and one message (`services.py:61-62`) | Minor | Separate check and message for the upper bound |
| N2 | Purchase quantity has no upper limit; 2,147,483,648 accepted | `Purchase.quantity` has only `MinValueValidator(1)`. The 32-bit column limit on PostgreSQL was not considered | Major | `MaxValueValidator(100000)` on the model and form |
| N3 | Purchase form failure returns 200 | Standard Django `CreateView` re-renders the invalid form | Minor | Return 400 from `form_invalid` (or a JSON API) if API clients must use it |
| N4 | The same sale sent twice is recorded twice | No idempotency key or duplicate check; every POST creates a sale | Major | Idempotency key per checkout, with a unique constraint on `Sale` |
| N5 | `false` accepted as 0 for tax, amount paid and points | `value or 0` treats every falsy value as missing (`services.py:74,77,80`) | Minor | Default only `None`/`""`; reject `bool` before conversion |
| W1 | Void never returns 4xx: an already-voided sale gives 302 with a flash message, and an invalid form gives 200 | HTML form view: errors are sent as messages or a re-rendered form (`views.py:268-277`) | Minor | Return 409 for an already-voided sale and 400 for an invalid form when the client asks for JSON. Stock is protected either way, so this is accepted for FR7 |
