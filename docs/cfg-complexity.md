# Control flow graphs and cyclomatic complexity

**To check:** compare each node with the code. The graphs were drawn by hand into a script, which computed the counts and paths.

How the graphs are drawn:

- One decision node for each `if`, `for`, `except` and conditional expression. A condition joined by `and` or `or` stays in one node.
- Every `return` and `raise` leads to a single exit node.
- Decision diamonds have a true (`T`) and a false (`F`) edge. For a loop, `T` means another item and `F` means done. For node 7 of `create_sale`, `T` means `DoesNotExist`.

## `void_sale`

[services.py:170](../transactions/services.py#L170)

```mermaid
flowchart TD
    n1{"[1] L175-177: lock sale; if sale.is_voided"}
    n2["[2] L178: raise already voided"]
    n3{"[3] L180: for detail in sale lines"}
    n4["[4] L181: return stock"]
    n5{"[5] L183-185: net_points; if net_points #lt; 0 and balance #lt; -net_points"}
    n6["[6] L188: net_points = -balance"]
    n7{"[7] L189: if net_points"}
    n8["[8] L190-193: apply reversal"]
    n9{"[9] L197: if user is not None and authenticated"}
    n10["[10] L197: voided_by = user"]
    n11["[11] L197: voided_by = None"]
    n12["[12] L198-200: reason, save, return"]
    n13(["[13] exit: return or raise"])
    n1 -->|"e1 T"| n2
    n1 -->|"e2 F"| n3
    n2 -->|"e3"| n13
    n3 -->|"e4 T"| n4
    n4 -->|"e5"| n3
    n3 -->|"e6 F"| n5
    n5 -->|"e7 T"| n6
    n5 -->|"e8 F"| n7
    n6 -->|"e9"| n7
    n7 -->|"e10 T"| n8
    n7 -->|"e11 F"| n9
    n8 -->|"e12"| n9
    n9 -->|"e13 T"| n10
    n9 -->|"e14 F"| n11
    n10 -->|"e15"| n12
    n11 -->|"e16"| n12
    n12 -->|"e17"| n13
```

### Nodes

| Node | Lines | Code | Decision |
| --- | --- | --- | --- |
| 1 | 175-177 | `with transaction.atomic(): sale = Sale.objects.select_for_update().get(pk=sale.pk) if sale.is_voided:` | Yes |
| 2 | 178 | `raise ValidationError('This sale has already been voided.')` |  |
| 3 | 180 | `for detail in sale.saledetail_set.select_related('item').order_by('item_id'):` | Yes |
| 4 | 181 | `Item.adjust_stock(detail.item_id, detail.quantity)` |  |
| 5 | 183-185 | `customer = Customer.objects.select_for_update().get(pk=sale.customer_id) net_points = sale.loyalty_points_redeemed - sale.loyalty_points_earned if ...` | Yes |
| 6 | 188 | `net_points = -customer.loyalty_points` |  |
| 7 | 189 | `if net_points:` | Yes |
| 8 | 190-193 | `loyalty.apply_points( customer.pk, net_points, LoyaltyTransaction.REVERSAL, sale=sale, user=user, note=f'Void of {sale.receipt_number}', )` |  |
| 9 | 197 | `sale.voided_by = user if user is not None and user.is_authenticated else None` | Yes |
| 10 | 197 | `sale.voided_by = user if user is not None and user.is_authenticated else None` |  |
| 11 | 197 | `sale.voided_by = user if user is not None and user.is_authenticated else None` |  |
| 12 | 198-200 | `sale.void_reason = (reason or '')[:200] sale.save(update_fields=['status', 'voided_at', 'voided_by', 'void_reason']) return sale` |  |
| 13 | | Single exit | |

### Edges

| Edge | From | To | Branch |
| --- | --- | --- | --- |
| e1 | 1 | 2 | T |
| e2 | 1 | 3 | F |
| e3 | 2 | 13 |  |
| e4 | 3 | 4 | T |
| e5 | 4 | 3 |  |
| e6 | 3 | 5 | F |
| e7 | 5 | 6 | T |
| e8 | 5 | 7 | F |
| e9 | 6 | 7 |  |
| e10 | 7 | 8 | T |
| e11 | 7 | 9 | F |
| e12 | 8 | 9 |  |
| e13 | 9 | 10 | T |
| e14 | 9 | 11 | F |
| e15 | 10 | 12 |  |
| e16 | 11 | 12 |  |
| e17 | 12 | 13 |  |

### Cyclomatic complexity

| Method | Working | V(G) |
| --- | --- | --- |
| E - N + 2 | 17 - 13 + 2 | **6** |
| Decision points + 1 | 5 decision nodes (1, 3, 5, 7, 9) + 1 | **6** |
| Independent paths | 6 paths below | **6** |

### Independent paths

Path 1 is the baseline. Each later path flips one decision. The script that built this table checked that the paths are linearly independent.

| Path | Flipped node | Nodes | Can it run? |
| --- | --- | --- | --- |
| P1 |  | 1 3 4 3 5 7 8 9 10 12 13 | Yes |
| P2 | 1 | 1 2 13 | Yes |
| P3 | 3 | 1 3 5 7 8 9 10 12 13 | Only for a sale with no lines, which `create_sale` never makes |
| P4 | 5 | 1 3 4 3 5 6 7 8 9 10 12 13 | Yes |
| P5 | 7 | 1 3 4 3 5 7 9 10 12 13 | Yes |
| P6 | 9 | 1 3 4 3 5 7 8 9 11 12 13 | Yes |

`reason or ''` on line 198 and the two `and` operators are inside nodes 12, 5 and 9; they are counted below.

## `create_sale`

[services.py:67](../transactions/services.py#L67)

```mermaid
flowchart TD
    n1{"[1] L73-75: parse lines and tax; if tax out of range"}
    n2["[2] L76: raise tax"]
    n3{"[3] L77-78: parse paid; if paid #lt; 0"}
    n4["[4] L79: raise paid"]
    n5{"[5] L80-81: parse redeem; if redeem #lt; 0"}
    n6["[6] L82: raise redeem"]
    n7{"[7] L84-87: try to get customer; DoesNotExist?"}
    n8["[8] L88: raise invalid customer"]
    n9{"[9] L91-96: lock stock; if missing"}
    n10["[10] L97: raise missing items"]
    n11["[11] L99-100: sub_total = 0, priced = []"]
    n12{"[12] L101: for item_id, qty in lines"}
    n13{"[13] L102-103: if item.quantity #lt; qty"}
    n14["[14] L104: raise not enough stock"]
    n15["[15] L107-109: add line total"]
    n16{"[16] L110-114: config; if redeem"}
    n17{"[17] L115: if not enabled"}
    n18["[18] L116: raise not enabled"]
    n19{"[19] L117: if redeem #lt; min_redeem"}
    n20["[20] L118: raise below minimum"]
    n21{"[21] L119: if redeem #gt; balance"}
    n22["[22] L120: raise not enough points"]
    n23{"[23] L123: if redeem #gt; max_redeemable"}
    n24["[24] L124: raise exceeds bill"]
    n25{"[25] L125: discount: if redeem"}
    n26["[26] L125: discount = value of points"]
    n27["[27] L125: discount = 0.00"]
    n28{"[28] L126-130: totals; if paid #lt; grand_total"}
    n29["[29] L131: raise underpaid"]
    n30{"[30] L134-139: change, earned; served_by: if authenticated user"}
    n31["[31] L139: served_by = user"]
    n32["[32] L139: served_by = None"]
    n33["[33] L137-153: create sale and lines"]
    n34{"[34] L154: for item in priced"}
    n35["[35] L155: reduce stock"]
    n36{"[36] L157: if redeem"}
    n37["[37] L158-161: apply redeem"]
    n38{"[38] L162: if earned"}
    n39["[39] L163-166: apply earn"]
    n40["[40] L167: return sale"]
    n41(["[41] exit: return or raise"])
    n1 -->|"e1 T"| n2
    n1 -->|"e2 F"| n3
    n2 -->|"e3"| n41
    n3 -->|"e4 T"| n4
    n3 -->|"e5 F"| n5
    n4 -->|"e6"| n41
    n5 -->|"e7 T"| n6
    n5 -->|"e8 F"| n7
    n6 -->|"e9"| n41
    n7 -->|"e10 T"| n8
    n7 -->|"e11 F"| n9
    n8 -->|"e12"| n41
    n9 -->|"e13 T"| n10
    n9 -->|"e14 F"| n11
    n10 -->|"e15"| n41
    n11 -->|"e16"| n12
    n12 -->|"e17 T"| n13
    n12 -->|"e18 F"| n16
    n13 -->|"e19 T"| n14
    n13 -->|"e20 F"| n15
    n14 -->|"e21"| n41
    n15 -->|"e22"| n12
    n16 -->|"e23 T"| n17
    n16 -->|"e24 F"| n25
    n17 -->|"e25 T"| n18
    n17 -->|"e26 F"| n19
    n18 -->|"e27"| n41
    n19 -->|"e28 T"| n20
    n19 -->|"e29 F"| n21
    n20 -->|"e30"| n41
    n21 -->|"e31 T"| n22
    n21 -->|"e32 F"| n23
    n22 -->|"e33"| n41
    n23 -->|"e34 T"| n24
    n23 -->|"e35 F"| n25
    n24 -->|"e36"| n41
    n25 -->|"e37 T"| n26
    n25 -->|"e38 F"| n27
    n26 -->|"e39"| n28
    n27 -->|"e40"| n28
    n28 -->|"e41 T"| n29
    n28 -->|"e42 F"| n30
    n29 -->|"e43"| n41
    n30 -->|"e44 T"| n31
    n30 -->|"e45 F"| n32
    n31 -->|"e46"| n33
    n32 -->|"e47"| n33
    n33 -->|"e48"| n34
    n34 -->|"e49 T"| n35
    n34 -->|"e50 F"| n36
    n35 -->|"e51"| n34
    n36 -->|"e52 T"| n37
    n36 -->|"e53 F"| n38
    n37 -->|"e54"| n38
    n38 -->|"e55 T"| n39
    n38 -->|"e56 F"| n40
    n39 -->|"e57"| n40
    n40 -->|"e58"| n41
```

### Nodes

| Node | Lines | Code | Decision |
| --- | --- | --- | --- |
| 1 | 73-75 | `lines = parse_lines(items) tax_pct = _decimal(tax_percentage or 0, 'Tax') if tax_pct < 0 or tax_pct > 100:` | Yes |
| 2 | 76 | `raise ValidationError('Tax must be between 0 and 100 percent.')` |  |
| 3 | 77-78 | `paid = _decimal(amount_paid or 0, 'Amount paid') if paid < 0:` | Yes |
| 4 | 79 | `raise ValidationError('Amount paid cannot be negative.')` |  |
| 5 | 80-81 | `redeem = _int(redeem_points or 0, 'Points to redeem') if redeem < 0:` | Yes |
| 6 | 82 | `raise ValidationError('Points to redeem cannot be negative.')` |  |
| 7 | 84-87 | `with transaction.atomic(): try: customer = Customer.objects.select_for_update().get(pk=_int(customer_id, 'Customer')) except Customer.DoesNotExist:` | Yes |
| 8 | 88 | `raise ValidationError('Select a valid customer.')` |  |
| 9 | 91-96 | `locked = { item.pk: item for item in Item.objects.select_for_update().filter(pk__in=lines.keys()).order_by('pk') } missing = [pk for pk in lines if...` | Yes |
| 10 | 97 | `raise ValidationError('One or more items no longer exist.')` |  |
| 11 | 99-100 | `sub_total = Decimal('0') priced = []` |  |
| 12 | 101 | `for item_id, qty in lines.items():` | Yes |
| 13 | 102-103 | `item = locked[item_id] if item.quantity < qty:` | Yes |
| 14 | 104 | `raise ValidationError(` |  |
| 15 | 107-109 | `line_total = _money(item.price * qty) sub_total += line_total priced.append((item, qty, item.price, line_total))` |  |
| 16 | 110-114 | `sub_total = _money(sub_total) # Loyalty redemption is a discount applied before tax. cfg = loyalty.config() if redeem:` | Yes |
| 17 | 115 | `if not cfg['enabled']:` | Yes |
| 18 | 116 | `raise ValidationError('Loyalty points are not enabled.')` |  |
| 19 | 117 | `if redeem < cfg['min_redeem']:` | Yes |
| 20 | 118 | `raise ValidationError(f'Redeem at least {cfg["min_redeem"]} points.')` |  |
| 21 | 119 | `if redeem > customer.loyalty_points:` | Yes |
| 22 | 120 | `raise ValidationError(` |  |
| 23 | 123 | `if redeem > loyalty.max_redeemable(customer.loyalty_points, sub_total):` | Yes |
| 24 | 124 | `raise ValidationError('Points redeemed cannot exceed the bill.')` |  |
| 25 | 125 | `discount = loyalty.value_of_points(redeem) if redeem else Decimal('0.00')` | Yes |
| 26 | 125 | `discount = loyalty.value_of_points(redeem) if redeem else Decimal('0.00')` |  |
| 27 | 125 | `discount = loyalty.value_of_points(redeem) if redeem else Decimal('0.00')` |  |
| 28 | 126-130 | `taxable = sub_total - discount tax_amount = _money(taxable * tax_pct / Decimal('100')) grand_total = _money(taxable + tax_amount) if paid < grand_t...` | Yes |
| 29 | 131 | `raise ValidationError(` |  |
| 30 | 134-139 | `change = _money(paid - grand_total) earned = loyalty.points_for_amount(taxable) sale = Sale.objects.create( customer=customer, served_by=user if us...` | Yes |
| 31 | 139 | `served_by=user if user is not None and user.is_authenticated else None,` |  |
| 32 | 139 | `served_by=user if user is not None and user.is_authenticated else None,` |  |
| 33 | 137-153 | `sale = Sale.objects.create( customer=customer, served_by=user if user is not None and user.is_authenticated else None, sub_total=sub_total, discoun...` |  |
| 34 | 154 | `for item, qty, _, _ in priced:` | Yes |
| 35 | 155 | `Item.adjust_stock(item.pk, -qty)` |  |
| 36 | 157 | `if redeem:` | Yes |
| 37 | 158-161 | `loyalty.apply_points( customer.pk, -redeem, LoyaltyTransaction.REDEEM, sale=sale, user=user, note=f'Redeemed on {sale.receipt_number}', )` |  |
| 38 | 162 | `if earned:` | Yes |
| 39 | 163-166 | `loyalty.apply_points( customer.pk, earned, LoyaltyTransaction.EARN, sale=sale, user=user, note=f'Earned on {sale.receipt_number}', )` |  |
| 40 | 167 | `return sale` |  |
| 41 | | Single exit | |

### Edges

| Edge | From | To | Branch |
| --- | --- | --- | --- |
| e1 | 1 | 2 | T |
| e2 | 1 | 3 | F |
| e3 | 2 | 41 |  |
| e4 | 3 | 4 | T |
| e5 | 3 | 5 | F |
| e6 | 4 | 41 |  |
| e7 | 5 | 6 | T |
| e8 | 5 | 7 | F |
| e9 | 6 | 41 |  |
| e10 | 7 | 8 | T |
| e11 | 7 | 9 | F |
| e12 | 8 | 41 |  |
| e13 | 9 | 10 | T |
| e14 | 9 | 11 | F |
| e15 | 10 | 41 |  |
| e16 | 11 | 12 |  |
| e17 | 12 | 13 | T |
| e18 | 12 | 16 | F |
| e19 | 13 | 14 | T |
| e20 | 13 | 15 | F |
| e21 | 14 | 41 |  |
| e22 | 15 | 12 |  |
| e23 | 16 | 17 | T |
| e24 | 16 | 25 | F |
| e25 | 17 | 18 | T |
| e26 | 17 | 19 | F |
| e27 | 18 | 41 |  |
| e28 | 19 | 20 | T |
| e29 | 19 | 21 | F |
| e30 | 20 | 41 |  |
| e31 | 21 | 22 | T |
| e32 | 21 | 23 | F |
| e33 | 22 | 41 |  |
| e34 | 23 | 24 | T |
| e35 | 23 | 25 | F |
| e36 | 24 | 41 |  |
| e37 | 25 | 26 | T |
| e38 | 25 | 27 | F |
| e39 | 26 | 28 |  |
| e40 | 27 | 28 |  |
| e41 | 28 | 29 | T |
| e42 | 28 | 30 | F |
| e43 | 29 | 41 |  |
| e44 | 30 | 31 | T |
| e45 | 30 | 32 | F |
| e46 | 31 | 33 |  |
| e47 | 32 | 33 |  |
| e48 | 33 | 34 |  |
| e49 | 34 | 35 | T |
| e50 | 34 | 36 | F |
| e51 | 35 | 34 |  |
| e52 | 36 | 37 | T |
| e53 | 36 | 38 | F |
| e54 | 37 | 38 |  |
| e55 | 38 | 39 | T |
| e56 | 38 | 40 | F |
| e57 | 39 | 40 |  |
| e58 | 40 | 41 |  |

### Cyclomatic complexity

| Method | Working | V(G) |
| --- | --- | --- |
| E - N + 2 | 58 - 41 + 2 | **19** |
| Decision points + 1 | 18 decision nodes (1, 3, 5, 7, 9, 12, 13, 16, 17, 19, 21, 23, 25, 28, 30, 34, 36, 38) + 1 | **19** |
| Independent paths | 19 paths below | **19** |

### Independent paths

Path 1 is the baseline. Each later path flips one decision. The script that built this table checked that the paths are linearly independent.

| Path | Flipped node | Nodes | Can it run? |
| --- | --- | --- | --- |
| P1 |  | 1 3 5 7 9 11 12 13 15 12 16 17 19 21 23 25 26 28 30 31 33 34 35 34 36 37 38 39 40 41 | Yes |
| P2 | 1 | 1 2 41 | Yes |
| P3 | 3 | 1 3 4 41 | Yes |
| P4 | 5 | 1 3 5 6 41 | Yes |
| P5 | 7 | 1 3 5 7 8 41 | Yes |
| P6 | 9 | 1 3 5 7 9 10 41 | Yes |
| P7 | 12 | 1 3 5 7 9 11 12 16 17 19 21 23 25 26 28 30 31 33 34 35 34 36 37 38 39 40 41 | No: `parse_lines` guarantees at least one line |
| P8 | 13 | 1 3 5 7 9 11 12 13 14 41 | Yes |
| P9 | 16 | 1 3 5 7 9 11 12 13 15 12 16 25 26 28 30 31 33 34 35 34 36 37 38 39 40 41 | No: nodes 16, 25 and 36 all test `redeem` and must agree |
| P10 | 17 | 1 3 5 7 9 11 12 13 15 12 16 17 18 41 | Yes |
| P11 | 19 | 1 3 5 7 9 11 12 13 15 12 16 17 19 20 41 | Yes |
| P12 | 21 | 1 3 5 7 9 11 12 13 15 12 16 17 19 21 22 41 | Yes |
| P13 | 23 | 1 3 5 7 9 11 12 13 15 12 16 17 19 21 23 24 41 | Yes |
| P14 | 25 | 1 3 5 7 9 11 12 13 15 12 16 17 19 21 23 25 27 28 30 31 33 34 35 34 36 37 38 39 40 41 | No: nodes 16, 25 and 36 all test `redeem` and must agree |
| P15 | 28 | 1 3 5 7 9 11 12 13 15 12 16 17 19 21 23 25 26 28 29 41 | Yes |
| P16 | 30 | 1 3 5 7 9 11 12 13 15 12 16 17 19 21 23 25 26 28 30 32 33 34 35 34 36 37 38 39 40 41 | Yes |
| P17 | 34 | 1 3 5 7 9 11 12 13 15 12 16 17 19 21 23 25 26 28 30 31 33 34 36 37 38 39 40 41 | No: `priced` has one entry for each line |
| P18 | 36 | 1 3 5 7 9 11 12 13 15 12 16 17 19 21 23 25 26 28 30 31 33 34 35 34 36 38 39 40 41 | No: nodes 16, 25 and 36 all test `redeem` and must agree |
| P19 | 38 | 1 3 5 7 9 11 12 13 15 12 16 17 19 21 23 25 26 28 30 31 33 34 35 34 36 37 38 40 41 | Yes |

The comprehensions on lines 91 to 96 and 150 to 153 are kept inside their nodes. Exceptions raised inside called functions are not drawn.

## Comparison with SonarQube

Values from [function-complexity-issues.json](../reports/sonar/function-complexity-issues.json).

| Function | Hand V(G) | Sonar cyclomatic | Sonar cognitive |
| --- | --- | --- | --- |
| `void_sale` | 6 | 9 | 8 |
| `create_sale` | 19 | 24 | 28 |
| `parse_lines` | not drawn | 10 | 10 |

### Why the cyclomatic values differ

How SonarQube counts was tested on one-construct functions ([source](../reports/sonar/complexity-probe.py.txt), [result](../reports/sonar/complexity-probe-issues.json)):

| Construct alone in a function | Sonar cyclomatic | Counts as a decision? |
| --- | --- | --- |
| `try` / `except` | 1 | No |
| Comprehension with `if` | 2 | Yes |
| `a or b` | 2 | Yes |
| Conditional expression | 2 | Yes |
| `with` | 1 | No |

**`void_sale`: 6 + 3 = 9.** Sonar adds one for each boolean operator: `and` on line 185, `and` on line 197, `or` on line 198.

**`create_sale`: 19 - 1 + 5 + 1 = 24.**

- minus 1: the `except` on line 87 is not counted.
- plus 5: `or` on lines 74, 75, 77 and 80, and `and` on line 139.
- plus 1: the `if` in the list comprehension on line 95.

The hand count follows the graph, where a short-circuit operator is not a separate node. Counting each atomic condition is the stricter reading, and is closer to what Sonar reports.

### Why cognitive complexity is different again

Cognitive complexity measures how hard code is to read, not the number of paths. It adds extra for nesting, so in `create_sale` the checks nested under `if redeem` and under the stock loop cost more than the same checks at the top level. That accounts for 28 against a cyclomatic value of 24. `void_sale` has almost no nesting, and its two values are close (8 and 9).

## Test effort

Basis path testing needs up to 6 tests for `void_sale` and 19 for `create_sale`. Paths marked "No" cannot be run, so fewer are possible. This document does not map paths to existing tests.
