"""Void rule: reason length limit and the points reversal direction."""
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from accounts.models import Customer, Profile
from store.models import Category, Item
from transactions.models import Sale
from transactions.services import create_sale, void_sale


@pytest.fixture
def item(db):
    category = Category.objects.create(name='Test')
    return Item.objects.create(name='Keyboard', category=category, quantity=10, price=Decimal('100.00'))


@pytest.mark.parametrize('length, voided', [(199, True), (200, True), (201, False)])
def test_void_reason_length_limit(client, item, length, voided):
    user = User.objects.create_user('manager_v', password='x')
    Profile.objects.filter(user=user).update(role='EX', status='A')
    customer = Customer.objects.create(first_name='Ali')
    sale = create_sale(user=None, customer_id=customer.pk,
                       items=[{'id': item.pk, 'quantity': 1}], amount_paid=1000)
    client.force_login(User.objects.get(pk=user.pk))
    client.post(reverse('sale-delete', args=[sale.pk]), {'reason': 'x' * length})
    sale.refresh_from_db()
    item.refresh_from_db()
    expected = (Sale.STATUS_VOIDED, 10) if voided else (Sale.STATUS_COMPLETED, 9)
    assert (sale.status, item.quantity) == expected


def test_void_gives_back_redeemed_points(settings, item):
    settings.LOYALTY = {'enabled': True, 'earn_per': '100', 'point_value': '1.00', 'min_redeem': 10}
    customer = Customer.objects.create(first_name='Ali', loyalty_points=50)
    sale = create_sale(user=None, customer_id=customer.pk,
                       items=[{'id': item.pk, 'quantity': 1}], amount_paid=1000, redeem_points=50)
    customer.refresh_from_db()
    assert customer.loyalty_points == 0  # redeemed 50, earned floor(50 / 100) = 0
    void_sale(sale, user=None, reason='test')
    customer.refresh_from_db()
    assert customer.loyalty_points == 50
