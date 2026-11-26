# Python Source Code Overview

All Python source files for the **University Scholarship Allocation System** are organized cleanly at the project root and in `tests/`:

1. **[`scholarship_logic.py`](../scholarship_logic.py)** — Core computational logic:
   - Tuple constants (`SUBJECT_TUPLE`, `DEPARTMENTS`, `ACADEMIC_YEARS`, `SCHOLARSHIP_CATEGORIES`)
   - Input validation (`validate_student_data`, `validate_rules_data`)
   - Academic totals & income merit slab lookup (`calculate_academic_totals`, `get_income_merit_score`)
   - Eligibility evaluation with detailed rejection reasons (`evaluate_eligibility`)
   - Weighted scholarship scoring (`calculate_scholarship_score`)
   - 5-level tuple-based tie-breaking & ranking engine (`build_tie_break_tuple`, `describe_tie_resolution`, `evaluate_and_rank_all`)
   - Loop-based pattern generation (`generate_merit_pattern`, `generate_award_banner`)
   - Nested department summary list generation inside `evaluate_and_rank_all`

2. **[`database.py`](../database.py)** — SQLite persistence layer:
   - Automatic schema creation (`init_db`) for `students` and `scholarship_rules`
   - Parameterized CRUD (`add_student`, `get_all_students`, `get_student_by_id`, `update_student`, `delete_student`)
   - Rule management (`get_rules`, `update_rules`, `reset_rules_to_default`)
   - Idempotent seeding of 18 realistic sample students (`SAMPLE_STUDENTS`, `load_sample_students`)

3. **[`app.py`](../app.py)** — Flask web server & routes:
   - Dashboard (`/`), Add/Edit Student (`/add`, `/student/<id>/edit`), Applicant Search/Filter/Sort (`/applicants`), Evaluation Profile (`/student/<id>`), Delete (`/student/<id>/delete`), Rankings (`/rankings`), Rules (`/rules`), Reports (`/reports`), and built-in `csv` export (`/reports/export-csv`).

4. **[`wsgi.py`](../wsgi.py)** — Production WSGI entry point for Waitress (Windows) and Gunicorn (Linux).

5. **[`tests/test_scholarship.py`](../tests/test_scholarship.py)** — 23 automated `unittest` cases validating every boundary, tie-breaker, CRUD route, CSRF protection, and CSV export.
