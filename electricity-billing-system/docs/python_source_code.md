# Python Source Code Overview

1. **[`billing_logic.py`](../billing_logic.py)** — Progressive tariff slab calculator, fixed/duty/surcharge/rebate/penalty computation, MoM percentage comparison, unusual consumption spike detector, and ASCII pattern generator.
2. **[`database.py`](../database.py)** — SQLite persistence for households, meter readings, bills, and tariff rules.
3. **[`app.py`](../app.py)** — Flask web dashboard, household management, billing engine, unusual usage alerts, and CSV export.
4. **[`tests/test_billing.py`](../tests/test_billing.py)** — Automated `unittest` suite (20 tests).
