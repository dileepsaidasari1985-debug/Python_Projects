"""Core Student Marks Matrix Analysis logic (Case Study #42).

Demonstrates Python syllabus concepts:
- Variables, data types, arithmetic & relational/logical operators
- Conditional statements and nested loops (row-wise & column-wise matrix traversal)
- Strings and ASCII bar/table pattern generation
- Lists and nested lists (2D matrix of [student_id, name, [marks...]])
- Tuples, tuple operations, and tuple unpacking
"""

DEFAULT_SUBJECTS = ("Mathematics", "Physics", "Chemistry", "English", "Computer Science")

GRADE_BANDS = (
    (90.0, "A+"),
    (80.0, "A"),
    (70.0, "B+"),
    (60.0, "B"),
    (50.0, "C"),
    (40.0, "D"),
    (0.0, "F"),
)


def compute_grade(avg_mark):
    """Return letter grade for a numeric average using tuple unpacking."""
    for cutoff, letter in GRADE_BANDS:
        if avg_mark >= cutoff:
            return letter
    return "F"


def generate_bar_pattern(percentage, width=16):
    """Generate an ASCII bar chart strip using a loop."""
    filled = int(round((float(percentage) / 100.0) * width))
    if filled < 0:
        filled = 0
    elif filled > width:
        filled = width
    bar = ""
    i = 0
    while i < width:
        bar += "█" if i < filled else "░"
        i += 1
    return bar


def validate_student_marks_row(student_id, student_name, raw_marks, subjects=DEFAULT_SUBJECTS):
    """Validate student ID, name, and mark list (0-100). Returns (ok, cleaned_row, errors)."""
    errors = []
    sid = str(student_id or "").strip().upper()
    sname = " ".join(str(student_name or "").strip().split()).title()
    if not sid:
        errors.append("Student ID is required.")
    if not sname:
        errors.append("Student name is required.")

    cleaned_marks = []
    for idx, subj in enumerate(subjects):
        raw_val = raw_marks[idx] if idx < len(raw_marks) else ""
        try:
            val = round(float(str(raw_val).strip()), 2)
            if val < 0 or val > 100:
                errors.append(f"{subj} marks must be between 0 and 100.")
            else:
                cleaned_marks.append(val)
        except (ValueError, TypeError):
            errors.append(f"{subj} marks must be numeric.")

    if errors:
        return (False, None, errors)
    return (True, (sid, sname, cleaned_marks), [])


def parse_matrix_text(raw_text, subjects=DEFAULT_SUBJECTS):
    """Parse multi-line CSV/pipe matrix rows: 'STU01, Aarav, 92, 78, 65, 88, 95'."""
    rows = []
    errors = []
    lines = [ln.strip() for ln in str(raw_text or "").splitlines() if ln.strip()]
    if not lines:
        return (False, [], ["Please enter at least one student marks row."])

    expected_cols = 2 + len(subjects)
    for line_no, line in enumerate(lines, start=1):
        sep = "|" if "|" in line else ","
        parts = [p.strip() for p in line.split(sep)]
        if len(parts) != expected_cols:
            errors.append(f"Line {line_no}: expected {expected_cols} columns (ID, Name, {len(subjects)} marks).")
            continue
        ok, cleaned, row_errs = validate_student_marks_row(parts[0], parts[1], parts[2:], subjects)
        if not ok:
            for e in row_errs:
                errors.append(f"Line {line_no}: {e}")
        else:
            rows.append(cleaned)

    return (len(errors) == 0, rows, errors)


def analyze_marks_matrix(student_rows, subjects=DEFAULT_SUBJECTS, low_avg_threshold=60.0, pass_mark=40.0):
    """Analyze a 2D nested list/tuple matrix of student marks.

    student_rows items: (student_id, student_name, [m0, m1, ..., mk])
    Computes:
    - Row-wise student stats (total, average, min, max, grade, pass/fail)
    - Column-wise subject stats (average, highest, lowest, pass rate, low-avg alert)
    - Ranked top performers (tuple comparison)
    - Low-average subjects list
    - ASCII matrix summary report
    """
    num_students = len(student_rows)
    num_subjects = len(subjects)

    row_stats = []
    for sid, sname, marks in student_rows:
        total = 0.0
        min_m = marks[0] if marks else 0.0
        max_m = marks[0] if marks else 0.0
        failed_subjs = []

        for idx, mark in enumerate(marks):
            total += mark
            if mark < min_m:
                min_m = mark
            if mark > max_m:
                max_m = mark
            if mark < pass_mark and idx < num_subjects:
                failed_subjs.append(subjects[idx])

        avg = round(total / num_subjects, 2) if num_subjects else 0.0
        row_stats.append({
            "student_id": sid,
            "student_name": sname,
            "marks": list(marks),
            "total": round(total, 2),
            "average": avg,
            "min_mark": round(min_m, 2),
            "max_mark": round(max_m, 2),
            "grade": compute_grade(avg),
            "passed_all": len(failed_subjs) == 0,
            "failed_subjects": failed_subjs,
            "bar": generate_bar_pattern(avg, 12),
        })

    # Rank students by (-average, -total, -min_mark, student_id)
    ranked_rows = list(row_stats)
    n = len(ranked_rows)
    for i in range(n):
        for j in range(i + 1, n):
            a = ranked_rows[i]
            b = ranked_rows[j]
            key_a = (-a["average"], -a["total"], -a["min_mark"], a["student_id"])
            key_b = (-b["average"], -b["total"], -b["min_mark"], b["student_id"])
            if key_b < key_a:
                ranked_rows[i], ranked_rows[j] = ranked_rows[j], ranked_rows[i]

    for rank_idx, item in enumerate(ranked_rows, start=1):
        item["rank"] = rank_idx

    top_performers = ranked_rows[:3]

    # Column-wise statistics using nested loop (subject column outer, student row inner)
    col_stats = []
    low_avg_subjects = []
    class_total_sum = 0.0

    for col_idx in range(num_subjects):
        subj_name = subjects[col_idx]
        if num_students == 0:
            col_stats.append({
                "subject": subj_name, "average": 0.0, "highest": 0.0, "lowest": 0.0,
                "pass_count": 0, "pass_rate": 0.0, "is_low_avg": True, "deficit": round(low_avg_threshold, 2),
                "bar": generate_bar_pattern(0, 14),
            })
            low_avg_subjects.append(col_stats[-1])
            continue

        col_sum = 0.0
        highest = student_rows[0][2][col_idx]
        lowest = student_rows[0][2][col_idx]
        pass_count = 0

        for row in student_rows:
            val = row[2][col_idx]
            col_sum += val
            if val > highest:
                highest = val
            if val < lowest:
                lowest = val
            if val >= pass_mark:
                pass_count += 1

        subj_avg = round(col_sum / num_students, 2)
        class_total_sum += subj_avg
        pass_rate = round((pass_count / num_students) * 100.0, 2)
        is_low = subj_avg < low_avg_threshold
        deficit = round(low_avg_threshold - subj_avg, 2) if is_low else 0.0

        stat = {
            "subject": subj_name,
            "average": subj_avg,
            "highest": round(highest, 2),
            "lowest": round(lowest, 2),
            "pass_count": pass_count,
            "pass_rate": pass_rate,
            "is_low_avg": is_low,
            "deficit": deficit,
            "bar": generate_bar_pattern(subj_avg, 14),
        }
        col_stats.append(stat)
        if is_low:
            low_avg_subjects.append(stat)

    overall_avg = round(class_total_sum / num_subjects, 2) if (num_subjects and num_students) else 0.0
    ascii_report = generate_ascii_matrix_report(row_stats, col_stats, top_performers, low_avg_subjects, subjects)

    return {
        "subjects": list(subjects),
        "student_count": num_students,
        "low_avg_threshold": low_avg_threshold,
        "pass_mark": pass_mark,
        "overall_average": overall_avg,
        "row_stats": row_stats,
        "ranked_rows": ranked_rows,
        "top_performers": top_performers,
        "col_stats": col_stats,
        "low_avg_subjects": low_avg_subjects,
        "ascii_report": ascii_report,
    }


def generate_ascii_matrix_report(row_stats, col_stats, top_performers, low_avg_subjects, subjects):
    """Format an ASCII marks matrix & statistical summary using loops."""
    subj_hdr = " ".join(f"{s[:6]:>6}" for s in subjects)
    lines = [
        "+" + "-" * 74 + "+",
        "| STUDENT MARKS MATRIX ANALYSIS REPORT".ljust(75) + "|",
        "+" + "-" * 74 + "+",
        f"| {'ID':<8} {'Student':<16} {subj_hdr} {'Avg':>7} {'Grd':>4} |",
        "|" + "-" * 74 + "|",
    ]
    for r in row_stats:
        m_str = " ".join(f"{m:6.1f}" for m in r["marks"])
        lines.append(f"| {r['student_id']:<8} {r['student_name'][:16]:<16} {m_str} {r['average']:7.2f} {r['grade']:>4} |")

    lines.append("+" + "-" * 74 + "+")
    avg_str = " ".join(f"{c['average']:6.1f}" for c in col_stats)
    lines.append(f"| {'COL AVG':<25} {avg_str} {'':>12} |")
    lines.append("+" + "-" * 74 + "+")

    if top_performers:
        top_line = ", ".join(f"#{t['rank']} {t['student_name']} ({t['average']:.2f}%)" for t in top_performers)
        lines.append(f"Top Performers: {top_line}")
    if low_avg_subjects:
        low_line = ", ".join(f"{c['subject']} ({c['average']:.2f}%)" for c in low_avg_subjects)
        lines.append(f"Low-Average Alerts: {low_line}")
    else:
        lines.append("Low-Average Alerts: None")

    return "\n".join(lines)
