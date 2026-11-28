"""
Repeated requests. Assumption A3: sending the same sale request twice (for
example a double click or a client retry) records one sale, and stock goes
down once. Suspected defect N4: the endpoint has no idempotency key.
"""
import pytest

from conftest import post_sale, sale_body, stock


@pytest.mark.xfail(strict=True, reason='Known defect N4 — issue #4, open')
def test_same_sale_posted_twice_records_one_sale(manager, cashier, item, customer):
    body = sale_body(item, customer, 2)
    before = stock(manager, item)

    first = post_sale(cashier, body)
    second = post_sale(cashier, body)

    assert first.status_code == 200, first.text
    sale_ids = {first.json()['sale_id']}
    if second.status_code == 200:
        sale_ids.add(second.json()['sale_id'])
    assert len(sale_ids) == 1, f'duplicate sale recorded: {sorted(sale_ids)}'
    assert stock(manager, item) == before - 2, 'stock reduced more than once'
