"""
University Scholarship Allocation System - SQLite Database Layer
----------------------------------------------------------------
Handles automatic database/table initialization, parameterized SQL queries,
rule persistence, student CRUD operations, and realistic sample data loading.
"""

import os
import shutil
import sqlite3
import tempfile
from scholarship_logic import DEFAULT_RULES, SUBJECT_TUPLE, calculate_academic_totals

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BUNDLED_DB_PATH = os.path.join(BASE_DIR, "database", "scholarship.db")


def resolve_default_db_path():
    """
    Use database/scholarship.db locally; on read-only serverless environments
    (e.g., Vercel), copy the seeded database into the writable temp directory.
    """
    db_dir = os.path.dirname(BUNDLED_DB_PATH)
    is_vercel = bool(os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV"))
    is_writable = os.path.isdir(db_dir) and os.access(db_dir, os.W_OK)

    if is_vercel or not is_writable:
        tmp_db = os.path.join(tempfile.gettempdir(), "scholarship.db")
        if not os.path.exists(tmp_db) and os.path.exists(BUNDLED_DB_PATH):
            shutil.copy2(BUNDLED_DB_PATH, tmp_db)
        return tmp_db
    return BUNDLED_DB_PATH


DEFAULT_DB_PATH = resolve_default_db_path()


# 18 realistic sample students demonstrating:
# - High-scoring eligible & selected students
# - Exact scholarship-score tie-breakers (resolved by aggregate, attendance, income, ID)
# - Eligible students who miss the quota of 10 (waitlisted ranks 11-12)
# - Rejected due to attendance, subject failure (despite high aggregate), low aggregate,
#   excess family income, missing income certificate, and multiple failures.
SAMPLE_STUDENTS = [
    {
        "student_id": "STU2026001",
        "full_name": "Aarav Sharma",
        "age": 20,
        "gender": "Male",
        "department": "Computer Science",
        "academic_year": "3rd Year",
        "phone": "9876543210",
        "email": "aarav.sharma@university.edu",
        "math_marks": 96,
        "physics_marks": 92,
        "chemistry_marks": 90,
        "english_marks": 94,
        "cs_marks": 98,
        "attendance_percentage": 96.0,
        "annual_income": 85000,
        "income_certificate_status": "Available",
        "scholarship_category": "Merit-cum-Means",
        "application_date": "2026-10-12",
    },
    {
        "student_id": "STU2026002",
        "full_name": "Priya Nair",
        "age": 19,
        "gender": "Female",
        "department": "Information Technology",
        "academic_year": "2nd Year",
        "phone": "9876501122",
        "email": "priya.nair@university.edu",
        "math_marks": 94,
        "physics_marks": 91,
        "chemistry_marks": 89,
        "english_marks": 92,
        "cs_marks": 94,
        "attendance_percentage": 94.0,
        "annual_income": 95000,
        "income_certificate_status": "Available",
        "scholarship_category": "Academic Excellence",
        "application_date": "2026-10-13",
    },
    {
        "student_id": "STU2026003",
        "full_name": "Rohan Deshmukh",
        "age": 21,
        "gender": "Male",
        "department": "Electronics & Communication",
        "academic_year": "4th Year",
        "phone": "9823456789",
        "email": "rohan.deshmukh@university.edu",
        "math_marks": 90,
        "physics_marks": 92,
        "chemistry_marks": 88,
        "english_marks": 86,
        "cs_marks": 94,
        "attendance_percentage": 90.0,
        "annual_income": 120000,
        "income_certificate_status": "Available",
        "scholarship_category": "STEM Merit",
        "application_date": "2026-10-14",
    },
    # Tie-breaker pair 1: Same score (89.00) -> STU2026004 (agg 90, att 90, inc 140k)
    # vs STU2026005 (agg 90, att 90, inc 110k) -> lower income wins!
    {
        "student_id": "STU2026004",
        "full_name": "Sneha Kulkarni",
        "age": 20,
        "gender": "Female",
        "department": "Computer Science",
        "academic_year": "3rd Year",
        "phone": "9765432109",
        "email": "sneha.kulkarni@university.edu",
        "math_marks": 92,
        "physics_marks": 88,
        "chemistry_marks": 89,
        "english_marks": 90,
        "cs_marks": 91,
        "attendance_percentage": 90.0,
        "annual_income": 140000,
        "income_certificate_status": "Available",
        "scholarship_category": "Merit-cum-Means",
        "application_date": "2026-10-14",
    },
    {
        "student_id": "STU2026005",
        "full_name": "Vikramaditya Rao",
        "age": 20,
        "gender": "Male",
        "department": "Electrical Engineering",
        "academic_year": "3rd Year",
        "phone": "9988776655",
        "email": "vikram.rao@university.edu",
        "math_marks": 91,
        "physics_marks": 90,
        "chemistry_marks": 88,
        "english_marks": 89,
        "cs_marks": 92,
        "attendance_percentage": 90.0,
        "annual_income": 110000,
        "income_certificate_status": "Available",
        "scholarship_category": "Merit-cum-Means",
        "application_date": "2026-10-15",
    },
    {
        "student_id": "STU2026006",
        "full_name": "Ananya Chatterjee",
        "age": 18,
        "gender": "Female",
        "department": "Mathematics",
        "academic_year": "1st Year",
        "phone": "9123456780",
        "email": "ananya.c@university.edu",
        "math_marks": 95,
        "physics_marks": 84,
        "chemistry_marks": 82,
        "english_marks": 88,
        "cs_marks": 86,
        "attendance_percentage": 92.0,
        "annual_income": 165000,
        "income_certificate_status": "Available",
        "scholarship_category": "STEM Merit",
        "application_date": "2026-10-16",
    },
    {
        "student_id": "STU2026007",
        "full_name": "Mohammed Faizal",
        "age": 21,
        "gender": "Male",
        "department": "Mechanical Engineering",
        "academic_year": "4th Year",
        "phone": "9345678123",
        "email": "faizal.m@university.edu",
        "math_marks": 85,
        "physics_marks": 86,
        "chemistry_marks": 82,
        "english_marks": 80,
        "cs_marks": 87,
        "attendance_percentage": 88.0,
        "annual_income": 90000,
        "income_certificate_status": "Available",
        "scholarship_category": "Need-Based Grant",
        "application_date": "2026-10-17",
    },
    # Tie-breaker pair 2: STU2026008 (agg 84, att 85, inc 180k -> 60 pts => 58.8+17+6 = 81.80)
    # vs STU2026009 (agg 86, att 76, inc 180k -> 60 pts => 60.2+15.2+6 = 81.40) - slightly different,
    # let's make STU2026009 agg=86, att=78 (60.2+15.6+6 = 81.80!) -> Higher aggregate wins!
    {
        "student_id": "STU2026008",
        "full_name": "Divya Menon",
        "age": 19,
        "gender": "Female",
        "department": "Physics",
        "academic_year": "2nd Year",
        "phone": "9445566778",
        "email": "divya.menon@university.edu",
        "math_marks": 84,
        "physics_marks": 88,
        "chemistry_marks": 82,
        "english_marks": 83,
        "cs_marks": 83,
        "attendance_percentage": 85.0,
        "annual_income": 180000,
        "income_certificate_status": "Available",
        "scholarship_category": "Academic Excellence",
        "application_date": "2026-10-18",
    },
    {
        "student_id": "STU2026009",
        "full_name": "Karthik Subramanian",
        "age": 20,
        "gender": "Male",
        "department": "Computer Science",
        "academic_year": "3rd Year",
        "phone": "9556677889",
        "email": "karthik.s@university.edu",
        "math_marks": 88,
        "physics_marks": 85,
        "chemistry_marks": 84,
        "english_marks": 85,
        "cs_marks": 88,
        "attendance_percentage": 78.0,
        "annual_income": 175000,
        "income_certificate_status": "Available",
        "scholarship_category": "Merit-cum-Means",
        "application_date": "2026-10-19",
    },
    {
        "student_id": "STU2026010",
        "full_name": "Neha Verma",
        "age": 19,
        "gender": "Female",
        "department": "Civil Engineering",
        "academic_year": "2nd Year",
        "phone": "9667788990",
        "email": "neha.verma@university.edu",
        "math_marks": 80,
        "physics_marks": 79,
        "chemistry_marks": 81,
        "english_marks": 82,
        "cs_marks": 78,
        "attendance_percentage": 86.0,
        "annual_income": 145000,
        "income_certificate_status": "Available",
        "scholarship_category": "Merit-cum-Means",
        "application_date": "2026-10-20",
    },
    # Eligible but Waitlisted (Ranks 11 and 12 when quota = 10)
    {
        "student_id": "STU2026011",
        "full_name": "Siddharth Joshi",
        "age": 21,
        "gender": "Male",
        "department": "Mechanical Engineering",
        "academic_year": "4th Year",
        "phone": "9778899001",
        "email": "siddharth.j@university.edu",
        "math_marks": 78,
        "physics_marks": 77,
        "chemistry_marks": 76,
        "english_marks": 80,
        "cs_marks": 79,
        "attendance_percentage": 82.0,
        "annual_income": 195000,
        "income_certificate_status": "Available",
        "scholarship_category": "Need-Based Grant",
        "application_date": "2026-10-21",
    },
    {
        "student_id": "STU2026012",
        "full_name": "Meera Krishnan",
        "age": 18,
        "gender": "Female",
        "department": "Information Technology",
        "academic_year": "1st Year",
        "phone": "9889900112",
        "email": "meera.k@university.edu",
        "math_marks": 76,
        "physics_marks": 75,
        "chemistry_marks": 76,
        "english_marks": 78,
        "cs_marks": 75,
        "attendance_percentage": 78.0,
        "annual_income": 230000,
        "income_certificate_status": "Available",
        "scholarship_category": "Merit-cum-Means",
        "application_date": "2026-10-22",
    },
    # Rejected #1: Fails Attendance (< 75%) despite strong marks
    {
        "student_id": "STU2026013",
        "full_name": "Arjun Malhotra",
        "age": 20,
        "gender": "Male",
        "department": "Computer Science",
        "academic_year": "3rd Year",
        "phone": "9001122334",
        "email": "arjun.m@university.edu",
        "math_marks": 90,
        "physics_marks": 88,
        "chemistry_marks": 85,
        "english_marks": 87,
        "cs_marks": 92,
        "attendance_percentage": 68.0,
        "annual_income": 120000,
        "income_certificate_status": "Available",
        "scholarship_category": "Academic Excellence",
        "application_date": "2026-10-22",
    },
    # Rejected #2: Fails single subject minimum (< 50) despite aggregate >= 75%
    {
        "student_id": "STU2026014",
        "full_name": "Tanvi Bansal",
        "age": 19,
        "gender": "Female",
        "department": "Electronics & Communication",
        "academic_year": "2nd Year",
        "phone": "9012233445",
        "email": "tanvi.bansal@university.edu",
        "math_marks": 92,
        "physics_marks": 44,
        "chemistry_marks": 88,
        "english_marks": 86,
        "cs_marks": 90,
        "attendance_percentage": 91.0,
        "annual_income": 135000,
        "income_certificate_status": "Available",
        "scholarship_category": "STEM Merit",
        "application_date": "2026-10-23",
    },
    # Rejected #3: Exceeds maximum family income (> 2,50,000)
    {
        "student_id": "STU2026015",
        "full_name": "Kabir Mehta",
        "age": 21,
        "gender": "Male",
        "department": "Electrical Engineering",
        "academic_year": "4th Year",
        "phone": "9023344556",
        "email": "kabir.mehta@university.edu",
        "math_marks": 88,
        "physics_marks": 85,
        "chemistry_marks": 84,
        "english_marks": 86,
        "cs_marks": 87,
        "attendance_percentage": 90.0,
        "annual_income": 320000,
        "income_certificate_status": "Available",
        "scholarship_category": "Merit-cum-Means",
        "application_date": "2026-10-24",
    },
    # Rejected #4: Missing income certificate
    {
        "student_id": "STU2026016",
        "full_name": "Ishita Sengupta",
        "age": 19,
        "gender": "Female",
        "department": "Mathematics",
        "academic_year": "2nd Year",
        "phone": "9034455667",
        "email": "ishita.s@university.edu",
        "math_marks": 89,
        "physics_marks": 82,
        "chemistry_marks": 80,
        "english_marks": 85,
        "cs_marks": 84,
        "attendance_percentage": 89.0,
        "annual_income": 115000,
        "income_certificate_status": "Missing",
        "scholarship_category": "Need-Based Grant",
        "application_date": "2026-10-25",
    },
    # Rejected #5: Aggregate below 75%
    {
        "student_id": "STU2026017",
        "full_name": "Devansh Tiwari",
        "age": 20,
        "gender": "Male",
        "department": "Civil Engineering",
        "academic_year": "3rd Year",
        "phone": "9045566778",
        "email": "devansh.t@university.edu",
        "math_marks": 70,
        "physics_marks": 68,
        "chemistry_marks": 72,
        "english_marks": 74,
        "cs_marks": 71,
        "attendance_percentage": 85.0,
        "annual_income": 140000,
        "income_certificate_status": "Available",
        "scholarship_category": "Merit-cum-Means",
        "application_date": "2026-10-26",
    },
    # Rejected #6: Multiple criteria failed (low aggregate, subject < 50, low attendance, missing cert)
    {
        "student_id": "STU2026018",
        "full_name": "Pooja Choudhary",
        "age": 18,
        "gender": "Female",
        "department": "Physics",
        "academic_year": "1st Year",
        "phone": "9056677889",
        "email": "pooja.c@university.edu",
        "math_marks": 62,
        "physics_marks": 46,
        "chemistry_marks": 65,
        "english_marks": 70,
        "cs_marks": 67,
        "attendance_percentage": 64.0,
        "annual_income": 275000,
        "income_certificate_status": "Missing",
        "scholarship_category": "Need-Based Grant",
        "application_date": "2026-10-27",
    },
]


def get_connection(db_path=DEFAULT_DB_PATH):
    """Create and return a SQLite connection with row_factory enabled."""
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path=DEFAULT_DB_PATH, seed_if_empty=True):
    """
    Create database tables (students and scholarship_rules) if they do not exist,
    insert default scholarship rules, and optionally seed sample students when empty.
    """
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL UNIQUE,
                full_name TEXT NOT NULL,
                age INTEGER NOT NULL,
                gender TEXT DEFAULT '',
                department TEXT NOT NULL,
                academic_year TEXT NOT NULL,
                phone TEXT DEFAULT '',
                email TEXT DEFAULT '',
                math_marks REAL NOT NULL,
                physics_marks REAL NOT NULL,
                chemistry_marks REAL NOT NULL,
                english_marks REAL NOT NULL,
                cs_marks REAL NOT NULL,
                total_marks REAL NOT NULL,
                aggregate_percentage REAL NOT NULL,
                attendance_percentage REAL NOT NULL,
                annual_income REAL NOT NULL,
                income_certificate_status TEXT NOT NULL,
                scholarship_category TEXT NOT NULL,
                application_date TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS scholarship_rules (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                min_aggregate REAL NOT NULL,
                min_subject_marks REAL NOT NULL,
                min_attendance REAL NOT NULL,
                max_family_income REAL NOT NULL,
                income_certificate_required INTEGER NOT NULL,
                scholarship_quota INTEGER NOT NULL,
                weight_aggregate REAL NOT NULL,
                weight_attendance REAL NOT NULL,
                weight_income REAL NOT NULL,
                slab1_limit REAL NOT NULL,
                slab1_points REAL NOT NULL,
                slab2_limit REAL NOT NULL,
                slab2_points REAL NOT NULL,
                slab3_limit REAL NOT NULL,
                slab3_points REAL NOT NULL,
                slab4_limit REAL NOT NULL,
                slab4_points REAL NOT NULL,
                slab_above_points REAL NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Ensure row id=1 exists in scholarship_rules
        cursor.execute("SELECT id FROM scholarship_rules WHERE id = 1")
        if cursor.fetchone() is None:
            cursor.execute(
                """
                INSERT INTO scholarship_rules (
                    id, min_aggregate, min_subject_marks, min_attendance,
                    max_family_income, income_certificate_required, scholarship_quota,
                    weight_aggregate, weight_attendance, weight_income,
                    slab1_limit, slab1_points, slab2_limit, slab2_points,
                    slab3_limit, slab3_points, slab4_limit, slab4_points,
                    slab_above_points
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    1,
                    DEFAULT_RULES["min_aggregate"],
                    DEFAULT_RULES["min_subject_marks"],
                    DEFAULT_RULES["min_attendance"],
                    DEFAULT_RULES["max_family_income"],
                    DEFAULT_RULES["income_certificate_required"],
                    DEFAULT_RULES["scholarship_quota"],
                    DEFAULT_RULES["weight_aggregate"],
                    DEFAULT_RULES["weight_attendance"],
                    DEFAULT_RULES["weight_income"],
                    DEFAULT_RULES["slab1_limit"],
                    DEFAULT_RULES["slab1_points"],
                    DEFAULT_RULES["slab2_limit"],
                    DEFAULT_RULES["slab2_points"],
                    DEFAULT_RULES["slab3_limit"],
                    DEFAULT_RULES["slab3_points"],
                    DEFAULT_RULES["slab4_limit"],
                    DEFAULT_RULES["slab4_points"],
                    DEFAULT_RULES["slab_above_points"],
                ),
            )

        conn.commit()
    finally:
        conn.close()

    if seed_if_empty and count_students(db_path) == 0:
        load_sample_students(db_path)


def count_students(db_path=DEFAULT_DB_PATH):
    """Return total number of student records in the database."""
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT COUNT(*) AS cnt FROM students").fetchone()
        return int(row["cnt"])
    finally:
        conn.close()


def get_rules(db_path=DEFAULT_DB_PATH):
    """Fetch the active scholarship rules as a dictionary."""
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT * FROM scholarship_rules WHERE id = 1").fetchone()
        return dict(row) if row else dict(DEFAULT_RULES)
    finally:
        conn.close()


def update_rules(rules_data, db_path=DEFAULT_DB_PATH):
    """Update the active scholarship rules using parameterized SQL."""
    conn = get_connection(db_path)
    try:
        conn.execute(
            """
            UPDATE scholarship_rules SET
                min_aggregate = ?,
                min_subject_marks = ?,
                min_attendance = ?,
                max_family_income = ?,
                income_certificate_required = ?,
                scholarship_quota = ?,
                weight_aggregate = ?,
                weight_attendance = ?,
                weight_income = ?,
                slab1_limit = ?,
                slab1_points = ?,
                slab2_limit = ?,
                slab2_points = ?,
                slab3_limit = ?,
                slab3_points = ?,
                slab4_limit = ?,
                slab4_points = ?,
                slab_above_points = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
            """,
            (
                rules_data["min_aggregate"],
                rules_data["min_subject_marks"],
                rules_data["min_attendance"],
                rules_data["max_family_income"],
                rules_data["income_certificate_required"],
                rules_data["scholarship_quota"],
                rules_data["weight_aggregate"],
                rules_data["weight_attendance"],
                rules_data["weight_income"],
                rules_data["slab1_limit"],
                rules_data["slab1_points"],
                rules_data["slab2_limit"],
                rules_data["slab2_points"],
                rules_data["slab3_limit"],
                rules_data["slab3_points"],
                rules_data["slab4_limit"],
                rules_data["slab4_points"],
                rules_data["slab_above_points"],
            ),
        )
        conn.commit()
    finally:
        conn.close()


def reset_rules_to_default(db_path=DEFAULT_DB_PATH):
    """Restore default scholarship rules."""
    update_rules(DEFAULT_RULES, db_path=db_path)


def get_all_students(db_path=DEFAULT_DB_PATH):
    """Return all student records ordered by application_date DESC, id DESC."""
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM students ORDER BY application_date DESC, id DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_student_by_id(student_id, db_path=DEFAULT_DB_PATH):
    """Fetch a single student record by its unique student_id."""
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM students WHERE UPPER(student_id) = UPPER(?)",
            (student_id.strip(),),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def add_student(student_data, db_path=DEFAULT_DB_PATH):
    """Insert a new student record using parameterized SQL."""
    conn = get_connection(db_path)
    try:
        conn.execute(
            """
            INSERT INTO students (
                student_id, full_name, age, gender, department, academic_year,
                phone, email, math_marks, physics_marks, chemistry_marks,
                english_marks, cs_marks, total_marks, aggregate_percentage,
                attendance_percentage, annual_income, income_certificate_status,
                scholarship_category, application_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                student_data["student_id"],
                student_data["full_name"],
                student_data["age"],
                student_data.get("gender", ""),
                student_data["department"],
                student_data["academic_year"],
                student_data.get("phone", ""),
                student_data.get("email", ""),
                student_data["math_marks"],
                student_data["physics_marks"],
                student_data["chemistry_marks"],
                student_data["english_marks"],
                student_data["cs_marks"],
                student_data["total_marks"],
                student_data["aggregate_percentage"],
                student_data["attendance_percentage"],
                student_data["annual_income"],
                student_data["income_certificate_status"],
                student_data["scholarship_category"],
                student_data["application_date"],
            ),
        )
        conn.commit()
    finally:
        conn.close()


def update_student(original_student_id, student_data, db_path=DEFAULT_DB_PATH):
    """Update an existing student record using parameterized SQL."""
    conn = get_connection(db_path)
    try:
        conn.execute(
            """
            UPDATE students SET
                student_id = ?,
                full_name = ?,
                age = ?,
                gender = ?,
                department = ?,
                academic_year = ?,
                phone = ?,
                email = ?,
                math_marks = ?,
                physics_marks = ?,
                chemistry_marks = ?,
                english_marks = ?,
                cs_marks = ?,
                total_marks = ?,
                aggregate_percentage = ?,
                attendance_percentage = ?,
                annual_income = ?,
                income_certificate_status = ?,
                scholarship_category = ?,
                application_date = ?
            WHERE UPPER(student_id) = UPPER(?)
            """,
            (
                student_data["student_id"],
                student_data["full_name"],
                student_data["age"],
                student_data.get("gender", ""),
                student_data["department"],
                student_data["academic_year"],
                student_data.get("phone", ""),
                student_data.get("email", ""),
                student_data["math_marks"],
                student_data["physics_marks"],
                student_data["chemistry_marks"],
                student_data["english_marks"],
                student_data["cs_marks"],
                student_data["total_marks"],
                student_data["aggregate_percentage"],
                student_data["attendance_percentage"],
                student_data["annual_income"],
                student_data["income_certificate_status"],
                student_data["scholarship_category"],
                student_data["application_date"],
                original_student_id.strip(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def delete_student(student_id, db_path=DEFAULT_DB_PATH):
    """Delete a student record by student_id. Returns True if a row was deleted."""
    conn = get_connection(db_path)
    try:
        cursor = conn.execute(
            "DELETE FROM students WHERE UPPER(student_id) = UPPER(?)",
            (student_id.strip(),),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def count_missing_sample_students(db_path=DEFAULT_DB_PATH):
    """Count how many built-in sample students are not currently in the database."""
    existing_ids = {s["student_id"].upper() for s in get_all_students(db_path)}
    missing = 0
    for sample in SAMPLE_STUDENTS:
        if sample["student_id"].upper() not in existing_ids:
            missing += 1
    return missing


def load_sample_students(db_path=DEFAULT_DB_PATH):
    """
    Insert sample students into the database while preventing duplicates.
    Returns tuple: (inserted_count, skipped_count).
    """
    existing_ids = {s["student_id"].upper() for s in get_all_students(db_path)}
    inserted = 0
    skipped = 0

    for sample in SAMPLE_STUDENTS:
        sid = sample["student_id"].upper()
        if sid in existing_ids:
            skipped += 1
            continue

        record = dict(sample)
        marks_list = [float(record[key]) for key, _ in SUBJECT_TUPLE]
        total, aggregate = calculate_academic_totals(marks_list)
        record["total_marks"] = total
        record["aggregate_percentage"] = aggregate
        add_student(record, db_path=db_path)
        existing_ids.add(sid)
        inserted += 1

    return inserted, skipped
