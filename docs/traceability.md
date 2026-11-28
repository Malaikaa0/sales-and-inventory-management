# Traceability matrix — Sale and Void sale

Lead: Member 2. Requirement IDs come from the draft scope in [member-2.md](member-2.md) §7, until [scope.md](scope.md) (Member 1) is agreed.

Results come from these runs on 28 Nov 2026:

- **API:** `reports/api/run-baseline.txt`, 143 tests: 137 passed, 6 failed.
- **Unit:** `python -m pytest tests/team/unit`: 162 passed (100% in-scope statement and branch coverage).
- **E2E & Security (M3):** `reports/e2e/e2e-run.txt`, 2 Playwright tests passed; `tests/team/security`, 35 RBAC/hardening tests passed.
- **E2E (M2 + M3 rerun):** `reports/e2e/run-m2.txt`, 20 Playwright tests on a fresh server: 18 passed, 2 failed (M2's `test_uc_m2_2_exc3_tax_out_of_range_rejected` and `test_uc_m2_2_exc5_session_expired`). Both M3 tests passed again.

E2E test names: `m3::` = `tests/team/e2e/test_e2e_workflows.py` (Member 3), `m2::` = `tests/team/e2e/test_e2e_m2_use_cases.py` (Member 2, one test per use-case flow).

## Requirements → tests → results

| ID | Requirement | Unit tests (M1, `tests/team/unit/`) | API tests (M2, `tests/team/api/`) | E2E (M3 and M2, `tests/team/e2e/`) | Result | Defect |
| --- | --- | --- | --- | --- | --- | --- |
| FR1 | Cashier completes a sale; stock decreases by each line's quantity | `test_services::test_sale_reduces_stock_and_totals`, `test_views::test_sale_success_updates_stock` | `test_sale_generated` (accepted cases, stock read back), `test_flow::test_sell_reject_void_flow`, `test_repeats::test_same_sale_posted_twice_records_one_sale` | `m3::test_e2e_make_sale_keyboard_and_rejected_values`, `m2::test_uc_m2_2_main_complete_sale`, `m2::test_uc_m2_2_alt2_same_item_added_twice_is_merged`, `m2::test_uc_m2_2_exc6_double_click_records_one_sale` | **Fail** (API repeat) / E2E Pass (UI double click records one sale) | [N4](https://github.com/Malaikaa0/sales-and-inventory-management/issues/4) |
| FR2 | Server computes totals, tax, change and points | `test_services::test_sale_reduces_stock_and_totals`, `test_services::test_tax_limits`, `test_models::test_points_for_amount`, `test_models::test_value_of_points` | `test_sale_rules::test_exact_payment_gives_zero_change`, `test_api_coverage::test_sale_success_has_every_property`, `test_sale_rules::test_redeem_equal_to_balance_accepted` | `m3::test_e2e_make_sale_keyboard_and_rejected_values`, `m2::test_uc_m2_2_main_complete_sale`, `m2::test_uc_m2_2_alt1_redeem_points`, `m2::test_uc_m2_2_alt3_exact_payment_change_zero` | Pass | – |
| FR3 | A sale is rejected if any line exceeds stock (or the item is unknown); nothing saved | `test_services::test_stock_boundary`, `test_unknown_customer_and_item`, `test_views::test_sale_oversell_rejected_and_stock_unchanged` | `test_sale_rules::test_oversell_boundary_*` (2), `test_sale_rules::test_merged_duplicate_lines_exceeding_stock_rejected`, `test_flow`, generated `*-not-found-*`, `test_api_coverage::test_item_id_beyond_64_bit_gives_500_and_saves_nothing` | `m3::test_e2e_make_sale_keyboard_and_rejected_values`, `m2::test_uc_m2_2_exc1_not_enough_stock` | Pass, defect open | [N6](https://github.com/Malaikaa0/sales-and-inventory-management/issues/6) |
| FR4 | Payment below the total is rejected | `test_services::test_amount_paid_limit` | `test_sale_rules::test_underpay_by_one_cent_rejected`, generated `SALE-amount_paid-BVA-total-d/total/total+d` | `m3::test_e2e_make_sale_keyboard_and_rejected_values`, `m2::test_uc_m2_2_exc2_amount_paid_below_total` | Pass | – |
| FR5 | Loyalty points earned and redeemed within limits | `test_services::test_redeem_negative_rejected`, `test_redeem_when_disabled_rejected`, `test_redeem_conditions`, `test_redeem_more_than_bill_rejected`, `test_models::test_max_redeemable`, `test_apply_points` | `test_sale_rules::test_redeem_equal_to_balance_accepted`, `test_redeem_above_balance_rejected`, `test_redeem_equal_to_bill_accepted`, `test_redeem_above_bill_rejected`, generated `SALE-redeem_points-*` | `m3::test_e2e_make_sale_keyboard_and_rejected_values`, `m2::test_uc_m2_2_alt1_redeem_points`, `m2::test_uc_m2_2_exc4_points_spent_elsewhere_rejected` | Pass | – |
| FR6 | Manager voids a sale; stock and points are restored | `test_services::test_void_restores_stock_and_cannot_repeat`, `test_void_when_earned_points_already_spent`, `test_views::test_void_flow` | `test_void::test_void_restores_stock_and_points`, generated `VOID-*` (voided), `test_flow` | `m3::test_e2e_void_sale_permissions_rejection_and_recovery`, `m2::test_uc_m2_1_main_void_sale`, `m2::test_uc_m2_1_alt1_earned_points_already_spent`, `m2::test_uc_m2_1_alt2_void_sale_with_redemption`, `m2::test_uc_m2_1_alt3_manager_cancels` | Pass | – |
| FR7 | Voiding an already voided sale is rejected | `test_services::test_void_restores_stock_and_cannot_repeat` | `test_void::test_second_void_rejected_and_stock_not_added_twice`, generated `VOID-reason-EP-already-voided` | `m3::test_e2e_void_sale_permissions_rejection_and_recovery`, `m2::test_uc_m2_1_exc1_already_voided` | Pass (W1: 302 + message, not 4xx) | – |
| FR8 | A cashier cannot void (403) | `test_views::test_void_forbidden_for_cashier`, `test_permissions::test_role_mixins` | `test_void::test_cashier_cannot_void`, `test_api_coverage::test_void_confirm_page` | `m3::test_e2e_void_sale_permissions_rejection_and_recovery`, `m2::test_uc_m2_1_exc2_not_a_manager` + `test_access_matrix` | Pass | – |
| BR1 | Boundaries: quantity 1..100000, 1..200 lines, tax 0..100, correct types | `test_parse_lines::test_quantity_outside_limits_rejected`, `test_quantity_inside_limits_accepted`, `test_200_lines_ok_201_rejected`, `test_services::test_tax_limits`, `test_services::test_non_whole_quantity_rejected` | `test_sale_generated` (29 BVA + 67 EP cases), `test_api_coverage::test_request_level_400` | `m3::test_e2e_make_sale_keyboard_and_rejected_values`, `m2::test_uc_m2_2_exc3_tax_out_of_range_rejected` (**fails**), `m2::test_uc_m2_1_exc3_reason_blank_or_too_long` | **Fail** (API and E2E) | [N1](https://github.com/Malaikaa0/sales-and-inventory-management/issues/1), [N5](https://github.com/Malaikaa0/sales-and-inventory-management/issues/5), N7 (candidate: till accepts tax 150% and saves at 100%) |
| BR2 | Decision: stock ≥ q AND paid ≥ total AND redemption valid | `test_services::test_stock_boundary`, `test_amount_paid_limit`, `test_redeem_conditions` (MCC tests) | `test_sale_rules.py` (9 tests), `test_flow` | `m3::test_e2e_make_sale_keyboard_and_rejected_values`, `m2::test_uc_m2_2_exc1_not_enough_stock`, `m2::test_uc_m2_2_exc2_amount_paid_below_total`, `m2::test_uc_m2_2_exc4_points_spent_elsewhere_rejected` | Pass | – |
| BR3 | State: Completed → Voided only, no second void | `test_services::test_void_restores_stock_and_cannot_repeat` | `test_void::test_second_void_rejected_and_stock_not_added_twice`, generated `VOID-reason-EP-already-voided`, `test_flow` | `m3::test_e2e_void_sale_permissions_rejection_and_recovery`, `m2::test_uc_m2_1_exc1_already_voided`, `m2::test_uc_m2_1_exc4_sale_does_not_exist` | Pass | – |
| BR4 | Access: active member AND role level ≥ required | `test_permissions::test_has_role_matrix`, `test_role_required_decorator`, `test_non_active_status_blocked`, `test_views::test_sale_requires_login` | `test_access_api::test_anonymous_new_sale_redirects_to_login_and_saves_nothing`, `test_void::test_cashier_cannot_void`, `test_api_coverage` (302/403 checks) | `m3::test_e2e_void_sale_permissions_rejection_and_recovery`, `m2::test_uc_m2_1_exc2_not_a_manager`, `m2::test_uc_m2_2_exc5_session_expired` (**fails**) + `test_access_matrix` (35 tests) | **Fail** (E2E) | N8 (candidate: logged-out till shows "Unexpected server response.", not a sign-in prompt; no sale saved) |

### Assumptions (agreed) that tests check

| ID | Assumption | Test | Result | Defect |
| --- | --- | --- | --- | --- |
| A1 | Purchase quantity at most 100000 (protects `Item.quantity`) | `test_purchase::test_purchase_above_int32_rejected_N2` | **Fail** | [N2](https://github.com/Malaikaa0/sales-and-inventory-management/issues/2) |
| A3 | The same sale sent twice records one sale | `test_repeats::test_same_sale_posted_twice_records_one_sale` | **Fail** | [N4](https://github.com/Malaikaa0/sales-and-inventory-management/issues/4) |
| A4 | A quantity above the maximum gets a message naming the limit | generated `SALE-items[].quantity-BVA-max+d` | **Fail** | [N1](https://github.com/Malaikaa0/sales-and-inventory-management/issues/1) |
| A5 | Booleans are rejected for number fields | generated `*-EP-wrong-type-bool-false` (3) | **Fail** | [N5](https://github.com/Malaikaa0/sales-and-inventory-management/issues/5) |

[N3](https://github.com/Malaikaa0/sales-and-inventory-management/issues/3) (a purchase form failure returns 200) is an observed weakness with no requirement attached. It is recorded by `test_purchase::test_purchase_validation_failure_returns_200_N3`.

## Requirements coverage

| Measure | Value |
| --- | --- |
| Requirements (FR1–FR8, BR1–BR4) | 12 |
| Covered by at least one test (unit or API) | 12 / 12 = **100%** |
| Covered by both unit and API tests | 12 / 12 = 100% |
| Covered by E2E | 12 / 12 = **100%** |
| Passing with no open defect | 8 / 12 = **67%** (FR1, BR1 and BR4 fail; FR3 passes with [N6](https://github.com/Malaikaa0/sales-and-inventory-management/issues/6) open) |
