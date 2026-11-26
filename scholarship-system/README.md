# University Scholarship Allocation System

A complete, beginner-friendly **Python 3 + Flask + SQLite** web application built for **Case Study #1 (Python Activity-Based Learning Assignment)**.

The system evaluates scholarship applicants using aggregate marks, subject-wise minimum scores, attendance percentage, annual family income, and income certificate status; calculates weighted scholarship scores; ranks eligible students; resolves ties deterministically using tuple operations; allocates limited scholarship seats by quota; and exports printable and CSV reports.

---

## Features

- **Dashboard Overview (`/`)**: Live KPI cards (total, eligible, rejected, available seats, allocated seats, remaining seats, average marks, highest-ranked scholar), quota progress bar, top recipients, and recent applications.
- **Add / Edit Student Application (`/add`, `/student/<id>/edit`)**: Validates required fields, numeric bounds (marks `0–100`, attendance `0–100`, income `>= 0`), unique Student IDs, and auto-calculates totals, aggregate %, eligibility, and projected score.
- **Applicant Management (`/applicants`)**: Search by name or Student ID, filter by department/eligibility/selection status, sort by rank/score/marks/name/date, inspect detailed evaluation breakdowns, edit records, or delete with modal confirmation.
- **Rankings & Tie-Breaking Engine (`/rankings`)**: Separates eligible and rejected applicants, sorts eligible candidates by descending scholarship score, and breaks ties in strict order:
  1. Higher Aggregate %
  2. Higher Attendance %
  3. Lower Annual Family Income
  4. Higher Total Marks
  5. Alphabetical Student ID
- **Configurable Scholarship Rules (`/rules`)**: Customize minimum aggregate, minimum subject marks, minimum attendance, income cap, certificate requirement, quota, score weights, and income merit slabs—automatically recalculating all rankings.
- **Reports & CSV Export (`/reports`, `/reports/export-csv`)**: Department-wise breakdown (nested lists), print-friendly layout, and one-click CSV download using Python's built-in `csv` module.
- **18 Realistic Sample Students**: Demonstrates selected scholars, tie-breaker pairs, waitlisted candidates outside quota, and multiple rejection causes (idempotent loading prevents duplicates).

---

## Project Structure

```text
scholarship-system/
├── app.py                     # Flask application & routes
├── scholarship_logic.py       # Validation, eligibility, scoring, ranking & patterns
├── database.py                # SQLite schema, parameterized CRUD & sample data
├── requirements.txt           # Flask dependency
├── README.md
├── database/
│   └── scholarship.db         # Auto-created SQLite database
├── templates/                 # Jinja2 HTML5 templates
├── static/
│   ├── css/style.css          # Navy/Royal Blue/Gold responsive stylesheet
│   ├── js/script.js           # Accessible drawer, modal dialog, live preview
│   └── images/university_crest.svg
├── tests/
│   └── test_scholarship.py    # Automated unittest suite (15+ test cases)
├── docs/                      # College assignment submission documentation
└── screenshots/               # Application screenshots
```

---

## Installation & Running Locally

### 1. Navigate to the project folder
```powershell
cd scholarship-system
```

### 2. Create & activate a Python virtual environment (recommended)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
*(Or use your installed Python 3 executable directly if `.venv` is already set up.)*

### 3. Install dependencies
```powershell
python -m pip install -r requirements.txt
```

### 4. Run the application
```powershell
python app.py
```
For production serving on Windows (recommended when sharing publicly):
```powershell
python wsgi.py
```
Open your browser and visit: **http://127.0.0.1:5000**

---

## Publishing Worldwide

### Option A: Instant Public Link (Cloudflare Quick Tunnel)
1. Start the production server: `python wsgi.py`
2. Run: `cloudflared tunnel --url http://127.0.0.1:5000`
3. Share the generated `https://*.trycloudflare.com` link (stays active while your PC and terminal are running).

### Option B: Deploy with Vercel (GitHub Integration)
1. Sign in at **https://vercel.com** and click **Add New → Project**.
2. Import your GitHub repository (`dileepsaidasari1985-debug/-University-Scholarship-Allocation`).
3. Leave Framework Preset as **Other** and Root Directory as `./` (configured via [`vercel.json`](vercel.json) to build [`app.py`](app.py) with `@vercel/python`, bundle `templates/`, `static/`, and `database/`, and route all paths directly to Flask without rewriting `PATH_INFO`).
4. *(Optional)* Under **Environment Variables**, add `FLASK_SECRET_KEY` with a random string.
5. Click **Deploy**.
*(Note: Vercel's filesystem is read-only, so `database.py` copies the seeded SQLite database into `/tmp/scholarship.db` automatically—changes live inside `/tmp` per instance and reset on cold starts.)*

### Option C: Permanent 24/7 Cloud Hosting (Render / Railway / PythonAnywhere)
The repository includes [`wsgi.py`](wsgi.py), [`Procfile`](Procfile), and `gunicorn` in [`requirements.txt`](requirements.txt) for Linux PaaS hosts (`web: gunicorn wsgi:app`). Use a persistent disk or PythonAnywhere for permanent SQLite writes across restarts.

---

## Running Automated Tests

```powershell
python -m unittest discover -s tests -v
```

---

## Assignment Documentation

All submission documents are located in `docs/`:
- [Problem Statement](docs/problem_statement.md)
- [Objectives](docs/objectives.md)
- [Assumptions](docs/assumptions.md)
- [Algorithm](docs/algorithm.md)
- [Pseudocode](docs/pseudocode.md)
- [Flowchart (Mermaid)](docs/flowchart.md)
- [Test Cases](docs/test_cases.md)
- [Conclusion](docs/conclusion.md)
