# Performance & Recovery Test Report

**Owner:** Member 3  
**Tools:** Grafana `k6` v2.4.0, Python `requests` + `sqlite3`  
**Scripts:** [tests/team/perf/load_test.js](../tests/team/perf/load_test.js), [tools/run_k6_load.py](../tools/run_k6_load.py), [tests/team/perf/recovery_test.py](../tests/team/perf/recovery_test.py)  
**Evidence:** [reports/perf/k6-summary.json](../reports/perf/k6-summary.json), [reports/perf/k6-output.txt](../reports/perf/k6-output.txt), [reports/perf/recovery-report.json](../reports/perf/recovery-report.json)

---

## 1. k6 Load Test

### 1.1 Scenario & Thresholds
- **Load profile:** 3 stages — ramp 0 → 5 VUs (5s), ramp/hold 10 VUs (15s), ramp down 10 → 0 VUs (5s); 25s active duration.
- **Traffic mix (authenticated `cashier` session):**
  - `GET /` (Dashboard)
  - `GET /get-items/?term=a` (POS item search)
  - `GET /accounts/get_customers/?term=a` (POS customer search)
  - `GET /transactions/new-sale/` + `POST /transactions/new-sale/` (1 in every 4 iterations, creating real completed sales with CSRF token)
- **Thresholds:**
  - `http_req_failed < 2%`
  - `http_req_duration p(95) < 1500ms`
  - `errors < 2%`

### 1.2 Measured Results (`reports/perf/k6-summary.json`)

| Metric | Target | Measured | Status |
| --- | --- | --- | --- |
| Total HTTP requests | — | **898** (35.26 req/s) | — |
| Completed VU iterations | — | **253** (9.93 iter/s) | — |
| `http_req_duration` avg / med | — | 107.35ms / 32.85ms | — |
| `http_req_duration` p(90) / **p(95)** | **< 1500ms** | 171.28ms / **228.60ms** | **PASS** |
| `sale_post_duration` avg / p(95) | — | 211.94ms / 1157.60ms | — |
| `http_req_failed` | **< 2.00%** | **1.00%** (9 / 898) | **PASS** |
| Custom `errors` rate | **< 2.00%** | **1.08%** (9 / 826) | **PASS** |
| Read checks (`dashboard`, `item search`, `customer search`) | 100% | **253 / 253 (100%)** each | **PASS** |
| Write checks (`sale POST 200`, `sale status success`) | — | **58 / 67 (86.6%)** | Observed contention |

### 1.3 Bottleneck Analysis
All 759 read requests succeeded with 0 errors. The **9 failed requests (out of 67 concurrent `POST /transactions/new-sale/` writes)** occurred during peak 10-VU concurrency against SQLite's file-level write lock (`transaction.atomic()` + `select_for_update()`). Under production PostgreSQL (configured in `InventoryMS/settings.py`), row-level locking eliminates whole-database write lock contention; for local/SQLite deployments, enabling WAL mode or a short `busy_timeout` is recommended.

---

## 2. Failure-and-Recovery Test

Executed [tests/team/perf/recovery_test.py](../tests/team/perf/recovery_test.py) against a seeded, isolated SQLite instance (`A4 paper ream`, initial stock set to `500`, initial `sales` count `115`):

1. **Pre-crash baseline:** `integrity = ok`, stock = `500`, `orphan_sales = 0`, `sold_for_item = 16`.
2. **Phase 1 concurrent sales + abrupt kill (`proc.kill()`):** 3 concurrent worker threads executed `POST /transactions/new-sale/` for 2.5s before the server process was forcefully killed mid-load (`81` sales committed, `50` in-flight/queued requests failed on socket drop).
3. **Post-crash database consistency check:**
   - `PRAGMA integrity_check` = **`ok`**
   - `orphan_sales` (any `Sale` missing `SaleDetail` lines) = **`0`**
   - `stock` = **`419`** (`500 - 81`, matching `sold_for_item = 97 = 16 + 81` exactly)
4. **Recovery & Phase 2 verification:**
   - Server restarted cleanly on the same database in **`2.49s`**.
   - Authenticated `GET /` and `GET /transactions/new-sale/` both returned HTTP **`200`**.
   - Post-recovery `POST /transactions/new-sale/` succeeded (`stock` became `418`, `sales_count = 197`, `orphan_sales = 0`, `PRAGMA integrity_check = ok`).
   - **`consistency_verified: true`** (exit code `0`).
