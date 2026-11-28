# API coverage — Sale and Void sale

Member 2. Measured on 28 Nov 2026 against `openapi/openapi.yaml` (spec version 1.0.0) and the tests in `tests/team/api/`. The baseline run has 143 tests, 137 passed and 6 failed with defects N1, N2, N4 and N5 (`reports/api/run-baseline.txt`). Each item was counted from the spec and the test code, not estimated.

Counting rules:

- **Asserted** means a test checks it with `assert`.
- Pages used only as setup, such as `/new-product/`, `/product/{slug}/`, `/accounts/customers/create/` and `/transactions/new-purchase/`, are not in the spec. They are not counted.

## Summary

| Criterion | Before (first measurement) | Now | % now |
| --- | --- | --- | --- |
| Paths | 6 / 6 | 6 / 6 | 100% |
| Operations | 7 / 8 | 8 / 8 | 100% |
| Parameters (path and query) | 4 / 5 | 5 / 5 | 100% |
| Request body fields sent | 12 / 12 | 12 / 12 | 100% |
| Request body fields partitioned (EP/BVA or valid/invalid) | 8 / 12 | 10 / 12 | 83% |
| Parameter values: generated EP/BVA cases run | 111 / 111 | 111 / 111 | 100% |
| Enum values asserted | 2 / 3 | 3 / 3 | 100% |
| Status codes per operation, asserted | 8 / 27 | 24 / 27 | 89% (100% of reachable) |
| Request content types | 3 / 3 | 3 / 3, plus a wrong type rejected | 100% |
| Response content types asserted | 5 / 8 | 8 / 8 | 100% |
| Response properties asserted | 11 / 25 | 25 / 25 | 100% |

The coverage tests are in `tests/team/api/test_api_coverage.py`, 13 tests.

## Status codes per operation

| Operation | Spec codes | Asserted | Test |
| --- | --- | --- | --- |
| POST new-sale | 200, 302, 400, 403, 500 | 200, 302, 400, 500 | generated cases, `test_access_api`, `test_request_level_400`, `test_item_id_beyond_64_bit_gives_500_and_saves_nothing` |
| POST void | 200, 302, 403, 404 | all 4 | `test_void.py`, `test_void_anonymous_redirects_to_login` |
| GET void | 200, 302, 403, 404 | all 4 | `test_void_confirm_page` |
| GET sale detail | 200, 302, 404 | all 3 | `test_sale_detail_status_codes` |
| GET get-items | 200, 302, 403, 405 | 200, 302, 405 | `test_get_items_properties_and_codes` |
| GET get_customers | 200, 302, 403, 405 | 200, 302, 405 | `test_get_customers_properties_and_codes` |
| GET login | 200 | 200 | `test_login_page_and_failed_login` |
| POST login | 200, 302 | 200, 302 | `login()`, `test_login_page_and_failed_login` |
| **Total** | **27** | **24** | |

**Not reachable (3): 403 on new-sale, get-items and get_customers.** These views need the Operative role, the lowest role. `role_level()` gives every logged-in active member level 1 or more (`accounts/permissions.py:65-72`). A user without an active profile is logged out by `ActiveProfileMiddleware` and redirected (302) before the view runs (`accounts/middleware.py:18-26`). So no user exists for whom these views would return 403. They are counted in the total so the gap stays visible.

**500 path.** The only safe trigger found is an item id above 2**63−1. The `pk__in` query overflows SQLite inside the sale's transaction, which is rolled back. The test asserts 500, the `Error` body and unchanged stock. By requirement this should be a 400, which is defect **N6**. A customer id that large is handled correctly with a 400.

## Content types

- **Request:**
  - `application/json` (new-sale) and `application/x-www-form-urlencoded` (void, login): 3 / 3.
  - `text/plain` on new-sale is rejected with 400 "Expected a JSON request.".
- **Response:** all 8 are asserted:
  - JSON from new-sale, get-items and get_customers.
  - HTML from the void POST invalid form, the void GET page, sale detail, and the login GET and POST pages.

## Response properties

| Schema | Asserted |
| --- | --- |
| `SaleSuccess` | 9 / 9: exact key set, values of `status`, `message`, `receipt_number`, `grand_total`, `change`, `points_earned`, `redirect`, `receipt_url`, `sale_id` |
| `Error` | 2 / 2: exact body for each request-level 400 and the 500 |
| `ItemSearchResult` | 8 / 8: exact object for a fresh item, including `quantity: 1` |
| `CustomerSearchResult` | 6 / 6: exact object for a fresh customer |

## Remaining gaps

1. Two body fields are only sent valid: `csrfmiddlewaretoken` on void and on login. CSRF rejection is a security check for Member 3.
2. 403 on new-sale, get-items and get_customers is unreachable (see above).

## Endpoint weaknesses

| # | Weakness | Root cause | Severity | Fix |
| --- | --- | --- | --- | --- |
| N1 | Quantity above 100000 gets the "at least 1" message | Two bounds share one condition and one message (`services.py:61-62`) | Minor | Separate check and message for the upper bound |
| N2 | Purchase quantity has no upper limit; 2,147,483,648 accepted | `Purchase.quantity` has only `MinValueValidator(1)`. The 32-bit column limit on PostgreSQL was not considered | Major | `MaxValueValidator(100000)` on the model and form |
| N3 | Purchase form failure returns 200 | Standard Django `CreateView` re-renders the invalid form | Minor | Return 400 from `form_invalid` (or a JSON API) if API clients must use it |
| N4 | The same sale sent twice is recorded twice | No idempotency key or duplicate check; every POST creates a sale | Major | Idempotency key per checkout, with a unique constraint on `Sale` |
| N5 | `false` accepted as 0 for tax, amount paid and points | `value or 0` treats every falsy value as missing (`services.py:74,77,80`) | Minor | Default only `None`/`""`; reject `bool` before conversion |
| N6 | Item id above 2**63−1 gives 500 | `_int` has no upper bound; `pk__in` overflows SQLite and the catch-all handler returns 500 | Minor | Bound ids in `_int`/`parse_lines` and return the normal 400 |
| W1 | Void never returns 4xx: an already-voided sale gives 302 with a flash message, and an invalid form gives 200 | HTML form view: errors are sent as messages or a re-rendered form (`views.py:268-277`) | Minor | Return 409 for an already-voided sale and 400 for an invalid form when the client asks for JSON. Stock is protected either way, so this is accepted for FR9 |
