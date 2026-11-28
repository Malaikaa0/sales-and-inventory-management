"""
Run an authenticated + unauthenticated OWASP ZAP passive scan against an
isolated seeded InventoryMS server and export JSON + HTML reports under
`reports/security/`.

Requires OWASP ZAP (`ZAP_2.17.0` in %LOCALAPPDATA% or PATH / Program Files)
and Java 17+.
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

BASE_DIR = Path(__file__).resolve().parents[1]
REPORTS_DIR = BASE_DIR / "reports" / "security"


def _free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _find_zap_bat():
    candidates = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "ZAP_2.17.0" / "zap.bat",
        Path(r"C:\Program Files\ZAP\Zed Attack Proxy\zap.bat"),
        Path(r"C:\Program Files (x86)\ZAP\Zed Attack Proxy\zap.bat"),
    ]
    for p in candidates:
        if p.exists():
            return p
    found = shutil.which("zap.bat")
    if found:
        return Path(found)
    raise RuntimeError("OWASP ZAP (zap.bat) not found.")


def _start_django():
    tmp_dir = Path(tempfile.mkdtemp(prefix="zap_db_"))
    db_path = tmp_dir / "zap.sqlite3"
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
    deadline = time.time() + 20
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return base_url, proc, tmp_dir
        except OSError:
            time.sleep(0.25)
    proc.kill()
    raise RuntimeError("Django server failed to start.")


def _start_zap(zap_bat):
    zap_port = _free_port()
    zap_api = f"http://127.0.0.1:{zap_port}"
    zap_jar = zap_bat.parent / "zap-2.17.0.jar"
    java_exe = shutil.which("java") or r"C:\Program Files\Eclipse Adoptium\jdk-17.0.20.101-hotspot\bin\java.exe"
    proc = subprocess.Popen(
        [
            str(java_exe),
            "-Xmx512m",
            "-jar",
            str(zap_jar),
            "-daemon",
            "-silent",
            "-host",
            "127.0.0.1",
            "-port",
            str(zap_port),
            "-config",
            "api.disablekey=true",
            "-config",
            "api.addrs.addr.name=.*",
            "-config",
            "api.addrs.addr.regex=true",
        ],
        cwd=zap_bat.parent,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    deadline = time.time() + 90
    while time.time() < deadline:
        try:
            r = requests.get(f"{zap_api}/JSON/core/view/version/", timeout=2)
            if r.status_code == 200:
                return zap_port, zap_api, proc
        except requests.RequestException:
            pass
        time.sleep(1.0)
    proc.kill()
    raise RuntimeError("OWASP ZAP daemon failed to start within 90s.")


def _browse_through_proxy(base_url, proxy_url):
    proxies = {"http": proxy_url, "https": proxy_url}

    # Unauthenticated pages
    anon = requests.Session()
    anon.proxies = proxies
    for path in ["/accounts/login/", "/accounts/register/", "/"]:
        anon.get(f"{base_url}{path}", timeout=10, allow_redirects=True)

    # Authenticated manager session exploring core workflow & admin surfaces
    sess = requests.Session()
    sess.proxies = proxies
    r = sess.get(f"{base_url}/accounts/login/", timeout=10)
    m = re.search(r'name="csrfmiddlewaretoken"\s+value="([^"]+)"', r.text)
    if m:
        sess.post(
            f"{base_url}/accounts/login/",
            data={"username": "manager", "password": "demo-pass-123", "csrfmiddlewaretoken": m.group(1)},
            headers={"Referer": f"{base_url}/accounts/login/"},
            timeout=10,
        )
    for path in [
        "/",
        "/transactions/new-sale/",
        "/transactions/sales/",
        "/transactions/sale/1/",
        "/transactions/sale/1/void/",
        "/transactions/purchases/",
        "/products/",
        "/accounts/customers/",
        "/accounts/profile/",
        "/get-items/?term=a",
        "/accounts/get_customers/?term=a",
    ]:
        sess.get(f"{base_url}{path}", timeout=10, allow_redirects=False)


def main():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    zap_bat = _find_zap_bat()

    base_url, dj_proc, db_tmp = _start_django()
    zap_proc = None
    zap_api = None
    try:
        zap_port, zap_api, zap_proc = _start_zap(zap_bat)
        # Clear any prior ZAP session so alerts are strictly from this run
        requests.get(f"{zap_api}/JSON/core/action/newSession/", params={"overwrite": "true"}, timeout=10)
        proxy_url = f"http://127.0.0.1:{zap_port}"

        # Passively record unauthenticated + authenticated traffic through ZAP proxy
        _browse_through_proxy(base_url, proxy_url)

        # Also run ZAP traditional spider on the unauthenticated entry points
        scan_resp = requests.get(
            f"{zap_api}/JSON/spider/action/scan/",
            params={"url": f"{base_url}/accounts/login/", "maxChildren": 30, "recurse": "true"},
            timeout=10,
        ).json()
        scan_id = scan_resp.get("scan")
        if scan_id is not None:
            for _ in range(45):
                status = requests.get(
                    f"{zap_api}/JSON/spider/view/status/", params={"scanId": scan_id}, timeout=5
                ).json()
                if int(status.get("status", 100)) >= 100:
                    break
                time.sleep(0.5)

        # Wait for passive scanner queue to drain
        for _ in range(60):
            rem = requests.get(f"{zap_api}/JSON/pscan/view/recordsToScan/", timeout=5).json()
            if int(rem.get("recordsToScan", 0)) == 0:
                break
            time.sleep(0.5)

        alerts_data = requests.get(
            f"{zap_api}/JSON/core/view/alerts/", params={"baseurl": base_url}, timeout=15
        ).json()
        html_report = requests.get(f"{zap_api}/OTHER/core/other/htmlreport/", timeout=15).text

        (REPORTS_DIR / "zap-passive-alerts.json").write_text(
            json.dumps(alerts_data, indent=2), encoding="utf-8"
        )
        (REPORTS_DIR / "zap-passive-report.html").write_text(html_report, encoding="utf-8")

        # Summarize unique alerts by risk & name
        unique = {}
        for a in alerts_data.get("alerts", []):
            key = (a.get("risk"), a.get("alert"))
            unique.setdefault(key, {"risk": a.get("risk"), "alert": a.get("alert"), "cweid": a.get("cweid"), "count": 0, "url_sample": a.get("url")})
            unique[key]["count"] += 1

        summary = sorted(unique.values(), key=lambda x: {"High": 0, "Medium": 1, "Low": 2, "Informational": 3}.get(x["risk"], 9))
        (REPORTS_DIR / "zap-passive-summary.json").write_text(
            json.dumps({"total_alert_instances": len(alerts_data.get("alerts", [])), "unique_alerts": summary}, indent=2),
            encoding="utf-8",
        )
        print(json.dumps({"total_alert_instances": len(alerts_data.get("alerts", [])), "unique_alerts": summary}, indent=2))
    finally:
        if zap_api:
            try:
                requests.get(f"{zap_api}/JSON/core/action/shutdown/", timeout=5)
            except requests.RequestException:
                pass
        if zap_proc and zap_proc.poll() is None:
            try:
                zap_proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                zap_proc.kill()
        if dj_proc.poll() is None:
            dj_proc.terminate()
            try:
                dj_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                dj_proc.kill()
        shutil.rmtree(db_tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
