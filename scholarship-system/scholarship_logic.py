"""
University Scholarship Allocation System - Core Business Logic
-------------------------------------------------------------
This module implements the beginner-friendly Python algorithms for:
1. Validating student application inputs
2. Calculating total marks, aggregate percentage, and income merit score
3. Evaluating eligibility rules and collecting specific rejection reasons
4. Calculating scholarship scores using configurable weights
5. Ranking eligible students and resolving ties using tuple operations
6. Generating text-based merit patterns and department summary tables

Python syllabus concepts demonstrated:
- Variables, data types (int, float, str, bool), and operators
- Conditional statements (if / elif / else)
- Loops (for, while)
- Strings and string operations (.strip, .upper, .title, slicing, f-strings)
- Pattern generation (merit star badges and ASCII award banners)
- Lists and nested lists
- Tuples, tuple operations, and tuple unpacking
"""

import re
from datetime import date

# Tuple of the 5 academic subjects (immutable sequence)
SUBJECT_TUPLE = (
    ("math_marks", "Mathematics"),
    ("physics_marks", "Physics"),
    ("chemistry_marks", "Chemistry"),
    ("english_marks", "English"),
    ("cs_marks", "Computer Science"),
)

# Tuple of valid university departments
DEPARTMENTS = (
    "Computer Science",
    "Information Technology",
    "Electronics & Communication",
    "Electrical Engineering",
    "Mechanical Engineering",
    "Civil Engineering",
    "Mathematics",
    "Physics",
)

# Tuple of valid academic years
ACADEMIC_YEARS = (
    "1st Year",
    "2nd Year",
    "3rd Year",
    "4th Year",
)

# Tuple of scholarship categories
SCHOLARSHIP_CATEGORIES = (
    "Merit-cum-Means",
    "Academic Excellence",
    "STEM Merit",
    "Need-Based Grant",
)

# Tuple of default rules dictionary keys & values
DEFAULT_RULES = {
    "min_aggregate": 75.0,
    "min_subject_marks": 50.0,
    "min_attendance": 75.0,
    "max_family_income": 250000.0,
    "income_certificate_required": 1,
    "scholarship_quota": 10,
    "weight_aggregate": 0.70,
    "weight_attendance": 0.20,
    "weight_income": 0.10,
    "slab1_limit": 100000.0,
    "slab1_points": 100.0,
    "slab2_limit": 150000.0,
    "slab2_points": 80.0,
    "slab3_limit": 200000.0,
    "slab3_points": 60.0,
    "slab4_limit": 250000.0,
    "slab4_points": 40.0,
    "slab_above_points": 0.0,
}


def format_inr(amount):
    """Format a numeric amount in Indian Rupee grouping (e.g., 2,50,000)."""
    value = int(round(float(amount)))
    negative = value < 0
    digits = str(abs(value))

    if len(digits) <= 3:
        formatted = digits
    else:
        last_three = digits[-3:]
        remaining = digits[:-3]
        groups = []
        while len(remaining) > 2:
            groups.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            groups.insert(0, remaining)
        formatted = ",".join(groups) + "," + last_three

    if negative:
        return f"-₹{formatted}"
    return f"₹{formatted}"


def clean_student_id(raw_id):
    """Normalize student ID using string operations (strip whitespace, uppercase)."""
    return str(raw_id or "").strip().upper()


def clean_name(raw_name):
    """Normalize student name using string operations (collapse spaces, title case)."""
    parts = str(raw_name or "").strip().split()
    return " ".join(parts).title()


def generate_merit_pattern(score, is_eligible):
    """
    Demonstrate pattern generation using loops and string operations.
    Returns a 5-star visual merit tier string based on scholarship score.
    """
    if not is_eligible:
        return "☆☆☆☆☆ (Not Eligible)"

    if score >= 90:
        filled_stars = 5
    elif score >= 80:
        filled_stars = 4
    elif score >= 70:
        filled_stars = 3
    elif score >= 60:
        filled_stars = 2
    else:
        filled_stars = 1

    pattern = ""
    index = 0
    while index < 5:
        if index < filled_stars:
            pattern = pattern + "★"
        else:
            pattern = pattern + "☆"
        index = index + 1

    return f"{pattern} (Tier {filled_stars}/5)"


def generate_award_banner(student_name, student_id, rank, score):
    """
    Generate a beginner-friendly ASCII decorative award certificate pattern
    using loops and string formatting for printable scholarship summaries.
    """
    title_line = f" UNIVERSITY SCHOLARSHIP AWARD - RANK #{rank} "
    detail_line = f" Recipient: {student_name} ({student_id}) | Score: {score:.2f} "
    box_width = max(len(title_line), len(detail_line)) + 4

    border = ""
    for _ in range(box_width):
        border = border + "="

    lines = [
        border,
        f"| {title_line.center(box_width - 4)} |",
        f"| {detail_line.center(box_width - 4)} |",
        border,
    ]
    return "\n".join(lines)


def validate_student_data(form_data):
    """
    Validate all student form inputs on the server side.
    Returns a tuple: (is_valid: bool, cleaned_data: dict, errors: list[str]).
    """
    errors = []
    cleaned = {}

    # 1. Student ID
    student_id = clean_student_id(form_data.get("student_id", ""))
    if not student_id:
        errors.append("Student ID is required.")
    elif not re.fullmatch(r"[A-Z0-9_-]{3,20}", student_id):
        errors.append("Student ID must be 3–20 characters (letters, numbers, hyphens, or underscores only).")
    cleaned["student_id"] = student_id

    # 2. Full Name
    full_name = clean_name(form_data.get("full_name", ""))
    if not full_name:
        errors.append("Full name is required.")
    elif len(full_name) < 2:
        errors.append("Full name must be at least 2 characters.")
    cleaned["full_name"] = full_name

    # 3. Age
    age_raw = str(form_data.get("age", "")).strip()
    if not age_raw:
        errors.append("Age is required.")
    else:
        try:
            age = int(age_raw)
            if age < 15 or age > 60:
                errors.append("Age must be between 15 and 60.")
            cleaned["age"] = age
        except ValueError:
            errors.append("Age must be a valid whole number.")

    # 4. Optional Gender
    cleaned["gender"] = str(form_data.get("gender", "")).strip()

    # 5. Department & Academic Year
    department = str(form_data.get("department", "")).strip()
    if not department:
        errors.append("Department is required.")
    cleaned["department"] = department

    academic_year = str(form_data.get("academic_year", "")).strip()
    if not academic_year:
        errors.append("Academic year is required.")
    cleaned["academic_year"] = academic_year

    # 6. Optional Phone & Email
    phone = str(form_data.get("phone", "")).strip()
    if phone:
        digits_only = "".join(ch for ch in phone if ch.isdigit())
        if len(digits_only) < 7 or len(digits_only) > 15:
            errors.append("Phone number must contain 7 to 15 digits if provided.")
    cleaned["phone"] = phone

    email = str(form_data.get("email", "")).strip().lower()
    if email:
        if "@" not in email or "." not in email.split("@")[-1]:
            errors.append("Please enter a valid email address.")
    cleaned["email"] = email

    # 7. Five Subject Marks (0 to 100) using tuple unpacking
    for field_key, subject_label in SUBJECT_TUPLE:
        raw_mark = str(form_data.get(field_key, "")).strip()
        if raw_mark == "":
            errors.append(f"{subject_label} marks are required.")
        else:
            try:
                mark_value = float(raw_mark)
                if mark_value < 0 or mark_value > 100:
                    errors.append(f"{subject_label} marks must be between 0 and 100.")
                cleaned[field_key] = round(mark_value, 2)
            except ValueError:
                errors.append(f"{subject_label} marks must be a valid number.")

    # 8. Attendance Percentage (0 to 100)
    att_raw = str(form_data.get("attendance_percentage", "")).strip()
    if att_raw == "":
        errors.append("Attendance percentage is required.")
    else:
        try:
            att_value = float(att_raw)
            if att_value < 0 or att_value > 100:
                errors.append("Attendance percentage must be between 0 and 100.")
            cleaned["attendance_percentage"] = round(att_value, 2)
        except ValueError:
            errors.append("Attendance percentage must be a valid number.")

    # 9. Annual Family Income (>= 0)
    inc_raw = str(form_data.get("annual_income", "")).strip()
    if inc_raw == "":
        errors.append("Annual family income is required.")
    else:
        try:
            inc_value = float(inc_raw)
            if inc_value < 0:
                errors.append("Annual family income cannot be negative.")
            cleaned["annual_income"] = round(inc_value, 2)
        except ValueError:
            errors.append("Annual family income must be a valid number.")

    # 10. Income Certificate Status
    cert_status = str(form_data.get("income_certificate_status", "")).strip()
    if cert_status not in ("Available", "Missing"):
        errors.append("Income certificate status must be 'Available' or 'Missing'.")
    cleaned["income_certificate_status"] = cert_status

    # 11. Scholarship Category & Application Date
    category = str(form_data.get("scholarship_category", "")).strip()
    if not category:
        errors.append("Scholarship category is required.")
    cleaned["scholarship_category"] = category

    app_date = str(form_data.get("application_date", "")).strip()
    if not app_date:
        app_date = date.today().isoformat()
    else:
        try:
            date.fromisoformat(app_date)
        except ValueError:
            errors.append("Application date must be in YYYY-MM-DD format.")
    cleaned["application_date"] = app_date

    # Auto-calculate total marks and aggregate percentage if all 5 marks are valid
    if all(key in cleaned for key, _ in SUBJECT_TUPLE):
        marks_list = [cleaned[key] for key, _ in SUBJECT_TUPLE]
        total, aggregate = calculate_academic_totals(marks_list)
        cleaned["total_marks"] = total
        cleaned["aggregate_percentage"] = aggregate

    is_valid = len(errors) == 0
    return is_valid, cleaned, errors


def validate_rules_data(form_data):
    """
    Validate administrator-configured scholarship rules.
    Returns a tuple: (is_valid: bool, cleaned_rules: dict, errors: list[str]).
    """
    errors = []
    cleaned = {}

    float_fields = (
        ("min_aggregate", "Minimum aggregate percentage", 0.0, 100.0),
        ("min_subject_marks", "Minimum subject marks", 0.0, 100.0),
        ("min_attendance", "Minimum attendance percentage", 0.0, 100.0),
        ("max_family_income", "Maximum annual family income", 0.0, 100000000.0),
        ("weight_aggregate", "Aggregate weight", 0.0, 1.0),
        ("weight_attendance", "Attendance weight", 0.0, 1.0),
        ("weight_income", "Income merit weight", 0.0, 1.0),
        ("slab1_limit", "Income Slab 1 upper limit", 0.0, 100000000.0),
        ("slab1_points", "Income Slab 1 points", 0.0, 100.0),
        ("slab2_limit", "Income Slab 2 upper limit", 0.0, 100000000.0),
        ("slab2_points", "Income Slab 2 points", 0.0, 100.0),
        ("slab3_limit", "Income Slab 3 upper limit", 0.0, 100000000.0),
        ("slab3_points", "Income Slab 3 points", 0.0, 100.0),
        ("slab4_limit", "Income Slab 4 upper limit", 0.0, 100000000.0),
        ("slab4_points", "Income Slab 4 points", 0.0, 100.0),
        ("slab_above_points", "Income above Slab 4 points", 0.0, 100.0),
    )

    for key, label, low, high in float_fields:
        raw_val = str(form_data.get(key, "")).strip()
        if raw_val == "":
            errors.append(f"{label} is required.")
        else:
            try:
                num_val = float(raw_val)
                if num_val < low or num_val > high:
                    errors.append(f"{label} must be between {low} and {high}.")
                cleaned[key] = num_val
            except ValueError:
                errors.append(f"{label} must be a valid number.")

    quota_raw = str(form_data.get("scholarship_quota", "")).strip()
    if quota_raw == "":
        errors.append("Scholarship quota is required.")
    else:
        try:
            quota = int(quota_raw)
            if quota < 1 or quota > 1000:
                errors.append("Scholarship quota must be between 1 and 1000.")
            cleaned["scholarship_quota"] = quota
        except ValueError:
            errors.append("Scholarship quota must be a whole number.")

    cert_req = str(form_data.get("income_certificate_required", "1")).strip()
    cleaned["income_certificate_required"] = 1 if cert_req in ("1", "true", "yes", "on") else 0

    # Check that score weights sum to 1.00
    if (
        "weight_aggregate" in cleaned
        and "weight_attendance" in cleaned
        and "weight_income" in cleaned
    ):
        weight_sum = round(
            cleaned["weight_aggregate"] + cleaned["weight_attendance"] + cleaned["weight_income"],
            4,
        )
        if abs(weight_sum - 1.0) > 0.001:
            errors.append(
                f"Score weights must sum to 1.00 (currently {weight_sum:.2f})."
            )

    # Check ascending income slab limits
    if all(k in cleaned for k in ("slab1_limit", "slab2_limit", "slab3_limit", "slab4_limit")):
        s1 = cleaned["slab1_limit"]
        s2 = cleaned["slab2_limit"]
        s3 = cleaned["slab3_limit"]
        s4 = cleaned["slab4_limit"]
        if not (s1 <= s2 <= s3 <= s4):
            errors.append("Income slab limits must be in ascending order (Slab 1 <= Slab 2 <= Slab 3 <= Slab 4).")

    return len(errors) == 0, cleaned, errors


def calculate_academic_totals(marks_list):
    """
    Calculate total marks and aggregate percentage from a list of 5 subject marks.
    Returns tuple: (total_marks, aggregate_percentage).
    """
    total = 0.0
    for mark in marks_list:
        total = total + float(mark)

    subject_count = len(marks_list)
    aggregate = total / subject_count if subject_count > 0 else 0.0
    return round(total, 2), round(aggregate, 2)


def get_income_merit_score(annual_income, rules):
    """
    Calculate the Income Merit Score using a tuple of income range slabs
    and tuple unpacking.
    """
    income = float(annual_income)

    # List of (upper_limit, points) tuples
    income_slabs = [
        (float(rules["slab1_limit"]), float(rules["slab1_points"])),
        (float(rules["slab2_limit"]), float(rules["slab2_points"])),
        (float(rules["slab3_limit"]), float(rules["slab3_points"])),
        (float(rules["slab4_limit"]), float(rules["slab4_points"])),
    ]

    for limit_amount, slab_points in income_slabs:
        if income <= limit_amount:
            return slab_points

    return float(rules["slab_above_points"])


def evaluate_eligibility(student, rules):
    """
    Evaluate all scholarship eligibility conditions for a single student.
    Returns a tuple: (is_eligible: bool, rejection_reasons: list[str]).
    """
    reasons = []

    aggregate = float(student["aggregate_percentage"])
    attendance = float(student["attendance_percentage"])
    income = float(student["annual_income"])
    cert_status = str(student["income_certificate_status"]).strip()

    # 1. Check aggregate percentage
    min_agg = float(rules["min_aggregate"])
    if aggregate < min_agg:
        reasons.append(
            f"Aggregate percentage below minimum ({aggregate:.2f}% < {min_agg:.2f}%)"
        )

    # 2. Check subject-wise minimum marks using a loop and tuple unpacking
    min_sub = float(rules["min_subject_marks"])
    failed_subjects = []
    for field_key, subject_name in SUBJECT_TUPLE:
        subject_mark = float(student[field_key])
        if subject_mark < min_sub:
            failed_subjects.append(f"{subject_name} ({subject_mark:.0f})")

    if len(failed_subjects) > 0:
        joined_subjects = ", ".join(failed_subjects)
        reasons.append(
            f"Subject marks below minimum ({min_sub:.0f}): {joined_subjects}"
        )

    # 3. Check minimum attendance
    min_att = float(rules["min_attendance"])
    if attendance < min_att:
        reasons.append(
            f"Attendance below minimum ({attendance:.2f}% < {min_att:.2f}%)"
        )

    # 4. Check maximum annual family income
    max_inc = float(rules["max_family_income"])
    if income > max_inc:
        reasons.append(
            f"Family income exceeds limit ({format_inr(income)} > {format_inr(max_inc)})"
        )

    # 5. Check income certificate requirement
    cert_required = bool(int(rules["income_certificate_required"]))
    if cert_required and cert_status != "Available":
        reasons.append("Income certificate missing")

    is_eligible = len(reasons) == 0
    return is_eligible, reasons


def calculate_scholarship_score(student, rules):
    """
    Calculate scholarship score using the configured weights:
    Score = (Aggregate * w_agg) + (Attendance * w_att) + (Income Merit Score * w_inc)
    Returns tuple: (scholarship_score, income_merit_score).
    """
    aggregate = float(student["aggregate_percentage"])
    attendance = float(student["attendance_percentage"])
    income_merit = get_income_merit_score(student["annual_income"], rules)

    w_agg = float(rules["weight_aggregate"])
    w_att = float(rules["weight_attendance"])
    w_inc = float(rules["weight_income"])

    raw_score = (aggregate * w_agg) + (attendance * w_att) + (income_merit * w_inc)
    return round(raw_score, 2), round(income_merit, 2)


def build_tie_break_tuple(student_record):
    """
    Build a Python tuple for sorting eligible students with tie-breaking rules:
    1. Higher scholarship score (negated for descending)
    2. Higher aggregate percentage (negated for descending)
    3. Higher attendance percentage (negated for descending)
    4. Lower annual family income (positive for ascending)
    5. Higher total marks (negated for descending)
    6. Student ID in alphabetical order (ascending)
    """
    return (
        -float(student_record["scholarship_score"]),
        -float(student_record["aggregate_percentage"]),
        -float(student_record["attendance_percentage"]),
        float(student_record["annual_income"]),
        -float(student_record["total_marks"]),
        str(student_record["student_id"]).upper(),
    )


def describe_tie_resolution(prev_student, curr_student):
    """
    Compare two eligible students who have the exact same scholarship score
    and return a human-readable explanation of which tie-breaker rule separated them.
    """
    if float(prev_student["aggregate_percentage"]) != float(curr_student["aggregate_percentage"]):
        return "Tie broken by higher aggregate percentage"
    if float(prev_student["attendance_percentage"]) != float(curr_student["attendance_percentage"]):
        return "Tie broken by higher attendance percentage"
    if float(prev_student["annual_income"]) != float(curr_student["annual_income"]):
        return "Tie broken by lower annual family income"
    if float(prev_student["total_marks"]) != float(curr_student["total_marks"]):
        return "Tie broken by higher total marks"
    return "Tie broken by alphabetical Student ID"


def evaluate_and_rank_all(students_rows, rules):
    """
    Core Ranking Engine:
    1. Evaluates all student records against current rules.
    2. Separates eligible and rejected students into two lists.
    3. Calculates scholarship scores for eligible students.
    4. Sorts eligible students using tuple-based tie-breaking rules.
    5. Assigns ranks (1..N) and allocates scholarships up to quota.
    6. Computes dashboard and report statistics including nested department lists.

    Returns a dictionary containing:
    - all_evaluated: list of all student dicts with computed fields
    - eligible_ranked: sorted list of eligible student dicts
    - selected_students: list of selected recipients
    - waitlisted_students: list of eligible but not selected students
    - rejected_students: list of rejected students with rejection reasons
    - summary: dashboard/report metrics
    - department_table: nested list of [department, total, eligible, selected, avg_agg]
    """
    eligible_students = []
    rejected_students = []
    all_evaluated = []

    total_aggregate_sum = 0.0

    # Step 1 & 2: Evaluate each applicant and separate into eligible vs rejected lists
    for row in students_rows:
        student = dict(row)

        marks_list = [float(student[key]) for key, _ in SUBJECT_TUPLE]
        total_marks, aggregate_pct = calculate_academic_totals(marks_list)
        student["total_marks"] = total_marks
        student["aggregate_percentage"] = aggregate_pct
        total_aggregate_sum = total_aggregate_sum + aggregate_pct

        is_eligible, rejection_reasons = evaluate_eligibility(student, rules)
        income_merit = get_income_merit_score(student["annual_income"], rules)
        student["income_merit_score"] = income_merit
        student["is_eligible"] = is_eligible
        student["rejection_reasons"] = rejection_reasons
        student["rejection_summary"] = "; ".join(rejection_reasons) if rejection_reasons else ""
        student["tie_note"] = ""

        if is_eligible:
            score, _ = calculate_scholarship_score(student, rules)
            student["scholarship_score"] = score
            student["merit_pattern"] = generate_merit_pattern(score, True)
            eligible_students.append(student)
        else:
            student["scholarship_score"] = 0.00
            student["rank"] = None
            student["selection_status"] = "Not Eligible"
            student["selection_code"] = "rejected"
            student["merit_pattern"] = generate_merit_pattern(0.0, False)
            rejected_students.append(student)

    # Step 3 & 4: Sort eligible students using tuple-based tie-breaking
    eligible_ranked = sorted(eligible_students, key=build_tie_break_tuple)

    # Step 5: Assign ranks, detect tie-breakers, and allocate quota
    quota = int(rules["scholarship_quota"])
    selected_students = []
    waitlisted_students = []

    for index in range(len(eligible_ranked)):
        current = eligible_ranked[index]
        rank_number = index + 1
        current["rank"] = rank_number

        # Check if current student tied on scholarship_score with previous or next
        if index > 0:
            prev_student = eligible_ranked[index - 1]
            if float(prev_student["scholarship_score"]) == float(current["scholarship_score"]):
                note = describe_tie_resolution(prev_student, current)
                current["tie_note"] = note
                if not prev_student["tie_note"]:
                    prev_student["tie_note"] = note

        if rank_number <= quota:
            current["selection_status"] = "Eligible & Selected"
            current["selection_code"] = "selected"
            current["award_banner"] = generate_award_banner(
                current["full_name"],
                current["student_id"],
                rank_number,
                current["scholarship_score"],
            )
            selected_students.append(current)
        else:
            current["selection_status"] = "Eligible (Waitlisted)"
            current["selection_code"] = "waitlisted"
            current["award_banner"] = ""
            waitlisted_students.append(current)

    # Combine back in deterministic order: ranked eligible first, then rejected by ID
    rejected_sorted = sorted(rejected_students, key=lambda s: str(s["student_id"]).upper())
    all_evaluated = eligible_ranked + rejected_sorted

    # Step 6: Build nested list for Department-wise summary
    # Each row in department_table: [department_name, total_count, eligible_count, selected_count, avg_aggregate]
    dept_buckets = {}
    for student in all_evaluated:
        dept = student["department"]
        if dept not in dept_buckets:
            dept_buckets[dept] = [0, 0, 0, 0.0]
        dept_buckets[dept][0] += 1
        if student["is_eligible"]:
            dept_buckets[dept][1] += 1
        if student["selection_code"] == "selected":
            dept_buckets[dept][2] += 1
        dept_buckets[dept][3] += float(student["aggregate_percentage"])

    department_table = []
    for dept_name in sorted(dept_buckets.keys()):
        counts = dept_buckets[dept_name]
        dept_total = counts[0]
        dept_elig = counts[1]
        dept_sel = counts[2]
        dept_avg = round(counts[3] / dept_total, 2) if dept_total > 0 else 0.0
        department_table.append([dept_name, dept_total, dept_elig, dept_sel, dept_avg])

    # Summary statistics
    total_applicants = len(all_evaluated)
    eligible_count = len(eligible_ranked)
    rejected_count = len(rejected_sorted)
    allocated_count = len(selected_students)
    remaining_seats = max(0, quota - allocated_count)
    avg_marks = round(total_aggregate_sum / total_applicants, 2) if total_applicants > 0 else 0.0
    highest_student = eligible_ranked[0] if eligible_ranked else None
    highest_score = highest_student["scholarship_score"] if highest_student else 0.0

    summary = {
        "total_applicants": total_applicants,
        "eligible_count": eligible_count,
        "rejected_count": rejected_count,
        "scholarships_available": quota,
        "scholarships_allocated": allocated_count,
        "remaining_seats": remaining_seats,
        "waitlisted_count": len(waitlisted_students),
        "average_marks": avg_marks,
        "highest_student": highest_student,
        "highest_score": highest_score,
        "allocation_percent": round((allocated_count / quota) * 100, 1) if quota > 0 else 0.0,
    }

    return {
        "all_evaluated": all_evaluated,
        "eligible_ranked": eligible_ranked,
        "selected_students": selected_students,
        "waitlisted_students": waitlisted_students,
        "rejected_students": rejected_sorted,
        "summary": summary,
        "department_table": department_table,
    }
