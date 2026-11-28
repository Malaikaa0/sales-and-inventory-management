"""
Access to the sale API (BR4): an anonymous client is sent to the login page
and no sale is recorded.
"""
import json

import requests

from conftest import TIMEOUT, csrf, sale_body, stock, url


def test_anonymous_new_sale_redirects_to_login_and_saves_nothing(manager, item, customer):
    anonymous = requests.Session()
    token = csrf(anonymous, '/accounts/login/')   # valid CSRF, so only the login check can stop it
    before = stock(manager, item)

    response = anonymous.post(
        url('/transactions/new-sale/'), data=json.dumps(sale_body(item, customer, 1)),
        headers={'X-CSRFToken': token, 'Content-Type': 'application/json',
                 'Referer': url('/transactions/new-sale/')},
        allow_redirects=False, timeout=TIMEOUT,
    )

    assert response.status_code == 302
    assert response.headers['Location'].startswith('/accounts/login/')
    assert stock(manager, item) == before
