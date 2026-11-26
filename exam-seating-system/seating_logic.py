"""Core Nested Loop Examination Seating Generator logic (Case Study #26).

Demonstrates Python syllabus concepts:
- Variables, data types, arithmetic (modulo %) & relational/logical operators
- Conditional statements and nested loops (row x column matrix generation)
- Strings and string operations (.strip, .upper, .split, slicing)
- Pattern generation (ASCII classroom seating chart)
- Lists and nested lists (2D seating grid)
- Tuples, tuple operations, and tuple unpacking
"""

ROW_LETTERS = tuple("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

SEATING_MODES = (
    ("ALTERNATE_CHECKERBOARD", "Alternate Checkerboard ((r + c) % 2 == 0)"),
    ("ALTERNATE_COLUMN", "Alternate Column (Every Even Column)"),
    ("FULL_CAPACITY", "Full Capacity (All Non-Reserved Seats)"),
)

RESERVED_REASONS = ("PROCTOR", "ACCESSIBLE", "BROKEN")


def build_seat_id(row_idx, col_idx):
    """Generate (row_label, col_num, seat_id) tuple for 0-based indices."""
    row_label = ROW_LETTERS[row_idx] if row_idx < len(ROW_LETTERS) else f"R{row_idx + 1}"
    col_num = col_idx + 1
    return (row_label, col_num, f"{row_label}{col_num}")


def parse_reserved_positions(raw_text, max_rows, max_cols):
    """Parse reserved seat specification string into validated tuples.

    Supports formats like: 'A1:PROCTOR, A6:ACCESSIBLE, C3'
    Returns (is_valid, reserved_tuples_list, error_messages)
    """
    text = str(raw_text or "").strip()
    if not text:
        return (True, [], [])

    valid_ids = []
    for r in range(max_rows):
        for c in range(max_cols):
            _, _, sid = build_seat_id(r, c)
            valid_ids.append(sid)

    parsed = []
    seen_ids = []
    errors = []
    tokens = [tok.strip() for tok in text.split(",") if tok.strip()]

    for token in tokens:
        if ":" in token:
            parts = token.split(":", 1)
            seat_code = parts[0].strip().upper()
            label = parts[1].strip().upper() or "RESERVED"
        else:
            seat_code = token.strip().upper()
            label = "RESERVED"

        if seat_code not in valid_ids:
            errors.append(f"Reserved seat '{seat_code}' is outside {max_rows}x{max_cols} classroom bounds.")
        elif seat_code not in seen_ids:
            seen_ids.append(seat_code)
            parsed.append((seat_code, label[:10]))

    return (len(errors) == 0, parsed, errors)


def parse_roll_numbers(raw_text):
    """Parse comma or newline-separated student roll numbers into a clean list."""
    normalized = str(raw_text or "").replace("\n", ",")
    rolls = []
    for item in normalized.split(","):
        cleaned = item.strip().upper()
        if cleaned and cleaned not in rolls:
            rolls.append(cleaned)
    return rolls


def generate_sequential_rolls(prefix, start_num, count):
    """Generate a list of sequential roll numbers using a loop."""
    rolls = []
    clean_prefix = str(prefix or "26CS").strip().upper()
    for offset in range(count):
        rolls.append(f"{clean_prefix}{start_num + offset:03d}")
    return rolls


def validate_hall_inputs(hall_name, rows_raw, cols_raw, capacity_raw):
    """Validate classroom dimension and fixed capacity inputs."""
    errors = []
    name = " ".join(str(hall_name or "").strip().split())
    if not name:
        errors.append("Classroom / Hall name is required.")

    try:
        rows = int(str(rows_raw).strip())
        if rows < 1 or rows > 20:
            errors.append("Rows must be between 1 and 20.")
    except (ValueError, TypeError):
        rows = 0
        errors.append("Rows must be an integer.")

    try:
        cols = int(str(cols_raw).strip())
        if cols < 1 or cols > 15:
            errors.append("Columns must be between 1 and 15.")
    except (ValueError, TypeError):
        cols = 0
        errors.append("Columns must be an integer.")

    try:
        cap = int(str(capacity_raw).strip())
        if cap < 1:
            errors.append("Fixed capacity must be at least 1.")
        elif rows > 0 and cols > 0 and cap > rows * cols:
            errors.append(f"Fixed capacity ({cap}) cannot exceed grid size ({rows * cols}).")
    except (ValueError, TypeError):
        cap = 0
        errors.append("Fixed capacity must be a positive integer.")

    return (len(errors) == 0, {"hall_name": name, "rows": rows, "cols": cols, "capacity": cap}, errors)


def generate_seating_plan(hall_name, rows, cols, fixed_capacity, student_rolls, reserved_tuples, seating_mode="ALTERNATE_CHECKERBOARD"):
    """Generate a 2D exam seating matrix using nested loops and tuple unpacking.

    Enforces:
    - Row & column identifiers (A1, A2, ...)
    - Reserved positions ((seat_id, reason) tuples)
    - Alternate seating restrictions (checkerboard or column buffer)
    - Fixed classroom capacity limit
    """
    matrix = []
    allocated_list = []
    reserved_count = 0
    gap_count = 0
    cap_blocked_count = 0
    assigned_count = 0
    usable_slots_available = 0
    student_idx = 0
    total_students = len(student_rolls)

    # Nested loops over rows and columns
    for r in range(rows):
        row_cells = []
        for c in range(cols):
            row_label, col_num, seat_id = build_seat_id(r, c)
            coord_label = f"R{r + 1}C{c + 1}"

            # 1. Check reserved position tuples
            reserved_reason = ""
            for res_id, res_label in reserved_tuples:
                if res_id == seat_id:
                    reserved_reason = res_label
                    break

            if reserved_reason:
                reserved_count += 1
                row_cells.append({
                    "seat_id": seat_id,
                    "coord": coord_label,
                    "row_label": row_label,
                    "col_num": col_num,
                    "status": "RESERVED",
                    "student": reserved_reason,
                })
                continue

            # 2. Check alternate seating restriction
            is_gap = False
            if seating_mode == "ALTERNATE_CHECKERBOARD" and (r + c) % 2 == 1:
                is_gap = True
            elif seating_mode == "ALTERNATE_COLUMN" and (c % 2 == 1):
                is_gap = True

            if is_gap:
                gap_count += 1
                row_cells.append({
                    "seat_id": seat_id,
                    "coord": coord_label,
                    "row_label": row_label,
                    "col_num": col_num,
                    "status": "GAP",
                    "student": "ALT-GAP",
                })
                continue

            # 3. Check fixed classroom capacity
            if usable_slots_available >= fixed_capacity:
                cap_blocked_count += 1
                row_cells.append({
                    "seat_id": seat_id,
                    "coord": coord_label,
                    "row_label": row_label,
                    "col_num": col_num,
                    "status": "CAP_LIMIT",
                    "student": "CAP-FULL",
                })
                continue

            usable_slots_available += 1

            # 4. Assign student if remaining in queue
            if student_idx < total_students:
                roll = student_rolls[student_idx]
                student_idx += 1
                assigned_count += 1
                allocated_list.append((seat_id, coord_label, roll))
                row_cells.append({
                    "seat_id": seat_id,
                    "coord": coord_label,
                    "row_label": row_label,
                    "col_num": col_num,
                    "status": "OCCUPIED",
                    "student": roll,
                })
            else:
                row_cells.append({
                    "seat_id": seat_id,
                    "coord": coord_label,
                    "row_label": row_label,
                    "col_num": col_num,
                    "status": "VACANT",
                    "student": "OPEN",
                })

        matrix.append({"row_label": ROW_LETTERS[r] if r < len(ROW_LETTERS) else f"R{r + 1}", "cells": row_cells})

    unassigned = student_rolls[student_idx:]
    ascii_chart = generate_ascii_seating_chart(hall_name, matrix, cols, assigned_count, fixed_capacity, len(unassigned))

    return {
        "hall_name": hall_name,
        "rows": rows,
        "cols": cols,
        "total_physical_seats": rows * cols,
        "fixed_capacity": fixed_capacity,
        "seating_mode": seating_mode,
        "usable_seats": usable_slots_available,
        "assigned_count": assigned_count,
        "reserved_count": reserved_count,
        "gap_count": gap_count,
        "cap_blocked_count": cap_blocked_count,
        "vacant_usable": max(0, usable_slots_available - assigned_count),
        "unassigned_students": unassigned,
        "matrix": matrix,
        "allocated_list": allocated_list,
        "ascii_chart": ascii_chart,
    }


def generate_ascii_seating_chart(hall_name, matrix, cols, assigned_count, fixed_capacity, overflow_count):
    """Build an ASCII seating map using nested loops and string formatting."""
    cell_w = 13
    total_w = cols * (cell_w + 1) + 5
    lines = [
        "+" + "-" * total_w + "+",
        f"| EXAM HALL: {hall_name:<{total_w - 13}} |",
        f"| Assigned: {assigned_count} | Fixed Cap: {fixed_capacity} | Overflow: {overflow_count:<{max(1, total_w - 46)}} |",
        "+" + "-" * total_w + "+",
        "| [ BLACKBOARD / INVIGILATOR DESK ]".ljust(total_w + 1) + "|",
        "+" + "-" * total_w + "+",
    ]

    for row in matrix:
        row_tokens = []
        for cell in row["cells"]:
            sid = cell["seat_id"]
            if cell["status"] == "OCCUPIED":
                label = f"{sid}:{cell['student'][:7]}"
            elif cell["status"] == "RESERVED":
                label = f"{sid}:RESV"
            elif cell["status"] == "GAP":
                label = f"{sid}:----"
            elif cell["status"] == "CAP_LIMIT":
                label = f"{sid}:CAPL"
            else:
                label = f"{sid}:OPEN"
            row_tokens.append(f"[{label:<11}]")
        lines.append(f"| {row['row_label']} | " + " ".join(row_tokens) + " |")

    lines.append("+" + "-" * total_w + "+")
    return "\n".join(lines)
