"""SQLite Persistence Layer for Student Marks Matrix Analysis (Case Study #42)."""

import os
import shutil
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "database", "marks_matrix.db")

# Seed 10 students across (Math, Physics, Chemistry, English, CS)
# Note: Physics (~52%) and Chemistry (~56%) intentionally show low-average subject detection (< 60%)
SAMPLE_MATRIX_STUDENTS = (
    ("STU4201", "Aarav Mehta", 94.0, 72.0, 68.0, 88.0, 96.0),
    ("STU4202", "Diya Nair", 91.0, 69.0, 74.0, 92.0, 94.0),
    ("STU4203", "Rohan Kulkarni", 78.0, 48.0, 52.0, 75.0, 82.0),
    ("STU4204", "Sneha Iyer", 86.0, 62.0, 65.0, 84.0, 90.0),
    ("STU4205", "Vikram Joshi", 64.0, 36.0, 42.0, 70.0, 72.0),
    ("STU4206", "Ananya Verma", 89.0, 58.0, 61.0, 90.0, 91.0),
    ("STU4207", "Karthik Rao", 72.0, 41.0, 38.0, 68.0, 77.0),
    ("STU4208", "Meera Sharma", 95.0, 76.0, 71.0, 91.0, 98.0),
    ("STU4209", "Arjun Das", 58.0, 32.0, 44.0, 65.0, 69.0),
    ("STU4210", "Priya Bose", 82.0, 51.0, 55.0, 80.0, 86.0),
)


def _resolve_db_path(db_path):
    target = db_path or DEFAULT_DB_PATH
    if os.environ.get("VERCEL") and not str(target).startswith("/tmp"):
        tmp_path = os.path.join("/tmp", os.path.basename(target))
        if not os.path.exists(tmp_path) and os.path.exists(target):
            shutil.copyfile(target, tmp_path)
        return tmp_path
    return target


def get_connection(db_path=None):
    resolved = _resolve_db_path(db_path)
    parent = os.path.dirname(resolved)
    if parent:
        os.makedirs(parent, exist_ok=True)
    conn = sqlite3.connect(resolved)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path=None, seed_if_empty=True):
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS matrix_settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                low_avg_threshold REAL NOT NULL DEFAULT 60.0,
                pass_mark REAL NOT NULL DEFAULT 40.0
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS student_marks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT UNIQUE NOT NULL,
                student_name TEXT NOT NULL,
                math_mark REAL NOT NULL,
                physics_mark REAL NOT NULL,
                chemistry_mark REAL NOT NULL,
                english_mark REAL NOT NULL,
                cs_mark REAL NOT NULL
            )
        """)
        conn.commit()
        if seed_if_empty:
            if cur.execute("SELECT COUNT(*) FROM matrix_settings").fetchone()[0] == 0:
                load_sample_data(db_path)
    finally:
        conn.close()


def load_sample_data(db_path=None):
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO matrix_settings (id, low_avg_threshold, pass_mark) VALUES (1, 60.0, 40.0)")
        for sid, sname, m1, m2, m3, m4, m5 in SAMPLE_MATRIX_STUDENTS:
            cur.execute(
                """
                INSERT OR IGNORE INTO student_marks
                (student_id, student_name, math_mark, physics_mark, chemistry_mark, english_mark, cs_mark)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (sid, sname, m1, m2, m3, m4, m5),
            )
        conn.commit()
    finally:
        conn.close()


def get_settings(db_path=None):
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT * FROM matrix_settings WHERE id = 1").fetchone()
        return dict(row) if row else {"low_avg_threshold": 60.0, "pass_mark": 40.0}
    finally:
        conn.close()


def update_settings(low_avg, pass_mark, db_path=None):
    conn = get_connection(db_path)
    try:
        conn.execute("UPDATE matrix_settings SET low_avg_threshold = ?, pass_mark = ? WHERE id = 1", (low_avg, pass_mark))
        conn.commit()
    finally:
        conn.close()


def get_student_matrix_rows(db_path=None):
    conn = get_connection(db_path)
    try:
        rows = conn.execute("SELECT * FROM student_marks ORDER BY student_id ASC").fetchall()
        return [
            (r["student_id"], r["student_name"], [r["math_mark"], r["physics_mark"], r["chemistry_mark"], r["english_mark"], r["cs_mark"]])
            for r in rows
        ]
    finally:
        conn.close()


def add_student_row(sid, sname, marks, db_path=None):
    conn = get_connection(db_path)
    try:
        if conn.execute("SELECT 1 FROM student_marks WHERE UPPER(student_id) = ?", (sid.upper(),)).fetchone():
            return (False, f"Student ID '{sid}' already exists.")
        conn.execute(
            """
            INSERT INTO student_marks
            (student_id, student_name, math_mark, physics_mark, chemistry_mark, english_mark, cs_mark)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (sid, sname, marks[0], marks[1], marks[2], marks[3], marks[4]),
        )
        conn.commit()
        return (True, f"Student '{sid}' added to marks matrix.")
    finally:
        conn.close()


def delete_student_by_id(student_id, db_path=None):
    conn = get_connection(db_path)
    try:
        conn.execute("DELETE FROM student_marks WHERE student_id = ?", (student_id,))
        conn.commit()
    finally:
        conn.close()
