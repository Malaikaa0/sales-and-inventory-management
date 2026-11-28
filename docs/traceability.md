# Traceability matrix — Sale and Void sale

Lead: Member 2. Requirement IDs come from the draft scope in [member-2.md](member-2.md) §7, until `docs/scope.md` (Member 1) is agreed.

Results come from two runs on 28 Nov 2026:

- **API:** `reports/api/run-baseline.txt`, 143 tests: 137 passed, 6 failed.
- **Unit:** `python -m pytest tests/team/unit`: 120 passed, 1 failed.

The failing unit test, `test_views.py::test_sale_bad_requests[-application/json-at least one item]`, gets "Expected a JSON request." for an empty body. It looks like a problem in the test, not the app, and has been reported to Member 1.

E2E tests are Member 3's (Playwright) and are still pending.

## Requirements → tests → results

| ID | Requirement | Unit tests (M1, `tests/team/unit/`) | API tests (M2, `tests/team/api/`) | E2E (M3) | Result | Defect |
| --- | --- | --- | --- | --- | --- | --- |
| FR1 | Cashier completes a sale; stock decreases by each line's quantity | `test_services::test_sale_reduces_stock_and_totals`, `test_views::test_sale_success_updates_stock` | `test_sale_generated` (accepted cases, stock read back), `test_flow::test_sell_reject_void_flow`, `test_repeats::test_same_sale_posted_twice_records_one_sale` | M3 pending | **Fail** | N4 |
| FR2 | Server computes totals, tax, change and points | `test_services::test_sale_reduces_stock_and_totals`, `test_services::test_tax_limits`, `test_models::test_points_for_amount`, `test_models::test_value_of_points` | `test_sale_rules::test_exact_payment_gives_zero_change`, `test_api_coverage::test_sale_success_has_every_property`, `test_sale_rules::test_redeem_equal_to_balance_accepted` | M3 pending | Pass | – |
| FR3 | A sale is rejected if any line exceeds stock (or the item is unknown); nothing saved | `test_services::test_stock_boundary`, `test_services::test_unknown_customer_and_item`, `test_views::test_sale_oversell_rejected_and_stock_unchanged` | `test_sale_rules::test_oversell_boundary_*` (2), `test_sale_rules::test_merged_duplicate_lines_exceeding_stock_rejected`, `test_flow`, generated `*-not-found-*`, `test_api_coverage::test_item_id_beyond_64_bit_gives_500_and_saves_nothing` | M3 pending | Pass, defect open | N6 |
| FR4 | Payment below the total is rejected | `test_services::test_amount_paid_limit` | `test_sale_rules::test_underpay_by_one_cent_rejected`, generated `SALE-amount_paid-BVA-total-d/total/total+d` | M3 pending | Pass | – |
| FR5 | Loyalty points earned and redeemed within limits | `test_services::test_redeem_negative_rejected`, `test_redeem_when_disabled_rejected`, `test_redeem_conditions`, `test_redeem_more_than_bill_rejected`, `test_models::test_max_redeemable`, `test_apply_points` | `test_sale_rules::test_redeem_equal_to_balance_accepted`, `test_redeem_above_balance_rejected`, `test_redeem_equal_to_bill_accepted`, `test_redeem_above_bill_rejected`, generated `SALE-redeem_points-*` | M3 pending | Pass | – |
| FR6 | Manager voids a sale; stock and points are restored | `test_services::test_void_restores_stock_and_cannot_repeat`, `test_services::test_void_when_earned_points_already_spent`, `test_views::test_void_flow` | `test_void::test_void_restores_stock_and_points`, generated `VOID-*` (voided), `test_flow` | M3 pending | Pass | – |
| FR7 | Voiding an already voided sale is rejected | `test_services::test_void_restores_stock_and_cannot_repeat` | `test_void::test_second_void_rejected_and_stock_not_added_twice`, generated `VOID-reason-EP-already-voided` | M3 pending | Pass (W1: 302 + message, not 4xx) | – |
| FR8 | A cashier cannot void (403) | `test_views::test_void_forbidden_for_cashier`, `test_permissions::test_role_mixins` | `test_void::test_cashier_cannot_void`, `test_api_coverage::test_void_confirm_page` | M3 pending | Pass | – |
| BR1 | Boundaries: quantity 1..100000, 1..200 lines, tax 0..100, correct types | `test_parse_lines::test_quantity_outside_limits_rejected`, `test_quantity_inside_limits_accepted`, `test_200_lines_ok_201_rejected`, `test_services::test_tax_limits`, `test_services::test_non_whole_quantity_rejected` | `test_sale_generated` (29 BVA + 67 EP cases), `test_api_coverage::test_request_level_400` | M3 pending | **Fail** | N1, N5 |
| BR2 | Decision: stock ≥ q AND paid ≥ total AND redemption valid | `test_services::test_stock_boundary`, `test_amount_paid_limit`, `test_redeem_conditions` (MCC tests) | `test_sale_rules.py` (9 tests), `test_flow` | M3 pending | Pass | – |
| BR3 | State: Completed → Voided only, no second void | `test_services::test_void_restores_stock_and_cannot_repeat` | `test_void::test_second_void_rejected_and_stock_not_added_twice`, generated `VOID-reason-EP-already-voided`, `test_flow` | M3 pending | Pass | – |
| BR4 | Access: active member AND role level ≥ required | `test_permissions::test_has_role_matrix`, `test_role_required_decorator`, `test_non_active_status_blocked`, `test_views::test_sale_requires_login` | `test_access_api::test_anonymous_new_sale_redirects_to_login_and_saves_nothing`, `test_void::test_cashier_cannot_void`, `test_api_coverage` (302/403 checks) | M3 pending | Pass | – |

### Assumptions (agreed) that tests check

| ID | Assumption | Test | Result | Defect |
| --- | --- | --- | --- | --- |
| A1 | Purchase quantity at most 100000 (protects `Item.quantity`) | `test_purchase::test_purchase_above_int32_rejected_N2` | **Fail** | N2 |
| A3 | The same sale sent twice records one sale | `test_repeats::test_same_sale_posted_twice_records_one_sale` | **Fail** | N4 |
| A4 | A quantity above the maximum gets a message naming the limit | generated `SALE-items[].quantity-BVA-max+d` | **Fail** | N1 |
| A5 | Booleans are rejected for number fields | generated `*-EP-wrong-type-bool-false` (3) | **Fail** | N5 |

N3 (a purchase form failure returns 200) is an observed weakness with no requirement attached. It is recorded by `test_purchase::test_purchase_validation_failure_returns_200_N3`.

## Requirements coverage

| Measure | Value |
| --- | --- |
| Requirements (FR1–FR8, BR1–BR4) | 12 |
| Covered by at least one test (unit or API) | 12 / 12 = **100%** |
| Covered by both unit and API tests | 12 / 12 = 100% |
| Covered by E2E | 0 / 12 = 0% (M3 pending) |
| Passing with no open defect | 9 / 12 = **75%** (FR1 and BR1 fail; FR3 passes with N6 open) |
