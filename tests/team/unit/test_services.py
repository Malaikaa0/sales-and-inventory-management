import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from accounts.models import Customer
from store.models import Category, Item
from transactions.models import Sale
from transactions.services import create_sale, parse_lines, void_sale


@pytest.fixture
def loyalty(settings):
    settings.LOYALTY = {"enabled": True, "earn_per": "100", "point_value": "1.00", "min_redeem": 10}
    return settings

@pytest.fixture
def item(db):
    cat = Category.objects.create(name="Test")
    return Item.objects.create(name="Keyboard", category=cat, quantity=10, price=Decimal("100.00"))

@pytest.fixture
def customer(db):
    return Customer.objects.create(first_name="Ali", loyalty_points=0)

def sell(customer, item, qty, **kw):
    kw.setdefault("amount_paid", 1000000)
    return create_sale(user=None, customer_id=customer.pk,
                       items=[{"id": item.pk, "quantity": qty}], **kw)


# ---- number parsing (no DB) ----
@pytest.mark.parametrize("bad", ["abc", 1.5, None])
def test_non_whole_quantity_rejected(bad):
    with pytest.raises(ValidationError):
        parse_lines([{"id": 1, "quantity": bad}])

def test_whole_number_float_is_rejected_current_behaviour():
    # Documents current behaviour: JSON 2.0 is rejected. Candidate defect.
    with pytest.raises(ValidationError):
        parse_lines([{"id": 1, "quantity": 2.0}])


# ---- stock: below / at / above the limit ----
@pytest.mark.django_db
@pytest.mark.parametrize("qty,ok", [(9, True), (10, True), (11, False)])
def test_stock_boundary(loyalty, item, customer, qty, ok):
    if ok:
        sell(customer, item, qty)
        item.refresh_from_db()
        assert item.quantity == 10 - qty
    else:
        with pytest.raises(ValidationError, match="Not enough stock"):
            sell(customer, item, qty)
        item.refresh_from_db()
        assert item.quantity == 10
        assert Sale.objects.count() == 0

@pytest.mark.django_db
def test_sale_reduces_stock_and_totals(loyalty, item, customer):
    s = sell(customer, item, 4)
    item.refresh_from_db()
    assert item.quantity == 6
    assert s.grand_total == Decimal("400.00")
    assert s.status == Sale.STATUS_COMPLETED

@pytest.mark.django_db
def test_unknown_customer_and_item(loyalty, item, customer):
    with pytest.raises(ValidationError):
        create_sale(user=None, customer_id=999999, items=[{"id": item.pk, "quantity": 1}], amount_paid=1000)
    with pytest.raises(ValidationError):
        create_sale(user=None, customer_id=None, items=[{"id": item.pk, "quantity": 1}], amount_paid=1000)
    with pytest.raises(ValidationError, match="no longer exist"):
        create_sale(user=None, customer_id=customer.pk, items=[{"id": 999999, "quantity": 1}], amount_paid=1000)


# ---- tax and payment limits ----
@pytest.mark.django_db
@pytest.mark.parametrize("tax,ok", [(-1, False), (0, True), (100, True), ("100.01", False), ("abc", False), ("nan", False)])
def test_tax_limits(loyalty, item, customer, tax, ok):
    if ok:
        sell(customer, item, 1, tax_percentage=tax)
    else:
        with pytest.raises(ValidationError):
            sell(customer, item, 1, tax_percentage=tax)

@pytest.mark.django_db
@pytest.mark.parametrize("paid,ok", [("99.99", False), ("100.00", True), ("100.01", True), (-1, False)])
def test_amount_paid_limit(loyalty, item, customer, paid, ok):
    if ok:
        sell(customer, item, 1, amount_paid=paid)
    else:
        with pytest.raises(ValidationError):
            sell(customer, item, 1, amount_paid=paid)


# ---- loyalty redemption: decision with several conditions ----
@pytest.mark.django_db
def test_redeem_negative_rejected(loyalty, item, customer):
    with pytest.raises(ValidationError):
        sell(customer, item, 1, redeem_points=-1)

@pytest.mark.django_db
def test_redeem_when_disabled_rejected(settings, item, customer):
    settings.LOYALTY = {"enabled": False}
    with pytest.raises(ValidationError, match="not enabled"):
        sell(customer, item, 1, redeem_points=10)

@pytest.mark.django_db
@pytest.mark.parametrize("points,ok", [
    (5, False),     # below minimum redeem
    (60, False),    # more than the customer's balance (50)
    (20, True),     # valid
])
def test_redeem_conditions(loyalty, item, customer, points, ok):
    customer.loyalty_points = 50
    customer.save()
    if ok:
        s = sell(customer, item, 1, redeem_points=points)
        assert s.discount_amount == Decimal("20.00")
    else:
        with pytest.raises(ValidationError):
            sell(customer, item, 1, redeem_points=points)

@pytest.mark.django_db
def test_redeem_more_than_bill_rejected(loyalty, item, customer):
    customer.loyalty_points = 500
    customer.save()
    with pytest.raises(ValidationError, match="exceed the bill"):
        sell(customer, item, 1, redeem_points=101)   # bill is 100.00
    sell(customer, item, 1, redeem_points=100)       # exactly the bill is allowed


# ---- void: allowed change and disallowed change ----
@pytest.mark.django_db
def test_void_restores_stock_and_cannot_repeat(loyalty, item, customer):
    s = sell(customer, item, 4)
    void_sale(s, user=None, reason="test")
    item.refresh_from_db()
    s.refresh_from_db()
    assert item.quantity == 10
    assert s.status == Sale.STATUS_VOIDED
    with pytest.raises(ValidationError, match="already been voided"):
        void_sale(s, user=None)
    item.refresh_from_db()
    assert item.quantity == 10

@pytest.mark.django_db
def test_void_when_earned_points_already_spent(loyalty, item, customer):
    s = sell(customer, item, 4)                 # earns 4 points
    Customer.objects.filter(pk=customer.pk).update(loyalty_points=0)
    void_sale(s, user=None)
    customer.refresh_from_db()
    assert customer.loyalty_points == 0
