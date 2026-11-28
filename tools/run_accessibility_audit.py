"""
Run axe-core (via Playwright) and Google Lighthouse accessibility/usability audits
against an isolated seeded InventoryMS server, saving JSON and HTML reports.

Usage:
    python tools/run_accessibility_audit.py before
    python tools/run_accessibility_audit.py after
"""
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import requests
from axe_playwright_python.sync_playwright import Axe
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parents[1]
REPORTS_DIR = BASE_DIR / "reports" / "accessibility"


def _free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _start_server():
    tmp_dir = Path(tempfile.mkdtemp(prefix="a11y_db_"))
    db_path = tmp_dir / "a11y.sqlite3"
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
    deadline = time.time() + 25
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return base_url, proc, tmp_dir
        except OSError:
            time.sleep(0.25)
    proc.kill()
    raise RuntimeError("Django server failed to start for accessibility audit.")


def _login_session_cookie(base_url):
    sess = requests.Session()
    r = sess.get(f"{base_url}/accounts/login/", timeout=10)
    m = re.search(r'name="csrfmiddlewaretoken"\s+value="([^"]+)"', r.text)
    if not m:
        raise RuntimeError("Could not find CSRF token on login page")
    resp = sess.post(
        f"{base_url}/accounts/login/",
        data={"username": "cashier", "password": "demo-pass-123", "csrfmiddlewaretoken": m.group(1)},
        headers={"Referer": f"{base_url}/accounts/login/"},
        timeout=10,
    )
    resp.raise_for_status()
    sessionid = sess.cookies.get("sessionid")
    if not sessionid:
        raise RuntimeError("Login failed: no sessionid cookie")
    return sessionid


def run_axe(base_url, phase):
    screens = [
        ("login", "/accounts/login/", False),
        ("dashboard", "/", True),
        ("new-sale", "/transactions/new-sale/", True),
        ("sales-list", "/transactions/sales/", True),
    ]
    results = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()

        # Login first when needed
        logged_in = False
        axe = Axe()
        for name, path, needs_auth in screens:
            if needs_auth and not logged_in:
                page.goto(f"{base_url}/accounts/login/", wait_until="domcontentloaded")
                page.locator("#id_username").fill("cashier")
                page.locator("#id_password").fill("demo-pass-123")
                page.locator("button[type='submit']").click()
                page.wait_for_url(f"{base_url}/**")
                logged_in = True
            page.goto(f"{base_url}{path}", wait_until="networkidle")
            res = axe.run(page)
            raw = res.response
            results[name] = {
                "url": path,
                "violations_count": len(raw.get("violations", [])),
                "passes_count": len(raw.get("passes", [])),
                "incomplete_count": len(raw.get("incomplete", [])),
                "violations": [
                    {
                        "id": v["id"],
                        "impact": v.get("impact"),
                        "description": v.get("description"),
                        "help": v.get("help"),
                        "nodes": [
                            {"target": n.get("target"), "html": n.get("html"), "failureSummary": n.get("failureSummary")}
                            for n in v.get("nodes", [])
                        ],
                    }
                    for v in raw.get("violations", [])
                ],
            }
        context.close()
        browser.close()

    out_path = REPORTS_DIR / f"axe-{phase}.json"
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return results


def run_lighthouse(base_url, sessionid, phase):
    lh_cmd = shutil.which("lighthouse") or shutil.which("lighthouse.cmd")
    if not lh_cmd:
        npm_bin = Path(os.environ.get("APPDATA", "")) / "npm" / "lighthouse.cmd"
        if npm_bin.exists():
            lh_cmd = str(npm_bin)
        else:
            raise RuntimeError("lighthouse CLI not found on PATH")

    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    env = os.environ.copy()
    if Path(chrome_path).exists():
        env["CHROME_PATH"] = chrome_path

    headers_file = REPORTS_DIR / f"_lh_headers_{phase}.json"
    headers_file.write_text(json.dumps({"Cookie": f"sessionid={sessionid}"}), encoding="utf-8")
    out_prefix = REPORTS_DIR / f"lighthouse-dashboard-{phase}"
    try:
        cmd = [
            lh_cmd,
            f"{base_url}/",
            "--only-categories=accessibility,best-practices,performance,seo",
            "--output=json",
            "--output=html",
            f"--output-path={out_prefix}",
            f"--extra-headers={headers_file}",
            "--chrome-flags=--headless --no-sandbox --disable-gpu",
            "--quiet",
        ]
        subprocess.run(cmd, env=env, check=True)
    finally:
        if headers_file.exists():
            headers_file.unlink()

    json_path = Path(f"{out_prefix}.report.json")
    data = json.loads(json_path.read_text(encoding="utf-8"))
    cats = data.get("categories", {})
    summary = {
        k: {
            "title": v.get("title"),
            "score": round((v.get("score") or 0) * 100),
        }
        for k, v in cats.items()
    }
    failing_a11y = [
        {
            "id": ref.get("id"),
            "title": data["audits"][ref["id"]].get("title"),
            "score": data["audits"][ref["id"]].get("score"),
        }
        for ref in cats.get("accessibility", {}).get("auditRefs", [])
        if ref.get("id") and data["audits"].get(ref["id"], {}).get("score") == 0
    ]
    return {"scores": summary, "failing_accessibility_audits": failing_a11y}


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("before", "after"):
        print("Usage: python tools/run_accessibility_audit.py <before|after>")
        sys.exit(2)
    phase = sys.argv[1]
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    base_url, proc, tmp_dir = _start_server()
    try:
        sessionid = _login_session_cookie(base_url)
        axe_res = run_axe(base_url, phase)
        lh_res = run_lighthouse(base_url, sessionid, phase)
        summary = {"phase": phase, "axe": axe_res, "lighthouse": lh_res}
        (REPORTS_DIR / f"summary-{phase}.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        axe_counts = {k: v["violations_count"] for k, v in axe_res.items()}
        print(json.dumps({"phase": phase, "lighthouse": lh_res, "axe_counts": axe_counts}, indent=2))
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
