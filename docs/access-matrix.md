
# Role-Based Access Control (RBAC) Matrix

**Owner:** Member 3  
**Source of truth:** `accounts/permissions.py`, `accounts/middleware.py`, `InventoryMS/middleware.py`, and URL configurations across `store`, `transactions`, `accounts`, `invoice`, `bills`.  
**Automated verification:** [tests/team/security/test_access_matrix.py](../tests/team/security/test_access_matrix.py)

## Roles & Account States

| Principal | Definition | Expected Behaviour |
| --- | --- | --- |
| **Anonymous** | Unauthenticated session | Redirected (`302`) to `/accounts/login/?next=...` on all protected routes. |
| **Inactive / Pending (`PEN`, `INA`)** | Authenticated user with `profile.status != 'A'` or `user.is_active == False` | Immediately signed out by `ActiveProfileMiddleware` and redirected (`302`) to `/accounts/login/`. |
| **Operative (`OP`)** | Cashier / point-of-sale staff (`role_level = 1`) | Can view dashboard, make sales, view sales/receipts, view products/customers/deliveries/invoices. Denied (`403`) on voids, purchases, exports, vendors, bills, product/category mutations, loyalty adjustments, and staff admin. |
| **Executive (`EX`)** | Manager (`role_level = 2`) | All Operative permissions + void sales, purchases, Excel exports, products/categories/vendors/bills/invoices mutations, loyalty adjustment, customer delete. Denied (`403`) on staff administration. |
| **Admin (`AD`)** | System admin / superuser (`role_level = 3`) | Full access including staff directory, staff creation, profile updates, approval, and deletion. |

## Endpoint Access Matrix

| Endpoint | Method | Workflow / Area | Anon | Inactive | Operative (`OP`) | Executive (`EX`) | Admin (`AD`) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `/accounts/login/` | GET | Auth | 200 | 200 | 200 | 200 | 200 |
| `/` | GET | Dashboard | 302 | 302 | 200 | 200 | 200 |
| `/transactions/new-sale/` | GET / POST | W1 Make a sale | 302 | 302 | 200 / 200* | 200 / 200* | 200 / 200* |
| `/get-items/` | GET | W1 POS item search | 302 | 302 | 200 | 200 | 200 |
| `/accounts/get_customers/` | GET | W1 POS customer search | 302 | 302 | 200 | 200 | 200 |
| `/transactions/sales/` | GET | Sales list | 302 | 302 | 200 | 200 | 200 |
| `/transactions/sale/<pk>/` | GET | Sale detail | 302 | 302 | 200 | 200 | 200 |
| `/transactions/sale/<pk>/void/` | GET / POST | W2 Void a sale | 302 | 302 | **403** | 200 / 302 | 200 / 302 |
| `/transactions/sales/export/` | GET | Sales Excel export | 302 | 302 | **403** | 200 | 200 |
| `/transactions/purchases/` | GET | Purchase orders | 302 | 302 | **403** | 200 | 200 |
| `/transactions/new-purchase/` | GET | Create purchase | 302 | 302 | **403** | 200 | 200 |
| `/transactions/purchases/export/` | GET | Purchases Excel export | 302 | 302 | **403** | 200 | 200 |
| `/products/?_export=xlsx` | GET | Products table export | 302 | 302 | **403** | 200 | 200 |
| `/new-product/` | GET | Create product | 302 | 302 | **403** | 200 | 200 |
| `/accounts/customers/<pk>/loyalty/` | POST | Adjust customer loyalty | 302 | 302 | **403** | 302 / 200 | 302 / 200 |
| `/accounts/vendors/` | GET | Vendors list | 302 | 302 | **403** | 200 | 200 |
| `/bills/bills/` | GET | Bills list | 302 | 302 | **403** | 200 | 200 |
| `/invoice/new-invoice/` | GET | Create invoice | 302 | 302 | **403** | 200 | 200 |
| `/accounts/profiles/` | GET | Staff directory | 302 | 302 | **403** | **403** | 200 |
| `/accounts/new-profile/` | GET | Create staff | 302 | 302 | **403** | **403** | 200 |
| `/accounts/profile/<pk>/approve/` | POST | Approve staff | 302 | 302 | **403** | **403** | 302 |
| `/accounts/profile/<pk>/delete/` | GET | Delete staff | 302 | 302 | **403** | **403** | 200 |

*\*Valid JSON payload returns `200`; invalid JSON payload returns `400`.*

## Security Controls Verified

1. **Role & Capability Enforcement:** All business endpoints enforce `RoleRequiredMixin`, `ManagerRequiredMixin`, `Staff*RequiredMixin`, `@role_required(...)`, or `@capability_required(...)` (`FR10`, `BR4`).
2. **Immediate Revocation (`ActiveProfileMiddleware`):** Pending or deactivated staff profiles cannot reuse an existing authenticated session.
3. **CSRF & Cookie Hardening:** `SESSION_COOKIE_HTTPONLY = True`, `CSRF_COOKIE_HTTPONLY = True`, and `CsrfViewMiddleware` active on state-changing POST requests (`new-sale`, `void`, `approve`).
4. **Browser Security Headers (`SecurityHeadersMiddleware`):** Enforces `Content-Security-Policy`, `Permissions-Policy`, `Cross-Origin-Embedder-Policy`, `Cross-Origin-Resource-Policy`, and `X-Frame-Options`.
5. **Login Throttling:** `LOGIN_MAX_ATTEMPTS` locks repeated invalid login attempts for a username/IP pair (`LOGIN_LOCKOUT_SECONDS`).
