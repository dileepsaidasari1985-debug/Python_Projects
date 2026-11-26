"""SQLite Persistence Layer for Student Timetable Conflict Detection (Case Study #23)."""

import os
import shutil
import sqlite3

from timetable_logic import build_schedule_string, parse_time_to_minutes

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "database", "timetable.db")

# Seed Rooms: (room_code, building, capacity, status, unavail_day, unavail_start, unavail_end, reason)
SAMPLE_ROOMS = (
    ("R-201", "Academic Block A", 60, "Available", "ALL", 0, 0, "Operational"),
    ("R-204", "Academic Block A", 60, "Available", "ALL", 0, 0, "Operational"),
    ("R-305", "Academic Block B", 45, "Available", "ALL", 0, 0, "Operational"),
    ("LAB-101", "CS Innovation Wing", 40, "Available", "ALL", 0, 0, "Operational"),
    ("LAB-102", "CS Innovation Wing", 40, "Maintenance", "Wed", 600, 780, "Network switch upgrade (Wed 10:00-13:00)"),
    ("SEM-12", "Management Block", 35, "Available", "ALL", 0, 0, "Operational"),
    ("AUD-01", "Central Auditorium", 180, "Reserved", "Fri", 540, 780, "Convocation rehearsal (Fri 09:00-13:00)"),
    ("R-108", "Science Block", 50, "Maintenance", "ALL", 420, 1260, "Projector & HVAC renovation"),
)

# Seed Courses: (course_code, course_title, instructor, day, start_time, end_time, room_code, credits)
SAMPLE_COURSES = (
    ("CS101", "Data Structures & Algorithms", "Dr. A. Nair", "Mon", "09:00", "10:30", "R-204", 4),
    ("MA102", "Discrete Mathematics", "Prof. R. Kulkarni", "Mon", "10:30", "12:00", "R-201", 4),
    ("CS103", "Computer Organization", "Dr. S. Menon", "Tue", "09:00", "10:30", "R-204", 3),
    ("EC104", "Digital Logic Lab", "Prof. V. Rao", "Tue", "11:00", "13:00", "LAB-101", 2),
    ("CS105", "Database Management Systems", "Dr. P. Iyer", "Wed", "09:00", "10:30", "R-305", 4),
    ("CS106", "Operating Systems Lab", "Prof. K. Verma", "Wed", "10:30", "12:30", "LAB-102", 2),
    ("HS107", "Technical Communication", "Dr. M. Das", "Thu", "10:00", "11:30", "SEM-12", 2),
    ("CS108", "Python Programming Studio", "Prof. N. Gupta", "Fri", "14:00", "16:00", "LAB-101", 3),
    ("CS109", "Web Engineering Elective", "Dr. T. Bose", "Mon", "09:30", "11:00", "R-204", 3),
    ("GE110", "Environmental Studies", "Prof. L. Joshi", "Fri", "10:00", "11:30", "AUD-01", 2),
)

SAMPLE_PROPOSALS = (
    (
        "TT-2026-001",
        "STU2301",
        "Aarav Sharma",
        "Fall 2026",
        "CS101,MA102,CS103,EC104,CS105,HS107,CS108",
        1,
        0,
        "Valid conflict-free core semester schedule (7 courses, 0 clashes).",
    ),
    (
        "TT-2026-002",
        "STU2302",
        "Priya Nair",
        "Fall 2026",
        "CS101,CS109,MA102,CS106",
        0,
        3,
        "Time overlap between CS101 & CS109 on Mon, CS109 & MA102 on Mon, plus LAB-102 maintenance on Wed.",
    ),
    (
        "TT-2026-003",
        "STU2303",
        "Rohan Verma",
        "Fall 2026",
        "CS103,EC104,GE110,CS108",
        0,
        1,
        "Room AUD-01 is reserved for convocation rehearsal on Fri 09:00-13:00 (GE110).",
    ),
)


def _resolve_db_path(db_path):
    """Return a writable database path (copying bundled seed into /tmp on read-only serverless FS)."""
    target = db_path or DEFAULT_DB_PATH
    if os.environ.get("VERCEL") and not str(target).startswith("/tmp"):
        tmp_path = os.path.join("/tmp", os.path.basename(target))
        if not os.path.exists(tmp_path) and os.path.exists(target):
            shutil.copyfile(target, tmp_path)
        return tmp_path
    return target


def get_connection(db_path=None):
    """Open a SQLite connection with Row factory enabled."""
    resolved = _resolve_db_path(db_path)
    parent = os.path.dirname(resolved)
    if parent:
        os.makedirs(parent, exist_ok=True)
    conn = sqlite3.connect(resolved)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path=None, seed_if_empty=True):
    """Create tables and idempotently seed sample campus rooms, courses, and proposals."""
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_code TEXT UNIQUE NOT NULL,
                building TEXT NOT NULL,
                capacity INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'Available',
                unavailable_day TEXT NOT NULL DEFAULT 'ALL',
                unavail_start_min INTEGER NOT NULL DEFAULT 0,
                unavail_end_min INTEGER NOT NULL DEFAULT 0,
                reason TEXT NOT NULL DEFAULT ''
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_code TEXT UNIQUE NOT NULL,
                course_title TEXT NOT NULL,
                instructor TEXT NOT NULL,
                day TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                start_min INTEGER NOT NULL,
                end_min INTEGER NOT NULL,
                room_code TEXT NOT NULL,
                credits INTEGER NOT NULL DEFAULT 3,
                schedule_string TEXT NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS proposed_timetables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proposal_id TEXT UNIQUE NOT NULL,
                student_id TEXT NOT NULL,
                student_name TEXT NOT NULL,
                semester TEXT NOT NULL,
                course_codes_csv TEXT NOT NULL,
                is_valid INTEGER NOT NULL,
                conflict_count INTEGER NOT NULL,
                summary_text TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            )
        """)
        conn.commit()

        if seed_if_empty:
            room_count = cur.execute("SELECT COUNT(*) FROM rooms").fetchone()[0]
            if room_count == 0:
                load_sample_data(db_path)
    finally:
        conn.close()


def load_sample_data(db_path=None):
    """Idempotently insert sample rooms, courses, and proposed timetables."""
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        for r_code, building, cap, status, u_day, u_start, u_end, reason in SAMPLE_ROOMS:
            cur.execute(
                """
                INSERT OR IGNORE INTO rooms
                (room_code, building, capacity, status, unavailable_day, unavail_start_min, unavail_end_min, reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (r_code, building, cap, status, u_day, u_start, u_end, reason),
            )

        for code, title, prof, day, st, et, room, creds in SAMPLE_COURSES:
            _, s_min, _, _ = parse_time_to_minutes(st)
            _, e_min, _, _ = parse_time_to_minutes(et)
            sched_str = build_schedule_string(code, title, day, st, et, room)
            cur.execute(
                """
                INSERT OR IGNORE INTO courses
                (course_code, course_title, instructor, day, start_time, end_time, start_min, end_min, room_code, credits, schedule_string)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (code, title, prof, day, st, et, s_min, e_min, room, creds, sched_str),
            )

        for pid, sid, sname, sem, csv_codes, valid_flag, c_count, summary in SAMPLE_PROPOSALS:
            cur.execute(
                """
                INSERT OR IGNORE INTO proposed_timetables
                (proposal_id, student_id, student_name, semester, course_codes_csv, is_valid, conflict_count, summary_text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (pid, sid, sname, sem, csv_codes, valid_flag, c_count, summary),
            )
        conn.commit()
    finally:
        conn.close()


def get_all_rooms(db_path=None):
    conn = get_connection(db_path)
    try:
        rows = conn.execute("SELECT * FROM rooms ORDER BY room_code ASC").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_room_tuples(db_path=None):
    rows = get_all_rooms(db_path)
    return [
        (
            r["room_code"],
            r["building"],
            r["capacity"],
            r["status"],
            r["unavailable_day"],
            r["unavail_start_min"],
            r["unavail_end_min"],
            r["reason"],
        )
        for r in rows
    ]


def toggle_room_status(room_id, new_status, unavail_day="ALL", start_min=420, end_min=1260, reason="", db_path=None):
    conn = get_connection(db_path)
    try:
        conn.execute(
            """
            UPDATE rooms
            SET status = ?, unavailable_day = ?, unavail_start_min = ?, unavail_end_min = ?, reason = ?
            WHERE id = ?
            """,
            (new_status, unavail_day, start_min, end_min, reason, room_id),
        )
        conn.commit()
    finally:
        conn.close()


def get_all_courses(db_path=None, day_filter="", search=""):
    conn = get_connection(db_path)
    try:
        query = "SELECT * FROM courses WHERE 1=1"
        params = []
        if day_filter:
            query += " AND day = ?"
            params.append(day_filter)
        if search:
            query += " AND (UPPER(course_code) LIKE ? OR UPPER(course_title) LIKE ? OR UPPER(room_code) LIKE ?)"
            like_val = f"%{search.strip().upper()}%"
            params.extend([like_val, like_val, like_val])
        query += " ORDER BY CASE day WHEN 'Mon' THEN 1 WHEN 'Tue' THEN 2 WHEN 'Wed' THEN 3 WHEN 'Thu' THEN 4 WHEN 'Fri' THEN 5 ELSE 6 END, start_min ASC"
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_courses_by_codes(codes, db_path=None):
    all_courses = get_all_courses(db_path)
    selected = []
    upper_codes = [c.strip().upper() for c in codes if c.strip()]
    for c in all_courses:
        if c["course_code"].upper() in upper_codes:
            selected.append(c)
    return selected


def courses_to_tuples(course_rows):
    return [
        (
            c["course_code"],
            c["course_title"],
            c["day"],
            c["start_time"],
            c["end_time"],
            c["start_min"],
            c["end_min"],
            c["room_code"],
        )
        for c in course_rows
    ]


def add_course(cleaned, db_path=None):
    conn = get_connection(db_path)
    try:
        existing = conn.execute(
            "SELECT id FROM courses WHERE UPPER(course_code) = ?",
            (cleaned["course_code"].upper(),),
        ).fetchone()
        if existing:
            return (False, f"Course code '{cleaned['course_code']}' already exists.")

        conn.execute(
            """
            INSERT INTO courses
            (course_code, course_title, instructor, day, start_time, end_time, start_min, end_min, room_code, credits, schedule_string)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cleaned["course_code"],
                cleaned["course_title"],
                cleaned["instructor"],
                cleaned["day"],
                cleaned["start_time"],
                cleaned["end_time"],
                cleaned["start_min"],
                cleaned["end_min"],
                cleaned["room_code"],
                cleaned["credits"],
                cleaned["schedule_string"],
            ),
        )
        conn.commit()
        return (True, f"Course '{cleaned['course_code']}' added successfully.")
    finally:
        conn.close()


def delete_course(course_id, db_path=None):
    conn = get_connection(db_path)
    try:
        conn.execute("DELETE FROM courses WHERE id = ?", (course_id,))
        conn.commit()
    finally:
        conn.close()


def get_all_proposals(db_path=None):
    conn = get_connection(db_path)
    try:
        rows = conn.execute("SELECT * FROM proposed_timetables ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_proposal_by_id(proposal_id, db_path=None):
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT * FROM proposed_timetables WHERE proposal_id = ?", (proposal_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def save_proposal(student_id, student_name, semester, course_codes_csv, is_valid, conflict_count, summary_text, db_path=None):
    conn = get_connection(db_path)
    try:
        count = conn.execute("SELECT COUNT(*) FROM proposed_timetables").fetchone()[0]
        proposal_id = f"TT-2026-{count + 1:03d}"
        while conn.execute("SELECT 1 FROM proposed_timetables WHERE proposal_id = ?", (proposal_id,)).fetchone():
            count += 1
            proposal_id = f"TT-2026-{count + 1:03d}"

        conn.execute(
            """
            INSERT INTO proposed_timetables
            (proposal_id, student_id, student_name, semester, course_codes_csv, is_valid, conflict_count, summary_text)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (proposal_id, student_id, student_name, semester, course_codes_csv, 1 if is_valid else 0, conflict_count, summary_text),
        )
        conn.commit()
        return proposal_id
    finally:
        conn.close()
