"""Store views, forms and mixins, plus the transactions admin and export helper."""
from datetime import datetime
from decimal import Decimal

import pytest
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.urls import reverse

from accounts.models import Customer, Profile, Vendor
from store.forms import DeliveryForm, ItemForm
from store.models import Category, Delivery, Item
from transactions.models import LoyaltyTransaction, Sale
from transactions.services import create_sale
from transactions.views import _naive


def make_user(username, role):
    user = User.objects.create_user(username, password='x')
    Profile.objects.filter(user=user).update(role=role, status='A')
    return User.objects.get(pk=user.pk)


@pytest.fixture
def cashier(db):
    return make_user('cashier_s', 'OP')


@pytest.fixture
def manager(db):
    return make_user('manager_s', 'EX')


@pytest.fixture
def category(db):
    return Category.objects.create(name='Hardware')


@pytest.fixture
def item(category):
    return Item.objects.create(name='Keyboard', category=category, quantity=10, price=Decimal('100.00'))


def test_dashboard_counts_only_completed_sales(client, cashier, item):
    customer = Customer.objects.create(first_name='Ali')

    def sell(quantity):
        return create_sale(user=None, customer_id=customer.pk,
                           items=[{'id': item.pk, 'quantity': quantity}], amount_paid=1000)

    sell(2)
    voided = sell(1)
    Sale.objects.filter(pk=voided.pk).update(status=Sale.STATUS_VOIDED)
    client.force_login(cashier)
    context = client.get(reverse('dashboard')).context
    assert context['sales_today'] == 1
    assert context['revenue_today'] == Decimal('200.00')
    assert context['revenue_month'] == Decimal('200.00')
    assert context['units_in_stock'] == 7
    assert context['stock_value'] == Decimal('700.00')
    assert context['chart_data']['sale_values'][-1] == 200.0


@pytest.mark.parametrize('name', ['productslist', 'item_search_list_view'])
def test_product_list(client, cashier, item, name):
    client.force_login(cashier)
    response = client.get(reverse(name), {'q': 'Keyboard'})
    assert list(response.context['items']) == [item]
    assert response.context['low_stock_threshold'] == 5


def test_table_export_is_for_managers_only(client, cashier, manager, item):
    client.force_login(cashier)
    assert client.get(reverse('productslist'), {'_export': 'csv'}).status_code == 403
    client.force_login(manager)
    response = client.get(reverse('productslist'), {'_export': 'csv'})
    assert response.status_code == 200 and b'Keyboard' in response.content


def test_product_and_delivery_pages(client, cashier, item):
    delivery = Delivery.objects.create(item=item, customer_name='Amina', date=datetime.now().astimezone())
    client.force_login(cashier)
    assert client.get(reverse('product-detail', args=[item.slug])).context['object'] == item
    assert list(client.get(reverse('deliveries')).context['deliveries']) == [delivery]
    assert client.get(reverse('delivery-detail', args=[delivery.pk])).status_code == 200


def test_category_pages(client, manager, category, item):
    client.force_login(manager)
    listing = client.get(reverse('category-list')).context['categories']
    assert [(row.name, row.item_count) for row in listing] == [('Hardware', 1)]
    assert list(client.get(reverse('category-detail', args=[category.pk])).context['items']) == [item]

    response = client.post(reverse('category-create'), {'name': 'Cables'})
    created = Category.objects.get(name='Cables')
    assert response.url == reverse('category-detail', args=[created.pk])
    response = client.post(reverse('category-update', args=[created.pk]), {'name': 'Leads'})
    assert response.url == reverse('category-detail', args=[created.pk])
    created.refresh_from_db()
    assert created.name == 'Leads'


def test_item_search_ajax(client, cashier, item, category):
    Item.objects.create(name='Mouse', category=category, quantity=0, price=Decimal('5'))
    client.force_login(cashier)
    assert [row['name'] for row in client.get(reverse('get_items')).json()] == ['Keyboard']
    assert client.get(reverse('get_items'), {'term': 'zzz'}).json() == []
    assert client.post(reverse('get_items')).status_code == 405


def test_store_forms(db):
    form = ItemForm()
    assert form.has_categories is False and form.has_vendors is False
    assert form.fields['vendor'].empty_label == 'No vendor (optional)'
    Category.objects.create(name='Hardware')
    Vendor.objects.create(name='Acme')
    form = ItemForm()
    assert form.has_categories is True and form.has_vendors is True
    delivery_form = DeliveryForm()
    assert delivery_form.has_items is False
    assert delivery_form.fields['item'].empty_label == 'Choose an item (optional)'


def test_delete_product_with_sales_is_blocked(client, manager, item):
    customer = Customer.objects.create(first_name='Ali')
    create_sale(user=None, customer_id=customer.pk,
                items=[{'id': item.pk, 'quantity': 1}], amount_paid=1000)
    client.force_login(manager)
    response = client.post(reverse('product-delete', args=[item.slug]))
    assert response.status_code == 302 and Item.objects.filter(pk=item.pk).exists()
    messages = [str(m) for m in get_messages(response.wsgi_request)]
    assert any('cannot be deleted' in m for m in messages)


def test_delete_reraises_unexpected_errors(client, manager, category, monkeypatch):
    def boom(self, *args, **kwargs):
        raise RuntimeError('db down')

    monkeypatch.setattr(Category, 'delete', boom)
    client.force_login(manager)
    with pytest.raises(RuntimeError, match='db down'):
        client.post(reverse('category-delete', args=[category.pk]))
    assert Category.objects.filter(pk=category.pk).exists()


def test_sale_and_ledger_are_read_only_in_admin(rf, db):
    request = rf.get('/')
    for model in (Sale, LoyaltyTransaction):
        model_admin = admin.site._registry[model]
        assert model_admin.get_readonly_fields(request) == [f.name for f in model._meta.fields]
        assert model_admin.has_add_permission(request) is False
        assert model_admin.has_delete_permission(request) is False
    inline = admin.site._registry[Sale].inlines[0](Sale, admin.site)
    assert inline.has_add_permission(request) is False


def test_naive_export_value():
    assert _naive(None) is None
    assert _naive(datetime(2026, 1, 2, 3, 4)) == datetime(2026, 1, 2, 3, 4)
