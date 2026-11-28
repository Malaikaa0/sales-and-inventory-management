"""
POST /transactions/sale/{pk}/void/ (Executive or higher).

Generated cases (reason length BVA, reason EP, pk EP) plus the state and
access rules (scope.md IDs): FR6/FR7 restore stock and points, FR9/BR4 no
second void, FR10/BR4 a cashier gets 403.
"""
import json
from pathlib import Path

import pytest

from conftest import make_sale, page_text, points, sale_status, stock, void

CASES_FILE = Path(__file__).resolve().parents[3] / 'tools' / 'generator' / 'out' / 'cases.json'
VOID_CASES = [c for c in json.loads(CASES_FILE.read_text(encoding='utf-8'))['cases']
              if c['endpoint'].endswith('/void/')]
QTY = 300  # 300 x 1.00 = 300.00 -> earns 3 points


@pytest.mark.parametrize('case', VOID_CASES, ids=[c['id'] for c in VOID_CASES])
def test_generated_void_case(case, manager, cashier, item, customer):
    sale = make_sale(cashier, item, customer, QTY)
    pk = sale['sale_id']
    if case['body']['pk'] == '<voided_sale_id>':
        assert void(manager, pk).status_code == 302
    ids = {'<sale_id>': pk, '<voided_sale_id>': pk, '<missing_sale_id>': 999999999}
    target = ids.get(case['body']['pk'], case['body']['pk'])
    before = stock(manager, item)

    response = void(manager, target, reason=case['body']['reason'] or '',
                    include_reason=not (case['field'] == 'reason' and case['value_missing']))

    assert response.status_code == case['expected_status'], response.text[:300]
    # Read the redirect page first: any later page view would consume the flash message.
    landing = page_text(manager, response.headers['Location']) if response.status_code == 302 else ''
    after = stock(manager, item)
    outcome = case['expected_outcome']
    if outcome == 'voided':
        assert response.headers['Location'] == f'/transactions/sale/{pk}/'
        assert sale_status(manager, pk) == 'Voided'
        assert after == before + QTY
    elif outcome == 'already-voided':
        assert 'already been voided' in landing
        assert after == before, 'stock added twice'
    else:  # invalid-form or not-found: nothing changes
        assert after == before
        assert sale_status(manager, pk) == 'Completed'


def test_void_restores_stock_and_points(manager, cashier, item, customer):
    make_sale(cashier, item, customer, 1000)                      # earns 10 points
    assert points(manager, customer) == 10
    sale = make_sale(cashier, item, customer, QTY, redeem_points=5)  # -5 + 2 earned
    assert points(manager, customer) == 7
    before = stock(manager, item)

    assert void(manager, sale['sale_id']).status_code == 302

    assert stock(manager, item) == before + QTY
    assert points(manager, customer) == 10
    assert sale_status(manager, sale['sale_id']) == 'Voided'


def test_second_void_rejected_and_stock_not_added_twice(manager, cashier, item, customer):
    sale = make_sale(cashier, item, customer, QTY)
    start = stock(manager, item)
    assert void(manager, sale['sale_id']).status_code == 302
    assert stock(manager, item) == start + QTY

    second = void(manager, sale['sale_id'])

    assert second.status_code == 302
    assert 'already been voided' in page_text(manager, second.headers['Location'])
    assert stock(manager, item) == start + QTY


def test_cashier_cannot_void(manager, cashier, item, customer):
    sale = make_sale(cashier, item, customer, QTY)
    before = stock(manager, item)

    response = void(cashier, sale['sale_id'])

    assert response.status_code == 403
    assert stock(manager, item) == before
    assert sale_status(manager, sale['sale_id']) == 'Completed'


def test_void_missing_sale_is_404(manager):
    assert void(manager, 999999999).status_code == 404
