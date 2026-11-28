# Mutation testing

Tool: Cosmic Ray 8.9.0. Mutated: `transactions/services.py`, `transactions/loyalty.py`, `store/models.py`, `accounts/permissions.py`. Test command: the unit tests in `tests/team/unit`, stopping at the first failure. A mutant is **killed** when a test fails.

## Results

| Session | Mutants | Killed | Survived | Kill rate | Raw results |
| --- | --- | --- | --- | --- | --- |
| Before the new tests | 608 | 494 | 114 | 81.2% | [before.summary.txt](../reports/mutation/before.summary.txt) |
| After the first new tests | 608 | 588 | 20 | 96.7% | [after.summary.txt](../reports/mutation/after.summary.txt) |
| Final | 608 | 591 | 17 | 97.2% | [final.summary.txt](../reports/mutation/final.summary.txt) |

Each session also has a `.dump.jsonl` file (every mutant, its diff and outcome), a `.survivors.txt` report and the `.sqlite` session. Nothing in `reports/mutation/` was edited by hand. No session had a timeout or a worker error.

The 17 final survivors are the equivalent mutants listed below. The sessions ran on commit `ec38112` plus the new tests, which were committed afterwards; each `.revision.txt` file records the state.

Per module, final session:

| Module or operator | Killed | Kill rate | Survived |
| --- | --- | --- | --- |
| `accounts/permissions.py` | 79 of 83 | 95.2% | 4 |
| `store/models.py` | 85 of 86 | 98.8% | 1 |
| `transactions/loyalty.py` | 114 of 119 | 95.8% | 5 |
| `transactions/services.py` | 313 of 320 | 97.8% | 7 |
| `sqe/break-stock-rule` | 15 of 18 | 83.3% | 3 |
| `sqe/shift-business-limit` | 10 of 10 | 100.0% | 0 |

## Custom operators

Defined in [sqe_operators.py](../tools/mutation/sqe_operators.py) and registered as the local Cosmic Ray plugin `sqe`. [check_operators.py](../tools/mutation/check_operators.py) checks them against examples and compiles every mutant they make.

| Operator | What it does | Business rule |
| --- | --- | --- |
| `shift-business-limit` | Moves `MAX_LINES`, `MAX_QTY_PER_LINE`, the tax limits 0 and 100, and `min_redeem` by +1 and -1 | BR1, BR2, BR3 |
| `break-stock-rule` | Drops one operand from an `and` chain, or flips the sign of an `adjust_stock` quantity | BR2, BR4, stock |

`transactions/models.py` also calls `adjust_stock` (purchases). It is not in the mutated list, so those calls are not mutated.

## Surviving mutants analysed

The first session had 114 survivors. The groups below cover more than 15 of them. New tests are in [test_mutation_gaps.py](../tests/team/unit/test_mutation_gaps.py). Line numbers are those of the mutated file.

### Killed by new tests

| # | Location | What changed | Why the old tests missed it | New test |
| --- | --- | --- | --- | --- |
| 1 | `services.py:128` | `taxable + tax_amount` to `taxable - tax_amount` | No test checked a total with tax above 0 | `test_totals_and_change_with_tax` |
| 2 | `services.py:134` | `paid - grand_total` to `+` or `*` | The change returned was never asserted | `test_totals_and_change_with_tax` |
| 3 | `services.py:127` | `/ 100` to `// 100` | Tax amounts used in tests divided exactly | `test_tax_keeps_the_fraction` |
| 4 | `services.py:117` | `redeem < min_redeem` to `<=`, and the custom shift to `min_redeem + 1` and `- 1` | Redemptions of 5 and 20 were tried, never 9, 10 or 11 | `test_minimum_redemption_boundary` |
| 5 | `services.py:162` | `if earned` to `if not earned` | No test read the balance or ledger after an earning sale | `test_sale_adds_earned_points_to_ledger` |
| 6 | `services.py:185` | `and` to `or`; the balance condition dropped (custom) | The clamp was only tried with a balance of 0 | `test_void_takes_back_only_what_it_should` |
| 7 | `services.py:188` | `-customer.loyalty_points` to `+` | With a balance of 0, `+0` equals `-0` | same, partly spent cases |
| 8 | `services.py:184` | `redeemed - earned` to `>>` or `<<` | Points after a void were not asserted | `test_void_with_points_redeemed_and_earned` |
| 9 | `services.py:78`, `81` | `< 0` to `== 0`, `<= 0`, `< 1`, `< -1` | Tests only expected "some error", and a later check also raised | `test_negative_amount_paid_is_named`, `test_negative_redemption_is_named`, `test_free_item_needs_no_payment` |
| 10 | `services.py:198` | `reason or ''` to `reason and ''`; cut at 199 or 201 | The stored reason was never read back | `test_void_reason_is_stored_and_cut_at_200` |
| 11 | `services.py:139`, `197`, `loyalty.py:71` | `user.is_authenticated` dropped (custom) | No anonymous user was passed in | `test_anonymous_user_is_not_recorded` |
| 12 | `services.py:57` | `or` to `and` in the cart line check | No line lacked only the id | `test_line_without_id_is_rejected` |
| 13 | `loyalty.py:35`, `43` | `*` to `/`, `//` or `**`; `/` to `*` | The point value was 1.00 everywhere, where these agree | `test_point_value_other_than_one` |
| 14 | `loyalty.py:19`, `22` | Default `enabled` and `min_redeem` changed | Every test set all four settings | `test_loyalty_defaults` |
| 15 | `loyalty.py:29` | `<= 0` limits moved | No negative `earn_per` or amount, and no amount of 1 | `test_points_for_amount_edges` |
| 16 | `permissions.py:62` | `status == 'A'` to `status <= 'A'` | No profile had an empty status, which sorts before "A" | `test_blank_status_is_not_active` |
| 17 | `permissions.py:120`, `134` | `@wraps` removed | View names were not checked | `test_guard_decorators_keep_the_view_name` |
| 18 | `models.py:28` to `117` | Field limits, `blank`, `null`, defaults, digits | Tests built valid objects only | `test_text_length_limit`, `test_price_digits`, `test_delivery_fields_are_optional` and neighbours |
| 19 | `models.py:29`, `43` | Slug `unique=True` to `False` | The slug library picks distinct values by itself | `test_database_rejects_a_duplicate_slug` |

Some group 18 mutants change only the schema. They are killed because the mutation run builds tables from the models (`--nomigrations`). In the normal test job, `makemigrations --check` is what would catch such a change.

### Equivalent mutants (17)

No input the application can produce gives a different result.

| # | Location | What changed | Why it is equivalent |
| --- | --- | --- | --- |
| E1 | `loyalty.py:31`, `43` (2) | `/` to `//` | Both operands are not negative, and the result is rounded down anyway |
| E2 | `loyalty.py:41` | `point_value <= 0` to `== 0` | For a negative value, `max(0, ...)` on line 44 still returns 0 |
| E3 | `loyalty.py:29` | `amount <= 0` to `< 0` | An amount of 0 earns 0 points either way |
| E4 | `loyalty.py:44` | `max(0, ...)` to `max(-1, ...)` | The balance cannot be negative, so the minimum is never below 0 |
| E5 | `services.py:42` (2) | `not` removed; `not value.is_integer()` dropped | Every float is rejected either way, because `int(str(value))` fails on "2.0" too. This is defect D4: the line has no effect |
| E6 | `services.py:185` (5) | `net_points < 0` to `!= 0`, `<= 0`, `< 1`, or dropped; `balance < -net_points` to `<=` | The balance is never negative, so `balance < -net_points` implies `net_points < 0`. When balance equals `-net_points`, clamping gives the same value |
| E7 | `permissions.py:32`, `37` (2) | Set union to symmetric difference | The two sets share no element, so both give the same set |
| E8 | `permissions.py:62` | `== 'A'` to `is 'A'` | CPython reuses one object for a one character string. This depends on the interpreter |
| E9 | `permissions.py:87` | `profile and` dropped | A user without a profile is stopped earlier by `is_active_member` |
| E10 | `models.py:67` | `quantity > 0` to `!= 0` | `quantity` cannot be negative |

## Reproduce

```powershell
pip install -r requirements.txt -r requirements-dev.txt
pip install -e tools/mutation
```

Then, in Git Bash from the repository root:

```bash
bash tools/mutation/run.sh mine /tmp/mutation
```

Cosmic Ray edits source files in place, so the script works on copies. It uses ports 9801 to 9804 and takes about 30 minutes with four workers on our machine.
