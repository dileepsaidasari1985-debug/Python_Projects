"""SQLite Persistence Layer for Comprehensive Smart Campus Simulation (Case Study #100)."""

import os
import shutil
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "database", "campus.db")

SAMPLE_STUDENTS = (
    ("CAMP101", "Aarav Sharma", "Computer Science", "2nd Year", 44, 48, 92.0, 95.0, 88.0),
    ("CAMP102", "Diya Krishnan", "Information Technology", "3rd Year", 46, 48, 90.0, 91.0, 93.0),
    ("CAMP103", "Rohan Verma", "Mechanical", "1st Year", 30, 48, 68.0, 72.0, 74.0),
    ("CAMP104", "Sneha Nair", "Electronics", "2nd Year", 41, 48, 84.0, 86.0, 82.0),
    ("CAMP105", "Vikram Patel", "Civil", "4th Year", 33, 48, 58.0, 61.0, 66.0),
    ("CAMP106", "Ananya Iyer", "Computer Science", "3rd Year", 45, 48, 94.0, 96.0, 89.0),
)

SAMPLE_EVENTS = (
    ("EVT101", "AI & Python Hackathon", "2026-12-05", "Auditorium A", 5),
    ("EVT102", "Robotics Design Expo", "2026-12-10", "Innovation Hall", 4),
    ("EVT103", "Campus Coding Cup", "2026-12-14", "CS Lab Block", 2),
)

SAMPLE_REGISTRATIONS = (
    ("CAMP101", "EVT101"),
    ("CAMP102", "EVT101"),
    ("CAMP106", "EVT103"),
    ("CAMP104", "EVT103"),
)

SAMPLE_RESOURCES = (
    ("RES-LAB1", "Python Computing Lab 1", "Lab", 40, "Available"),
    ("RES-AUD1", "Main Seminar Auditorium", "Hall", 180, "Available"),
    ("RES-PROJ", "4K Laser Projector Kit", "Equipment", 1, "Available"),
    ("RES-CONF", "Boardroom Conference Hall", "Hall", 24, "Maintenance"),
)

SAMPLE_ALLOCATIONS = (
    ("RES-LAB1", "CAMP101", "Mon 14:00-16:00", "Coding Club Workshop"),
    ("RES-AUD1", "CAMP102", "Wed 10:00-12:00", "Tech Talk Series"),
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
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                department TEXT NOT NULL,
                year TEXT NOT NULL,
                attended_classes INTEGER NOT NULL DEFAULT 0,
                total_classes INTEGER NOT NULL DEFAULT 48,
                math_mark REAL NOT NULL DEFAULT 0.0,
                cs_mark REAL NOT NULL DEFAULT 0.0,
                eng_mark REAL NOT NULL DEFAULT 0.0
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_code TEXT UNIQUE NOT NULL,
                event_name TEXT NOT NULL,
                event_date TEXT NOT NULL,
                venue TEXT NOT NULL,
                capacity INTEGER NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS event_registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                event_code TEXT NOT NULL,
                registered_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                UNIQUE(student_id, event_code)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resource_code TEXT UNIQUE NOT NULL,
                resource_name TEXT NOT NULL,
                kind TEXT NOT NULL,
                capacity INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'Available'
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS resource_allocations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resource_code TEXT NOT NULL,
                requester_id TEXT NOT NULL,
                slot_label TEXT NOT NULL,
                purpose TEXT NOT NULL
            )
        """)
        conn.commit()
        if seed_if_empty and cur.execute("SELECT COUNT(*) FROM students").fetchone()[0] == 0:
            load_sample_data(db_path)
    finally:
        conn.close()


def load_sample_data(db_path=None):
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        for row in SAMPLE_STUDENTS:
            cur.execute(
                "INSERT OR IGNORE INTO students (student_id, name, department, year, attended_classes, total_classes, math_mark, cs_mark, eng_mark) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                row,
            )
        for ev in SAMPLE_EVENTS:
            cur.execute("INSERT OR IGNORE INTO events (event_code, event_name, event_date, venue, capacity) VALUES (?, ?, ?, ?, ?)", ev)
        for reg in SAMPLE_REGISTRATIONS:
            cur.execute("INSERT OR IGNORE INTO event_registrations (student_id, event_code) VALUES (?, ?)", reg)
        for res in SAMPLE_RESOURCES:
            cur.execute("INSERT OR IGNORE INTO resources (resource_code, resource_name, kind, capacity, status) VALUES (?, ?, ?, ?, ?)", res)
        if cur.execute("SELECT COUNT(*) FROM resource_allocations").fetchone()[0] == 0:
            for al in SAMPLE_ALLOCATIONS:
                cur.execute("INSERT INTO resource_allocations (resource_code, requester_id, slot_label, purpose) VALUES (?, ?, ?, ?)", al)
        conn.commit()
    finally:
        conn.close()


def get_students(db_path=None):
    conn = get_connection(db_path)
    try:
        return [dict(r) for r in conn.execute("SELECT * FROM students ORDER BY student_id ASC").fetchall()]
    finally:
        conn.close()


def add_student(sid, name, dept, year, db_path=None):
    conn = get_connection(db_path)
    try:
        if conn.execute("SELECT 1 FROM students WHERE student_id = ?", (sid,)).fetchone():
            return (False, f"Student ID '{sid}' already exists.")
        conn.execute(
            "INSERT INTO students (student_id, name, department, year, attended_classes, total_classes, math_mark, cs_mark, eng_mark) VALUES (?, ?, ?, ?, 40, 48, 75.0, 80.0, 78.0)",
            (sid, name, dept, year),
        )
        conn.commit()
        return (True, f"Student '{sid}' registered.")
    finally:
        conn.close()


def update_attendance(sid, attended, total, db_path=None):
    conn = get_connection(db_path)
    try:
        conn.execute("UPDATE students SET attended_classes = ?, total_classes = ? WHERE student_id = ?", (attended, total, sid))
        conn.commit()
    finally:
        conn.close()


def update_marks(sid, math_m, cs_m, eng_m, db_path=None):
    conn = get_connection(db_path)
    try:
        conn.execute("UPDATE students SET math_mark = ?, cs_mark = ?, eng_mark = ? WHERE student_id = ?", (math_m, cs_m, eng_m, sid))
        conn.commit()
    finally:
        conn.close()


def get_events(db_path=None):
    conn = get_connection(db_path)
    try:
        return [dict(r) for r in conn.execute("SELECT * FROM events ORDER BY event_code ASC").fetchall()]
    finally:
        conn.close()


def get_registrations(db_path=None):
    conn = get_connection(db_path)
    try:
        return [dict(r) for r in conn.execute("SELECT * FROM event_registrations ORDER BY id DESC").fetchall()]
    finally:
        conn.close()


def register_student_event(sid, ecode, db_path=None):
    conn = get_connection(db_path)
    try:
        conn.execute("INSERT INTO event_registrations (student_id, event_code) VALUES (?, ?)", (sid, ecode))
        conn.commit()
    finally:
        conn.close()


def get_resources(db_path=None):
    conn = get_connection(db_path)
    try:
        return [dict(r) for r in conn.execute("SELECT * FROM resources ORDER BY resource_code ASC").fetchall()]
    finally:
        conn.close()


def get_allocations(db_path=None):
    conn = get_connection(db_path)
    try:
        return [dict(r) for r in conn.execute("SELECT * FROM resource_allocations ORDER BY id DESC").fetchall()]
    finally:
        conn.close()


def allocate_resource(rcode, req_id, slot_label, purpose, db_path=None):
    conn = get_connection(db_path)
    try:
        conn.execute("INSERT INTO resource_allocations (resource_code, requester_id, slot_label, purpose) VALUES (?, ?, ?, ?)", (rcode, req_id, slot_label, purpose))
        conn.commit()
    finally:
        conn.close()
