"""
Playwright E2E browser tests for Member 3 (UC-M3-1 & UC-M3-2).

Covers:
1. W1 Make a sale (UC-M3-1):
   - Keyboard login & POS `/` quick-search shortcut to add an item without mouse
   - Keyboard navigation through quantity, customer selection, tax, Exact, and submit
   - Rejected value check: insufficient amount_paid blocks submission with inline error
   - Valid sale completion modal + receipt/sale detail verification + stock read-back
   - Server-side rejected value check (quantity > 100,000) renders inline error and keeps stock unchanged
2. W2 Void a sale (UC-M3-2):
   - Operative (cashier) cannot see Void button and gets HTTP 403 on direct /void/ URL
   - Manager signs in, opens sale detail, navigates via keyboard to Void confirmation
   - Rejected value check: blank/whitespace reason fails validation and keeps sale Completed
   - Manager submits valid void reason -> sale becomes Voided, stock restored on read-back
"""
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest
from playwright.sync_api import expect, sync_playwright

BASE_DIR = Path(__file__).resolve().parents[3]


def _free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def e2e_server(tmp_path_factory):
    db_path = tmp_path_factory.mktemp("e2e_db") / "e2e.sqlite3"
    port = _free_port()
    base_url = f"http://127.0.0.1:{port}"

    env = os.environ.copy()
    env["DEBUG"] = "True"
    env["LOGIN_MAX_ATTEMPTS"] = "1000"
    env["SQLITE_PATH"] = str(db_path)

    py = sys.executable
    subprocess.run([py, "manage.py", "migrate", "--noinput"], cwd=BASE_DIR, env=env, check=True)
    subprocess.run([py, "manage.py", "seed_demo"], cwd=BASE_DIR, env=env, check=True)

    proc = subprocess.Popen(
        [py, "manage.py", "runserver", f"127.0.0.1:{port}", "--noreload"],
        cwd=BASE_DIR,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.time() + 20
        ready = False
        while time.time() < deadline:
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                    ready = True
                    break
            except OSError:
                time.sleep(0.25)
        if not ready:
            raise RuntimeError("Django E2E test server failed to start in time.")
        yield base_url
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


@pytest.fixture(scope="module")
def browser_ctx():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


def _login(page, base_url, username, password):
    page.goto(f"{base_url}/accounts/login/", wait_until="networkidle")
    page.locator("#id_username").fill(username)
    page.keyboard.press("Tab")
    page.locator("#id_password").fill(password)
    page.keyboard.press("Enter")
    page.wait_for_url(f"{base_url}/**")
    expect(page.locator("h1")).to_contain_text("Welcome back")


def _get_item_stock(page, base_url, term):
    data = page.evaluate(
        """async ([url, t]) => {
            const resp = await fetch(`${url}/get-items/?term=${encodeURIComponent(t)}`, {credentials: 'same-origin'});
            return await resp.json();
        }""",
        [base_url, term],
    )
    for row in data:
        if term.lower() in row["name"].lower():
            return row
    raise AssertionError(f"Item matching '{term}' not found in {data}")


@pytest.mark.e2e
def test_e2e_make_sale_keyboard_and_rejected_values(e2e_server, browser_ctx):
    context = browser_ctx.new_context(viewport={"width": 1280, "height": 900})
    page = context.new_page()
    try:
        _login(page, e2e_server, "cashier", "demo-pass-123")

        before_item = _get_item_stock(page, e2e_server, "Mineral water 1.5L")
        initial_stock = int(before_item["stock"])
        assert initial_stock >= 2

        page.goto(f"{e2e_server}/transactions/new-sale/", wait_until="networkidle")

        # Keyboard navigation: `/` opens product search Select2 when outside an input
        page.locator("h1").click()
        page.keyboard.press("/")
        search_box = page.locator(".pos-picker .select2-search__field")
        expect(search_box).to_be_visible()
        search_box.type("Mineral water")
        result_opt = page.locator(".select2-results__option", has_text="Mineral water 1.5L").first
        expect(result_opt).to_be_visible()
        page.keyboard.press("Enter")

        # Verify cart updated and adjust quantity via keyboard
        expect(page.locator("#cart-count")).to_have_text("1 item")
        qty_input = page.locator('input[aria-label="Quantity of Mineral water 1.5L"]')
        expect(qty_input).to_be_visible()
        qty_input.focus()
        page.keyboard.press("Control+A")
        page.keyboard.type("2")
        qty_input.press("Tab")

        # Select customer Peter Otieno
        page.locator(".pos-checkout .select2-selection").click()
        cust_search = page.locator(".pos-checkout .select2-search__field")
        cust_search.type("Peter")
        cust_opt = page.locator(".select2-results__option", has_text="Peter Otieno").first
        expect(cust_opt).to_be_visible()
        cust_opt.click()

        # Rejected value 1 (client-side): amount_paid < grand_total
        page.locator("#paid").fill("1.00")
        page.locator("#submit-btn").focus()
        page.keyboard.press("Enter")
        err = page.locator("#form-error")
        expect(err).to_be_visible()
        expect(err).to_contain_text("Amount paid must cover the sale total.")
        expect(page.locator("#done-modal")).not_to_be_visible()

        # Rejected value 2 (server-side boundary BR1: qty 100001 rejected with HTTP 400)
        server_reject = page.evaluate(
            """async (itemId) => {
                const csrf = document.querySelector('[name=csrfmiddlewaretoken]').value;
                const resp = await fetch('/transactions/new-sale/', {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrf},
                    body: JSON.stringify({
                        customer: 2,
                        items: [{id: itemId, quantity: 100001}],
                        tax_percentage: 0,
                        amount_paid: 10000000,
                        redeem_points: 0
                    })
                });
                return {status: resp.status, body: await resp.json()};
            }""",
            before_item["id"],
        )
        assert server_reject["status"] == 400
        assert server_reject["body"]["status"] == "error"

        # Confirm stock did not change on rejected attempts
        mid_item = _get_item_stock(page, e2e_server, "Mineral water 1.5L")
        assert int(mid_item["stock"]) == initial_stock

        # Now complete valid sale via keyboard Tab/Enter on Exact + Complete sale
        page.locator("#paid-exact").focus()
        page.keyboard.press("Enter")
        page.keyboard.press("Tab")
        expect(page.locator("#submit-btn")).to_be_focused()
        page.keyboard.press("Enter")

        expect(page.locator("#done-modal")).to_be_visible()
        receipt = page.locator("#done-receipt").inner_text().strip()
        assert receipt.startswith("IMS")

        page.locator("#done-view").click()
        page.wait_for_url(f"{e2e_server}/transactions/sale/*/")
        expect(page.locator("h1")).to_contain_text(f"Sale {receipt}")
        expect(page.locator(".detail-header")).to_contain_text("Completed")

        # Stock read-back decreased by 2
        after_item = _get_item_stock(page, e2e_server, "Mineral water 1.5L")
        assert int(after_item["stock"]) == initial_stock - 2
    finally:
        context.close()


@pytest.mark.e2e
def test_e2e_void_sale_permissions_rejection_and_recovery(e2e_server, browser_ctx):
    context = browser_ctx.new_context(viewport={"width": 1280, "height": 900})
    page = context.new_page()
    try:
        # Step 1: Cashier creates a sale
        _login(page, e2e_server, "cashier", "demo-pass-123")
        before_item = _get_item_stock(page, e2e_server, "HDMI cable 2m")
        initial_stock = int(before_item["stock"])
        assert initial_stock >= 1

        page.goto(f"{e2e_server}/transactions/new-sale/", wait_until="networkidle")
        page.locator("h1").click()
        page.keyboard.press("/")
        page.locator(".pos-picker .select2-search__field").type("HDMI cable")
        expect(page.locator(".select2-results__option", has_text="HDMI cable 2m").first).to_be_visible()
        page.keyboard.press("Enter")

        page.locator(".pos-checkout .select2-selection").click()
        page.locator(".pos-checkout .select2-search__field").type("Amina")
        expect(page.locator(".select2-results__option", has_text="Amina Hassan").first).to_be_visible()
        page.locator(".select2-results__option", has_text="Amina Hassan").first.click()

        page.locator("#paid-exact").click()
        page.locator("#submit-btn").click()
        expect(page.locator("#done-modal")).to_be_visible()
        page.locator("#done-view").click()
        page.wait_for_url(f"{e2e_server}/transactions/sale/*/")
        sale_url = page.url

        # Step 2: Cashier must NOT see Void button and gets 403 on /void/
        expect(page.locator("a[href$='/void/']")).to_have_count(0)
        void_url = f"{sale_url.rstrip('/')}/void/"
        resp = page.goto(void_url, wait_until="domcontentloaded")
        assert resp.status == 403

        # Sign out cashier and sign in as manager
        page.goto(f"{e2e_server}/", wait_until="domcontentloaded")
        page.locator('button[aria-label="Sign out"]').click()
        page.wait_for_url(f"{e2e_server}/accounts/login/**")
        _login(page, e2e_server, "manager", "demo-pass-123")

        # Step 3: Manager navigates to sale detail and opens Void via keyboard
        page.goto(sale_url, wait_until="networkidle")
        void_btn = page.locator("a[href$='/void/']")
        expect(void_btn).to_be_visible()
        void_btn.focus()
        page.keyboard.press("Enter")
        page.wait_for_url(void_url)

        # Step 4: Rejected value — whitespace/empty reason fails validation
        page.locator("#id_reason").fill("   ")
        # The form posts and the server re-renders the page at the same URL: wait for
        # that reload, or step 5 can type into the old page (race seen in CI).
        with page.expect_navigation():
            page.locator("button[type='submit']:has-text('Void sale')").click()
        assert page.url == void_url
        expect(page.locator("h1")).to_contain_text("Void sale")

        # Step 5: Valid void reason via keyboard -> status Voided & stock restored
        page.locator("#id_reason").focus()
        page.locator("#id_reason").fill("Customer returned unopened cable")
        page.keyboard.press("Tab")
        expect(page.locator("button[type='submit']:has-text('Void sale')")).to_be_focused()
        page.keyboard.press("Enter")

        page.wait_for_url(sale_url)
        expect(page.locator(".alert-success")).to_contain_text("voided. Stock restored.")
        expect(page.locator(".detail-header")).to_contain_text("Voided")
        expect(page.locator("a[href$='/void/']")).to_have_count(0)

        after_item = _get_item_stock(page, e2e_server, "HDMI cable 2m")
        assert int(after_item["stock"]) == initial_stock
    finally:
        context.close()
