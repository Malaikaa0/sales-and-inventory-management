import json
import pytest
from decimal import Decimal
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.http import HttpResponse
from django.urls import reverse

from accounts.models import Customer, Profile, Vendor
from store.models import Category, Item
from transactions.models import Purchase, Sale
from transactions.services import create_sale


def make_user(username, role):
    u = User.objects.create_user(username, password="x")
    Profile.objects.filter(user=u).update(role=role, status="A")
    return User.objects.get(pk=u.pk)

@pytest.fixture
def cashier(db): return make_user("cashier_t", "OP")

@pytest.fixture
def manager(db): return make_user("manager_t", "EX")

@pytest.fixture
def item(db):
    c = Category.objects.create(name="Test")
    return Item.objects.create(name="Keyboard", category=c, quantity=10, price=Decimal("100.00"))

@pytest.fixture
def customer(db): return Customer.objects.create(first_name="Ali")

@pytest.fixture
def vendor(db): return Vendor.objects.create(name="Acme")

def stock(item):
    item.refresh_from_db()
    return item.quantity

def post_sale(client, payload, **kw):
    return client.post(reverse("sale-create"), data=json.dumps(payload),
                       content_type=kw.pop("content_type", "application/json"))

def sale_payload(item, customer, qty, **extra):
    return {"customer": customer.pk, "items": [{"id": item.pk, "quantity": qty}],
            "amount_paid": 100000, **extra}

def make_sale(item, customer, qty=4):
    return create_sale(user=None, customer_id=customer.pk,
                       items=[{"id": item.pk, "quantity": qty}], amount_paid=100000)

def purchase_data(item, vendor, qty, status, price="10.00"):
    return {"item": item.pk, "vendor": vendor.pk, "quantity": qty, "price": price,
            "description": "", "delivery_date": "", "delivery_status": status}

def msgs(response):
    return [str(m) for m in get_messages(response.wsgi_request)]


# ---------------- POST /transactions/new-sale/ (JSON API) ----------------
@pytest.mark.django_db
def test_sale_page_renders(client, cashier):
    client.force_login(cashier)
    assert client.get(reverse("sale-create")).status_code == 200

@pytest.mark.django_db
def test_sale_requires_login(client, item, customer):
    r = post_sale(client, sale_payload(item, customer, 1))
    assert r.status_code == 302 and "login" in r.url
    assert stock(item) == 10

@pytest.mark.django_db
def test_sale_success_updates_stock(client, cashier, item, customer):
    client.force_login(cashier)
    r = post_sale(client, sale_payload(item, customer, 4))
    body = r.json()
    assert r.status_code == 200 and body["status"] == "success"
    assert body["grand_total"] == "400.00"
    assert stock(item) == 6
    assert Sale.objects.get(pk=body["sale_id"]).status == Sale.STATUS_COMPLETED

@pytest.mark.django_db
def test_sale_oversell_rejected_and_stock_unchanged(client, cashier, item, customer):
    client.force_login(cashier)
    post_sale(client, sale_payload(item, customer, 4))
    r = post_sale(client, sale_payload(item, customer, 7))
    assert r.status_code == 400 and r.json()["status"] == "error"
    assert "Not enough stock" in r.json()["message"]
    assert stock(item) == 6 and Sale.objects.count() == 1

@pytest.mark.django_db
@pytest.mark.parametrize("body,ctype,text", [
    ("{}", "text/plain", "Expected a JSON request"),
    ("not json", "application/json", "Invalid JSON"),
    ("[1, 2]", "application/json", "Invalid request"),
    ("", "application/json", "at least one item"),
])
def test_sale_bad_requests(client, cashier, body, ctype, text):
    client.force_login(cashier)
    r = client.post(reverse("sale-create"), data=body, content_type=ctype)
    assert r.status_code == 400 and text in r.json()["message"]

@pytest.mark.django_db
def test_sale_unexpected_error_is_500(client, cashier, item, customer, monkeypatch):
    def boom(**kw): raise RuntimeError("db down")
    monkeypatch.setattr("transactions.views.create_sale", boom)
    client.force_login(cashier)
    r = post_sale(client, sale_payload(item, customer, 1))
    assert r.status_code == 500 and "could not be saved" in r.json()["message"]


# ---------------- sale pages ----------------
@pytest.mark.django_db
def test_sale_list_detail_and_search(client, cashier, item, customer):
    s = make_sale(item, customer)
    client.force_login(cashier)
    assert client.get(reverse("saleslist")).status_code == 200
    r = client.get(reverse("saleslist"), {"q": s.receipt_number})
    assert r.status_code == 200 and s in list(r.context["sales"])
    assert client.get(reverse("saleslist"), {"q": "Ali"}).status_code == 200
    assert client.get(reverse("sale-detail", kwargs={"pk": s.pk})).status_code == 200

@pytest.mark.django_db
def test_receipt_pdf(client, cashier, item, customer, monkeypatch):
    seen = {}
    def fake(template, context, **kw):
        seen.update(context=context, **kw)
        return HttpResponse(b"pdf")
    monkeypatch.setattr("transactions.views.render_pdf_response", fake)
    s = make_sale(item, customer)
    client.force_login(cashier)
    assert client.get(reverse("sale-receipt", kwargs={"pk": s.pk})).status_code == 200
    assert seen["download"] is False
    client.get(reverse("sale-receipt", kwargs={"pk": s.pk}), {"download": "1"})
    assert seen["download"] is True and seen["context"]["units"] == 4
    assert client.get(reverse("sale-receipt", kwargs={"pk": 99999})).status_code == 404


# ---------------- void (Executive only) ----------------
@pytest.mark.django_db
def test_void_forbidden_for_cashier(client, cashier, item, customer):
    s = make_sale(item, customer)
    client.force_login(cashier)
    url = reverse("sale-delete", kwargs={"pk": s.pk})
    assert client.get(url).status_code == 403
    assert client.post(url, {"reason": "x"}).status_code == 403
    s.refresh_from_db()
    assert s.status == Sale.STATUS_COMPLETED and stock(item) == 6

@pytest.mark.django_db
def test_void_flow(client, manager, item, customer):
    s = make_sale(item, customer)
    client.force_login(manager)
    url = reverse("sale-delete", kwargs={"pk": s.pk})
    assert client.get(url).status_code == 200
    r = client.post(url, {"reason": "customer returned"})
    assert r.status_code == 302
    s.refresh_from_db()
    assert s.status == Sale.STATUS_VOIDED and stock(item) == 10
    r2 = client.post(url, {"reason": "again"})                 # invalid transition
    assert r2.status_code == 302 and any("already been voided" in m for m in msgs(r2))
    assert stock(item) == 10

@pytest.mark.django_db
def test_void_requires_reason(client, manager, item, customer):
    s = make_sale(item, customer)
    client.force_login(manager)
    r = client.post(reverse("sale-delete", kwargs={"pk": s.pk}), {"reason": ""})
    assert r.status_code == 200
    s.refresh_from_db()
    assert s.status == Sale.STATUS_COMPLETED and stock(item) == 6


# ---------------- purchases (Executive only) ----------------
@pytest.mark.django_db
@pytest.mark.parametrize("name", ["purchaseslist", "purchase-create", "purchases-export", "sales-export"])
def test_purchase_pages_forbidden_for_cashier(client, cashier, name):
    client.force_login(cashier)
    assert client.get(reverse(name)).status_code == 403

@pytest.mark.django_db
def test_purchase_create_successful_adds_stock(client, manager, item, vendor):
    client.force_login(manager)
    assert client.get(reverse("purchase-create")).status_code == 200
    r = client.post(reverse("purchase-create"), purchase_data(item, vendor, 10, "S"))
    assert r.status_code == 302
    assert Purchase.objects.count() == 1 and stock(item) == 20

@pytest.mark.django_db
def test_purchase_create_pending_keeps_stock(client, manager, item, vendor):
    client.force_login(manager)
    client.post(reverse("purchase-create"), purchase_data(item, vendor, 10, "P"))
    assert Purchase.objects.count() == 1 and stock(item) == 10

@pytest.mark.django_db
@pytest.mark.parametrize("qty", [0, -1, "abc"])
def test_purchase_create_invalid_quantity(client, manager, item, vendor, qty):
    client.force_login(manager)
    r = client.post(reverse("purchase-create"), purchase_data(item, vendor, qty, "S"))
    assert r.status_code == 200 and Purchase.objects.count() == 0 and stock(item) == 10

@pytest.mark.django_db
def test_purchase_list_detail_search(client, manager, item, vendor):
    p = Purchase.objects.create(item=item, vendor=vendor, quantity=3, price=Decimal("5"), delivery_status="P")
    client.force_login(manager)
    assert client.get(reverse("purchaseslist")).status_code == 200
    r = client.get(reverse("purchaseslist"), {"q": "Acme"})
    assert p in list(r.context["purchases"])
    assert client.get(reverse("purchase-detail", kwargs={"pk": p.pk})).status_code == 200

@pytest.mark.django_db
def test_purchase_update_status_change(client, manager, item, vendor):
    p = Purchase.objects.create(item=item, vendor=vendor, quantity=5, price=Decimal("5"), delivery_status="P")
    client.force_login(manager)
    url = reverse("purchase-update", kwargs={"pk": p.pk})
    assert client.get(url).status_code == 200
    client.post(url, purchase_data(item, vendor, 5, "S"))
    assert stock(item) == 15
    client.post(url, purchase_data(item, vendor, 5, "P"))
    assert stock(item) == 10

@pytest.mark.django_db
def test_purchase_update_rejected_when_stock_sold(client, manager, item, customer, vendor):
    p = Purchase.objects.create(item=item, vendor=vendor, quantity=5, price=Decimal("5"), delivery_status="S")
    make_sale(item, customer, qty=14)                         # stock 15 -> 1
    client.force_login(manager)
    r = client.post(reverse("purchase-update", kwargs={"pk": p.pk}), purchase_data(item, vendor, 5, "P"))
    assert r.status_code == 200                               # form re-shown with an error
    p.refresh_from_db()
    assert p.delivery_status == "S" and stock(item) == 1

@pytest.mark.django_db
def test_purchase_delete(client, manager, item, customer, vendor):
    p = Purchase.objects.create(item=item, vendor=vendor, quantity=5, price=Decimal("5"), delivery_status="S")
    client.force_login(manager)
    url = reverse("purchase-delete", kwargs={"pk": p.pk})
    assert client.get(url).status_code == 200
    r = client.post(url)
    assert r.status_code == 302 and not Purchase.objects.filter(pk=p.pk).exists()
    assert stock(item) == 10

@pytest.mark.django_db
def test_purchase_delete_blocked_when_stock_sold(client, manager, item, customer, vendor):
    p = Purchase.objects.create(item=item, vendor=vendor, quantity=5, price=Decimal("5"), delivery_status="S")
    make_sale(item, customer, qty=14)
    client.force_login(manager)
    r = client.post(reverse("purchase-delete", kwargs={"pk": p.pk}))
    assert r.status_code == 302 and Purchase.objects.filter(pk=p.pk).exists()
    assert any("Not enough stock" in m for m in msgs(r)) and stock(item) == 1


# ---------------- exports ----------------
@pytest.mark.django_db
def test_exports_for_manager(client, manager, item, customer, vendor):
    make_sale(item, customer)
    Purchase.objects.create(item=item, vendor=vendor, quantity=1, price=Decimal("1"), delivery_status="P")
    client.force_login(manager)
    for name in ("sales-export", "purchases-export"):
        r = client.get(reverse(name))
        assert r.status_code == 200 and "spreadsheetml" in r["Content-Type"]
