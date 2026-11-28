"""
Playwright E2E tests for Member 2's use cases, one test per flow:

  UC-M2-1 Void a sale             docs/use-cases/UC-M2-1-void-sale.md
  UC-M2-2 Complete a sale, with rejections   docs/use-cases/UC-M2-2-sale-rejections.md

Uses Member 3's setup from test_e2e_workflows.py (fresh SQLite database with
seed_demo, runserver on a free port, headless Chromium, keyboard login). Each test
asserts what the user sees and reads stock back from the product page, which
also works at stock 0 (/get-items/ hides empty items).

Each test creates its own product and customer through the app's own forms, so
tests do not depend on each other or on seed values. Background actions that the
flow needs (another till selling the same item, points spent elsewhere) are made
with fetch() from a second page, as in Member 3's tests.
"""
import itertools
import re
import time

import pytest
from playwright.sync_api import expect

from test_e2e_workflows import _login, browser_ctx, e2e_server  # noqa: F401  (Member 3's fixtures)

PASSWORD = 'demo-pass-123'
_counter = itertools.count(1)
_RUN = format(int(time.time()) % 0xFFFFFF, 'x')


# --------------------------------------------------------------------- helpers
def unique(prefix):
    return f'{prefix}-{_RUN}-{next(_counter)}'


def new_page(browser, base, user=None):
    context = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = context.new_page()
    if user:
        _login(page, base, user, PASSWORD)
    return context, page


def create_item(manager_page, base, quantity, price='1.00'):
    """Add a product through the New product form (manager)."""
    name = unique('e2e-item')
    page = manager_page.context.new_page()
    page.goto(f'{base}/new-product/', wait_until='domcontentloaded')
    page.locator('#id_name').fill(name)
    page.locator('#id_category').select_option(index=1)
    page.locator('#id_vendor').select_option(index=1)
    page.locator('#id_quantity').fill(str(quantity))
    page.locator('#id_price').fill(price)
    page.locator('form button[type="submit"]').last.click()
    page.wait_for_url(f'{base}/products/**')
    page.close()
    return {'name': name, 'slug': name}


def create_customer(page_any, base):
    """Add a customer through the New customer form; new customers have 0 points."""
    first = unique('e2ecust')
    page = page_any.context.new_page()
    page.goto(f'{base}/accounts/customers/create/', wait_until='domcontentloaded')
    page.locator('#id_first_name').fill(first)
    page.locator('#id_last_name').fill('Test')
    page.locator('form button[type="submit"]').last.click()
    page.wait_for_url(f'{base}/accounts/customers/**')
    page.close()
    return {'name': f'{first} Test', 'first': first}


def stock(page_any, base, item):
    """Stock read back from the product page in a separate tab (keeps the till intact)."""
    page = page_any.context.new_page()
    page.goto(f'{base}/product/{item["slug"]}/', wait_until='domcontentloaded')
    text = page.locator('dt:has-text("In stock") + dd').inner_text()
    page.close()
    return int(text.replace(',', ''))


def lookup(page, base, path, term):
    return page.evaluate(
        """async ([url, t]) => (await fetch(url + '?term=' + encodeURIComponent(t),
                                          {credentials: 'same-origin'})).json()""",
        [f'{base}{path}', term])


def item_id(page, base, item):
    return [i for i in lookup(page, base, '/get-items/', item['name']) if i['name'] == item['name']][0]['id']


def customer_row(page, base, customer):
    rows = lookup(page, base, '/accounts/get_customers/', customer['first'])['results']
    return [r for r in rows if r['label'] == customer['name']][0]


def points(page, base, customer):
    return customer_row(page, base, customer)['loyalty_points']


def background_sale(page_any, base, item, customer, quantity, redeem=0):
    """Another till sells the same item (fetch from a second tab, same user)."""
    page = page_any.context.new_page()
    page.goto(f'{base}/transactions/new-sale/', wait_until='domcontentloaded')
    result = page.evaluate(
        """async (body) => {
            const csrf = document.querySelector('[name=csrfmiddlewaretoken]').value;
            const r = await fetch('/transactions/new-sale/', {method: 'POST', credentials: 'same-origin',
                headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrf},
                body: JSON.stringify(body)});
            return {status: r.status, body: await r.json()};
        }""",
        {'customer': customer_row(page, base, customer)['id'],
         'items': [{'id': item_id(page, base, item), 'quantity': quantity}],
         'tax_percentage': 0, 'amount_paid': 10000000, 'redeem_points': redeem})
    page.close()
    assert result['status'] == 200, result
    return result['body']


def open_till(page, base):
    page.goto(f'{base}/transactions/new-sale/', wait_until='networkidle')


def add_item(page, item, times=1):
    """Keyboard: '/' opens product search, type, Enter adds (Member 3's pattern)."""
    for _ in range(times):
        page.locator('h1').click()
        page.keyboard.press('/')
        search = page.locator('.pos-picker .select2-search__field')
        expect(search).to_be_visible()
        search.type(item['name'])
        expect(page.locator('.select2-results__option', has_text=item['name']).first).to_be_visible()
        page.keyboard.press('Enter')


def set_quantity(page, item, quantity):
    box = page.locator(f'input[aria-label="Quantity of {item["name"]}"]')
    box.fill(str(quantity))
    box.press('Tab')


def choose_customer(page, customer):
    page.locator('.pos-checkout .select2-selection').click()
    page.locator('.pos-checkout .select2-search__field').type(customer['first'])
    option = page.locator('.select2-results__option', has_text=customer['name']).first
    expect(option).to_be_visible()
    option.click()


def submit(page):
    page.locator('#submit-btn').focus()
    page.keyboard.press('Enter')


def form_error(page):
    return page.locator('#form-error')


def sale_status_text(page):
    return page.locator('.detail-header')


def void_via_ui(page, base, sale_id, reason='Customer returned all items'):
    page.goto(f'{base}/transactions/sale/{sale_id}/', wait_until='domcontentloaded')
    page.locator("a[href$='/void/']").click()
    page.wait_for_url(f'{base}/transactions/sale/{sale_id}/void/')
    page.locator('#id_reason').fill(reason)
    page.locator("button[type='submit']:has-text('Void sale')").click()
    page.wait_for_url(f'{base}/transactions/sale/{sale_id}/')


@pytest.fixture
def cashier(e2e_server, browser_ctx):
    context, page = new_page(browser_ctx, e2e_server, 'cashier')
    yield page
    context.close()


@pytest.fixture
def manager(e2e_server, browser_ctx):
    context, page = new_page(browser_ctx, e2e_server, 'manager')
    yield page
    context.close()


# =================================================================== UC-M2-2: sale
@pytest.mark.e2e
def test_uc_m2_2_main_complete_sale(e2e_server, cashier, manager):
    base = e2e_server
    item = create_item(manager, base, quantity=10, price='2.50')
    customer = create_customer(cashier, base)

    open_till(cashier, base)
    add_item(cashier, item)
    set_quantity(cashier, item, 4)
    choose_customer(cashier, customer)
    cashier.locator('#paid').fill('20.00')
    expect(cashier.locator('#t-total')).to_contain_text('10.00')
    submit(cashier)

    expect(cashier.locator('#done-modal')).to_be_visible()
    expect(cashier.locator('#done-receipt')).to_have_text(re.compile(r'^IMS\d+$'))
    expect(cashier.locator('#done-total')).to_contain_text('10.00')
    expect(cashier.locator('#done-change')).to_contain_text('10.00')
    assert stock(manager, base, item) == 6


@pytest.mark.e2e
def test_uc_m2_2_alt1_redeem_points(e2e_server, cashier, manager):
    base = e2e_server
    item = create_item(manager, base, quantity=20, price='100.00')
    customer = create_customer(cashier, base)
    background_sale(cashier, base, item, customer, 10)            # 1000.00 -> 10 points
    assert points(cashier, base, customer) == 10

    open_till(cashier, base)
    add_item(cashier, item)                                        # 100.00
    choose_customer(cashier, customer)
    cashier.locator('#redeem').fill('5')
    expect(cashier.locator('#t-total')).to_contain_text('95.00')
    cashier.locator('#paid-exact').click()
    submit(cashier)

    expect(cashier.locator('#done-modal')).to_be_visible()
    expect(cashier.locator('#done-total')).to_contain_text('95.00')
    assert points(cashier, base, customer) == 5                    # 10 - 5 + 0 earned (95 < 100)
    assert stock(manager, base, item) == 9


@pytest.mark.e2e
def test_uc_m2_2_alt2_same_item_added_twice_is_merged(e2e_server, cashier, manager):
    base = e2e_server
    item = create_item(manager, base, quantity=5)
    customer = create_customer(cashier, base)

    open_till(cashier, base)
    add_item(cashier, item, times=2)
    expect(cashier.locator('#cart-count')).to_have_text('1 item')
    expect(cashier.locator(f'input[aria-label="Quantity of {item["name"]}"]')).to_have_value('2')
    choose_customer(cashier, customer)
    cashier.locator('#paid-exact').click()
    submit(cashier)

    expect(cashier.locator('#done-modal')).to_be_visible()
    assert stock(manager, base, item) == 3


@pytest.mark.e2e
def test_uc_m2_2_alt3_exact_payment_change_zero(e2e_server, cashier, manager):
    base = e2e_server
    item = create_item(manager, base, quantity=5, price='3.00')
    customer = create_customer(cashier, base)

    open_till(cashier, base)
    add_item(cashier, item)
    choose_customer(cashier, customer)
    cashier.locator('#paid-exact').focus()
    cashier.keyboard.press('Enter')
    expect(cashier.locator('#paid')).to_have_value('3.00')
    submit(cashier)

    expect(cashier.locator('#done-modal')).to_be_visible()
    expect(cashier.locator('#done-change')).to_contain_text('0.00')
    assert stock(manager, base, item) == 4


@pytest.mark.e2e
def test_uc_m2_2_exc1_not_enough_stock(e2e_server, cashier, manager):
    base = e2e_server
    item = create_item(manager, base, quantity=5)
    customer = create_customer(cashier, base)

    open_till(cashier, base)
    add_item(cashier, item)
    set_quantity(cashier, item, 5)                       # all 5 in stock when added
    choose_customer(cashier, customer)
    background_sale(cashier, base, item, customer, 1)    # another till sells 1 -> 4 left
    cashier.locator('#paid').fill('100')
    submit(cashier)

    expect(form_error(cashier)).to_be_visible()
    expect(form_error(cashier)).to_contain_text(f'Not enough stock for {item["name"]}: 4 available.')
    expect(cashier.locator('#done-modal')).not_to_be_visible()
    assert stock(manager, base, item) == 4               # only the other till's sale


@pytest.mark.e2e
def test_uc_m2_2_exc2_amount_paid_below_total(e2e_server, cashier, manager):
    base = e2e_server
    item = create_item(manager, base, quantity=5, price='3.00')
    customer = create_customer(cashier, base)

    open_till(cashier, base)
    add_item(cashier, item)
    choose_customer(cashier, customer)
    cashier.locator('#paid').fill('2.99')                # total 3.00, short by 0.01
    submit(cashier)

    expect(form_error(cashier)).to_be_visible()
    expect(form_error(cashier)).to_contain_text('Amount paid must cover the sale total.')
    expect(cashier.locator('#paid')).to_be_focused()
    expect(cashier.locator('#done-modal')).not_to_be_visible()
    assert stock(manager, base, item) == 5


@pytest.mark.e2e
def test_uc_m2_2_exc3_tax_out_of_range_rejected(e2e_server, cashier, manager):
    """BR1: tax must be 0..100. UC-M2-2 E3 requires the sale to be rejected with a
    message and nothing saved when the cashier enters an out-of-range tax."""
    base = e2e_server
    item = create_item(manager, base, quantity=5, price='10.00')
    customer = create_customer(cashier, base)

    open_till(cashier, base)
    add_item(cashier, item)
    choose_customer(cashier, customer)
    cashier.locator('#tax').fill('150')
    cashier.locator('#paid').fill('100')
    submit(cashier)

    expect(cashier.locator('#done-modal')).not_to_be_visible()
    expect(form_error(cashier)).to_be_visible()
    assert stock(manager, base, item) == 5


@pytest.mark.e2e
def test_uc_m2_2_exc4_points_spent_elsewhere_rejected(e2e_server, cashier, manager):
    base = e2e_server
    item = create_item(manager, base, quantity=30, price='100.00')
    customer = create_customer(cashier, base)
    background_sale(cashier, base, item, customer, 10)             # 10 points
    assert points(cashier, base, customer) == 10

    open_till(cashier, base)
    add_item(cashier, item)
    choose_customer(cashier, customer)                             # till sees 10 points
    cashier.locator('#redeem').fill('10')
    cashier.locator('#paid-exact').click()
    background_sale(cashier, base, item, customer, 1, redeem=8)    # spends 8 -> 2 left
    before = stock(manager, base, item)
    submit(cashier)

    expect(form_error(cashier)).to_be_visible()
    expect(form_error(cashier)).to_contain_text(f'{customer["name"]} only has 2 points.')
    expect(cashier.locator('#done-modal')).not_to_be_visible()
    assert stock(manager, base, item) == before
    assert points(cashier, base, customer) == 2


@pytest.mark.e2e
def test_uc_m2_2_exc5_session_expired(e2e_server, cashier, manager):
    """BR4: a logged-out till cannot save a sale, and the cashier is told to sign in again."""
    base = e2e_server
    item = create_item(manager, base, quantity=5)
    customer = create_customer(cashier, base)

    open_till(cashier, base)
    add_item(cashier, item)
    choose_customer(cashier, customer)
    cashier.locator('#paid-exact').click()
    other = cashier.context.new_page()                    # same browser, other tab: sign out
    other.goto(f'{base}/', wait_until='domcontentloaded')
    other.locator('button[aria-label="Sign out"]').click()
    other.wait_for_url(f'{base}/accounts/login/**')
    other.close()
    submit(cashier)

    expect(cashier.locator('#done-modal')).not_to_be_visible()
    _, reader = new_page(cashier.context.browser, base, 'manager')
    assert stock(reader, base, item) == 5                 # nothing saved
    reader.context.close()
    told_to_sign_in = re.compile(r'sign in|log in|session', re.I)
    on_login_page = '/accounts/login/' in cashier.url
    assert on_login_page or told_to_sign_in.search(form_error(cashier).inner_text()), (
        f'Cashier sees: {form_error(cashier).inner_text()!r} on {cashier.url}'
    )


@pytest.mark.e2e
def test_uc_m2_2_exc6_double_click_records_one_sale(e2e_server, cashier, manager):
    base = e2e_server
    item = create_item(manager, base, quantity=5)
    customer = create_customer(cashier, base)

    open_till(cashier, base)
    add_item(cashier, item)
    choose_customer(cashier, customer)
    cashier.locator('#paid-exact').click()
    cashier.locator('#submit-btn').dblclick()

    expect(cashier.locator('#done-modal')).to_be_visible()
    cashier.wait_for_timeout(1000)                        # let any second request finish
    assert stock(manager, base, item) == 4                # one sale, not two


# =================================================================== UC-M2-1: void
def _sold(cashier, manager, base, quantity=3, price='1.00', item_stock=10):
    item = create_item(manager, base, quantity=item_stock, price=price)
    customer = create_customer(cashier, base)
    sale = background_sale(cashier, base, item, customer, quantity)
    return item, customer, sale['sale_id']


@pytest.mark.e2e
def test_uc_m2_1_main_void_sale(e2e_server, cashier, manager):
    base = e2e_server
    item, _, sale_id = _sold(cashier, manager, base)
    assert stock(manager, base, item) == 7

    manager.goto(f'{base}/transactions/sale/{sale_id}/', wait_until='domcontentloaded')
    expect(sale_status_text(manager)).to_contain_text('Completed')
    manager.locator("a[href$='/void/']").focus()
    manager.keyboard.press('Enter')
    manager.wait_for_url(f'{base}/transactions/sale/{sale_id}/void/')
    manager.locator('#id_reason').fill('Customer returned all items')
    manager.keyboard.press('Enter')
    manager.wait_for_url(f'{base}/transactions/sale/{sale_id}/')

    expect(manager.locator('.alert-success')).to_contain_text('voided. Stock restored.')
    expect(sale_status_text(manager)).to_contain_text('Voided')
    expect(manager.locator("a[href$='/void/']")).to_have_count(0)
    assert stock(manager, base, item) == 10


@pytest.mark.e2e
def test_uc_m2_1_alt1_earned_points_already_spent(e2e_server, cashier, manager):
    base = e2e_server
    item = create_item(manager, base, quantity=10, price='100.00')
    customer = create_customer(cashier, base)
    first = background_sale(cashier, base, item, customer, 1)       # earns 1 point
    background_sale(cashier, base, item, customer, 1, redeem=1)     # spends it
    assert points(cashier, base, customer) == 0

    void_via_ui(manager, base, first['sale_id'])

    expect(manager.locator('.alert-success')).to_contain_text('voided. Stock restored.')
    expect(sale_status_text(manager)).to_contain_text('Voided')
    assert points(manager, base, customer) == 0                     # nothing left to take back
    assert stock(manager, base, item) == 9                          # first sale's unit restored


@pytest.mark.e2e
def test_uc_m2_1_alt2_void_sale_with_redemption(e2e_server, cashier, manager):
    base = e2e_server
    item = create_item(manager, base, quantity=20, price='100.00')
    customer = create_customer(cashier, base)
    background_sale(cashier, base, item, customer, 10)              # 10 points
    sale = background_sale(cashier, base, item, customer, 3, redeem=5)  # 10 - 5 + 2 = 7
    assert points(cashier, base, customer) == 7
    before = stock(manager, base, item)

    void_via_ui(manager, base, sale['sale_id'])

    expect(sale_status_text(manager)).to_contain_text('Voided')
    assert points(manager, base, customer) == 10
    assert stock(manager, base, item) == before + 3


@pytest.mark.e2e
def test_uc_m2_1_alt3_manager_cancels(e2e_server, cashier, manager):
    base = e2e_server
    item, _, sale_id = _sold(cashier, manager, base)

    manager.goto(f'{base}/transactions/sale/{sale_id}/void/', wait_until='domcontentloaded')
    manager.locator('#id_reason').fill('Changed my mind')
    manager.get_by_role('link', name='Cancel').click()
    manager.wait_for_url(f'{base}/transactions/sale/{sale_id}/')

    expect(sale_status_text(manager)).to_contain_text('Completed')
    assert stock(manager, base, item) == 7


@pytest.mark.e2e
def test_uc_m2_1_exc1_already_voided(e2e_server, cashier, manager):
    base = e2e_server
    item, _, sale_id = _sold(cashier, manager, base)
    void_url = f'{base}/transactions/sale/{sale_id}/void/'
    tab_a = manager
    tab_b = manager.context.new_page()                   # a second manager tab, same sale
    tab_a.goto(void_url, wait_until='domcontentloaded')
    tab_b.goto(void_url, wait_until='domcontentloaded')

    tab_a.locator('#id_reason').fill('Returned')
    tab_a.locator("button[type='submit']:has-text('Void sale')").click()
    tab_a.wait_for_url(f'{base}/transactions/sale/{sale_id}/')
    expect(tab_a.locator('.alert-success')).to_contain_text('voided. Stock restored.')

    tab_b.locator('#id_reason').fill('Returned again')
    tab_b.locator("button[type='submit']:has-text('Void sale')").click()
    tab_b.wait_for_url(f'{base}/transactions/sale/{sale_id}/')
    expect(tab_b.locator('.alert-danger[role="alert"]')).to_contain_text('This sale has already been voided.')
    expect(sale_status_text(tab_b)).to_contain_text('Voided')
    assert stock(manager, base, item) == 10              # restored once, not twice


@pytest.mark.e2e
def test_uc_m2_1_exc2_not_a_manager(e2e_server, browser_ctx, cashier, manager):
    base = e2e_server
    item, _, sale_id = _sold(cashier, manager, base)

    cashier.goto(f'{base}/transactions/sale/{sale_id}/', wait_until='domcontentloaded')
    expect(cashier.locator("a[href$='/void/']")).to_have_count(0)
    response = cashier.goto(f'{base}/transactions/sale/{sale_id}/void/')
    assert response.status == 403

    context, anonymous = new_page(browser_ctx, base)
    anonymous.goto(f'{base}/transactions/sale/{sale_id}/void/', wait_until='domcontentloaded')
    expect(anonymous).to_have_url(re.compile(r'/accounts/login/'))
    context.close()

    manager.goto(f'{base}/transactions/sale/{sale_id}/', wait_until='domcontentloaded')
    expect(sale_status_text(manager)).to_contain_text('Completed')
    assert stock(manager, base, item) == 7


@pytest.mark.e2e
def test_uc_m2_1_exc3_reason_blank_or_too_long(e2e_server, cashier, manager):
    base = e2e_server
    item, _, sale_id = _sold(cashier, manager, base)
    void_url = f'{base}/transactions/sale/{sale_id}/void/'
    manager.goto(void_url, wait_until='domcontentloaded')

    manager.locator("button[type='submit']:has-text('Void sale')").click()   # blank
    expect(manager).to_have_url(void_url)
    expect(manager.locator('h1')).to_contain_text('Void sale')

    reason = manager.locator('#id_reason')
    reason.click()
    manager.keyboard.type('r' * 201)                      # typing stops at 200
    assert len(reason.input_value()) == 200

    manager.goto(f'{base}/transactions/sale/{sale_id}/', wait_until='domcontentloaded')
    expect(sale_status_text(manager)).to_contain_text('Completed')
    assert stock(manager, base, item) == 7


@pytest.mark.e2e
def test_uc_m2_1_exc4_sale_does_not_exist(e2e_server, manager):
    base = e2e_server
    response = manager.goto(f'{base}/transactions/sale/999999999/void/')
    assert response.status == 404
    response = manager.goto(f'{base}/transactions/sale/999999999/')
    assert response.status == 404
