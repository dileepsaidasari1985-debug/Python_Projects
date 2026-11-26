# Python Source Code Overview

1. **[`billing_logic.py`](../billing_logic.py)** — Multi-product line billing, category-specific tax calculation, threshold discount slabs, maximum concession capping, and cash change calculator.
2. **[`database.py`](../database.py)** — SQLite persistence for products, tax/discount rules, and snapshotted invoices.
3. **[`app.py`](../app.py)** — Flask POS billing counter, catalog CRUD, rule editor, and CSV export.
4. **[`tests/test_billing.py`](../tests/test_billing.py)** — Automated `unittest` suite (13 tests).
