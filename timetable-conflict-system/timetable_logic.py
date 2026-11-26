"""Core Student Timetable Conflict Detection logic (Case Study #23).

Demonstrates Python syllabus concepts:
- Variables, data types (int, float, str, bool), arithmetic & logical operators
- Conditional statements (if / elif / else) and loops (for, while, nested loops)
- Strings and string operations (.strip, .upper, .split, slicing, formatting)
- Pattern generation (ASCII weekly timetable grid and conflict status banners)
- Lists and nested lists (2D weekly schedule grids and conflict matrices)
- Tuples, tuple operations (concatenation, membership, indexing), and tuple unpacking
"""

# ---------------------------------------------------------------------------
# Tuple Constants (demonstrating Tuples & Tuple Operations)
# ---------------------------------------------------------------------------

VALID_DAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat")
WEEKEND_DAYS = ("Sat",)
CORE_DAYS = VALID_DAYS[:5]  # Tuple slicing

DAY_ALIASES = (
    ("MONDAY", "Mon"),
    ("MON", "Mon"),
    ("TUESDAY", "Tue"),
    ("TUE", "Tue"),
    ("WEDNESDAY", "Wed"),
    ("WED", "Wed"),
    ("THURSDAY", "Thu"),
    ("THU", "Thu"),
    ("FRIDAY", "Fri"),
    ("FRI", "Fri"),
    ("SATURDAY", "Sat"),
    ("SAT", "Sat"),
)

ROOM_STATUSES = ("Available", "Maintenance", "Reserved")

# Standard hourly grid slots for ASCII pattern & weekly matrix
GRID_SLOTS = (
    ("08:00-09:00", 480, 540),
    ("09:00-10:00", 540, 600),
    ("10:00-11:00", 600, 660),
    ("11:00-12:00", 660, 720),
    ("12:00-13:00", 720, 780),
    ("13:00-14:00", 780, 840),
    ("14:00-15:00", 840, 900),
    ("15:00-16:00", 900, 960),
    ("16:00-17:00", 960, 1020),
)


def normalize_day(raw_day):
    """Normalize a day string such as 'monday' or 'MON' into canonical 3-letter format."""
    cleaned = str(raw_day or "").strip().upper()
    for alias, canonical in DAY_ALIASES:
        if cleaned == alias:
            return canonical
    return ""


def parse_time_to_minutes(time_str):
    """Convert 'HH:MM' 24-hour string into integer minutes since midnight.

    Returns tuple: (is_valid, minutes_int, normalized_hhmm, error_message)
    """
    cleaned = str(time_str or "").strip()
    if ":" not in cleaned:
        return (False, 0, "", f"Time '{cleaned}' must use HH:MM format.")

    parts = cleaned.split(":")
    if len(parts) != 2:
        return (False, 0, "", f"Time '{cleaned}' has invalid colon format.")

    hour_str, minute_str = parts[0].strip(), parts[1].strip()
    if not (hour_str.isdigit() and minute_str.isdigit()):
        return (False, 0, "", f"Time '{cleaned}' must contain numeric digits only.")

    hour = int(hour_str)
    minute = int(minute_str)
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        return (False, 0, "", f"Time '{cleaned}' is out of 00:00-23:59 range.")

    total_minutes = hour * 60 + minute
    normalized = f"{hour:02d}:{minute:02d}"
    return (True, total_minutes, normalized, "")


def minutes_to_time_str(total_minutes):
    """Convert integer minutes since midnight back to 'HH:MM' string."""
    hours = int(total_minutes) // 60
    mins = int(total_minutes) % 60
    return f"{hours:02d}:{mins:02d}"


def build_schedule_string(course_code, course_title, day, start_time, end_time, room_code):
    """Format course schedule fields into a canonical pipe-delimited string."""
    return f"{course_code.strip().upper()} | {course_title.strip()} | {day} {start_time}-{end_time} | {room_code.strip().upper()}"


def parse_schedule_string(raw_string):
    """Parse a timetable entry string into a validated tuple.

    Supported formats:
    1) 'CS101 | Data Structures | Mon 09:00-10:30 | R-204'
    2) 'CS101 | Mon 09:00-10:30 | R-204'

    Returns tuple:
    (is_valid, course_tuple_or_none, error_message)
    where course_tuple is:
    (course_code, course_title, day, start_str, end_str, start_min, end_min, room_code)
    """
    text = str(raw_string or "").strip()
    if not text:
        return (False, None, "Schedule string cannot be empty.")

    segments = [seg.strip() for seg in text.split("|")]
    if len(segments) == 4:
        raw_code, raw_title, raw_slot, raw_room = segments
    elif len(segments) == 3:
        raw_code, raw_slot, raw_room = segments
        raw_title = raw_code
    else:
        return (
            False,
            None,
            "Invalid format. Use 'CODE | TITLE | Day HH:MM-HH:MM | ROOM'.",
        )

    course_code = raw_code.strip().upper()
    course_title = raw_title.strip()
    room_code = raw_room.strip().upper()

    if not course_code:
        return (False, None, "Course code is required.")
    if not room_code:
        return (False, None, "Room code is required.")

    slot_parts = raw_slot.split()
    if len(slot_parts) != 2:
        return (
            False,
            None,
            f"Slot '{raw_slot}' must be 'Day HH:MM-HH:MM' (e.g. 'Mon 09:00-10:30').",
        )

    day_token, window_token = slot_parts[0], slot_parts[1]
    day = normalize_day(day_token)
    if not day:
        return (False, None, f"Invalid day '{day_token}'. Valid days: {', '.join(VALID_DAYS)}.")

    if "-" not in window_token:
        return (False, None, f"Time window '{window_token}' must use HH:MM-HH:MM.")

    time_bounds = window_token.split("-")
    if len(time_bounds) != 2:
        return (False, None, f"Time window '{window_token}' has invalid range format.")

    ok_start, start_min, start_str, err_start = parse_time_to_minutes(time_bounds[0])
    if not ok_start:
        return (False, None, err_start)

    ok_end, end_min, end_str, err_end = parse_time_to_minutes(time_bounds[1])
    if not ok_end:
        return (False, None, err_end)

    if end_min <= start_min:
        return (False, None, "End time must be strictly after start time.")

    if start_min < 420 or end_min > 1260:
        return (False, None, "Classes must be scheduled between 07:00 and 21:00.")

    parsed_tuple = (
        course_code,
        course_title,
        day,
        start_str,
        end_str,
        start_min,
        end_min,
        room_code,
    )
    return (True, parsed_tuple, "")


def validate_course_fields(course_code, course_title, instructor, day, start_time, end_time, room_code, credits_raw):
    """Validate individual course form fields. Returns (is_valid, cleaned_dict, errors_list)."""
    errors = []
    code = str(course_code or "").strip().upper()
    title = " ".join(str(course_title or "").strip().split())
    prof = " ".join(str(instructor or "").strip().split()) or "TBA"
    norm_day = normalize_day(day)
    room = str(room_code or "").strip().upper()

    if not code or len(code) < 2:
        errors.append("Course code must be at least 2 characters.")
    if not title:
        errors.append("Course title is required.")
    if not norm_day:
        errors.append("Please select a valid day (Mon-Sat).")
    if not room:
        errors.append("Room code is required.")

    ok_s, s_min, s_str, err_s = parse_time_to_minutes(start_time)
    if not ok_s:
        errors.append(f"Start time: {err_s}")

    ok_e, e_min, e_str, err_e = parse_time_to_minutes(end_time)
    if not ok_e:
        errors.append(f"End time: {err_e}")

    if ok_s and ok_e:
        if e_min <= s_min:
            errors.append("End time must be strictly greater than start time.")
        elif s_min < 420 or e_min > 1260:
            errors.append("Class hours must be within 07:00 to 21:00.")

    try:
        credits = int(str(credits_raw).strip())
        if credits < 1 or credits > 6:
            errors.append("Credits must be between 1 and 6.")
    except (ValueError, TypeError):
        credits = 0
        errors.append("Credits must be an integer between 1 and 6.")

    if errors:
        return (False, {}, errors)

    schedule_string = build_schedule_string(code, title, norm_day, s_str, e_str, room)
    cleaned = {
        "course_code": code,
        "course_title": title,
        "instructor": prof,
        "day": norm_day,
        "start_time": s_str,
        "end_time": e_str,
        "start_min": s_min,
        "end_min": e_min,
        "room_code": room,
        "credits": credits,
        "schedule_string": schedule_string,
    }
    return (True, cleaned, [])


def intervals_overlap(start_a, end_a, start_b, end_b):
    """Return True if [start_a, end_a) and [start_b, end_b) strictly overlap.

    Adjacent back-to-back periods (e.g., 09:00-10:00 and 10:00-11:00) do NOT overlap.
    """
    return start_a < end_b and start_b < end_a


def compute_overlap_window(start_a, end_a, start_b, end_b):
    """Return (overlap_start_min, overlap_end_min, duration_min, formatted_window)."""
    ov_start = start_a if start_a > start_b else start_b
    ov_end = end_a if end_a < end_b else end_b
    duration = ov_end - ov_start
    if duration <= 0:
        return (0, 0, 0, "")
    window_str = f"{minutes_to_time_str(ov_start)}-{minutes_to_time_str(ov_end)}"
    return (ov_start, ov_end, duration, window_str)


def detect_overlapping_periods(course_tuples):
    """Compare all pairs of courses using nested loops and tuple unpacking.

    Each item in course_tuples is:
    (course_code, course_title, day, start_str, end_str, start_min, end_min, room_code)

    Returns a list of conflict dictionaries.
    """
    conflicts = []
    total = len(course_tuples)

    for i in range(total):
        code1, title1, day1, s1_str, e1_str, s1_min, e1_min, room1 = course_tuples[i]
        for j in range(i + 1, total):
            code2, title2, day2, s2_str, e2_str, s2_min, e2_min, room2 = course_tuples[j]

            if code1 == code2 and day1 == day2 and s1_min == s2_min and e1_min == e2_min:
                conflicts.append({
                    "kind": "DUPLICATE_COURSE",
                    "severity": "High",
                    "course_a": code1,
                    "title_a": title1,
                    "course_b": code2,
                    "title_b": title2,
                    "day": day1,
                    "slot_a": f"{s1_str}-{e1_str}",
                    "slot_b": f"{s2_str}-{e2_str}",
                    "overlap_window": f"{s1_str}-{e1_str}",
                    "overlap_minutes": e1_min - s1_min,
                    "room_a": room1,
                    "room_b": room2,
                    "same_room": room1 == room2,
                    "message": f"Duplicate entry for {code1} on {day1} ({s1_str}-{e1_str}).",
                })
                continue

            if day1 == day2 and intervals_overlap(s1_min, e1_min, s2_min, e2_min):
                _, _, dur, ov_window = compute_overlap_window(s1_min, e1_min, s2_min, e2_min)
                same_room = room1 == room2
                kind = "TIME_AND_ROOM_CLASH" if same_room else "STUDENT_TIME_OVERLAP"
                msg = (
                    f"{code1} ({s1_str}-{e1_str}) and {code2} ({s2_str}-{e2_str}) overlap on {day1} "
                    f"for {dur} mins ({ov_window})"
                )
                if same_room:
                    msg += f" and both claim room {room1}."
                else:
                    msg += "."

                conflicts.append({
                    "kind": kind,
                    "severity": "High",
                    "course_a": code1,
                    "title_a": title1,
                    "course_b": code2,
                    "title_b": title2,
                    "day": day1,
                    "slot_a": f"{s1_str}-{e1_str}",
                    "slot_b": f"{s2_str}-{e2_str}",
                    "overlap_window": ov_window,
                    "overlap_minutes": dur,
                    "room_a": room1,
                    "room_b": room2,
                    "same_room": same_room,
                    "message": msg,
                })

    return conflicts


def detect_unavailable_rooms(course_tuples, room_tuples):
    """Identify courses assigned to missing, maintenance, reserved, or blocked-window rooms.

    room_tuples items:
    (room_code, building, capacity, status, unavailable_day, unavail_start_min, unavail_end_min, reason)
    """
    issues = []

    for course in course_tuples:
        code, title, day, s_str, e_str, s_min, e_min, room_code = course
        matched_room = None
        for r_tuple in room_tuples:
            if r_tuple[0].upper() == room_code.upper():
                matched_room = r_tuple
                break

        if matched_room is None:
            issues.append({
                "course_code": code,
                "course_title": title,
                "room_code": room_code,
                "day": day,
                "slot": f"{s_str}-{e_str}",
                "status": "Unknown",
                "reason": f"Room '{room_code}' does not exist in campus room registry.",
            })
            continue

        r_code, building, capacity, status, un_day, un_start, un_end, reason = matched_room

        if status != "Available":
            # If unavailable_day is 'ALL' or matches course day with overlapping window (or full day 0..1440)
            day_matches = (un_day == "ALL") or (un_day == day)
            if day_matches and intervals_overlap(s_min, e_min, un_start, un_end):
                issues.append({
                    "course_code": code,
                    "course_title": title,
                    "room_code": r_code,
                    "day": day,
                    "slot": f"{s_str}-{e_str}",
                    "status": status,
                    "reason": f"Room {r_code} ({building}) is {status}: {reason}",
                })

    return issues


def build_weekly_matrix(course_tuples):
    """Build a 2D nested list representing the weekly timetable grid across GRID_SLOTS x VALID_DAYS.

    Returns nested list of rows: each row = [slot_label, [cell_for_Mon, cell_for_Tue, ...]]
    """
    matrix = []
    for slot_label, slot_start, slot_end in GRID_SLOTS:
        day_cells = []
        for day in VALID_DAYS:
            cell_courses = []
            for course in course_tuples:
                c_code, c_title, c_day, s_str, e_str, s_min, e_min, room_code = course
                if c_day == day and intervals_overlap(s_min, e_min, slot_start, slot_end):
                    cell_courses.append({
                        "code": c_code,
                        "title": c_title,
                        "room": room_code,
                        "slot": f"{s_str}-{e_str}",
                    })
            day_cells.append({
                "day": day,
                "courses": cell_courses,
                "has_conflict": len(cell_courses) > 1,
            })
        matrix.append({
            "slot_label": slot_label,
            "cells": day_cells,
        })
    return matrix


def suggest_alternative_slots(conflicting_codes, course_tuples, room_tuples):
    """Find conflict-free 1-hour alternative slots for conflicting courses using loops."""
    suggestions = []
    checked = []

    for code in conflicting_codes:
        if code in checked:
            continue
        checked.append(code)

        target = None
        for course in course_tuples:
            if course[0] == code:
                target = course
                break
        if target is None:
            continue

        _, _, _, _, _, s_min, e_min, pref_room = target
        duration = e_min - s_min
        if duration <= 0:
            duration = 60

        found_slot = ""
        for cand_day in CORE_DAYS:
            if found_slot:
                break
            for _, g_start, _ in GRID_SLOTS:
                cand_start = g_start
                cand_end = cand_start + duration
                if cand_end > 1080:
                    continue

                # Check against all other courses in timetable
                overlaps_other = False
                for other in course_tuples:
                    if other[0] == code:
                        continue
                    if other[2] == cand_day and intervals_overlap(cand_start, cand_end, other[5], other[6]):
                        overlaps_other = True
                        break

                if overlaps_other:
                    continue

                # Find an available room for this day/window
                chosen_room = ""
                for r_tuple in room_tuples:
                    r_code, _, _, r_status, un_day, un_s, un_e, _ = r_tuple
                    room_blocked = (r_status != "Available") and (un_day == "ALL" or un_day == cand_day) and intervals_overlap(cand_start, cand_end, un_s, un_e)
                    if not room_blocked:
                        chosen_room = r_code
                        if r_code == pref_room:
                            break
                if chosen_room:
                    found_slot = f"{cand_day} {minutes_to_time_str(cand_start)}-{minutes_to_time_str(cand_end)} in {chosen_room}"
                    break

        if found_slot:
            suggestions.append((code, found_slot))

    return suggestions


def generate_timetable_pattern(course_tuples, is_valid, total_conflicts):
    """Generate an ASCII timetable summary & validation banner using loops and strings."""
    lines = []
    border = "+" + "-" * 66 + "+"
    status_text = "VALID TIMETABLE (CONFLICT-FREE)" if is_valid else f"INVALID TIMETABLE ({total_conflicts} CONFLICT(S) FOUND)"
    lines.append(border)
    lines.append(f"| {status_text:<64} |")
    lines.append(border)
    lines.append(f"| {'Slot':<13} | " + " | ".join(f"{d:<6}" for d in VALID_DAYS) + " |")
    lines.append("|" + "-" * 15 + "+" + "+".join("-" * 8 for _ in VALID_DAYS) + "|")

    for slot_label, slot_start, slot_end in GRID_SLOTS:
        row_cells = []
        for day in VALID_DAYS:
            matches = []
            for c in course_tuples:
                if c[2] == day and intervals_overlap(c[5], c[6], slot_start, slot_end):
                    matches.append(c[0][:6])
            if not matches:
                cell_str = "  --  "
            elif len(matches) == 1:
                cell_str = f"{matches[0]:<6}"
            else:
                cell_str = "CLASH!"
            row_cells.append(cell_str)
        lines.append(f"| {slot_label:<13} | " + " | ".join(row_cells) + " |")

    lines.append(border)
    return "\n".join(lines)


def validate_proposed_timetable(course_tuples, room_tuples):
    """Run complete timetable conflict detection and room availability validation."""
    time_conflicts = detect_overlapping_periods(course_tuples)
    room_issues = detect_unavailable_rooms(course_tuples, room_tuples)

    total_conflicts = len(time_conflicts) + len(room_issues)
    is_valid = total_conflicts == 0

    conflicting_codes = []
    for tc in time_conflicts:
        conflicting_codes.append(tc["course_a"])
        conflicting_codes.append(tc["course_b"])
    for ri in room_issues:
        conflicting_codes.append(ri["course_code"])

    weekly_matrix = build_weekly_matrix(course_tuples)
    suggestions = suggest_alternative_slots(conflicting_codes, course_tuples, room_tuples)
    ascii_pattern = generate_timetable_pattern(course_tuples, is_valid, total_conflicts)

    # Calculate total scheduled minutes & day distribution list
    total_minutes = 0
    day_counts = []
    for day in VALID_DAYS:
        count = 0
        for c in course_tuples:
            if c[2] == day:
                count += 1
                total_minutes += (c[6] - c[5])
        day_counts.append([day, count])

    return {
        "is_valid": is_valid,
        "status_label": "Valid Timetable" if is_valid else "Conflicts Detected",
        "total_courses": len(course_tuples),
        "total_conflicts": total_conflicts,
        "time_conflict_count": len(time_conflicts),
        "room_issue_count": len(room_issues),
        "time_conflicts": time_conflicts,
        "room_issues": room_issues,
        "weekly_matrix": weekly_matrix,
        "suggestions": suggestions,
        "ascii_pattern": ascii_pattern,
        "total_hours": round(total_minutes / 60.0, 2),
        "day_counts": day_counts,
    }
