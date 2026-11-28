# Member 3 — Use Cases, Usability, Security, Performance & Risk Lead

Working notes and deliverable index for **Member 3**, following [project-guide.md](project-guide.md).

## Deliverables Checklist

- [x] **Risk register & exit criteria** → [risk-register.md](risk-register.md) (8 product risks, 2 project risks, release exit criteria)
- [x] **Two use case specifications** (≥ 2 alternative & ≥ 2 exception flows each) → [UC-M3-1-make-sale-pos.md](use-cases/UC-M3-1-make-sale-pos.md), [UC-M3-2-void-sale-recovery.md](use-cases/UC-M3-2-void-sale-recovery.md)
- [x] **Playwright E2E automation** (1 per workflow, rejected value, keyboard navigation) → [tests/team/e2e/test_e2e_workflows.py](../tests/team/e2e/test_e2e_workflows.py)
- [x] **Lighthouse & axe-core audits + 1 screen fixed** (Dashboard before/after) → [accessibility-report.md](accessibility-report.md), [reports/accessibility/](../reports/accessibility/)
- [x] **Access matrix & 4+ automated security checks** → [access-matrix.md](access-matrix.md), [tests/team/security/test_access_matrix.py](../tests/team/security/test_access_matrix.py)
- [x] **Dependency audit** (`pip-audit`) → [reports/security/pip-audit.json](../reports/security/pip-audit.json)
- [x] **OWASP ZAP passive scan** → [security-report.md](security-report.md), [reports/security/zap-passive-report.html](../reports/security/zap-passive-report.html)
- [x] **k6 load test + failure-and-recovery test** → [performance-report.md](performance-report.md), [tests/team/perf/](../tests/team/perf/)
- [x] **Weekly progress, GQM metrics & test completion report** → [weekly-progress.md](weekly-progress.md), [test-completion-report.md](test-completion-report.md)

## Quick Re-Run Commands (Windows PowerShell)

```powershell
$env:DEBUG="True"
# Security access matrix checks (35 tests)
.\.venv\Scripts\python.exe -m pytest tests/team/security -v

# Playwright E2E browser tests (2 end-to-end workflows)
.\.venv\Scripts\python.exe -m pytest tests/team/e2e -v

# Accessibility audit (Lighthouse + axe-core)
.\.venv\Scripts\python.exe tools/run_accessibility_audit.py after

# k6 load test & failure/recovery test
.\.venv\Scripts\python.exe tools/run_k6_load.py
.\.venv\Scripts\python.exe tests/team/perf/recovery_test.py

# OWASP ZAP 2.17.0 passive scan
.\.venv\Scripts\python.exe tools/run_zap_passive.py

# Dependency vulnerability audit
.\.venv\Scripts\python.exe -m pip_audit --local
```
