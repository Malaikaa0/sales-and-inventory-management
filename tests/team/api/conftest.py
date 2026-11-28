"""
Shared helpers for the API and integration tests.

These tests talk to a running server over HTTP (requests), not Django's test
client, so they see exactly what a browser or API client sees.

    $env:DEBUG="True"; $env:LOGIN_MAX_ATTEMPTS="1000"
    python manage.py runserver          # one window
    python -m pytest tests/team/api     # another window

Every test here is marked `api`; run the rest of the suite with -m "not api".
If the server cannot be reached, all api tests are skipped, not failed.
"""
import itertools
import os
import re
import time

import pytest
import requests

BASE_URL = os.environ.get('API_BASE_URL', 'http://127.0.0.1:8000').rstrip('/')
PASSWORD = os.environ.get('API_PASSWORD', 'demo-pass-123')
TIMEOUT = 30

CSRF_RE = re.compile(r'name="csrfmiddlewaretoken" value="([^"]+)"')
STOCK_RE = re.compile(r'<dt>In stock</dt>\s*<dd>([\d,]+)</dd>')
OPTION_RE = r'<select[^>]*name="{name}"[^>]*>(.*?)</select>'

_counter = itertools.count(1)
_RUN = format(int(time.time()) % 0xFFFFFF, 'x')


# --------------------------------------------------------------- pytest hooks
def pytest_configure(config):
    config.addinivalue_line('markers', 'api: needs a running server at API_BASE_URL')


def _server_up():
    try:
        requests.get(f'{BASE_URL}/accounts/login/', timeout=3)
        return True
    except requests.RequestException:
        return False


def pytest_collection_modifyitems(config, items):
    here = os.path.dirname(__file__)
    api_items = [i for i in items if str(i.fspath).startswith(here)]
    for item in api_items:
        item.add_marker(pytest.mark.api)
    if api_items and not _server_up():
        skip = pytest.mark.skip(reason=f'API server not reachable at {BASE_URL}')
        for item in api_items:
            item.add_marker(skip)


# --------------------------------------------------------------- helpers
def url(path):
    return BASE_URL + path


def csrf(session, path):
    """GET a page and return the csrfmiddlewaretoken in its HTML.
    (CSRF_COOKIE_HTTPONLY is on, so the token is read from the page.)"""
    response = session.get(url(path), timeout=TIMEOUT)
    match = CSRF_RE.search(response.text)
    assert match, f'No CSRF token on {path} (status {response.status_code})'
    return match.group(1)


def post_form(session, path, data, token_path=None, **kwargs):
    data = dict(data)
    data['csrfmiddlewaretoken'] = csrf(session, token_path or path)
    return session.post(url(path), data=data, headers={'Referer': url(path)},
                        allow_redirects=False, timeout=TIMEOUT, **kwargs)


def login(username):
    session = requests.Session()
    response = post_form(session, '/accounts/login/',
                         {'username': username, 'password': PASSWORD})
    assert response.status_code == 302, f'Login as {username} failed: {response.status_code}'
    return session


def post_sale(session, body, raw=None, content_type='application/json'):
    """POST to new-sale with a fresh token in X-CSRFToken."""
    token = csrf(session, '/transactions/new-sale/')
    headers = {'X-CSRFToken': token, 'Referer': url('/transactions/new-sale/'),
               'Content-Type': content_type}
    import json
    data = raw if raw is not None else json.dumps(body)
    return session.post(url('/transactions/new-sale/'), data=data, headers=headers,
                        allow_redirects=False, timeout=TIMEOUT)


def stock(session, item):
    """Stock from the product detail page; works at 0 too (get-items hides 0)."""
    response = session.get(url(f'/product/{item["slug"]}/'), timeout=TIMEOUT)
    assert response.status_code == 200, f'Product page {item["slug"]}: {response.status_code}'
    match = STOCK_RE.search(response.text)
    assert match, f'No "In stock" value on /product/{item["slug"]}/'
    return int(match.group(1).replace(',', ''))


def points(session, customer):
    data = session.get(url('/accounts/get_customers/'), params={'term': customer['name']},
                       timeout=TIMEOUT).json()
    match = [c for c in data['results'] if c['id'] == customer['id']]
    assert match, f'Customer {customer["name"]} not found'
    return match[0]['loyalty_points']


def first_option(session, page, name):
    html = session.get(url(page), timeout=TIMEOUT).text
    select = re.search(OPTION_RE.format(name=name), html, re.S)
    values = re.findall(r'<option value="(\d+)"', select.group(1)) if select else []
    assert values, f'No {name} options on {page}'
    return values[0]


def unique(prefix):
    return f'{prefix}-{_RUN}-{next(_counter)}'


def create_item(manager, quantity=100000, price='1.00'):
    """Create a product through the app's own form (Executive)."""
    name = unique('api-item')
    response = post_form(manager, '/new-product/', {
        'name': name, 'description': 'API test item',
        'category': first_option(manager, '/new-product/', 'category'),
        'vendor': first_option(manager, '/new-product/', 'vendor'),
        'quantity': quantity, 'price': price, 'expiring_date': '',
    })
    assert response.status_code == 302, f'Product create failed: {response.status_code}'
    slug = name  # lower-case letters, digits and hyphens: AutoSlugField keeps it as is
    html = manager.get(url(f'/product/{slug}/'), timeout=TIMEOUT)
    assert html.status_code == 200, f'Created product not at /product/{slug}/'
    found = manager.get(url('/get-items/'), params={'term': name}, timeout=TIMEOUT).json()
    ids = [i['id'] for i in found if i['name'] == name]
    item = {'name': name, 'slug': slug, 'price': price}
    if ids:
        item['id'] = ids[0]
    else:  # quantity 0 is hidden by get-items; fall back to the edit link
        item['id'] = int(re.search(r'/product/\d+|"id":\s*(\d+)', html.text).group(1))
    return item


def create_customer(session):
    """Create a customer through the app's own form; new customers have 0 points."""
    name = unique('apicust')
    response = post_form(session, '/accounts/customers/create/', {
        'first_name': name, 'last_name': 'Test', 'address': '', 'email': '', 'phone': '',
    })
    assert response.status_code == 302, f'Customer create failed: {response.status_code}'
    data = session.get(url('/accounts/get_customers/'), params={'term': name},
                       timeout=TIMEOUT).json()
    match = [c for c in data['results'] if c['label'].startswith(name)]
    assert len(match) == 1, f'Customer {name} not found after create'
    return {'id': match[0]['id'], 'name': name}


def fill(value, ids):
    """Replace generator placeholders such as "<item_id>" or "<item_id:str>"."""
    if isinstance(value, dict):
        return {k: fill(v, ids) for k, v in value.items()}
    if isinstance(value, list):
        return [fill(v, ids) for v in value]
    if isinstance(value, str) and value.startswith('<') and value.endswith('>'):
        key, _, form = value[1:-1].partition(':')
        if key in ids:
            return str(ids[key]) if form == 'str' else ids[key]
    return value


def sale_body(item, customer, quantity, amount_paid=1000000, **extra):
    body = {'customer': customer['id'], 'items': [{'id': item['id'], 'quantity': quantity}],
            'tax_percentage': 0, 'amount_paid': amount_paid, 'redeem_points': 0}
    body.update(extra)
    return body


def make_sale(cashier, item, customer, quantity, **extra):
    """Complete a sale and return its JSON; fails the test if it is rejected."""
    response = post_sale(cashier, sale_body(item, customer, quantity, **extra))
    assert response.status_code == 200, response.text[:300]
    return response.json()


VOID_TOKEN_PAGE = '/transactions/new-sale/'  # any page works; void pages are 403 for cashiers


def void(session, pk, reason='Customer returned all items', include_reason=True):
    data = {'reason': reason} if include_reason else {}
    return post_form(session, f'/transactions/sale/{pk}/void/', data, token_path=VOID_TOKEN_PAGE)


def sale_status(session, pk):
    """'Completed' or 'Voided', read back from the sale detail page."""
    html = session.get(url(f'/transactions/sale/{pk}/'), timeout=TIMEOUT).text
    match = re.search(r'<span class="status (?:ok|bad)">(\w+)</span>', html)
    assert match, f'No status on sale {pk}'
    return match.group(1)


def page_text(session, path):
    return session.get(url(path), timeout=TIMEOUT).text


# --------------------------------------------------------------- fixtures
@pytest.fixture(scope='session')
def manager():
    return login('manager')


@pytest.fixture(scope='session')
def cashier():
    return login('cashier')


@pytest.fixture
def item(manager):
    """Fresh item matching the generator context: price 1.00, stock 100000."""
    return create_item(manager)


@pytest.fixture
def customer(manager):
    """Fresh customer matching the generator context: 0 loyalty points."""
    return create_customer(manager)
