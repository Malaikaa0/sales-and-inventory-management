import pytest
from decimal import Decimal
from django.utils import timezone
from django.core.exceptions import ValidationError
from accounts.models import Customer, Vendor
from store.models import Category, Delivery, InsufficientStock, Item
from transactions import loyalty
from transactions.models import LoyaltyTransaction, Purchase, Sale, SaleDetail
from transactions.services import create_sale


@pytest.fixture
def cfg(settings):
    settings.LOYALTY = {"enabled": True, "earn_per": "100", "point_value": "1.00", "min_redeem": 10}
    return settings


@pytest.fixture
def category(db):
    return Category.objects.create(name="Test")


@pytest.fixture
def item(db, category):
    return Item.objects.create(name="Keyboard", category=category, quantity=0, price=Decimal("100.00"))


@pytest.fixture
def item2(db, category):
    return Item.objects.create(name="Mouse", category=category, quantity=0, price=Decimal("50.00"))


@pytest.fixture
def vendor(db):
    return Vendor.objects.create(name="Acme")


@pytest.fixture
def customer(db):
    return Customer.objects.create(first_name="Ali", loyalty_points=0)


def order(item, vendor, qty, status="P", price="10.00"):
    return Purchase.objects.create(item=item, vendor=vendor, quantity=qty,
                                   price=Decimal(price), delivery_status=status)


def stock(item):
    item.refresh_from_db()
    return item.quantity


# ---------- Item / Category / Delivery ----------
@pytest.mark.django_db
def test_item_helpers(item, category):
    assert str(category) == "Test"
    assert str(item) == "Keyboard"
    assert item.get_absolute_url().startswith("/product/")
    assert item.in_stock is False
    Item.adjust_stock(item.pk, 3)
    item.refresh_from_db()
    assert item.in_stock is True
    data = item.to_json()
    assert data["stock"] == 3 and data["name"] == "Keyboard" and data["category"] == "Test"


@pytest.mark.django_db
def test_adjust_stock_zero_is_noop(item):
    Item.adjust_stock(item.pk, 0)
    assert stock(item) == 0


@pytest.mark.django_db
def test_adjust_stock_cannot_go_negative(item):
    Item.adjust_stock(item.pk, 5)
    with pytest.raises(InsufficientStock, match="Not enough stock"):
        Item.adjust_stock(item.pk, -6)
    assert stock(item) == 5
    Item.adjust_stock(item.pk, -5)          # exactly to zero is allowed
    assert stock(item) == 0


@pytest.mark.django_db
def test_delivery_str(item):
    d = Delivery.objects.create(item=item, customer_name="Sara", location="Isb", date=timezone.now())
    assert "Keyboard" in str(d) and "Sara" in str(d)


# ---------- Loyalty ----------
def test_points_for_amount(cfg):
    assert loyalty.points_for_amount(Decimal("399")) == 3
    assert loyalty.points_for_amount(Decimal("0")) == 0
    cfg.LOYALTY = {"enabled": False}
    assert loyalty.points_for_amount(Decimal("500")) == 0
    cfg.LOYALTY = {"enabled": True, "earn_per": "0"}
    assert loyalty.points_for_amount(Decimal("500")) == 0


def test_value_of_points(cfg):
    assert loyalty.value_of_points(20) == Decimal("20.00")


def test_max_redeemable(cfg):
    assert loyalty.max_redeemable(500, Decimal("100")) == 100   # limited by bill
    assert loyalty.max_redeemable(30, Decimal("100")) == 30     # limited by balance
    cfg.LOYALTY = {"enabled": False}
    assert loyalty.max_redeemable(500, Decimal("100")) == 0
    cfg.LOYALTY = {"enabled": True, "point_value": "0"}
    assert loyalty.max_redeemable(500, Decimal("100")) == 0


@pytest.mark.django_db
def test_apply_points(cfg, customer):
    assert loyalty.apply_points(customer.pk, 0, LoyaltyTransaction.ADJUST) is None
    row = loyalty.apply_points(customer.pk, 25, LoyaltyTransaction.ADJUST, note="bonus")
    customer.refresh_from_db()
    assert customer.loyalty_points == 25 and row.balance_after == 25
    assert "+25" in str(row)
    with pytest.raises(ValidationError, match="cannot remove"):
        loyalty.apply_points(customer.pk, -26, LoyaltyTransaction.ADJUST)
    customer.refresh_from_db()
    assert customer.loyalty_points == 25


# ---------- Sale models ----------
@pytest.mark.django_db
def test_sale_model_helpers(cfg, item, customer):
    Item.adjust_stock(item.pk, 10)
    s = create_sale(user=None, customer_id=customer.pk,
                    items=[{"id": item.pk, "quantity": 3}], amount_paid=1000)
    assert s.receipt_number == f"IMS{s.pk:06d}"
    assert Sale().receipt_number == ""
    assert s.is_voided is False
    assert s.sum_products() == 3
    assert "Sale IMS" in str(s)
    assert s.get_absolute_url() == f"/transactions/sale/{s.pk}/"
    assert "x 3" in str(SaleDetail.objects.get(sale=s))


# ---------- Purchase = Workflow 1 (receive stock) ----------
@pytest.mark.django_db
def test_pending_purchase_does_not_change_stock(item, vendor):
    p = order(item, vendor, 10)
    assert p.received is False and p.stock_applied == 0
    assert p.total_value == Decimal("100.00")
    assert stock(item) == 0
    assert str(p) == "Keyboard from Acme"


@pytest.mark.django_db
def test_successful_purchase_adds_stock(item, vendor):
    p = order(item, vendor, 10, status="S")
    assert p.received is True and p.stock_applied == 10
    assert stock(item) == 10


@pytest.mark.django_db
def test_pending_to_successful_and_back(item, vendor):
    p = order(item, vendor, 10)
    p.delivery_status = "S"
    p.save()
    assert stock(item) == 10
    p.delivery_status = "P"
    p.save()
    assert stock(item) == 0 and p.stock_applied == 0


@pytest.mark.django_db
def test_editing_quantity_adjusts_by_difference(item, vendor):
    p = order(item, vendor, 10, status="S")
    p.quantity = 15
    p.save()
    assert stock(item) == 15
    p.quantity = 4
    p.save()
    assert stock(item) == 4


@pytest.mark.django_db
def test_unreceive_rejected_when_stock_already_sold(cfg, item, vendor, customer):
    p = order(item, vendor, 10, status="S")
    create_sale(user=None, customer_id=customer.pk,
                items=[{"id": item.pk, "quantity": 8}], amount_paid=10000)
    assert stock(item) == 2
    p.delivery_status = "P"
    with pytest.raises(InsufficientStock):
        p.save()
    assert stock(item) == 2
    p.refresh_from_db()
    assert p.delivery_status == "S" and p.stock_applied == 10


@pytest.mark.django_db
def test_changing_item_moves_stock(item, item2, vendor):
    p = order(item, vendor, 6, status="S")
    p.item = item2
    p.save()
    assert stock(item) == 0 and stock(item2) == 6


@pytest.mark.django_db
def test_delete_purchase(item, vendor, cfg, customer):
    order(item, vendor, 5).delete()                    # pending: no change
    assert stock(item) == 0
    p = order(item, vendor, 5, status="S")
    p.delete()                                         # received: stock removed
    assert stock(item) == 0
    p2 = order(item, vendor, 5, status="S")
    create_sale(user=None, customer_id=customer.pk,
                items=[{"id": item.pk, "quantity": 4}], amount_paid=10000)
    with pytest.raises(InsufficientStock):
        p2.delete()
    assert stock(item) == 1 and Purchase.objects.filter(pk=p2.pk).exists()
