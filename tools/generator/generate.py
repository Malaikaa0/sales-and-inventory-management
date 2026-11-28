"""
Test data generator: equivalence partitioning (EP) + 3-point boundary value
analysis (BVA) for the Sale and Void sale endpoints.

    python tools/generator/generate.py openapi/openapi.yaml [-o tools/generator/out/cases.json]

Everything comes from the spec, including its x- extensions:
  minimum / maximum / x-delta        -> BVA points  (min-d, min, min+d, max-d, max, max+d) + nominal
  minItems / maxItems                -> array lengths
  minLength / maxLength              -> string lengths
  required, nullable                 -> EP missing / null
  x-defaults-when-missing            -> missing, null, "", false count as the default
  x-accepts-numeric-strings          -> "3" accepted; on integers every float (2.0 too) rejected
  x-rejects-non-finite               -> "NaN" rejected
  x-must-cover-total                 -> extra BVA around the baseline grand total
  x-limited-by-balance               -> values above the baseline customer balance rejected
  x-invalid-status, x-outcome        -> void's 200 / 302 outcomes
  x-error-message*                   -> expected message

Output is deterministic: no randomness, cases sorted by id, keys sorted.

Values that depend on test fixtures are placeholders the API tests substitute:
  "<customer_id>", "<item_id>", "<sale_id>", "<missing_sale_id>",
  and "<x:str>" for the numeric-string form of x.
"""
import argparse
import json
import sys
from decimal import Decimal
from pathlib import Path

import yaml

SALE_PATH = '/transactions/new-sale/'
VOID_PATH = '/transactions/sale/{pk}/void/'

# Fixture assumptions the API tests must create (recorded in the output).
CONTEXT = {
    'item_price': '1.00',          # fresh item, price 1.00
    'item_stock': 100000,          # enough for the quantity maximum
    'customer_points': 0,          # fresh customer, no loyalty points
    'baseline_amount_paid': '1000000.00',
    'note': 'Each case varies one field of the baseline; everything else stays valid.',
}
BASE_SALE = {
    'customer': '<customer_id>',
    'items': [{'id': '<item_id>', 'quantity': 1}],
    'tax_percentage': 0,
    'amount_paid': 1000000,
    'redeem_points': 0,
}
MISSING = object()


# ---------------------------------------------------------------- helpers
def resolve(spec, node):
    while isinstance(node, dict) and '$ref' in node:
        target = spec
        for part in node['$ref'].lstrip('#/').split('/'):
            target = target[part]
        node = target
    return node


def falsy(value):
    return value is MISSING or value is None or value == '' or value is False or value == 0


# ------------------------------------------------- the code's acceptance model
def check_scalar(schema, value):
    """Return (ok, normalised, message_if_not_ok) for one scalar field,
    mirroring services.py _int / _decimal plus the spec's range."""
    if 'x-defaults-when-missing' in schema and falsy(value):
        value = schema['x-defaults-when-missing']
    if value is MISSING:
        return False, None, schema.get('x-error-message-type') or schema.get('x-error-message')
    typ = schema['type']
    if isinstance(value, str) and value.startswith('<'):
        # Fixture placeholder: "<x>" is a valid id, "<x:str>" its numeric-string form.
        ok = not value.endswith(':str>') or schema.get('x-accepts-numeric-strings', False)
        return ok, Decimal(1), None if ok else schema.get('x-error-message')
    type_msg = schema.get('x-error-message-type') or schema.get('x-error-message')
    if typ == 'integer':
        if isinstance(value, bool) or isinstance(value, float) or value is None:
            return False, None, type_msg
        if isinstance(value, str):
            if not schema.get('x-accepts-numeric-strings') or not value.strip().lstrip('-').isdigit():
                return False, None, type_msg
            value = int(value)
        if not isinstance(value, int):
            return False, None, type_msg
        d = Decimal(value)
    else:  # number
        if isinstance(value, bool) or value is None or isinstance(value, (list, dict)):
            return False, None, type_msg
        try:
            d = Decimal(str(value))
        except Exception:
            return False, None, type_msg
        if not d.is_finite():
            return False, None, type_msg
        if isinstance(value, str) and not schema.get('x-accepts-numeric-strings'):
            return False, None, type_msg
    range_msg = schema.get('x-error-message')
    if 'minimum' in schema and d < Decimal(str(schema['minimum'])):
        return False, None, range_msg
    if 'maximum' in schema and d > Decimal(str(schema['maximum'])):
        return False, None, range_msg
    return True, d, None


class Builder:
    def __init__(self, spec):
        self.spec = spec
        self.cases = []
        self.req = resolve(spec, spec['components']['schemas']['SaleRequest'])
        self.line = resolve(spec, self.req['properties']['items']['items'])

    def add(self, **case):
        self.cases.append(case)

    # ------------------------------------------------------------ sale
    def sale_case(self, field, technique, partition, value, body, ok, outcome, message, rule):
        self.add(
            id=f'SALE-{field}-{technique}-{partition}',
            endpoint=f'POST {SALE_PATH}', field=field, technique=technique,
            partition=partition, value=None if value is MISSING else value,
            value_missing=value is MISSING, body=body, valid=ok,
            expected_status=200 if ok else 400,
            expected_outcome='accepted' if ok else outcome,
            expected_message=None if ok else message, rule=rule,
        )

    def total_for(self, body):
        price = Decimal(CONTEXT['item_price'])
        qty = sum(int(l['quantity']) for l in body['items'])
        tax = Decimal(str(body.get('tax_percentage') or 0))
        sub = price * qty
        return (sub + (sub * tax / 100).quantize(Decimal('0.01'))).quantize(Decimal('0.01'))

    def top_field(self, name, technique, partition, value):
        schema = self.req['properties'][name]
        body = json.loads(json.dumps(BASE_SALE))
        if value is MISSING:
            body.pop(name)
        else:
            body[name] = value
        ok, norm, msg = check_scalar(schema, value)
        outcome = 'rejected:field'
        if ok and name == 'customer':
            # The code has no range check: anything but the fixture id is not found.
            if value not in ('<customer_id>', '<customer_id:str>'):
                ok, msg, outcome = False, schema['x-error-message-not-found'], 'rejected:not-found'
        if ok and schema.get('x-limited-by-balance') and norm > CONTEXT['customer_points']:
            ok, msg, outcome = False, f'only has {CONTEXT["customer_points"]} points.', 'rejected:balance'
        if ok and schema.get('x-must-cover-total') and norm < self.total_for(body):
            ok, msg, outcome = False, 'is less than the total', 'rejected:underpayment'
        self.sale_case(name, technique, partition, value, body, ok, outcome, msg, schema.get('x-rule'))

    def line_field(self, name, technique, partition, value):
        schema = self.line['properties'][name]
        line = {'id': '<item_id>', 'quantity': 1}
        if value is MISSING:
            line.pop(name)
        else:
            line[name] = value
        body = json.loads(json.dumps(BASE_SALE))
        body['items'] = [line]
        if value is MISSING:
            ok, msg, outcome = False, self.line['x-error-message-shape'], 'rejected:shape'
        else:
            ok, _, msg = check_scalar(schema, value)
            outcome = 'rejected:field'
            if ok and name == 'id' and value not in ('<item_id>', '<item_id:str>'):
                ok, msg, outcome = False, schema['x-error-message-not-found'], 'rejected:not-found'
        rule = schema.get('x-rule') or 'FR1'
        self.sale_case(f'items[].{name}', technique, partition, value, body, ok, outcome, msg, rule)

    def scalar_bva(self, schema, emit):
        is_int = schema['type'] == 'integer'
        delta = Decimal('1') if is_int else Decimal(str(schema.get('x-delta', '0.01')))
        fmt = (lambda d: int(d)) if is_int else (lambda d: float(d))
        if 'minimum' in schema:
            lo = Decimal(str(schema['minimum']))
            emit('BVA', 'min-d', fmt(lo - delta))
            emit('BVA', 'min', fmt(lo))
            emit('BVA', 'min+d', fmt(lo + delta))
        if 'maximum' in schema:
            hi = Decimal(str(schema['maximum']))
            emit('BVA', 'max-d', fmt(hi - delta))
            emit('BVA', 'max', fmt(hi))
            emit('BVA', 'max+d', fmt(hi + delta))
            if 'minimum' in schema:
                emit('BVA', 'nominal', fmt(((lo + hi) / 2).to_integral_value()))

    def scalar_ep(self, schema, emit, valid_token=None):
        emit('EP', 'missing', MISSING)
        emit('EP', 'null', None)
        emit('EP', 'empty-string', '')
        emit('EP', 'wrong-type-string', 'abc')
        emit('EP', 'wrong-type-bool-true', True)
        emit('EP', 'wrong-type-bool-false', False)
        if valid_token:
            emit('EP', 'numeric-string', valid_token.replace('>', ':str>'))
        elif schema['type'] == 'integer':
            emit('EP', 'numeric-string', str(schema.get('minimum', 1)))
        else:
            emit('EP', 'numeric-string', '12.5')
        emit('EP', 'float-whole', 2.0)
        emit('EP', 'float-half', 2.5)
        if schema.get('x-rejects-non-finite'):
            emit('EP', 'non-finite', 'NaN')

    def build_sale(self):
        for name in ('customer', 'tax_percentage', 'amount_paid', 'redeem_points'):
            schema = self.req['properties'][name]
            emit = lambda t, p, v, n=name: self.top_field(n, t, p, v)
            self.scalar_bva(schema, emit)
            if name == 'customer':
                emit('EP', 'valid', '<customer_id>')
                emit('EP', 'not-found-zero', 0)
                emit('EP', 'not-found-negative', -1)
            if schema.get('x-must-cover-total'):
                total = self.total_for(BASE_SALE)
                emit('BVA', 'total-d', float(total - Decimal('0.01')))
                emit('BVA', 'total', float(total))
                emit('BVA', 'total+d', float(total + Decimal('0.01')))
            self.scalar_ep(schema, emit, '<customer_id>' if name == 'customer' else None)

        for name in ('id', 'quantity'):
            schema = self.line['properties'][name]
            emit = lambda t, p, v, n=name: self.line_field(n, t, p, v)
            self.scalar_bva(schema, emit)
            if name == 'id':
                emit('EP', 'valid', '<item_id>')
                emit('EP', 'not-found-zero', 0)
            self.scalar_ep(schema, emit, '<item_id>' if name == 'id' else None)

        items = self.req['properties']['items']
        lo, hi = items['minItems'], items['maxItems']
        for partition, n in (('min-d', lo - 1), ('min', lo), ('min+d', lo + 1),
                             ('max-d', hi - 1), ('max', hi), ('max+d', hi + 1)):
            body = json.loads(json.dumps(BASE_SALE))
            body['items'] = [{'id': '<item_id>', 'quantity': 1} for _ in range(n)]
            ok = lo <= n <= hi
            msg = items['x-error-message-empty'] if n < lo else items['x-error-message-too-many']
            self.sale_case('items', 'BVA', f'length-{partition}', f'<{n} lines of item_id x1>',
                           body, ok, 'rejected:field', msg, items.get('x-rule'))
        for partition, value in (('missing', MISSING), ('null', None), ('wrong-type-string', 'abc'),
                                 ('wrong-type-object', {}), ('element-not-object', ['abc'])):
            body = json.loads(json.dumps(BASE_SALE))
            if value is MISSING:
                body.pop('items')
            else:
                body['items'] = value
            msg = (self.line['x-error-message-shape'] if partition == 'element-not-object'
                   else items['x-error-message-empty'])
            self.sale_case('items', 'EP', partition, value, body, False,
                           'rejected:shape' if partition == 'element-not-object' else 'rejected:field',
                           msg, items.get('x-rule'))
        body = json.loads(json.dumps(BASE_SALE))
        body['items'] = [{'id': '<item_id>', 'quantity': 1}, {'id': '<item_id>', 'quantity': 2}]
        self.sale_case('items', 'EP', 'duplicate-ids-merged', body['items'], body, True,
                       'accepted', None, items.get('x-rule'))

    # ------------------------------------------------------------ void
    def build_void(self):
        op = self.spec['paths'][VOID_PATH]['post']
        form = resolve(self.spec, op['requestBody']['content']['application/x-www-form-urlencoded']['schema'])
        reason = form['properties']['reason']
        bad = reason.get('x-invalid-status', 400)

        def add(field, technique, partition, value, pk, ok, status, outcome, rule):
            self.add(
                id=f'VOID-{field}-{technique}-{partition}', endpoint=f'POST {VOID_PATH}',
                field=field, technique=technique, partition=partition,
                value=None if value is MISSING else value, value_missing=value is MISSING,
                body={'pk': pk, 'reason': None if value is MISSING else value} if field == 'reason'
                else {'pk': value, 'reason': 'Customer returned all items'},
                valid=ok, expected_status=status, expected_outcome=outcome,
                expected_message=None, rule=rule,
            )

        lo, hi = reason['minLength'], reason['maxLength']
        for partition, n in (('min-d', lo - 1), ('min', lo), ('min+d', lo + 1),
                             ('max-d', hi - 1), ('max', hi), ('max+d', hi + 1),
                             ('nominal', (lo + hi) // 2)):
            ok = lo <= n <= hi
            add('reason', 'BVA', f'length-{partition}', 'r' * n, '<sale_id>', ok,
                302 if ok else bad, 'voided' if ok else 'invalid-form', reason.get('x-rule'))
        add('reason', 'EP', 'missing', MISSING, '<sale_id>', False, bad, 'invalid-form', reason.get('x-rule'))
        add('reason', 'EP', 'whitespace-only', '   ', '<sale_id>', False, bad, 'invalid-form', reason.get('x-rule'))
        add('reason', 'EP', 'already-voided', 'Second void', '<voided_sale_id>', True, 302,
            'already-voided', 'BR3')
        add('pk', 'EP', 'valid', '<sale_id>', None, True, 302, 'voided', 'FR6')
        add('pk', 'EP', 'not-found', '<missing_sale_id>', None, False, 404, 'not-found', 'FR6')
        add('pk', 'BVA', 'min-d', 0, None, False, 404, 'not-found', 'FR6')
        add('pk', 'EP', 'negative', -1, None, False, 404, 'not-found', 'FR6')
        add('pk', 'EP', 'wrong-type-string', 'abc', None, False, 404, 'not-found', 'FR6')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument('spec')
    parser.add_argument('-o', '--out', default=str(Path(__file__).parent / 'out' / 'cases.json'))
    args = parser.parse_args(argv)

    spec = yaml.safe_load(Path(args.spec).read_text(encoding='utf-8'))
    builder = Builder(spec)
    builder.build_sale()
    builder.build_void()
    cases = sorted(builder.cases, key=lambda c: c['id'])
    ids = [c['id'] for c in cases]
    if len(ids) != len(set(ids)):
        sys.exit('Duplicate case ids: ' + ', '.join(sorted({i for i in ids if ids.count(i) > 1})))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {'spec': args.spec, 'spec_version': spec['info']['version'],
               'context': CONTEXT, 'base_sale': BASE_SALE, 'count': len(cases), 'cases': cases}
    out.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + '\n',
                   encoding='utf-8')
    print(f'{len(cases)} cases -> {out}')


if __name__ == '__main__':
    main()
