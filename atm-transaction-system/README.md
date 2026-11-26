# Smart ATM Transaction and Banking Simulation System

**Case Study #13:** *ATM Transaction Sequence Simulation — Process a sequence of deposits and withdrawals, maintain a simulated balance, enforce withdrawal limits, reject invalid transactions, and produce a transaction summary.*

An educational, beginner-friendly **Python 3 + Flask + SQLite** web application built for a Python Activity-Based Learning college assignment.

> **Disclaimer:** This is strictly an educational ATM simulation using a demo account (`DEMO1001`). It does not connect to any real bank accounts, payment gateways, or financial services.

## Key Features

- **Live SQLite Dashboard**: Displays simulated account details, current balance, total deposits, total withdrawals, successful vs. rejected counts, daily withdrawal limit progress, an activity bar chart, and recent transactions.
- **Interactive ATM Terminal Menu**: Simulates an ATM screen with Balance Inquiry, Cash Deposit, Cash Withdrawal, Transaction History, Sequence Simulator, and Exit session summary.
- **Deposit & Withdrawal Engine**:
  - Rejects invalid numeric inputs, zero, and negative amounts.
  - Enforces configurable minimum withdrawal (`₹100`), denomination multiples (`₹100`), per-transaction limit (`₹10,000`), daily limit (`₹25,000`), and sufficient balance (never allows negative balances).
  - Logs both `SUCCESS` and `REJECTED` attempts in SQLite with unique `TXN-YYYYMMDD-...` IDs.
- **Transaction Sequence Simulator**: Process multiple deposits and withdrawals sequentially via a Python `for` loop and tuple unpacking, showing step-by-step balance before/after, status, and rejection reasons.
- **Searchable Transaction History & Details**: Search by Transaction ID/note, filter by type, status, and date, sort by amount/date, and print Python-generated ASCII ATM receipt slips.
- **Transaction Summary & CSV Export**: Computes opening/closing balance, totals, largest deposit/withdrawal, average transaction amount, net change, and exports CSV reports using Python's built-in `csv` module.
- **Configurable ATM Settings & Safe Reset**: Modify ATM limits dynamically and reset the demo account safely using a native `<dialog>` confirmation modal.

## Python Syllabus Concepts Demonstrated

- **Variables & Data Types**: `float` balances/amounts, `int` denominations/counts, `str` transaction IDs/notes, `bool` validation flags.
- **Operators**: Arithmetic (`+`, `-`, `%`, `/`), relational (`<`, `>`, `<=`, `>=`, `==`), and logical (`and`, `or`, `not`).
- **Conditionals & Loops**: Multi-rule validation branches and `for`/`while` loops across sequence simulation, summaries, and currency formatting.
- **Strings & Pattern Generation**: Unique `TXN-...` IDs, `format_inr()`, `generate_atm_receipt_pattern()`, and `generate_summary_pattern()`.
- **Lists & Nested Lists**: Filtered ledger lists, `nested_rows` (`[step, id, type, amount, before, after, status, reason]`), and `rejection_breakdown` pairs.
- **Tuples, Tuple Operations & Tuple Unpacking**: `TRANSACTION_TYPES`, `DEFAULT_SETTINGS_TUPLE`, `DEPOSIT_PRESETS` concatenation, and unpacking `(txn_type, raw_amount, description)` during sequence execution.

## Project Structure

```text
atm-transaction-system/
├── app.py                      # Flask routes, CSRF protection, CSV export
├── transaction_logic.py        # Core Python ATM validation, sequence & summary engine
├── database.py                 # SQLite schema, parameterized queries & persistence
├── requirements.txt            # Flask>=3.0.0
├── README.md
├── database/
│   └── atm.db                  # Auto-created SQLite database
├── templates/                  # Jinja2 HTML5 templates (11 pages)
├── static/
│   ├── css/style.css           # Responsive Navy/Royal Blue/Green/Red theme + print styles
│   ├── js/script.js            # Mobile drawer, form validation ARIA, modal & sequence builder
│   └── images/atm-logo.svg     # ATM emblem
├── tests/
│   └── test_transactions.py    # Comprehensive unittest suite
└── docs/                       # College assignment submission docs & Mermaid flowchart
```

## Setup & Running Locally

```powershell
cd atm-transaction-system
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000` in your browser.

## Running Automated Tests

```powershell
python -m unittest discover -s tests -v
```
