# Progressive Electricity Billing & Monthly Consumption Analysis System

A complete, beginner-friendly **Python 3 + Flask + SQLite** web application built for **Case Study #2 (Python Activity-Based Learning Assignment)**.

The system registers households, validates monthly meter readings, calculates progressive electricity charges across configurable consumption slabs, applies fixed charges, electricity duty, surcharges, rebates, and late payment penalties, compares monthly usage, flags unusual consumption increases using transparent rule-based Python logic, and exports printable bills and CSV reports.

---

## Features

- **Dashboard (`/`)**: Live KPI metrics from SQLite (total households, total bills, current month consumption & charges, average monthly consumption, highest/lowest consumption months, total surcharges, total rebates), interactive Canvas charts, recent billing records, and consumption warning alerts.
- **Household Registration & Management (`/households`, `/households/add`)**: Full CRUD with duplicate Household ID and Meter Number prevention, search by consumer name/ID/meter number, filter by area and connection type, and accessible `<dialog>` deletion confirmation.
- **Meter Reading & Progressive Bill Generator (`/meter-reading`, `/generate-bill`)**: Auto-fills latest reading, validates non-negative readings (`Current >= Previous`), prevents duplicate household billing months, previews live units and slab-by-slab breakdown, and generates unique bill numbers (`BILL-YYYYMM-HHID-SEQ`).
- **Official Bill View & Print/CSV (`/bill/<id>`)**: Print-friendly utility statement (`@media print`), payment status toggle (`Paid` / `Unpaid`), and single-bill CSV export.
- **Billing History (`/billing-history`)**: Filter by month, household, or payment status; search by Household ID/name/bill number; sort by month, units, or amount.
- **Monthly Consumption Comparison (`/monthly-analysis`)**: Aggregate or per-household monthly analysis, percentage change calculations (handling zero previous consumption safely), highest/lowest/average summary, and interactive charts.
- **Unusual Consumption Detection (`/unusual-consumption`)**: Rule-based anomaly detection (month-over-month >50% increase, 3-month moving average spike, high usage limit, high bill limit).
- **Configurable Tariff & Billing Rules (`/tariff-rules`)**: Edit all 5 progressive slabs, fixed charge, electricity duty %, surcharge % & threshold, rebate mode/value/threshold, late payment penalty, and warning thresholds (plus Reset to Academic Defaults).
- **Reports & CSV Export (`/reports`)**: Utility revenue and consumption summaries, household ranking, Python pattern-generation summary, print report, and CSV exports (`all_bills`, `monthly`, `unusual`) using Python's built-in `csv` module.
- **22 Preloaded Sample Billing Records**: Across 6 diverse households (`2026-06` to `2026-11`), demonstrating zero consumption, rebate-eligible usage, 250-unit multi-slab calculations, high-usage surcharges, late penalties, and unusual consumption spikes.

---

## Project Structure

```text
electricity-billing-system/
├── app.py                     # Flask application & HTTP routes
├── billing_logic.py           # Progressive slab engine, validation & analytics
├── database.py                # SQLite schema, parameterized SQL & sample data
├── requirements.txt           # Flask dependency
├── README.md
├── database/
│   └── electricity.db         # Auto-created SQLite database
├── templates/                 # Jinja2 HTML5 templates
├── static/
│   ├── css/style.css          # Dark Navy & Electric Blue responsive stylesheet
│   ├── js/script.js           # Accessible drawer, modal dialog, validation & charts
│   └── images/voltgrid_logo.svg
├── tests/
│   └── test_billing.py        # Automated unittest suite (20+ test cases)
├── docs/                      # College assignment submission documentation
└── screenshots/               # Application screenshots
```

---

## Running Locally

### 1. Navigate to the project directory
```powershell
cd electricity-billing-system
```

### 2. Activate the virtual environment (or create one)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies
```powershell
python -m pip install -r requirements.txt
```

### 4. Run the application
```powershell
python app.py
```
Open **http://127.0.0.1:5000** in your browser.

### 5. Run automated tests
```powershell
python -m unittest discover -s tests -v
```
