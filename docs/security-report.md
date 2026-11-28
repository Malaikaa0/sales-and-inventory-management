# Security Testing Report

**Owner:** Member 3  
**Scope:** Role-based access control (`accounts/permissions.py`), session/CSRF/header middleware (`accounts/middleware.py`, `InventoryMS/middleware.py`), dependency vulnerabilities (`requirements.txt` / `.venv`), and OWASP ZAP passive scanning.  
**Evidence:** [access-matrix.md](access-matrix.md), [tests/team/security/test_access_matrix.py](../tests/team/security/test_access_matrix.py), [reports/security/](../reports/security/)

---

## 1. Automated Access Control & Hardening Checks (`pytest`)

Command:
```powershell
$env:DEBUG="True"
.\.venv\Scripts\python.exe -m pytest tests/team/security -v
```

Result: **35 / 35 PASSED** across 8 test groups:
- **Anonymous isolation (12 checks):** All protected GET endpoints and state-changing POST mutations (`/transactions/new-sale/`, `/transactions/sale/<pk>/void/`) redirect (`302`) to `/accounts/login/` without modifying stock or sales.
- **Immediate profile revocation (2 checks):** Authenticated sessions for `PEN` (Pending) and `INA` (Inactive) staff are immediately logged out by `ActiveProfileMiddleware` (`_auth_user_id` cleared from session).
- **Operative (`OP`) least-privilege enforcement (14 checks):** Denied (`403`) on sale voiding, Excel exports, purchase orders, product creation, table `? _export=xlsx`, vendors, bills, invoices, customer loyalty adjustment, and staff administration.
- **Executive (`EX`) boundary (3 checks):** Denied (`403`) on staff directory, staff creation, approval, and deletion.
- **Admin (`AD`) verification (1 check):** Allowed (`200`) on staff administration routes.
- **CSRF protection (1 check):** `Client(enforce_csrf_checks=True)` blocks `POST /transactions/new-sale/` and `POST /transactions/sale/<pk>/void/` with `403` when `X-CSRFToken` / CSRF token is omitted.
- **Security headers (1 check):** Verified `Content-Security-Policy`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Cross-Origin-Resource-Policy: same-origin`, `Cross-Origin-Embedder-Policy: require-corp`, and `Permissions-Policy`.
- **Login brute-force throttling (1 check):** Locked out after `LOGIN_MAX_ATTEMPTS` failed attempts (`Too many failed attempts. Try again in a few minutes.`), blocking even the valid password during lockout.

---

## 2. Dependency Vulnerability Audit (`pip-audit`)

Command:
```powershell
.\.venv\Scripts\python.exe -m pip_audit --local --format json -o reports/security/pip-audit.json
```

Result: **No known vulnerabilities found** across all installed dependencies (Django 5.2.19, WeasyPrint 70.0, Pillow 13.0.0, openpyxl 3.1.5, whitenoise 6.12.0, psycopg2-binary 2.9.13, etc.).  
Evidence: [reports/security/pip-audit.json](../reports/security/pip-audit.json), [reports/security/pip-audit.txt](../reports/security/pip-audit.txt).

---

## 3. OWASP ZAP 2.17.0 Passive Scan

Executed [tools/run_zap_passive.py](../tools/run_zap_passive.py) against an isolated seeded InventoryMS server (`DEBUG=True`) with both unauthenticated spidering and authenticated `manager` browsing across all W1/W2, inventory, customer, and purchase endpoints.

### Summary (`reports/security/zap-passive-summary.json`)

| Risk | Unique Alerts | Instances | Triage & Analysis |
| --- | --- | --- | --- |
| **High** | **0** | **0** | None |
| **Medium** | **1** | **4** | `Content Security Policy (CSP) Header Not Set` (CWE-693) — occurred exclusively on **404 responses** (`/sitemap.xml`, `/robots.txt`, `/update/`, `/delete/`) because `InventoryMS/middleware.py:32` intentionally skips CSP on `DEBUG=True` error pages (`response.status_code >= 400`). Production (`DEBUG=False`) applies CSP on all custom error pages. **Every 200 HTML page had strict CSP.** |
| **Low** | **2** | **27** | 1) `Server Leaks Version Information` (24 instances) — Django dev `runserver` `WSGIServer/0.2` header; mitigated in production by `gunicorn` + Azure reverse proxy.<br>2) `X-Content-Type-Options Header Missing` (3 instances) — Django `DEBUG=True` static dev handler on `/static/...`; mitigated in production by `WhiteNoise` + `SecurityMiddleware`. |
| **Informational** | **4** | **29** | Session/auth identification (`19`), `Modern Web Application` (`1`), and form attribute detection (`9` on login/register). |

Evidence: [reports/security/zap-passive-report.html](../reports/security/zap-passive-report.html), [reports/security/zap-passive-alerts.json](../reports/security/zap-passive-alerts.json), [reports/security/zap-passive-summary.json](../reports/security/zap-passive-summary.json).
