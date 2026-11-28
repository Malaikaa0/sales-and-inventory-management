"""Profile, Vendor and Customer models, and the form branch without an item field."""
from decimal import Decimal

import pytest
from django.contrib.auth.models import User

from accounts.models import Customer, Profile, Vendor
from transactions.forms import BootstrapMixin
from transactions.models import Purchase


# ---------- Customer: the points balance both workflows use ----------
def test_customer_names():
    assert Customer(first_name='Amina', last_name='Hassan').get_full_name() == 'Amina Hassan'
    assert str(Customer(first_name='Amina', last_name=None)) == 'Amina'


@pytest.mark.parametrize('points, value', [(0, '0.00'), (1, '0.50'), (250, '125.00')])
def test_customer_loyalty_value(settings, points, value):
    settings.LOYALTY = {'point_value': '0.50'}
    assert Customer(loyalty_points=points).loyalty_value == Decimal(value)


@pytest.mark.parametrize('phone, shown', [('0712345678', '0712345678'), (None, '')])
def test_customer_to_select2(db, phone, shown):
    customer = Customer.objects.create(first_name='Amina', phone=phone, loyalty_points=7)
    assert customer.to_select2() == {
        'id': customer.pk, 'text': 'Amina', 'label': 'Amina', 'value': customer.pk,
        'phone': shown, 'loyalty_points': 7,
    }


# ---------- Vendor ----------
def test_vendor_str(db):
    vendor = Vendor.objects.create(name='Coast Beverages', phone_number='0733 666 777')
    assert str(vendor) == 'Coast Beverages'
    assert vendor.slug == 'coast-beverages'
    assert vendor.phone_number == '0733 666 777'


# ---------- Profile ----------
@pytest.fixture
def profile(db):
    return User.objects.create_user('jdoe', password='x').profile


def test_profile_names_and_initials(profile):
    assert str(profile) == 'jdoe Profile'
    assert (profile.display_name, profile.initials) == ('jdoe', 'J')
    profile.user.first_name, profile.user.last_name = 'Jane', 'Doe'
    assert (profile.display_name, profile.initials) == ('Jane Doe', 'JD')
    profile.first_name, profile.last_name = 'Mary', 'Wanjiku'
    assert (profile.display_name, profile.initials) == ('Mary Wanjiku', 'MW')
    profile.first_name, profile.last_name = '.', ''
    assert profile.initials == '?'


def test_profile_image_url(profile):
    assert profile.image_url.endswith('profile_pics/default.jpg')
    profile.profile_picture = None
    assert profile.image_url == ''


@pytest.mark.parametrize('name', ['', 'profile_pics/default.jpg'])
def test_profile_without_uploaded_picture(profile, name):
    profile.profile_picture = name
    assert profile.has_picture is False


@pytest.mark.parametrize('exists', [True, False])
def test_profile_picture_must_exist_in_storage(profile, monkeypatch, exists):
    profile.profile_picture = 'profile_pics/me.jpg'
    monkeypatch.setattr(profile.profile_picture.storage, 'exists', lambda name: exists)
    assert profile.has_picture is exists


def test_profile_picture_storage_error(profile, monkeypatch):
    def broken(name):
        raise OSError('storage unavailable')

    profile.profile_picture = 'profile_pics/me.jpg'
    monkeypatch.setattr(profile.profile_picture.storage, 'exists', broken)
    assert profile.has_picture is False
    assert Profile.objects.filter(pk=profile.pk).exists()


# ---------- BootstrapMixin on a form without an item field ----------
def test_bootstrap_mixin_without_item_field():
    class QuantityOnlyForm(BootstrapMixin):
        class Meta:
            model = Purchase
            fields = ['quantity']

    form = QuantityOnlyForm()
    assert form.fields['quantity'].widget.attrs['class'] == 'form-control'
    assert not hasattr(form, 'has_items') and not hasattr(form, 'has_vendors')
