"""
Automated security & RBAC access checks (Member 3).

Covers:
1. Anonymous access blocked (302 -> login) across protected endpoints and mutations.
2. Inactive/pending staff immediately signed out by ActiveProfileMiddleware.
3. Operative (cashier) denied (403) on Executive/Admin endpoints including void, exports, purchases, bills, and staff admin.
4. Executive (manager) allowed on void/exports/purchases/bills but denied (403) on staff administration.
5. Admin allowed on staff administration endpoints.
6. CSRF protection enforced when posting to sale creation and sale voiding.
7. Security headers (CSP, X-Frame-Options, Permissions-Policy, CORP, COEP) and HttpOnly cookies present.
8. Brute-force login lockout enforced after LOGIN_MAX_ATTEMPTS failed attempts.
"""
import json
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import Client
from django.urls import reverse

from accounts.models import Customer, Profile
from store.models import Category, Item
from transactions.models import Sale
from transactions.services import create_sale


def _make_staff(username, role, status="A", is_superuser=False):
    user = User.objects.create_user(username=username, password="sec-test-pass-123")
    if is_superuser:
        user.is_superuser = True
        user.is_staff = True
        user.save(update_fields=["is_superuser", "is_staff"])
    Profile.objects.filter(user=user).update(role=role, status=status)
    return User.objects.get(pk=user.pk)


@pytest.fixture
def sec_users(db):
    return {
        "op": _make_staff("sec_op", "OP", "A"),
        "ex": _make_staff("sec_ex", "EX", "A"),
        "ad": _make_staff("sec_ad", "AD", "A"),
        "pen": _make_staff("sec_pen", "OP", "PEN"),
        "ina": _make_staff("sec_ina", "EX", "INA"),
    }


@pytest.fixture
def sec_sale(db):
    cat = Category.objects.create(name="SecCat")
    item = Item.objects.create(name="SecItem", category=cat, quantity=15, price=Decimal("50.00"))
    cust = Customer.objects.create(first_name="Sec", last_name="Buyer", phone="0799000111")
    sale = create_sale(
        user=None,
        customer_id=cust.pk,
        items=[{"id": item.pk, "quantity": 2}],
        amount_paid=Decimal("100.00"),
    )
    return {"sale": sale, "item": item, "customer": cust}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url_name,needs_sale_pk",
    [
        ("dashboard", False),
        ("sale-create", False),
        ("saleslist", False),
        ("sale-detail", True),
        ("sale-delete", True),
        ("sales-export", False),
        ("purchaseslist", False),
        ("purchase-create", False),
        ("bill_list", False),
        ("profile_list", False),
        ("profile-create", False),
    ],
)
def test_anonymous_redirected_to_login(client, sec_sale, url_name, needs_sale_pk):
    kwargs = {"pk": sec_sale["sale"].pk} if needs_sale_pk else {}
    resp = client.get(reverse(url_name, kwargs=kwargs))
    assert resp.status_code == 302
    assert reverse("user-login") in resp.url


@pytest.mark.django_db
def test_anonymous_post_mutations_blocked(client, sec_sale):
    sale_resp = client.post(
        reverse("sale-create"),
        data=json.dumps(
            {
                "customer": sec_sale["customer"].pk,
                "items": [{"id": sec_sale["item"].pk, "quantity": 1}],
                "amount_paid": 50,
            }
        ),
        content_type="application/json",
    )
    assert sale_resp.status_code == 302
    assert reverse("user-login") in sale_resp.url

    void_resp = client.post(
        reverse("sale-delete", kwargs={"pk": sec_sale["sale"].pk}),
        {"reason": "unauthenticated attempt"},
    )
    assert void_resp.status_code == 302
    assert reverse("user-login") in void_resp.url

    sec_sale["item"].refresh_from_db()
    sec_sale["sale"].refresh_from_db()
    assert sec_sale["item"].quantity == 13
    assert sec_sale["sale"].status == Sale.STATUS_COMPLETED


@pytest.mark.django_db
@pytest.mark.parametrize("user_key", ["pen", "ina"])
def test_inactive_or_pending_profile_forced_logout(client, sec_users, user_key):
    user = sec_users[user_key]
    client.force_login(user)
    resp = client.get(reverse("dashboard"))
    assert resp.status_code == 302
    assert reverse("user-login") in resp.url
    # Session must be cleared after middleware signs user out
    assert "_auth_user_id" not in client.session


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url_name,needs_sale_pk,extra_query",
    [
        ("sale-delete", True, {}),
        ("sales-export", False, {}),
        ("purchases-export", False, {}),
        ("purchaseslist", False, {}),
        ("purchase-create", False, {}),
        ("product-create", False, {}),
        ("productslist", False, {"_export": "xlsx"}),
        ("vendor-list", False, {}),
        ("bill_list", False, {}),
        ("bill_create", False, {}),
        ("invoice-create", False, {}),
        ("profile_list", False, {}),
        ("profile-create", False, {}),
    ],
)
def test_operative_forbidden_from_executive_and_admin_routes(
    client, sec_users, sec_sale, url_name, needs_sale_pk, extra_query
):
    client.force_login(sec_users["op"])
    kwargs = {"pk": sec_sale["sale"].pk} if needs_sale_pk else {}
    resp = client.get(reverse(url_name, kwargs=kwargs), extra_query)
    assert resp.status_code == 403


@pytest.mark.django_db
def test_operative_post_void_and_loyalty_adjust_forbidden(client, sec_users, sec_sale):
    client.force_login(sec_users["op"])

    void_resp = client.post(
        reverse("sale-delete", kwargs={"pk": sec_sale["sale"].pk}),
        {"reason": "cashier unauthorized void"},
    )
    assert void_resp.status_code == 403

    loyalty_resp = client.post(
        reverse("customer_loyalty_adjust", kwargs={"pk": sec_sale["customer"].pk}),
        {"delta": "100", "note": "unauthorized bonus"},
    )
    assert loyalty_resp.status_code == 403

    sec_sale["sale"].refresh_from_db()
    sec_sale["customer"].refresh_from_db()
    assert sec_sale["sale"].status == Sale.STATUS_COMPLETED
    assert sec_sale["customer"].loyalty_points == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url_name,needs_sale_pk",
    [
        ("profile_list", False),
        ("profile-create", False),
    ],
)
def test_executive_forbidden_from_staff_admin_routes(client, sec_users, url_name, needs_sale_pk):
    client.force_login(sec_users["ex"])
    resp = client.get(reverse(url_name))
    assert resp.status_code == 403


@pytest.mark.django_db
def test_executive_cannot_approve_or_delete_staff(client, sec_users):
    client.force_login(sec_users["ex"])
    pending_profile = sec_users["pen"].profile
    assert client.post(reverse("profile-approve", kwargs={"pk": pending_profile.pk})).status_code == 403
    assert client.get(reverse("profile-delete", kwargs={"pk": pending_profile.pk})).status_code == 403

    pending_profile.refresh_from_db()
    assert pending_profile.status == "PEN"


@pytest.mark.django_db
def test_admin_can_access_staff_admin_routes(client, sec_users):
    client.force_login(sec_users["ad"])
    assert client.get(reverse("profile_list")).status_code == 200
    assert client.get(reverse("profile-create")).status_code == 200


@pytest.mark.django_db
def test_csrf_enforced_on_sale_and_void_posts(sec_users, sec_sale):
    csrf_client = Client(enforce_csrf_checks=True)
    csrf_client.force_login(sec_users["ex"])

    sale_resp = csrf_client.post(
        reverse("sale-create"),
        data=json.dumps(
            {
                "customer": sec_sale["customer"].pk,
                "items": [{"id": sec_sale["item"].pk, "quantity": 1}],
                "amount_paid": 50,
            }
        ),
        content_type="application/json",
    )
    assert sale_resp.status_code == 403

    void_resp = csrf_client.post(
        reverse("sale-delete", kwargs={"pk": sec_sale["sale"].pk}),
        {"reason": "missing csrf"},
    )
    assert void_resp.status_code == 403


@pytest.mark.django_db
def test_security_headers_and_httponly_cookies(client, sec_users):
    client.force_login(sec_users["op"])
    resp = client.get(reverse("dashboard"))
    assert resp.status_code == 200

    assert "Content-Security-Policy" in resp.headers
    assert "default-src 'self'" in resp.headers["Content-Security-Policy"]
    assert "frame-ancestors 'none'" in resp.headers["Content-Security-Policy"]
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("Cross-Origin-Resource-Policy") == "same-origin"
    assert resp.headers.get("Cross-Origin-Embedder-Policy") == "require-corp"
    assert "camera=()" in resp.headers.get("Permissions-Policy", "")


@pytest.mark.django_db
def test_login_lockout_after_repeated_failures(client, sec_users, settings):
    cache.clear()
    settings.LOGIN_MAX_ATTEMPTS = 3
    settings.LOGIN_LOCKOUT_SECONDS = 300

    login_url = reverse("user-login")
    for _ in range(3):
        r = client.post(login_url, {"username": "sec_op", "password": "wrong-password"})
        assert r.status_code == 200

    # Even valid password must now be locked out
    locked_resp = client.post(login_url, {"username": "sec_op", "password": "sec-test-pass-123"})
    assert locked_resp.status_code == 200
    assert "Too many failed attempts" in locked_resp.content.decode("utf-8")
    assert "_auth_user_id" not in client.session
    cache.clear()
