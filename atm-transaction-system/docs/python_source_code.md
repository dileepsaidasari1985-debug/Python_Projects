# Python Source Code Overview

1. **[`transaction_logic.py`](../transaction_logic.py)** — Deposit/withdrawal validation, denomination & daily limit checks, sequential transaction processor using tuple unpacking, summary metrics, and ASCII ATM receipt generator.
2. **[`database.py`](../database.py)** — SQLite persistence for demo account balances, transaction ledger, and ATM settings.
3. **[`app.py`](../app.py)** — Flask ATM dashboard, terminal menu, sequence simulator, and CSV export.
4. **[`tests/test_transactions.py`](../tests/test_transactions.py)** — Automated `unittest` suite (10 tests).
