"""
Two Cosmic Ray operators built from this project's business rules.

shift-business-limit
    Moves a business limit by one in each direction: MAX_LINES,
    MAX_QTY_PER_LINE, the tax limits 0 and 100, and min_redeem.

break-stock-rule
    Drops one operand from an ``and`` chain, or flips the sign of the
    quantity passed to ``adjust_stock``.
"""
from cosmic_ray.operators.operator import Example, Operator
from parso.python import tree

OFFSETS = (1, -1)
LIMIT_CONSTANTS = ('MAX_LINES', 'MAX_QTY_PER_LINE')


def _children(node):
    return getattr(node, 'children', [])


def _span(node):
    return (node.start_pos, node.end_pos)


def _shifted(number, offset):
    value = int(number.value) + offset
    return tree.Number(str(value) if value >= 0 else f'({value})', number.start_pos, number.prefix)


class ShiftBusinessLimit(Operator):
    """Shift one business limit by +1 or -1."""

    def _targets(self, node):
        """Nodes that hold a business limit, found from the parent ``node``."""
        # MAX_LINES = 200 and MAX_QTY_PER_LINE = 100000
        if node.type == 'expr_stmt':
            name, _, value = node.children[:3]
            if name.type == 'name' and name.value in LIMIT_CONSTANTS and value.type == 'number':
                yield node, 2
        if node.type == 'comparison':
            left, _, right = node.children[:3]
            if left.type == 'name' and left.value == 'tax_pct' and right.type == 'number':
                # tax_pct < 0 and tax_pct > 100
                yield node, 2
            elif left.type == 'name' and left.value == 'redeem' and right.get_code().strip() == "cfg['min_redeem']":
                # redeem < cfg['min_redeem']
                yield node, 2

    def mutation_positions(self, node):
        # A list, not a generator: the node changes once one mutation is applied.
        return [_span(parent.children[index]) for parent, index in self._targets(node) for _ in OFFSETS]

    def mutate(self, node, index):
        parent, position = next(self._targets(node))
        limit = parent.children[position]
        offset = OFFSETS[index]
        if limit.type == 'number':
            new = _shifted(limit, offset)
        else:
            sign = '+' if offset > 0 else '-'
            new = tree.String(f"(cfg['min_redeem'] {sign} 1)", limit.start_pos, limit.get_first_leaf().prefix)
        new.parent = parent
        parent.children[position] = new
        return node

    @classmethod
    def examples(cls):
        return (
            Example('MAX_LINES = 200', 'MAX_LINES = 201'),
            Example('MAX_LINES = 200', 'MAX_LINES = 199', occurrence=1),
            Example('MAX_QTY_PER_LINE = 100000', 'MAX_QTY_PER_LINE = 100001'),
            Example('tax_pct < 0', 'tax_pct < 1'),
            Example('tax_pct < 0', 'tax_pct < (-1)', occurrence=1),
            Example('tax_pct > 100', 'tax_pct > 99', occurrence=1),
            Example("redeem < cfg['min_redeem']", "redeem < (cfg['min_redeem'] + 1)"),
            Example("redeem < cfg['min_redeem']", "redeem < (cfg['min_redeem'] - 1)", occurrence=1),
        )


class BreakStockRule(Operator):
    """Drop an ``and`` operand, or flip the sign of an adjust_stock quantity."""

    @staticmethod
    def _and_operands(node):
        if node.type != 'and_test':
            return []
        return list(range(0, len(node.children), 2))

    @staticmethod
    def _adjust_stock_quantity(node):
        """The trailer ``(...)`` of ``X.adjust_stock(...)`` and its second argument."""
        children = _children(node)
        for position, child in enumerate(children[:-1]):
            if child.type != 'trailer' or child.children[0].type != 'operator':
                continue
            if child.children[0].value != '.' or child.children[1].value != 'adjust_stock':
                continue
            call = children[position + 1]
            if call.type == 'trailer' and call.children[0].value == '(' and call.children[1].type == 'arglist':
                return call.children[1], 2
        return None

    def mutation_positions(self, node):
        # A list, not a generator: the node changes once one mutation is applied.
        spans = [_span(node.children[position]) for position in self._and_operands(node)]
        found = self._adjust_stock_quantity(node)
        if found:
            spans.append(_span(found[0].children[found[1]]))
        return spans

    def mutate(self, node, index):
        if node.type == 'and_test':
            position = self._and_operands(node)[index]
            children = list(node.children)
            # Remove the operand together with one neighbouring "and".
            if position == 0:
                prefix = children[0].get_first_leaf().prefix
                del children[0:2]
                children[0].get_first_leaf().prefix = prefix
            else:
                del children[position - 1:position + 1]
            if len(children) == 1:
                only = children[0]
                only.get_first_leaf().prefix = node.get_first_leaf().prefix if position else only.get_first_leaf().prefix
                only.parent = node.parent
                return only
            node.children = children
            return node

        arguments, position = self._adjust_stock_quantity(node)
        quantity = arguments.children[position]
        prefix = quantity.get_first_leaf().prefix
        quantity.get_first_leaf().prefix = ''
        code = quantity.get_code()
        flipped = tree.String(f'-({code})', quantity.start_pos, prefix)
        flipped.parent = arguments
        arguments.children[position] = flipped
        return node

    @classmethod
    def examples(cls):
        return (
            Example('if a and b:\n    pass', 'if b:\n    pass'),
            Example('if a and b:\n    pass', 'if a:\n    pass', occurrence=1),
            Example('x = a and b and c', 'x = a and c', occurrence=1),
            Example('Item.adjust_stock(item.pk, -qty)', 'Item.adjust_stock(item.pk, -(-qty))'),
            Example('Item.adjust_stock(d.item_id, d.quantity)', 'Item.adjust_stock(d.item_id, -(d.quantity))'),
        )


class Provider:
    """Entry point read by Cosmic Ray."""

    _operators = {'shift-business-limit': ShiftBusinessLimit, 'break-stock-rule': BreakStockRule}

    def __iter__(self):
        return iter(self._operators)

    def __getitem__(self, name):
        return self._operators[name]
