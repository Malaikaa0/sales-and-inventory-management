"""
Browser tests for Member 1's use cases, one test per flow.

UC-M1-1 Redeem loyalty points on a sale   docs/use-cases/UC-M1-1-redeem-points.md
UC-M1-2 Void a sale and reverse points    docs/use-cases/UC-M1-2-void-and-reverse-points.md

Needs: pip install -r requirements-dev.txt and playwright install chromium.
"""
import re
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from playwright.sync_api import expect, sync_playwright

from accounts.models import Customer, Profile
from store.models import Category, Item
from transactions.models import Sale
from transactions.services import create_sale

PASSWORD = 'm1-pass-123'


@pytest.fixture
def shop(transactional_db, settings, monkeypatch):
    """A cashier, a manager, one item and one customer with known loyalty rules."""
    # Playwright's sync API runs an event loop in this thread; Django must allow ORM calls beside it.
    monkeypatch.setenv('DJANGO_ALLOW_ASYNC_UNSAFE', 'true')
    settings.LOYALTY = {'enabled': True, 'earn_per': '100', 'point_value': '1.00', 'min_redeem': 10}
    for username, role in (('m1cashier', 'OP'), ('m1manager', 'EX')):
        user = User.objects.create_user(username, password=PASSWORD)
        Profile.objects.filter(user=user).update(role=role, status='A')
    category = Category.objects.create(name='Hardware')
    item = Item.objects.create(name='Keyboard', category=category, quantity=20, price=Decimal('100.00'))
    customer = Customer.objects.create(first_name='Amina', loyalty_points=100)
    return {'item': item, 'customer': customer}


@pytest.fixture
def browser():
    with sync_playwright() as playwright:
        chromium = playwright.chromium.launch()
        yield chromium
        chromium.close()


def sign_in(browser, server, username):
    page = browser.new_context(viewport={'width': 1280, 'height': 900}).new_page()
    page.goto(f'{server.url}/accounts/login/')
    page.fill('#id_username', username)
    page.fill('#id_password', PASSWORD)
    page.click('button[type=submit]')
    page.wait_for_url(lambda url: '/accounts/login' not in url)
    return page


def set_balance(shop, points):
    Customer.objects.filter(pk=shop['customer'].pk).update(loyalty_points=points)


def state(shop):
    """Stock, points balance and number of sales, read back from the database."""
    shop['item'].refresh_from_db()
    shop['customer'].refresh_from_db()
    return shop['item'].quantity, shop['customer'].loyalty_points, Sale.objects.count()


def pick(page, select_id, term):
    page.click(f'#{select_id} + .select2 .select2-selection')
    page.fill('.select2-container--open .select2-search__field', term)
    page.locator('.select2-results__option', has_text=term).first.click()


def start_sale(browser, server):
    """Cashier opens the till with one Keyboard in the cart and the customer chosen."""
    page = sign_in(browser, server, 'm1cashier')
    page.goto(f'{server.url}/transactions/new-sale/')
    pick(page, 'item-search', 'Keyboard')
    pick(page, 'customer', 'Amina')
    expect(page.locator('#t-total')).to_have_text('Ksh 100.00')
    return page


def pay_and_submit(page):
    page.click('#paid-exact')
    page.click('#submit-btn')


def expect_completed(page, total):
    expect(page.locator('#done-modal')).to_be_visible()
    expect(page.locator('#done-total')).to_have_text(f'Ksh {total}')


# ---------------------------------------------------------------- UC-M1-1
def test_uc1_main_redeem_part_of_balance(live_server, browser, shop):
    page = start_sale(browser, live_server)
    page.fill('#redeem', '40')
    expect(page.locator('#t-total')).to_have_text('Ksh 60.00')
    pay_and_submit(page)
    expect_completed(page, '60.00')
    assert state(shop) == (19, 60, 1)
    assert Sale.objects.get().loyalty_points_redeemed == 40


def test_uc1_alternative_use_max(live_server, browser, shop):
    set_balance(shop, 70)
    page = start_sale(browser, live_server)
    page.click('#redeem-max')
    expect(page.locator('#redeem')).to_have_value('70')
    pay_and_submit(page)
    expect_completed(page, '30.00')
    assert state(shop) == (19, 0, 1)


def test_uc1_alternative_more_than_balance_is_reduced(live_server, browser, shop):
    set_balance(shop, 30)
    page = start_sale(browser, live_server)
    page.fill('#redeem', '500')
    expect(page.locator('#t-total')).to_have_text('Ksh 70.00')
    pay_and_submit(page)
    expect_completed(page, '70.00')
    assert state(shop) == (19, 0, 1)
    assert Sale.objects.get().loyalty_points_redeemed == 30


def test_uc1_exception_below_minimum_then_corrected(live_server, browser, shop):
    page = start_sale(browser, live_server)
    page.fill('#redeem', '9')
    pay_and_submit(page)
    expect(page.locator('#form-error')).to_have_text('Redeem at least 10 points.')
    assert state(shop) == (20, 100, 0)

    page.fill('#redeem', '10')
    pay_and_submit(page)
    expect_completed(page, '90.00')
    assert state(shop) == (19, 90, 1)


def test_uc1_exception_amount_paid_too_low(live_server, browser, shop):
    page = start_sale(browser, live_server)
    page.fill('#redeem', '40')
    page.fill('#paid', '59.99')
    page.click('#submit-btn')
    expect(page.locator('#form-error')).to_have_text('Amount paid must cover the sale total.')
    expect(page.locator('#done-modal')).to_be_hidden()
    assert state(shop) == (20, 100, 0)


# ---------------------------------------------------------------- UC-M1-2
def completed_sale(shop, quantity, **extra):
    return create_sale(user=None, customer_id=shop['customer'].pk,
                       items=[{'id': shop['item'].pk, 'quantity': quantity}], amount_paid=100000, **extra)


def void_link(page, sale):
    # Matched by address: the icon inside the link adds to its accessible name.
    return page.locator(f'a[href="/transactions/sale/{sale.pk}/void/"]')


def void_through_pages(browser, server, sale, reason):
    page = sign_in(browser, server, 'm1manager')
    page.goto(f'{server.url}/transactions/sale/{sale.pk}/')
    void_link(page, sale).click()
    page.fill('input[name=reason]', reason)
    page.get_by_role('button', name='Void sale').click()
    return page


def expect_voided(page, sale):
    expect(page.locator('body')).to_contain_text(f'Sale {sale.receipt_number} voided. Stock restored.')
    expect(page.locator('.status.bad')).to_have_text('Voided')
    sale.refresh_from_db()
    assert sale.status == Sale.STATUS_VOIDED


def test_uc2_main_earned_points_taken_back(live_server, browser, shop):
    sale = completed_sale(shop, 4)  # earns 4 points
    assert state(shop) == (16, 104, 1)
    page = void_through_pages(browser, live_server, sale, 'Customer returned all items')
    expect_voided(page, sale)
    assert state(shop) == (20, 100, 1)
    assert sale.void_reason == 'Customer returned all items'
    assert sale.voided_by.username == 'm1manager'


def test_uc2_alternative_redeemed_points_given_back(live_server, browser, shop):
    sale = completed_sale(shop, 2, redeem_points=100)  # pays 100, earns 1
    assert state(shop) == (18, 1, 1)
    page = void_through_pages(browser, live_server, sale, 'Wrong item')
    expect_voided(page, sale)
    assert state(shop) == (20, 100, 1)


def test_uc2_alternative_earned_points_already_spent(live_server, browser, shop):
    sale = completed_sale(shop, 4)
    set_balance(shop, 1)
    page = void_through_pages(browser, live_server, sale, 'Faulty goods')
    expect_voided(page, sale)
    assert state(shop) == (20, 0, 1)


def test_uc2_exception_blank_reason(live_server, browser, shop):
    sale = completed_sale(shop, 4)
    page = void_through_pages(browser, live_server, sale, '   ')
    expect(page.locator('body')).to_contain_text('This field is required.')
    sale.refresh_from_db()
    assert sale.status == Sale.STATUS_COMPLETED
    assert state(shop) == (16, 104, 1)


def test_uc2_exception_cashier_not_allowed(live_server, browser, shop):
    sale = completed_sale(shop, 4)
    page = sign_in(browser, live_server, 'm1cashier')
    page.goto(f'{live_server.url}/transactions/sale/{sale.pk}/')
    expect(page.locator('h1')).to_have_text(f'Sale {sale.receipt_number}')
    expect(void_link(page, sale)).to_have_count(0)
    response = page.goto(f'{live_server.url}/transactions/sale/{sale.pk}/void/')
    assert response.status == 403
    sale.refresh_from_db()
    assert sale.status == Sale.STATUS_COMPLETED
    assert state(shop) == (16, 104, 1)


def test_uc2_exception_already_voided(live_server, browser, shop):
    sale = completed_sale(shop, 4)
    page = void_through_pages(browser, live_server, sale, 'First time')
    expect_voided(page, sale)

    page.goto(f'{live_server.url}/transactions/sale/{sale.pk}/void/')
    page.fill('input[name=reason]', 'Second time')
    page.get_by_role('button', name='Void sale').click()
    expect(page.locator('body')).to_contain_text(re.compile('already been voided'))
    sale.refresh_from_db()
    assert sale.void_reason == 'First time'
    assert state(shop) == (20, 100, 1)
