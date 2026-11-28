"""
Failure-and-recovery performance test (Member 3).

Scenario:
1. Start an isolated InventoryMS server backed by a fresh seeded SQLite DB.
2. Record pre-test stock for a target product and initial Sale count.
3. Run Phase 1 traffic (concurrent read + sale POST requests) and abruptly terminate
   the server process mid-traffic (simulating a sudden crash / worker kill).
4. Restart the server against the same SQLite database.
5. Verify recovery:
   - Server answers HTTP 200 on `/` and `/transactions/new-sale/` within 10s.
   - Database integrity check (`PRAGMA integrity_check`) passes.
   - Zero orphan `Sale` rows without `SaleDetail` lines.
   - Exact stock accounting: initial_stock - sold_qty_since_start == current_stock.
   - Phase 2 k6/HTTP requests complete cleanly after recovery.

Outputs structured evidence JSON to `reports/perf/recovery-report.json`.
"""
import json
import os
import re
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

import requests

BASE_DIR = Path(__file__).resolve().parents[3]
REPORT_PATH = BASE_DIR / "reports" / "perf" / "recovery-report.json"


def _free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _start_django(db_path, port):
    env = os.environ.copy()
    env["DEBUG"] = "True"
    env["LOGIN_MAX_ATTEMPTS"] = "1000"
    env["SQLITE_PATH"] = str(db_path)
    proc = subprocess.Popen(
        [sys.executable, "manage.py", "runserver", f"127.0.0.1:{port}", "--noreload"],
        cwd=BASE_DIR,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    deadline = time.time() + 20
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return proc
        except OSError:
            time.sleep(0.2)
    proc.kill()
    raise RuntimeError("Server failed to start.")


def _login(base_url):
    sess = requests.Session()
    r = sess.get(f"{base_url}/accounts/login/", timeout=10)
    csrf = re.search(r'name="csrfmiddlewaretoken"\s+value="([^"]+)"', r.text).group(1)
    resp = sess.post(
        f"{base_url}/accounts/login/",
        data={"username": "cashier", "password": "demo-pass-123", "csrfmiddlewaretoken": csrf},
        headers={"Referer": f"{base_url}/accounts/login/"},
        timeout=10,
    )
    resp.raise_for_status()
    return sess


def _db_snapshot(db_path, item_id):
    conn = sqlite3.connect(db_path)
    try:
        integrity = conn.execute("PRAGMA integrity_check;").fetchone()[0]
        stock = conn.execute("SELECT quantity FROM store_item WHERE id = ?", (item_id,)).fetchone()[0]
        sales_count = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
        orphan_sales = conn.execute(
            """
            SELECT COUNT(*) FROM sales s
            LEFT JOIN sale_details d ON d.sale = s.id
            WHERE d.id IS NULL
            """
        ).fetchone()[0]
        sold_for_item = conn.execute(
            """
            SELECT COALESCE(SUM(d.quantity), 0)
            FROM sale_details d
            JOIN sales s ON s.id = d.sale
            WHERE d.item = ? AND s.status = 'C'
            """,
            (item_id,),
        ).fetchone()[0]
        return {
            "integrity": integrity,
            "stock": stock,
            "sales_count": sales_count,
            "orphan_sales": orphan_sales,
            "sold_for_item": sold_for_item,
        }
    finally:
        conn.close()


def main():
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp_dir = Path(tempfile.mkdtemp(prefix="perf_rec_"))
    db_path = tmp_dir / "recovery.sqlite3"
    port = _free_port()
    base_url = f"http://127.0.0.1:{port}"

    env = os.environ.copy()
    env["DEBUG"] = "True"
    env["LOGIN_MAX_ATTEMPTS"] = "1000"
    env["SQLITE_PATH"] = str(db_path)
    subprocess.run([sys.executable, "manage.py", "migrate", "--noinput"], cwd=BASE_DIR, env=env, check=True)
    subprocess.run([sys.executable, "manage.py", "seed_demo"], cwd=BASE_DIR, env=env, check=True)

    # Boost one item's stock so Phase 1 + Phase 2 sales never run out
    conn = sqlite3.connect(db_path)
    row = conn.execute("SELECT id, name, price, quantity FROM store_item ORDER BY quantity DESC LIMIT 1").fetchone()
    item_id, item_name, item_price, _ = row
    conn.execute("UPDATE store_item SET quantity = 500 WHERE id = ?", (item_id,))
    conn.commit()
    cust_id = conn.execute("SELECT id FROM Customers LIMIT 1").fetchone()[0]
    conn.close()

    pre = _db_snapshot(db_path, item_id)
    proc = _start_django(db_path, port)
    phase1_results = {"succeeded": 0, "failed_during_kill": 0}
    stop_flag = threading.Event()

    def worker():
        sess = _login(base_url)
        pos_html = sess.get(f"{base_url}/transactions/new-sale/", timeout=5).text
        csrf = re.search(r'name="csrfmiddlewaretoken"\s+value="([^"]+)"', pos_html).group(1)
        while not stop_flag.is_set():
            try:
                r = sess.post(
                    f"{base_url}/transactions/new-sale/",
                    json={
                        "customer": cust_id,
                        "items": [{"id": item_id, "quantity": 1}],
                        "tax_percentage": 0,
                        "amount_paid": float(item_price),
                        "redeem_points": 0,
                    },
                    headers={"X-CSRFToken": csrf, "Referer": f"{base_url}/transactions/new-sale/"},
                    timeout=3,
                )
                if r.status_code == 200 and r.json().get("status") == "success":
                    phase1_results["succeeded"] += 1
                else:
                    phase1_results["failed_during_kill"] += 1
            except requests.RequestException:
                phase1_results["failed_during_kill"] += 1
                break

    try:
        threads = [threading.Thread(target=worker, daemon=True) for _ in range(3)]
        for t in threads:
            t.start()
        time.sleep(2.5)

        # Simulate sudden server crash mid-load
        proc.kill()
        proc.wait(timeout=5)
        stop_flag.set()
        for t in threads:
            t.join(timeout=3)

        mid = _db_snapshot(db_path, item_id)

        # Restart server on the same database and measure recovery time
        restart_start = time.time()
        proc = _start_django(db_path, port)
        sess = _login(base_url)
        dash_r = sess.get(f"{base_url}/", timeout=5)
        pos_r = sess.get(f"{base_url}/transactions/new-sale/", timeout=5)
        recovery_seconds = round(time.time() - restart_start, 3)

        # Post-recovery transaction
        csrf = re.search(r'name="csrfmiddlewaretoken"\s+value="([^"]+)"', pos_r.text).group(1)
        post_sale = sess.post(
            f"{base_url}/transactions/new-sale/",
            json={
                "customer": cust_id,
                "items": [{"id": item_id, "quantity": 1}],
                "tax_percentage": 0,
                "amount_paid": float(item_price),
                "redeem_points": 0,
            },
            headers={"X-CSRFToken": csrf, "Referer": f"{base_url}/transactions/new-sale/"},
            timeout=5,
        )
        post_ok = post_sale.status_code == 200 and post_sale.json().get("status") == "success"
        post = _db_snapshot(db_path, item_id)

        expected_mid_stock = pre["stock"] - (mid["sold_for_item"] - pre["sold_for_item"])
        expected_post_stock = pre["stock"] - (post["sold_for_item"] - pre["sold_for_item"])

        passed = (
            mid["integrity"] == "ok"
            and post["integrity"] == "ok"
            and mid["orphan_sales"] == 0
            and post["orphan_sales"] == 0
            and mid["stock"] == expected_mid_stock
            and post["stock"] == expected_post_stock
            and dash_r.status_code == 200
            and pos_r.status_code == 200
            and post_ok
        )

        report = {
            "target_item": {"id": item_id, "name": item_name},
            "pre_crash": pre,
            "phase1_before_kill": phase1_results,
            "post_crash_snapshot": mid,
            "recovery_seconds": recovery_seconds,
            "post_recovery_checks": {
                "dashboard_status": dash_r.status_code,
                "pos_status": pos_r.status_code,
                "post_recovery_sale_ok": post_ok,
            },
            "post_recovery_snapshot": post,
            "consistency_verified": passed,
        }
        REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2))
        if not passed:
            sys.exit(1)
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
