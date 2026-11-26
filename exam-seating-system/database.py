"""SQLite Persistence Layer for Nested Loop Examination Seating Generator (Case Study #26)."""

import os
import shutil
import sqlite3

from seating_logic import generate_sequential_rolls

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "database", "seating.db")

SAMPLE_HALLS = (
    ("HALL-101", "Main Academic Block", 5, 6, 16, "A1:PROCTOR,A6:ACCESSIBLE,C3:BROKEN"),
    ("HALL-202", "Engineering Wing", 6, 8, 24, "A1:PROCTOR,A8:PROCTOR,F1:ACCESSIBLE"),
    ("LAB-301", "Computing Center", 4, 5, 12, "A1:PROCTOR,D5:BROKEN"),
)

SAMPLE_PLANS = (
    (
        "PLAN-2026-001",
        "CS301 Data Structures Midterm",
        "HALL-101",
        "ALTERNATE_CHECKERBOARD",
        14,
        0,
        "A1:PROCTOR,A6:ACCESSIBLE,C3:BROKEN",
        ",".join(generate_sequential_rolls("26CS", 1, 14)),
    ),
    (
        "PLAN-2026-002",
        "MA201 Linear Algebra Final",
        "HALL-202",
        "ALTERNATE_COLUMN",
        20,
        0,
        "A1:PROCTOR,A8:PROCTOR,F1:ACCESSIBLE",
        ",".join(generate_sequential_rolls("26MA", 101, 20)),
    ),
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
            CREATE TABLE IF NOT EXISTS halls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hall_name TEXT UNIQUE NOT NULL,
                building TEXT NOT NULL,
                rows INTEGER NOT NULL,
                cols INTEGER NOT NULL,
                fixed_capacity INTEGER NOT NULL,
                default_reserved TEXT NOT NULL DEFAULT ''
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS seating_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id TEXT UNIQUE NOT NULL,
                exam_title TEXT NOT NULL,
                hall_name TEXT NOT NULL,
                seating_mode TEXT NOT NULL,
                assigned_count INTEGER NOT NULL,
                overflow_count INTEGER NOT NULL,
                reserved_spec TEXT NOT NULL,
                students_csv TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            )
        """)
        conn.commit()
        if seed_if_empty:
            if cur.execute("SELECT COUNT(*) FROM halls").fetchone()[0] == 0:
                load_sample_data(db_path)
    finally:
        conn.close()


def load_sample_data(db_path=None):
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        for h_name, bldg, rows, cols, cap, resv in SAMPLE_HALLS:
            cur.execute(
                "INSERT OR IGNORE INTO halls (hall_name, building, rows, cols, fixed_capacity, default_reserved) VALUES (?, ?, ?, ?, ?, ?)",
                (h_name, bldg, rows, cols, cap, resv),
            )
        for pid, title, h_name, mode, assigned, overflow, resv, stud_csv in SAMPLE_PLANS:
            cur.execute(
                """
                INSERT OR IGNORE INTO seating_plans
                (plan_id, exam_title, hall_name, seating_mode, assigned_count, overflow_count, reserved_spec, students_csv)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (pid, title, h_name, mode, assigned, overflow, resv, stud_csv),
            )
        conn.commit()
    finally:
        conn.close()


def get_all_halls(db_path=None):
    conn = get_connection(db_path)
    try:
        return [dict(r) for r in conn.execute("SELECT * FROM halls ORDER BY hall_name ASC").fetchall()]
    finally:
        conn.close()


def get_hall_by_name(hall_name, db_path=None):
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT * FROM halls WHERE hall_name = ?", (hall_name,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def add_hall(hall_name, building, rows, cols, fixed_capacity, default_reserved, db_path=None):
    conn = get_connection(db_path)
    try:
        if conn.execute("SELECT 1 FROM halls WHERE UPPER(hall_name) = ?", (hall_name.upper(),)).fetchone():
            return (False, f"Hall '{hall_name}' already exists.")
        conn.execute(
            "INSERT INTO halls (hall_name, building, rows, cols, fixed_capacity, default_reserved) VALUES (?, ?, ?, ?, ?, ?)",
            (hall_name.upper(), building, rows, cols, fixed_capacity, default_reserved),
        )
        conn.commit()
        return (True, f"Hall '{hall_name.upper()}' added.")
    finally:
        conn.close()


def get_all_plans(db_path=None):
    conn = get_connection(db_path)
    try:
        return [dict(r) for r in conn.execute("SELECT * FROM seating_plans ORDER BY id DESC").fetchall()]
    finally:
        conn.close()


def get_plan_by_id(plan_id, db_path=None):
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT * FROM seating_plans WHERE plan_id = ?", (plan_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def save_plan(exam_title, hall_name, seating_mode, assigned_count, overflow_count, reserved_spec, students_csv, db_path=None):
    conn = get_connection(db_path)
    try:
        count = conn.execute("SELECT COUNT(*) FROM seating_plans").fetchone()[0]
        plan_id = f"PLAN-2026-{count + 1:03d}"
        while conn.execute("SELECT 1 FROM seating_plans WHERE plan_id = ?", (plan_id,)).fetchone():
            count += 1
            plan_id = f"PLAN-2026-{count + 1:03d}"
        conn.execute(
            """
            INSERT INTO seating_plans
            (plan_id, exam_title, hall_name, seating_mode, assigned_count, overflow_count, reserved_spec, students_csv)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (plan_id, exam_title, hall_name, seating_mode, assigned_count, overflow_count, reserved_spec, students_csv),
        )
        conn.commit()
        return plan_id
    finally:
        conn.close()
