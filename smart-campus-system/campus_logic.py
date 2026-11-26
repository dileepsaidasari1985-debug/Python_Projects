"""Core Comprehensive Smart Campus Management Simulation logic (Case Study #100).

Integrates 6 modules using Python syllabus concepts ONLY:
- Variables, data types, arithmetic/relational/logical operators
- Conditional statements (if / elif / else) and loops (for, while)
- Strings and ASCII summary report pattern generation
- Lists and nested lists (student marks rows, attendance logs, bookings)
- Tuples, tuple operations, and tuple unpacking
"""

DEPARTMENTS = ("Computer Science", "Information Technology", "Electronics", "Mechanical", "Civil")
ACADEMIC_YEARS = ("1st Year", "2nd Year", "3rd Year", "4th Year")
MENU_OPTIONS = (
    (1, "Student Records"),
    (2, "Attendance Tracking"),
    (3, "Marks & Grading"),
    (4, "Event Registration"),
    (5, "Resource Allocation"),
    (6, "Summary Reporting"),
    (0, "Exit Simulation"),
)

GRADE_SCALE = ((90.0, "A+"), (80.0, "A"), (70.0, "B+"), (60.0, "B"), (50.0, "C"), (40.0, "D"), (0.0, "F"))
ATTENDANCE_MIN_PCT = 75.0


def clean_code(raw_val):
    return str(raw_val or "").strip().upper()


def clean_title_name(raw_val):
    return " ".join(str(raw_val or "").strip().split()).title()


def compute_grade(avg):
    for cutoff, grade in GRADE_SCALE:
        if avg >= cutoff:
            return grade
    return "F"


def validate_student_record(student_id, name, department, year):
    errors = []
    sid = clean_code(student_id)
    sname = clean_title_name(name)
    if not sid or len(sid) < 3:
        errors.append("Student ID must be at least 3 characters.")
    if not sname:
        errors.append("Student name is required.")
    if department not in DEPARTMENTS:
        errors.append("Select a valid department.")
    if year not in ACADEMIC_YEARS:
        errors.append("Select a valid academic year.")
    return (len(errors) == 0, (sid, sname, department, year), errors)


def evaluate_attendance_record(attended_raw, total_raw):
    try:
        attended = int(str(attended_raw).strip())
        total = int(str(total_raw).strip())
    except (ValueError, TypeError):
        return (False, 0, 0, 0.0, "Attendance counts must be integers.")

    if total <= 0 or attended < 0 or attended > total:
        return (False, 0, 0, 0.0, "Attended classes must be between 0 and total classes (> 0).")

    pct = round((attended / total) * 100.0, 2)
    return (True, attended, total, pct, "")


def evaluate_marks_tuple(marks_tuple):
    """Compute total, average, grade, and pass flag from a tuple of subject marks."""
    total = 0.0
    passed_all = True
    for mark in marks_tuple:
        total += float(mark)
        if float(mark) < 40.0:
            passed_all = False
    avg = round(total / len(marks_tuple), 2) if marks_tuple else 0.0
    return (round(total, 2), avg, compute_grade(avg), passed_all)


def process_event_registration(student_id, event_code, events_list, registrations_list):
    """Register a student into an event enforcing duplicate checks and event capacity."""
    sid = clean_code(student_id)
    ecode = clean_code(event_code)

    target_event = None
    for ev in events_list:
        if ev["event_code"] == ecode:
            target_event = ev
            break

    if target_event is None:
        return (False, f"Event '{ecode}' not found.")

    current_count = 0
    for reg in registrations_list:
        if reg["event_code"] == ecode:
            current_count += 1
            if reg["student_id"] == sid:
                return (False, f"Student '{sid}' is already registered for {target_event['event_name']}.")

    if current_count >= int(target_event["capacity"]):
        return (False, f"Event '{target_event['event_name']}' is full (capacity {target_event['capacity']}).")

    return (True, f"Registered {sid} for {target_event['event_name']}.")


def check_resource_allocation(resource_code, requester_id, slot_label, resources_list, allocations_list):
    """Check if a campus resource is operational and free in the requested time slot."""
    rcode = clean_code(resource_code)
    req = clean_code(requester_id)
    slot = " ".join(str(slot_label or "").strip().split())

    if not req or not slot:
        return (False, "Requester ID and time slot are required.")

    target_res = None
    for res in resources_list:
        if res["resource_code"] == rcode:
            target_res = res
            break

    if target_res is None:
        return (False, f"Resource '{rcode}' does not exist.")
    if target_res["status"] != "Available":
        return (False, f"Resource '{rcode}' is currently {target_res['status']}.")

    for alloc in allocations_list:
        if alloc["resource_code"] == rcode and alloc["slot_label"].upper() == slot.upper():
            return (False, f"Conflict: {rcode} is already allocated for '{slot}' to {alloc['requester_id']}.")

    return (True, f"Allocated {target_res['resource_name']} ({rcode}) for {slot}.")


def build_campus_summary(students, events, registrations, resources, allocations):
    """Aggregate campus-wide metrics and build a loop-generated ASCII summary report."""
    total_students = len(students)
    shortage_students = []
    honors_students = []
    sum_att = 0.0
    sum_avg = 0.0

    for st in students:
        marks_tuple = (st["math_mark"], st["cs_mark"], st["eng_mark"])
        total_m, avg_m, grade, passed_all = evaluate_marks_tuple(marks_tuple)
        att_pct = round((st["attended_classes"] / st["total_classes"]) * 100.0, 2) if st["total_classes"] > 0 else 0.0
        st["total_marks"] = total_m
        st["avg_marks"] = avg_m
        st["grade"] = grade
        st["passed_all"] = passed_all
        st["attendance_pct"] = att_pct

        sum_att += att_pct
        sum_avg += avg_m
        if att_pct < ATTENDANCE_MIN_PCT:
            shortage_students.append(st)
        if avg_m >= 85.0 and att_pct >= 80.0:
            honors_students.append(st)

    avg_attendance = round(sum_att / total_students, 2) if total_students else 0.0
    avg_marks = round(sum_avg / total_students, 2) if total_students else 0.0

    event_summary = []
    for ev in events:
        reg_cnt = sum(1 for r in registrations if r["event_code"] == ev["event_code"])
        event_summary.append({**ev, "registered": reg_cnt, "seats_left": max(0, ev["capacity"] - reg_cnt)})

    lines = [
        "+" + "-" * 66 + "+",
        "| SMART CAMPUS EXECUTIVE SUMMARY REPORT (CASE STUDY #100)".ljust(67) + "|",
        "+" + "-" * 66 + "+",
        f"| Students: {total_students:<5} | Avg Attendance: {avg_attendance:5.1f}% | Avg Marks: {avg_marks:5.1f}%      |",
        f"| Attendance Shortage (<75%): {len(shortage_students):<3} | Honors Scholars: {len(honors_students):<15} |",
        f"| Event Registrations: {len(registrations):<5} | Resource Bookings: {len(allocations):<16} |",
        "+" + "-" * 66 + "+",
        f"| {'ID':<8} {'Name':<18} {'Dept':<14} {'Att%':>6} {'Avg%':>6} {'Grd':>4} |",
        "|" + "-" * 66 + "|",
    ]
    for st in students:
        lines.append(
            f"| {st['student_id']:<8} {st['name'][:18]:<18} {st['department'][:14]:<14} {st['attendance_pct']:6.1f} {st['avg_marks']:6.1f} {st['grade']:>4} |"
        )
    lines.append("+" + "-" * 66 + "+")

    return {
        "total_students": total_students,
        "avg_attendance": avg_attendance,
        "avg_marks": avg_marks,
        "shortage_students": shortage_students,
        "honors_students": honors_students,
        "event_summary": event_summary,
        "total_registrations": len(registrations),
        "total_allocations": len(allocations),
        "total_resources": len(resources),
        "ascii_summary": "\n".join(lines),
    }
