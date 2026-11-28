# Accessibility & Usability Audit Report (Lighthouse & axe-core)

**Owner:** Member 3  
**Tooling:** Google Lighthouse (via Node.js `lighthouse` CLI + Chrome headless) and `axe-core` (via `axe-playwright-python` + Playwright Chromium 159).  
**Evidence directory:** [reports/accessibility/](../reports/accessibility/)  
**Runner script:** [tools/run_accessibility_audit.py](../tools/run_accessibility_audit.py)

---

## 1. Before-Fix Baseline Audit

Audited against an isolated seeded InventoryMS server (`python manage.py seed_demo`) as signed-in `cashier` (`Operative`), plus unauthenticated `/accounts/login/`.

### 1.1 Lighthouse — Dashboard (`/`) Before Fix

| Category | Score | Notes |
| --- | --- | --- |
| Performance | **99** | Strong baseline |
| Accessibility | **95** | Failed 2 audits (`color-contrast`, `td-has-header`) |
| Best Practices | **100** | Clean |
| SEO | **90** | Missing `<meta name="description">` on internal page |

Failing Lighthouse accessibility audits (`summary-before.json`):
1. **`td-has-header`** — *"`<td>` elements in a large `<table>` do not have table headers."*  
   Both the **Low stock** table (`store/templates/store/dashboard.html:75`) and **Recent sales** table (`store/templates/store/dashboard.html:94`) lacked `<thead>` / `<th scope="col">` headers (matching candidate defects `DEF-01` and `DEF-02` in [defects.md](defects.md)).
2. **`color-contrast`** — *"Background and foreground colors do not have a sufficient contrast ratio."*  
   Muted secondary table cells (`.table .text-muted` / `.table small.text-muted` at `#77867d` on `#ffffff`) measured **3.82:1**, below the WCAG 2.1 AA minimum of **4.5:1**.

### 1.2 axe-core Multi-Screen Scan Before Fix

| Screen | URL | Violations | Passes | Key Issues |
| --- | --- | --- | --- | --- |
| Login | `/accounts/login/` | 2 | 26 | `landmark-one-main` (1 node), `region` (7 nodes) |
| **Dashboard** | `/` | **1** | **28** | `color-contrast` (**20 nodes** — `#77867d` on `#ffffff`, ratio 3.82:1) |
| New Sale (POS) | `/transactions/new-sale/` | 1 | 39 | `color-contrast` (3 nodes — Select2 placeholders `#87948c` and `.pos-secure-note` `#849188`) |
| Sales List | `/transactions/sales/` | 1 | 38 | `empty-table-header` (1 node — empty action `<th></th>` column) |

---

## 2. Screen Fixed — Dashboard (`/`)

Target screen selected for remediation: **Dashboard** ([store/templates/store/dashboard.html](../store/templates/store/dashboard.html) and [static/css/style.css](../static/css/style.css)).

### Changes applied
1. **`store/templates/store/dashboard.html`:**
   - Added `aria-label="Low stock products"` and `<thead class="visually-hidden"><tr><th scope="col">Product</th><th scope="col">Stock</th></tr></thead>` to the **Low stock** table (`DEF-01`).
   - Added `aria-label="Recent sales"` and `<thead class="visually-hidden"><tr><th scope="col">Receipt</th><th scope="col">When</th><th scope="col">Amount</th></tr></thead>` to the **Recent sales** table (`DEF-02`).
   - Uses Bootstrap's `.visually-hidden` class so screen readers and assistive technologies receive column context while preserving the clean visual card design.
2. **`static/css/style.css` (line 763):**
   - Updated `.table .text-muted, .table small.text-muted` foreground color from `#77867d` (3.82:1) to `#59665e` (**5.89:1** on `#ffffff`), exceeding the WCAG 2.1 AA 4.5:1 contrast threshold across all dashboard table metadata.

---

## 3. After-Fix Verification

Re-ran `python tools/run_accessibility_audit.py after` against the updated code.

### 3.1 Before vs. After Comparison (Dashboard `/`)

| Metric / Audit | Before | After | Delta |
| --- | --- | --- | --- |
| **Lighthouse Accessibility** | **95** | **100** | **+5** |
| Lighthouse Performance | 99 | 99 | 0 |
| Lighthouse Best Practices | 100 | 100 | 0 |
| Lighthouse `td-has-header` | Failed (0) | Passed | Fixed |
| Lighthouse `color-contrast` | Failed (0) | Passed | Fixed |
| **axe-core Dashboard Violations** | **1 (20 nodes)** | **0 (0 nodes)** | **-100%** |
| axe-core Dashboard Passes | 28 | 30 | +2 |

### 3.2 Saved Evidence Artifacts
- [reports/accessibility/summary-before.json](../reports/accessibility/summary-before.json)
- [reports/accessibility/summary-after.json](../reports/accessibility/summary-after.json)
- [reports/accessibility/axe-before.json](../reports/accessibility/axe-before.json)
- [reports/accessibility/axe-after.json](../reports/accessibility/axe-after.json)
- [reports/accessibility/lighthouse-dashboard-before.report.html](../reports/accessibility/lighthouse-dashboard-before.report.html) & `.json`
- [reports/accessibility/lighthouse-dashboard-after.report.html](../reports/accessibility/lighthouse-dashboard-after.report.html) & `.json`

---

## 4. Remaining Out-of-Scope Screen Findings (Logged for Backlog)

- **Login (`/accounts/login/`):** Missing `<main>` landmark (`landmark-one-main`, `region`) — moderate severity.
- **POS (`/transactions/new-sale/`):** Select2 placeholder `#87948c` (3.16:1) and `.pos-secure-note` `#849188` (3.28:1) contrast below 4.5:1 — minor/moderate severity.
- **Sales list (`/transactions/sales/`):** Empty `<th></th>` in action column (`empty-table-header`) — minor severity.
