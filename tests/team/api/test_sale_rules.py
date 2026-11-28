"""
Business rules of POST /transactions/new-sale/ (scope.md FR3, FR4, BR1, BR2, BR3).
Every rejection also checks that stock is unchanged (nothing saved).
"""
from conftest import create_item, make_sale, points, post_sale, sale_body, stock


def test_oversell_boundary_stock_equals_quantity_accepted(manager, cashier, customer):
    item = create_item(manager, quantity=5)
    response = post_sale(cashier, sale_body(item, customer, 5))
    assert response.status_code == 200, response.text
    assert stock(manager, item) == 0


def test_oversell_boundary_stock_one_below_quantity_rejected(manager, cashier, customer):
    item = create_item(manager, quantity=4)
    response = post_sale(cashier, sale_body(item, customer, 5))
    assert response.status_code == 400
    assert 'Not enough stock' in response.json()['message']
    assert stock(manager, item) == 4


def test_underpay_by_one_cent_rejected(manager, cashier, item, customer):
    before = stock(manager, item)
    response = post_sale(cashier, sale_body(item, customer, 3, amount_paid=2.99))
    assert response.status_code == 400
    assert 'is less than the total (3.00)' in response.json()['message']
    assert stock(manager, item) == before


def test_exact_payment_gives_zero_change(manager, cashier, item, customer):
    data = make_sale(cashier, item, customer, 3, amount_paid=3.00)
    assert data['grand_total'] == '3.00'
    assert data['change'] == '0.00'


def _customer_with_10_points(manager, cashier, item, customer):
    make_sale(cashier, item, customer, 1000)   # 1000.00 / 100 = 10 points
    assert points(manager, customer) == 10


def test_redeem_equal_to_balance_accepted(manager, cashier, item, customer):
    _customer_with_10_points(manager, cashier, item, customer)
    data = make_sale(cashier, item, customer, 50, redeem_points=10)
    assert data['grand_total'] == '40.00'
    assert points(manager, customer) == 0


def test_redeem_above_balance_rejected(manager, cashier, item, customer):
    _customer_with_10_points(manager, cashier, item, customer)
    before = stock(manager, item)
    response = post_sale(cashier, sale_body(item, customer, 50, redeem_points=11))
    assert response.status_code == 400
    assert 'only has 10 points' in response.json()['message']
    assert stock(manager, item) == before
    assert points(manager, customer) == 10


def test_redeem_equal_to_bill_accepted(manager, cashier, item, customer):
    _customer_with_10_points(manager, cashier, item, customer)
    data = make_sale(cashier, item, customer, 5, redeem_points=5, amount_paid=0)
    assert data['grand_total'] == '0.00'


def test_redeem_above_bill_rejected(manager, cashier, item, customer):
    _customer_with_10_points(manager, cashier, item, customer)
    before = stock(manager, item)
    response = post_sale(cashier, sale_body(item, customer, 5, redeem_points=6))
    assert response.status_code == 400
    assert 'cannot exceed the bill' in response.json()['message']
    assert stock(manager, item) == before


def test_merged_duplicate_lines_exceeding_stock_rejected(manager, cashier, customer):
    item = create_item(manager, quantity=5)
    body = sale_body(item, customer, 3)
    body['items'].append({'id': item['id'], 'quantity': 3})   # 3 + 3 = 6 > 5
    response = post_sale(cashier, body)
    assert response.status_code == 400
    assert 'Not enough stock' in response.json()['message']
    assert stock(manager, item) == 5
