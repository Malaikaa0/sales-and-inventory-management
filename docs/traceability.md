# Traceability matrix — Sale and Void sale

Lead: Member 2. Requirement and rule IDs are those of [scope.md](scope.md) (Member 1), the group authority: FR1–FR10 and BR1–BR4. Member 2's earlier draft IDs are mapped below.

Results come from these runs on 28 Nov 2026. No tests were rerun for the re-mapping.

- **API:** `reports/api/run-baseline.txt`, 143 tests: 137 passed, 6 failed.
- **Unit:** `python -m pytest tests/team/unit`: 162 passed (100% in-scope statement and branch coverage, Member 1).
- **E2E and security (M3):** `reports/e2e/e2e-run.txt`, 2 Playwright tests passed. `tests/team/security`: 35 RBAC and hardening tests passed.
- **E2E (M2 + M3 rerun):** `reports/e2e/run-m2.txt`, 20 Playwright tests on a fresh server: 18 passed, 2 failed (M2's `test_uc_m2_2_exc3_tax_out_of_range_rejected` and `test_uc_m2_2_exc5_session_expired`). Both M3 tests passed again.

E2E test names: `m3::` is `tests/team/e2e/test_e2e_workflows.py` (Member 3), and `m2::` is `tests/team/e2e/test_e2e_m2_use_cases.py` (Member 2, one test per use-case flow).

## ID mapping: draft → scope.md

| Draft ID (member-2.md §7) | Draft meaning | scope.md ID(s) |
| --- | --- | --- |
| FR1 | Cashier completes a sale; stock decreases | FR2 |
| FR2 | Server computes totals, tax, change and points | FR1, FR5 |
| FR3 | Sale rejected if a line exceeds stock; nothing saved | FR3 |
| FR4 | Payment below the total rejected | BR3 |
| FR5 | Loyalty points earned and redeemed within limits | FR4, FR5, BR2 |
| FR6 | Manager voids; stock and points restored | FR6, FR7 |
| FR7 | Voiding an already voided sale rejected | FR9 (and BR4) |
| FR8 | A cashier cannot void | FR10 (and BR4) |
| BR1 | Boundaries: quantity, lines, tax, types | BR1 (lines, quantity, stock), BR3 (tax, amount paid) |
| BR2 | Decision: stock AND payment AND redemption | BR2 (redemption); stock is in BR1, payment in BR3 |
| BR3 | State: Completed → Voided only | BR4 |
| BR4 | Access: active member and role level | FR10 and BR4 (void); scope §User roles (sale) |
| – | (not in the draft) | FR8: a voided sale is kept, with time, user and reason |

Re-mapped on 28 Nov 2026:

- `openapi/openapi.yaml` `x-rule` tags, and `tools/generator/out/cases.json` regenerated. The 111 case IDs are unchanged; only the `rule` field differs.
- The use cases UC-M2-1 and UC-M2-2, `docs/test-plan.md`, `docs/defects/N*.md`, `docs/api-coverage.md`, and the test docstrings.

## Requirements → tests → results

| ID | Requirement (scope.md) | Unit tests (M1, `tests/team/unit/`) | API tests (M2, `tests/team/api/`) | E2E (M3 and M2, `tests/team/e2e/`) | Result | Defect |
| --- | --- | --- | --- | --- | --- | --- |
| FR1 | The server works out prices, totals, tax and change from its own data | `test_services::test_sale_reduces_stock_and_totals`, `test_services::test_tax_limits` | `test_sale_rules::test_exact_payment_gives_zero_change`, `test_api_coverage::test_sale_success_has_every_property`, generated `SALE-tax_percentage-*` (accepted) | `m3::test_e2e_make_sale_keyboard_and_rejected_values`, `m2::test_uc_m2_2_main_complete_sale`, `m2::test_uc_m2_2_alt3_exact_payment_change_zero` | Pass | – |
| FR2 | A completed sale reduces the stock of each item by the quantity sold | `test_services::test_sale_reduces_stock_and_totals`, `test_views::test_sale_success_updates_stock` | `test_sale_generated` (accepted cases, stock read back), `test_flow::test_sell_reject_void_flow`, `test_repeats::test_same_sale_posted_twice_records_one_sale` | `m3::test_e2e_make_sale_keyboard_and_rejected_values`, `m2::test_uc_m2_2_main_complete_sale`, `m2::test_uc_m2_2_alt2_same_item_added_twice_is_merged`, `m2::test_uc_m2_2_exc6_double_click_records_one_sale` | **Fail** (API repeat) / E2E Pass | [N4](https://github.com/Malaikaa0/sales-and-inventory-management/issues/4) |
| FR3 | A sale for more than the available stock is rejected and nothing is saved | `test_services::test_stock_boundary`, `test_services::test_unknown_customer_and_item`, `test_views::test_sale_oversell_rejected_and_stock_unchanged` | `test_sale_rules::test_oversell_boundary_*` (2), `test_sale_rules::test_merged_duplicate_lines_exceeding_stock_rejected`, `test_flow`, generated `*-not-found-*`, `test_api_coverage::test_item_id_beyond_64_bit_gives_500_and_saves_nothing` | `m2::test_uc_m2_2_exc1_not_enough_stock` | Pass, defect open | [N6](https://github.com/Malaikaa0/sales-and-inventory-management/issues/6) |
| FR4 | A customer can redeem loyalty points as a discount before tax | `test_services::test_redeem_conditions`, `test_models::test_value_of_points`, `test_mcc_loyalty::test_redemption_mcc` | `test_sale_rules::test_redeem_equal_to_balance_accepted`, `test_sale_rules::test_redeem_equal_to_bill_accepted` | `m2::test_uc_m2_2_alt1_redeem_points` | Pass | – |
| FR5 | A sale earns loyalty points on the amount after discount and before tax | `test_models::test_points_for_amount`, `test_models::test_apply_points` | `test_api_coverage::test_sale_success_has_every_property` (`points_earned`), `test_void::test_void_restores_stock_and_points` | `m2::test_uc_m2_2_alt1_redeem_points` (0 earned below 100) | Pass | – |
| FR6 | Voiding a sale returns its items to stock | `test_services::test_void_restores_stock_and_cannot_repeat`, `test_views::test_void_flow` | `test_void::test_void_restores_stock_and_points`, generated `VOID-*` (voided), `test_flow` | `m3::test_e2e_void_sale_permissions_rejection_and_recovery`, `m2::test_uc_m2_1_main_void_sale` | Pass | – |
| FR7 | Voiding reverses loyalty points, without taking the balance below zero | `test_services::test_void_when_earned_points_already_spent`, `test_void_rules::test_void_gives_back_redeemed_points` | `test_void::test_void_restores_stock_and_points` | `m2::test_uc_m2_1_alt1_earned_points_already_spent`, `m2::test_uc_m2_1_alt2_void_sale_with_redemption` | Pass | – |
| FR8 | A voided sale is kept, with the time, user and reason | `test_views::test_void_flow` | `test_void` (sale still readable, status `Voided`; time, user and reason not asserted) | `m2::test_uc_m2_1_main_void_sale`, `m2::test_uc_m2_1_exc1_already_voided` (status `Voided`) | Pass (time/user/reason asserted only at unit level) | – |
| FR9 | A sale cannot be voided twice | `test_services::test_void_restores_stock_and_cannot_repeat` | `test_void::test_second_void_rejected_and_stock_not_added_twice`, generated `VOID-reason-EP-already-voided` | `m2::test_uc_m2_1_exc1_already_voided` | Pass (W1: 302 + message, not 4xx) | – |
| FR10 | Only an Executive or Admin can void a sale | `test_views::test_void_forbidden_for_cashier`, `test_permissions::test_role_mixins`, `test_permissions::test_has_role_matrix` | `test_void::test_cashier_cannot_void`, `test_api_coverage::test_void_confirm_page`, `test_api_coverage::test_void_anonymous_redirects_to_login` | `m3::test_e2e_void_sale_permissions_rejection_and_recovery`, `m2::test_uc_m2_1_exc2_not_a_manager`; security `test_access_matrix` | Pass | – |
| BR1 | Boundary: 1–200 lines, quantity 1–100,000, quantity ≤ stock | `test_parse_lines::test_quantity_outside_limits_rejected`, `test_quantity_inside_limits_accepted`, `test_200_lines_ok_201_rejected`, `test_services::test_stock_boundary` | `test_sale_generated` (`items`, `items[].quantity`, `items[].id` cases), `test_sale_rules::test_oversell_boundary_*` | `m3::test_e2e_make_sale_keyboard_and_rejected_values` (quantity 100001), `m2::test_uc_m2_2_exc1_not_enough_stock` | **Fail** | [N1](https://github.com/Malaikaa0/sales-and-inventory-management/issues/1) |
| BR2 | Decision: redemption accepted only if enabled AND ≥ minimum AND ≤ balance AND ≤ redeemable maximum | `test_mcc_loyalty::test_redemption_mcc` (MCC/MC-DC), `test_services::test_redeem_*` (4), `test_models::test_max_redeemable` | `test_sale_rules::test_redeem_*` (4), generated `SALE-redeem_points-*` | `m2::test_uc_m2_2_alt1_redeem_points`, `m2::test_uc_m2_2_exc4_points_spent_elsewhere_rejected` | **Fail** | [N5](https://github.com/Malaikaa0/sales-and-inventory-management/issues/5) |
| BR3 | Boundary: tax 0–100%; amount paid ≥ 0 and ≥ grand total | `test_services::test_tax_limits`, `test_services::test_amount_paid_limit` | generated `SALE-tax_percentage-*`, `SALE-amount_paid-*` (incl. total−0.01/total/total+0.01), `test_sale_rules::test_underpay_by_one_cent_rejected` | `m3::test_e2e_make_sale_keyboard_and_rejected_values`, `m2::test_uc_m2_2_exc2_amount_paid_below_total`, `m2::test_uc_m2_2_exc3_tax_out_of_range_rejected` (**fails**) | **Fail** (API and E2E) | [N5](https://github.com/Malaikaa0/sales-and-inventory-management/issues/5), [N7](https://github.com/Malaikaa0/sales-and-inventory-management/issues/8) |
| BR4 | State change: Completed → Voided only once; needs an Executive or Admin and a reason of 1–200 characters | `test_services::test_void_restores_stock_and_cannot_repeat`, `test_void_rules::test_void_reason_length_limit`, `test_views::test_void_requires_reason` | generated `VOID-reason-*` (length BVA, EP), `test_void::test_second_void_rejected_and_stock_not_added_twice`, `test_void::test_cashier_cannot_void` | `m3::test_e2e_void_sale_permissions_rejection_and_recovery`, `m2::test_uc_m2_1_exc1_already_voided`, `m2::test_uc_m2_1_exc2_not_a_manager`, `m2::test_uc_m2_1_exc3_reason_blank_or_too_long` | Pass | – |

### Roles (scope.md §User roles)

| Role check | Unit | API | E2E | Result | Defect |
| --- | --- | --- | --- | --- | --- |
| Operative and Executive may make a sale; anonymous may not | `test_views::test_sale_requires_login`, `test_permissions::test_role_required_decorator` | `test_access_api::test_anonymous_new_sale_redirects_to_login_and_saves_nothing` | `m2::test_uc_m2_2_exc5_session_expired` (**fails**: no sale saved, but the cashier sees "Unexpected server response.") | **Fail** (E2E) | [N8](https://github.com/Malaikaa0/sales-and-inventory-management/issues/9) |

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
| Requirements and rules (FR1–FR10, BR1–BR4) | 14 |
| Covered by at least one test | 14 / 14 = **100%** |
| Covered by unit, API and E2E tests | 14 / 14 = 100% |
| Passing with no open defect | 9 / 14 = **64%** (FR2, BR1, BR2 and BR3 fail; FR3 passes with [N6](https://github.com/Malaikaa0/sales-and-inventory-management/issues/6) open) |
| Roles check (not counted in the 14) | Fails E2E (N8) |
