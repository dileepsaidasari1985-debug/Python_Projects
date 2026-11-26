# Python Source Code Overview

1. **[`timetable_logic.py`](../timetable_logic.py)** — Core syllabus-compliant timetable parser, overlap detector, room availability checker, slot suggester, 2D weekly matrix builder, and ASCII pattern generator.
2. **[`database.py`](../database.py)** — SQLite schema (`rooms`, `courses`, `proposed_timetables`), parameterized CRUD, and idempotent sample seeding.
3. **[`app.py`](../app.py)** — Flask web server with CSRF protection, timetable validator, course/room management, and built-in `csv` export.
4. **[`wsgi.py`](../wsgi.py)** — Production WSGI entry point.
5. **[`tests/test_timetable.py`](../tests/test_timetable.py)** — Automated `unittest` suite covering parsing, overlaps, unavailable rooms, and Flask routes.
