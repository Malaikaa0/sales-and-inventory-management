"""Tests written for mutants that survived the first Cosmic Ray session. See docs/mutation.md."""
from datetime import datetime
from decimal import Decimal

import pytest
from django.contrib.auth.models import AnonymousUser, User
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from accounts.models import Customer, Profile
from accounts.permissions import capability_required, is_active_member, role_required
from store.forms import ItemForm
from store.models import Category, Delivery, InsufficientStock, Item
from transactions import loyalty
from transactions.models import LoyaltyTransaction
from transactions.services import create_sale, parse_lines, void_sale


def set_loyalty(settings, **changes):
    settings.LOYALTY = {'enabled': True, 'earn_per': '100', 'point_value': '1.00', 'min_redeem': 10, **changes}


@pytest.fixture
def category(db):
    return Category.objects.create(name='Test')


@pytest.fixture
def item(category):
    return Item.objects.create(name='Keyboard', category=category, quantity=50, price=Decimal('100.00'))


@pytest.fixture
def customer(db):
    return Customer.objects.create(first_name='Ali')


def sell(customer, item, quantity=1, **extra):
    extra.setdefault('amount_paid', 100000)
    return create_sale(user=extra.pop('user', None), customer_id=customer.pk,
                       items=[{'id': item.pk, 'quantity': quantity}], **extra)


def points(customer):
    customer.refresh_from_db()
    return customer.loyalty_points


# ---------- totals, change and amount paid ----------
def test_totals_and_change_with_tax(settings, customer, item):
    set_loyalty(settings)
    sale = sell(customer, item, 2, tax_percentage=16, amount_paid=250)
    assert (sale.sub_total, sale.tax_amount, sale.grand_total, sale.amount_change) == (
        Decimal('200.00'), Decimal('32.00'), Decimal('232.00'), Decimal('18.00'))


def test_tax_keeps_the_fraction(customer, item):
    sale = sell(customer, item, tax_percentage='12.5')
    assert (sale.tax_amount, sale.grand_total) == (Decimal('12.50'), Decimal('112.50'))


@pytest.mark.parametrize('amount', [-1, '-0.50'])
def test_negative_amount_paid_is_named(customer, item, amount):
    with pytest.raises(ValidationError, match='cannot be negative'):
        sell(customer, item, amount_paid=amount)


@pytest.mark.parametrize('extra', [{}, {'amount_paid': None}, {'amount_paid': 0}])
def test_free_item_needs_no_payment(customer, category, extra):
    free = Item.objects.create(name='Leaflet', category=category, quantity=5, price=Decimal('0.00'))
    sale = create_sale(user=None, customer_id=customer.pk, items=[{'id': free.pk, 'quantity': 1}], **extra)
    assert (sale.amount_paid, sale.amount_change) == (Decimal('0.00'), Decimal('0.00'))


def test_payment_below_one_unit(customer, category):
    cheap = Item.objects.create(name='Clip', category=category, quantity=5, price=Decimal('0.50'))
    assert sell(customer, cheap, amount_paid='0.50').amount_change == Decimal('0.00')


# ---------- redemption limits ----------
def test_negative_redemption_is_named(settings, customer, item):
    set_loyalty(settings)
    with pytest.raises(ValidationError, match='cannot be negative'):
        sell(customer, item, redeem_points=-1)


@pytest.mark.parametrize('redeem, accepted', [(9, False), (10, True), (11, True)])
def test_minimum_redemption_boundary(settings, customer, item, redeem, accepted):
    set_loyalty(settings)
    Customer.objects.filter(pk=customer.pk).update(loyalty_points=50)
    if accepted:
        assert sell(customer, item, redeem_points=redeem).loyalty_points_redeemed == redeem
    else:
        with pytest.raises(ValidationError, match='at least'):
            sell(customer, item, redeem_points=redeem)


# ---------- earning and reversing points ----------
def test_sale_adds_earned_points_to_ledger(settings, customer, item):
    set_loyalty(settings)
    sale = sell(customer, item, 4)
    assert points(customer) == 4
    assert list(sale.loyalty_transactions.values_list('kind', 'points')) == [(LoyaltyTransaction.EARN, 4)]


@pytest.mark.parametrize('quantity, balance_before_void, expected', [
    (4, 4, 0),    # exactly the earned points left
    (4, 10, 6),   # more than enough: only the earned points are taken
    (4, 3, 0),    # one short of the earned points
    (4, 2, 0),    # partly spent
    (1, 0, 0),    # earned one point, already spent
])
def test_void_takes_back_only_what_it_should(settings, customer, item, quantity, balance_before_void, expected):
    set_loyalty(settings)
    sale = sell(customer, item, quantity)
    Customer.objects.filter(pk=customer.pk).update(loyalty_points=balance_before_void)
    void_sale(sale, user=None)
    assert points(customer) == expected


def test_void_with_points_redeemed_and_earned(settings, customer, item):
    set_loyalty(settings)
    Customer.objects.filter(pk=customer.pk).update(loyalty_points=100)
    sale = sell(customer, item, 5, redeem_points=100)    # pays 400, earns 4
    assert points(customer) == 4
    void_sale(sale, user=None)
    assert points(customer) == 100


@pytest.mark.parametrize('length, stored', [(0, 0), (6, 6), (200, 200), (201, 200)])
def test_void_reason_is_stored_and_cut_at_200(customer, item, length, stored):
    sale = void_sale(sell(customer, item), user=None, reason='r' * length)
    sale.refresh_from_db()
    assert sale.void_reason == 'r' * stored


def test_void_sale_takes_user_by_name_only(customer, item):
    sale = sell(customer, item)
    with pytest.raises(TypeError):
        void_sale(sale, None)
    with pytest.raises(TypeError):
        loyalty.apply_points(customer.pk, 1, LoyaltyTransaction.ADJUST, None)


# ---------- anonymous users are not recorded ----------
def test_anonymous_user_is_not_recorded(settings, customer, item):
    set_loyalty(settings)
    sale = sell(customer, item, user=AnonymousUser())
    assert sale.served_by is None
    assert sale.loyalty_transactions.get().created_by is None
    assert void_sale(sale, user=AnonymousUser()).voided_by is None


# ---------- cart validation ----------
def test_line_without_id_is_rejected():
    with pytest.raises(ValidationError, match='needs an id and a quantity'):
        parse_lines([{'quantity': 1}])


# ---------- loyalty configuration and arithmetic ----------
def test_loyalty_defaults(settings):
    settings.LOYALTY = {}
    assert loyalty.config() == {
        'enabled': True, 'earn_per': Decimal('100'), 'point_value': Decimal('1.00'), 'min_redeem': 0}


def test_point_value_other_than_one(settings):
    set_loyalty(settings, point_value='0.50')
    assert loyalty.value_of_points(10) == Decimal('5.00')
    assert loyalty.max_redeemable(1000, Decimal('100')) == 200
    assert loyalty.max_redeemable(0, Decimal('100')) == 0


@pytest.mark.parametrize('earn_per, amount, expected', [
    ('1', '1', 1), ('1', '5', 5), ('-100', '500', 0), ('100', '-50', 0), ('100', '-0.50', 0),
])
def test_points_for_amount_edges(settings, earn_per, amount, expected):
    set_loyalty(settings, earn_per=earn_per)
    assert loyalty.points_for_amount(Decimal(amount)) == expected


def test_points_error_and_note_length(customer):
    Customer.objects.filter(pk=customer.pk).update(loyalty_points=25)
    with pytest.raises(ValidationError, match=r'cannot remove 26\.'):
        loyalty.apply_points(customer.pk, -26, LoyaltyTransaction.ADJUST)
    row = loyalty.apply_points(customer.pk, 1, LoyaltyTransaction.ADJUST, note='n' * 201)
    assert row.note == 'n' * 200


# ---------- permissions ----------
def test_blank_status_is_not_active(db):
    user = User.objects.create_user('blank', password='x')
    Profile.objects.filter(user=user).update(status='')
    assert is_active_member(User.objects.get(pk=user.pk)) is False


@pytest.mark.parametrize('decorator', [role_required('OP'), capability_required('sales.create')])
def test_guard_decorators_keep_the_view_name(decorator):
    def my_view(request):
        """Doc."""

    wrapped = decorator(my_view)
    assert (wrapped.__name__, wrapped.__doc__) == ('my_view', 'Doc.')


# ---------- stock ----------
def test_one_unit_is_in_stock():
    assert Item(quantity=1).in_stock is True


def test_item_json_starts_with_one_unit(item):
    assert item.to_json()['quantity'] == 1


def test_stock_error_says_how_many_are_needed(item):
    with pytest.raises(InsufficientStock, match=r'50 available, 56 needed\.'):
        Item.adjust_stock(item.pk, -56)


# ---------- field limits of the store models ----------
def errors(instance):
    try:
        instance.full_clean()
    except ValidationError as error:
        return set(error.message_dict)
    return set()


def new_item(category, **changes):
    values = {'name': 'A', 'category': category, 'quantity': 1, 'price': Decimal('1.00'), **changes}
    return Item(**values)


def new_delivery(**changes):
    return Delivery(date=datetime.now().astimezone(), **changes)


@pytest.mark.parametrize('model, field, limit', [
    (Category, 'name', 50), (Item, 'name', 50),
    (Delivery, 'customer_name', 30), (Delivery, 'location', 20),
])
def test_text_length_limit(category, model, field, limit):
    def build(length):
        value = {field: 'a' * length}
        if model is Item:
            return new_item(category, **value)
        return new_delivery(**value) if model is Delivery else Category(**value)

    assert field not in errors(build(limit))
    assert field in errors(build(limit + 1))


@pytest.mark.parametrize('price, valid', [
    ('1.01', True), ('1.001', False), ('9999999999.99', True), ('10000000000', False),
])
def test_price_digits(category, price, valid):
    assert ('price' not in errors(new_item(category, price=Decimal(price)))) is valid


def test_optional_item_fields_may_be_empty(category):
    assert errors(new_item(category, description='', expiring_date=None, vendor=None)) == set()


@pytest.mark.parametrize('length, valid', [(256, True), (257, False)])
def test_description_limit_is_enforced_by_the_form(category, length, valid):
    # Django checks a text area's max_length in the form, not in the model.
    form = ItemForm(data={'name': 'A', 'category': category.pk, 'quantity': 1, 'price': '1.00',
                          'description': 'a' * length})
    assert ('description' not in form.errors) is valid


def test_new_item_has_no_stock(category):
    assert Item(name='A', category=category).quantity == 0


def test_delivery_fields_are_optional(db):
    delivery = new_delivery(item=None, customer_name=None, phone_number=None, location=None)
    assert errors(delivery) == set()
    with transaction.atomic():
        delivery.save()
    assert delivery.is_delivered is False


@pytest.mark.parametrize('field', ['item', 'customer_name', 'phone_number', 'location'])
def test_delivery_accepts_null_in_the_database(db, field):
    try:
        with transaction.atomic():
            new_delivery(**{field: None}).save()
    except IntegrityError:
        pytest.fail(f'{field} must accept NULL')


@pytest.mark.parametrize('model', [Category, Item])
def test_database_rejects_a_duplicate_slug(category, model):
    # The slug field picks distinct values by itself; this checks the constraint behind it.
    if model is Category:
        first, second = category, Category.objects.create(name='Other')
    else:
        first, second = new_item(category, name='One'), new_item(category, name='Two')
        first.save()
        second.save()
    with pytest.raises(IntegrityError), transaction.atomic():
        model.objects.filter(pk=second.pk).update(slug=first.slug)


def test_slugs_stay_unique(category):
    other = Category.objects.create(name=category.name)
    assert other.slug != category.slug
    first, second = new_item(category), new_item(category)
    first.save()
    second.save()
    assert first.slug != second.slug
