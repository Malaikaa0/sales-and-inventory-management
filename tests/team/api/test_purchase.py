"""
POST /transactions/new-purchase/ (Executive), used to add stock to Item.quantity.

N2: requirement A1 says a purchase quantity is at most 100000; the app has no
    upper limit, so 2,147,483,648 (2**31, one past the 32-bit integer maximum)
    is accepted and added to stock.
N3: a purchase that fails form validation returns 200 (form shown again), not
    a 4xx. Documented as observed; the test checks nothing was saved.
"""
from conftest import create_item, first_option, post_form, stock

A1_MAX_PURCHASE_QTY = 100000
INT32_MAX = 2**31 - 1


def purchase(manager, item, quantity, status='S'):
    return post_form(manager, '/transactions/new-purchase/', {
        'item': item['id'],
        'vendor': first_option(manager, '/transactions/new-purchase/', 'vendor'),
        'quantity': quantity, 'price': '1.00', 'description': 'API test purchase',
        'delivery_date': '', 'delivery_status': status,
    })


def test_purchase_at_limit_is_accepted(manager):
    item = create_item(manager, quantity=46)
    response = purchase(manager, item, A1_MAX_PURCHASE_QTY)
    assert response.status_code == 302
    assert stock(manager, item) == 46 + A1_MAX_PURCHASE_QTY


def test_purchase_above_int32_rejected_N2(manager):
    item = create_item(manager, quantity=46)
    response = purchase(manager, item, INT32_MAX + 1)
    assert response.status_code != 302, (
        f'N2: quantity {INT32_MAX + 1} accepted (A1 max is {A1_MAX_PURCHASE_QTY}); '
        f'stock is now {stock(manager, item)}'
    )
    assert stock(manager, item) == 46


def test_purchase_validation_failure_returns_200_N3(manager):
    """Observed behaviour (N3): invalid form -> 200 with the form, not 4xx."""
    item = create_item(manager, quantity=46)
    response = purchase(manager, item, 0)
    assert response.status_code == 200
    assert 'quantity' in response.text.lower()
    assert stock(manager, item) == 46
