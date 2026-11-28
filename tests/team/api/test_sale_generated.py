"""
Generated EP + 3-point BVA cases for POST /transactions/new-sale/.

Cases come from tools/generator/out/cases.json (generated from openapi/openapi.yaml).
For each case: send the body as the cashier, check status, the JSON status
field, the outcome and message, then read the item's stock back:
unchanged when rejected, minus the total quantity when accepted.
"""
import json
from pathlib import Path

import pytest

from conftest import fill, post_sale, stock, points

CASES_FILE = Path(__file__).resolve().parents[3] / 'tools' / 'generator' / 'out' / 'cases.json'
DATA = json.loads(CASES_FILE.read_text(encoding='utf-8'))
SALE_CASES = [c for c in DATA['cases'] if c['endpoint'].endswith('/new-sale/')]


def sold_quantity(body):
    return sum(int(line['quantity']) for line in body['items'])


@pytest.mark.parametrize('case', SALE_CASES, ids=[c['id'] for c in SALE_CASES])
def test_generated_sale_case(case, cashier, manager, item, customer):
    body = fill(case['body'], {'item_id': item['id'], 'customer_id': customer['id']})
    before = stock(manager, item)
    assert before == DATA['context']['item_stock']

    response = post_sale(cashier, body)

    assert response.status_code == case['expected_status'], (
        f'{case["id"]}: expected {case["expected_status"]}, got {response.status_code}: '
        f'{response.text[:300]}'
    )
    payload = response.json()
    after = stock(manager, item)

    if case['expected_outcome'] == 'accepted':
        assert payload['status'] == 'success'
        assert isinstance(payload['sale_id'], int)
        assert after == before - sold_quantity(body), 'stock not reduced by the sold quantity'
    else:
        assert payload['status'] == 'error'
        if case['expected_message']:
            assert case['expected_message'] in payload['message'], payload['message']
        assert after == before, 'stock changed although the sale was rejected'
        assert points(manager, customer) == DATA['context']['customer_points']
