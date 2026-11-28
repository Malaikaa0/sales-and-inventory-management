# Triage of the 6 baseline API test failures

**Proposal for discussion.** Nothing is marked `xfail`, and no test or application file on `area2-Rehan` was changed.

Reproduced on 2026-11-28 at commit `5eebd6a` of `area2-Rehan`, against a freshly migrated and seeded server: **6 failed, 137 passed**, the same failures as `reports/api/run-baseline.txt` on that branch. The application code is identical on `area2-Rehan` and `area1-malaika`.

## Verdict

The six failures come from four defects. In none of them does the test send or read the wrong thing. They differ in how firm the expected result is, because several rest on our own assumptions (A1, A3, A4, A5) and not on the application's documentation.

| # | Failing test | Issue | Verdict | Expected result rests on |
| --- | --- | --- | --- | --- |
| 1 | `test_purchase_above_int32_rejected_N2` | #2 | App defect | A1, and the missing upper bound |
| 2 | `test_same_sale_posted_twice_records_one_sale` | #4 | App defect, expectation to confirm | A3, and the brief's "no duplicates" |
| 3 | `...[SALE-items[].quantity-BVA-max+d]` | #1 | App defect | The message is wrong on any reading |
| 4 | `...[SALE-tax_percentage-EP-wrong-type-bool-false]` | #5 | App defect | A5 |
| 5 | `...[SALE-redeem_points-EP-wrong-type-bool-false]` | #5 | App defect, low impact | A5 |
| 6 | `...[SALE-amount_paid-EP-wrong-type-bool-false]` | #5 | Weakest: rejected anyway, only the message differs | A5 and the message wording |

## Evidence

| # | Observed in our run | Cause in the code |
| --- | --- | --- |
| 1 | 302, then "stock is now 2147483694" | `Purchase.quantity` has only `MinValueValidator(1)` |
| 2 | "duplicate sale recorded: [122, 123]" | `sale_create_view` has no duplicate check. `static/js/pos.js:254` disables the button while submitting, so a double click is guarded in the till; a retried request is not |
| 3 | 400 "Quantities must be at least 1." for 100001 | `transactions/services.py:61-62` uses one message for both bounds |
| 4 | 200, sale saved with `grand_total` 1.00 | `transactions/services.py:74` `tax_percentage or 0` turns `false` into 0 |
| 5 | 200, sale saved | `transactions/services.py:80` `redeem_points or 0` |
| 6 | 400 "Amount paid (0.00) is less than the total (1.00)." | `transactions/services.py:77` `amount_paid or 0` |

`true` is rejected for the same fields, which supports treating the acceptance of `false` as an inconsistency.

## Points to agree with Member 2

1. **A3:** do we require idempotency? If not, #4 is a documented weakness rather than a defect, and the test changes.
2. **#6:** is the exact message part of the requirement?
3. **N2 test:** it sends 2147483648. A fix with a maximum of 100000 also needs a case at 100001.
4. **Tests that pass on defective behaviour:** the N3 and N6 tests assert the current 200 and 500. They will fail when those are fixed.
5. **Overlap:** #1 is the same finding as D1 in the [test plan](test-plan.md#candidate-defects). Keep one.

## Issue text drafts

Issues #1 to #6 already exist, so these are **comments to add to #1, #2, #4 and #5**, not new issues.

### Comment for #1

> Reproduced on 2026-11-28 at `5eebd6a` on a freshly seeded server: quantity 100001 returns 400 "Quantities must be at least 1." The rejection is right and the message is wrong. Cause: `transactions/services.py:61-62` shares one message between both bounds. Same finding as D1 in the unit test plan. Proposed triage: confirmed, fix.

### Comment for #2

> Reproduced on 2026-11-28 at `5eebd6a`: quantity 2147483648 is saved (302) and stock becomes 2147483694. `Purchase.quantity` has no upper bound. The PostgreSQL overflow is our inference and has not been run. Proposed triage: confirmed, fix; add a 100001 case with the fix.

### Comment for #4

> Reproduced on 2026-11-28 at `5eebd6a`: the same body posted twice created sales 122 and 123. The till disables its button while submitting (`static/js/pos.js:254`), so the realistic trigger is a retried request or another API client. The expected result rests on assumption A3, which the team should confirm before this is fixed. Proposed triage: confirmed behaviour, priority to be agreed.

### Comment for #5

> Reproduced on 2026-11-28 at `5eebd6a`. `tax_percentage: false` and `redeem_points: false` return 200 and save the sale. `amount_paid: false` returns 400 with a message about the total. Cause: `value or 0` at `transactions/services.py:74`, `77`, `80`. Expected result rests on assumption A5. Proposed triage: confirmed, fix; the `amount_paid` case is a message problem only.

## What this means for CI

CI runs these tests against a seeded server. After `area2-Rehan` merges, the test job stays red until these six are fixed or the team agrees how to record them.
