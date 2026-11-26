# Step-by-Step Algorithm

1. **Start** and read classroom parameters (`hall_name`, `rows`, `cols`, `fixed_capacity`, `reserved_spec`, `seating_mode`, `student_rolls`).
2. **Validate Inputs**: Confirm `rows`, `cols`, `fixed_capacity <= rows * cols`, and ensure all reserved seat IDs lie within the grid.
3. **Initialize Counters**: Set `usable = 0`, `student_idx = 0`, `matrix = []`.
4. **Outer Loop (`r` from `0` to `rows - 1`)**:
   - Initialize `row_cells = []`.
   - **Inner Loop (`c` from `0` to `cols - 1`)**:
     1. Build `seat_id = ROW_LETTERS[r] + str(c + 1)`.
     2. If `seat_id` is in `reserved_tuples`, mark cell `RESERVED` and continue.
     3. If `seating_mode == "ALTERNATE_CHECKERBOARD"` and `(r + c) % 2 == 1`, mark `GAP` and continue (or `c % 2 == 1` for `ALTERNATE_COLUMN`).
     4. If `usable >= fixed_capacity`, mark `CAP_LIMIT` and continue.
     5. Increment `usable += 1`. If `student_idx < len(student_rolls)`, assign `student_rolls[student_idx]`, increment `student_idx`, mark `OCCUPIED`; else mark `VACANT`.
   - Append `row_cells` to `matrix`.
5. **Compute Overflow & ASCII Chart**: Any students from `student_idx` onward form `unassigned_students`. Build ASCII grid via nested loop.
6. **End**.
