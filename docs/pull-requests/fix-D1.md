## Defect

D1, Issue #1 (Minor): a cart line with quantity 100001 is rejected with "Quantities must be at least 1.", which describes the wrong limit.

Fixes #1

## Root cause

`parse_lines` in `transactions/services.py` tested both limits in one condition, `qty < 1 or qty > MAX_QTY_PER_LINE`, and raised one message for both. The existing tests expected only "some error" for a quantity out of range, so the wrong text went unnoticed.

## Test

`tests/team/unit/test_quantity_message.py` expects the lower limit message for 0 and the upper limit message for 100001.

First commit (test only): the case for 100001 fails, because the message is "Quantities must be at least 1."

## Fix

Second commit: one condition and message per limit. Above the maximum the message is "Quantities cannot be more than 100000.". The same quantities are accepted and rejected as before.

## Note

The fix adds two lines to `services.py`. Line numbers after line 61 in `cfg-complexity.md` and `mutation.md` refer to the code before this change.
