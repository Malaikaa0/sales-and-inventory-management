"""
Status codes, content types and response properties from openapi/openapi.yaml
that the workflow tests do not reach. See docs/api-coverage.md.

Not reachable (explained in docs/api-coverage.md):
  403 on new-sale, get-items and get_customers: every logged-in active member has
  at least the Operative role, and ActiveProfileMiddleware logs inactive users
  out (302) before the view runs.
"""
import re

import pytest
import requests

from conftest import (TIMEOUT, csrf, make_sale, post_form, post_sale, sale_body, stock, url,
                      VOID_TOKEN_PAGE)

MONEY = re.compile(r'^-?\d+\.\d{2}$')
BIG_ID = 2**63  # one past SQLite's 64-bit INTEGER


@pytest.fixture
def anonymous():
    return requests.Session()


def get(session, path, **kw):
    return session.get(url(path), allow_redirects=False, timeout=TIMEOUT, **kw)


def assert_login_redirect(response):
    assert response.status_code == 302
    assert response.headers['Location'].startswith('/accounts/login/')


# ---------------------------------------------------------------- new-sale
def test_sale_success_has_every_property(manager, cashier, item, customer):
    response = post_sale(cashier, sale_body(item, customer, 300, amount_paid=500))
    assert response.status_code == 200
    assert response.headers['Content-Type'].startswith('application/json')
    data = response.json()
    assert set(data) == {'status', 'message', 'sale_id', 'receipt_number', 'grand_total',
                         'change', 'points_earned', 'redirect', 'receipt_url'}
    assert data['status'] == 'success'
    assert data['receipt_number'] == f'IMS{data["sale_id"]:06d}'
    assert data['message'] == f'Sale {data["receipt_number"]} completed.'
    assert data['grand_total'] == '300.00' and MONEY.match(data['grand_total'])
    assert data['change'] == '200.00' and MONEY.match(data['change'])
    assert data['points_earned'] == 3                      # 300.00 / 100
    assert data['redirect'] == f'/transactions/sale/{data["sale_id"]}/'
    assert data['receipt_url'] == f'/transactions/sale/{data["sale_id"]}/receipt.pdf'


@pytest.mark.parametrize('raw, content_type, message', [
    ('{"customer": 1}', 'text/plain', 'Expected a JSON request.'),
    ('{not json', 'application/json', 'Invalid JSON in request body.'),
    ('[1, 2]', 'application/json', 'Invalid request.'),
], ids=['wrong-content-type', 'invalid-json', 'not-an-object'])
def test_request_level_400(manager, cashier, item, raw, content_type, message):
    before = stock(manager, item)
    response = post_sale(cashier, None, raw=raw, content_type=content_type)
    assert response.status_code == 400
    assert response.json() == {'status': 'error', 'message': message}
    assert stock(manager, item) == before


def test_customer_id_beyond_64_bit_is_rejected_cleanly(manager, cashier, item, customer):
    """Django guards the single pk= lookup: out-of-range id -> not found -> 400."""
    body = sale_body(item, customer, 1)
    body['customer'] = BIG_ID
    before = stock(manager, item)
    response = post_sale(cashier, body)
    assert response.status_code == 400
    assert response.json() == {'status': 'error', 'message': 'Select a valid customer.'}
    assert stock(manager, item) == before


def test_item_id_beyond_64_bit_gives_500_and_saves_nothing(manager, cashier, item, customer):
    """500 path (views.py:223-225). Item ids go through pk__in, which SQLite cannot
    bind above 2**63-1 (OverflowError), inside the rolled-back transaction, so the
    request is safe. By requirement this should be 400 "One or more items no longer
    exist." (unknown item); logged as N6."""
    body = sale_body(item, customer, 1)
    body['items'].append({'id': BIG_ID, 'quantity': 1})
    before = stock(manager, item)
    response = post_sale(cashier, body)
    assert response.status_code == 500
    assert response.json() == {'status': 'error',
                               'message': 'The sale could not be saved. Please try again.'}
    assert stock(manager, item) == before


# ---------------------------------------------------------------- void
def test_void_anonymous_redirects_to_login(manager, cashier, item, customer, anonymous):
    pk = make_sale(cashier, item, customer, 1)['sale_id']
    token = csrf(anonymous, '/accounts/login/')
    response = anonymous.post(url(f'/transactions/sale/{pk}/void/'),
                              data={'reason': 'x', 'csrfmiddlewaretoken': token},
                              headers={'Referer': url('/accounts/login/')},
                              allow_redirects=False, timeout=TIMEOUT)
    assert_login_redirect(response)


def test_void_confirm_page(manager, cashier, item, customer, anonymous):
    pk = make_sale(cashier, item, customer, 1)['sale_id']
    page = get(manager, f'/transactions/sale/{pk}/void/')
    assert page.status_code == 200
    assert page.headers['Content-Type'].startswith('text/html')
    assert 'name="reason"' in page.text
    assert get(cashier, f'/transactions/sale/{pk}/void/').status_code == 403
    assert_login_redirect(get(anonymous, f'/transactions/sale/{pk}/void/'))
    assert get(manager, '/transactions/sale/999999999/void/').status_code == 404


def test_void_invalid_form_returns_html_form(manager, cashier, item, customer):
    pk = make_sale(cashier, item, customer, 1)['sale_id']
    response = post_form(manager, f'/transactions/sale/{pk}/void/', {'reason': ''},
                         token_path=VOID_TOKEN_PAGE)
    assert response.status_code == 200
    assert response.headers['Content-Type'].startswith('text/html')
    assert 'name="reason"' in response.text


# ---------------------------------------------------------------- sale detail
def test_sale_detail_status_codes(manager, cashier, item, customer, anonymous):
    pk = make_sale(cashier, item, customer, 1)['sale_id']
    page = get(cashier, f'/transactions/sale/{pk}/')
    assert page.status_code == 200
    assert page.headers['Content-Type'].startswith('text/html')
    assert_login_redirect(get(anonymous, f'/transactions/sale/{pk}/'))
    assert get(cashier, '/transactions/sale/999999999/').status_code == 404


# ---------------------------------------------------------------- search endpoints
def test_get_items_properties_and_codes(manager, cashier, item, anonymous):
    response = get(cashier, '/get-items/', params={'term': item['name']})
    assert response.status_code == 200
    assert response.headers['Content-Type'].startswith('application/json')
    [found] = response.json()
    assert found == {'id': item['id'], 'text': item['name'], 'name': item['name'],
                     'category': found['category'], 'price': '1.00', 'stock': 100000,
                     'quantity': 1, 'total_item': '1.00'}
    assert isinstance(found['category'], str) and found['category']
    assert len(get(cashier, '/get-items/').json()) <= 20
    assert_login_redirect(get(anonymous, '/get-items/'))
    token = csrf(cashier, '/transactions/new-sale/')
    post = cashier.post(url('/get-items/'), data={'csrfmiddlewaretoken': token},
                        headers={'Referer': url('/get-items/')}, timeout=TIMEOUT)
    assert post.status_code == 405


def test_get_customers_properties_and_codes(manager, cashier, customer, anonymous):
    response = get(cashier, '/accounts/get_customers/', params={'term': customer['name']})
    assert response.status_code == 200
    assert response.headers['Content-Type'].startswith('application/json')
    [found] = response.json()['results']
    full_name = f'{customer["name"]} Test'
    assert found == {'id': customer['id'], 'text': full_name, 'label': full_name,
                     'value': customer['id'], 'phone': '', 'loyalty_points': 0}
    assert_login_redirect(get(anonymous, '/accounts/get_customers/'))
    token = csrf(cashier, '/transactions/new-sale/')
    post = cashier.post(url('/accounts/get_customers/'), data={'csrfmiddlewaretoken': token},
                        headers={'Referer': url('/accounts/get_customers/')}, timeout=TIMEOUT)
    assert post.status_code == 405


# ---------------------------------------------------------------- login
def test_login_page_and_failed_login(anonymous):
    page = get(anonymous, '/accounts/login/')
    assert page.status_code == 200
    assert page.headers['Content-Type'].startswith('text/html')
    response = post_form(anonymous, '/accounts/login/',
                         {'username': 'no-such-user-api', 'password': 'wrong'})
    assert response.status_code == 200
    assert response.headers['Content-Type'].startswith('text/html')
    assert 'sessionid' not in anonymous.cookies
