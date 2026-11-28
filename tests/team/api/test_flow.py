"""
End-to-end integration scenario on the shared record Item.quantity:
stock 10 -> sell 4 -> 6 -> sell 7 rejected -> still 6 -> void the first sale -> 10.
"""
from conftest import create_item, post_sale, sale_body, sale_status, stock, void


def test_sell_reject_void_flow(manager, cashier, customer):
    item = create_item(manager, quantity=10)
    assert stock(manager, item) == 10

    first = post_sale(cashier, sale_body(item, customer, 4))
    assert first.status_code == 200, first.text
    assert stock(manager, item) == 6

    rejected = post_sale(cashier, sale_body(item, customer, 7))
    assert rejected.status_code == 400
    assert 'Not enough stock' in rejected.json()['message']
    assert stock(manager, item) == 6

    sale_id = first.json()['sale_id']
    assert void(manager, sale_id).status_code == 302
    assert sale_status(manager, sale_id) == 'Voided'
    assert stock(manager, item) == 10
