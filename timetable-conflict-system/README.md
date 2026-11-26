# Student Timetable Conflict Detection System

**Case Study #23:** *Compare course schedules represented by strings and tuples, detect overlapping periods, identify unavailable rooms, and validate a proposed timetable.*

A complete **Python 3 + Flask + SQLite** web application designed around the core Python syllabus (variables, data types, operators, conditionals, loops, strings, pattern generation, lists, nested lists, tuples, tuple operations, and tuple unpacking).

## Key Features
- **Schedule String & Tuple Parser**: Parses pipe-delimited schedule strings (`CODE | TITLE | Day HH:MM-HH:MM | ROOM`) into validated immutable tuples.
- **Pairwise Time Overlap Detector**: Compares courses via nested loops and interval math (`start_a < end_b and start_b < end_a`), cleanly permitting back-to-back periods while reporting exact overlap duration and windows.
- **Room Availability & Maintenance Checker**: Flags courses mapped to unknown rooms, rooms under maintenance, reserved auditoriums, or double-booked rooms.
- **Proposed Timetable Validator**: Validates course selections or raw strings, builds a 2D weekly timetable matrix, suggests conflict-free alternative slots, and generates a loop-driven ASCII timetable grid.
- **SQLite Persistence & CSV Export**: Stores rooms, course schedules, and saved student proposals in SQLite with parameterized queries and built-in `csv` exports.

## Running Locally & Tests
```powershell
python -m pip install -r requirements.txt
python app.py
python -m unittest discover -s tests -v
```
