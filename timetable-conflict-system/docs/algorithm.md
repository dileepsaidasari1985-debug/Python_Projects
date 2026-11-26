# Step-by-Step Algorithm

1. **Start** and initialize the SQLite database (`rooms`, `courses`, `proposed_timetables`).
2. **Input Schedules**: Accept either selected course codes from the SQLite catalog or multi-line schedule strings (`CODE | TITLE | Day HH:MM-HH:MM | ROOM`).
3. **Parse & Validate Strings**:
   - Split each line by `|`, trim whitespace, normalize course/room codes to uppercase, normalize weekday alias to `Mon..Sat`, convert `HH:MM` start and end times into integer minutes, verify `end_min > start_min`, and pack into an immutable course tuple.
4. **Detect Time Overlaps**:
   - Loop `i` from `0` to `N-1`, and inner loop `j` from `i+1` to `N-1`.
   - Unpack course tuples `i` and `j`.
   - If `day1 == day2` and `s1 < e2 and s2 < e1`, compute overlap window `[max(s1, s2), min(e1, e2)]`, duration, and record `TIME_AND_ROOM_CLASH` (if `room1 == room2`) or `STUDENT_TIME_OVERLAP`.
5. **Detect Unavailable Rooms**:
   - For each course tuple, look up `room_code` in `room_tuples`.
   - If missing, record an `Unknown` room issue.
   - If `status != "Available"` and `(unavail_day == "ALL" or unavail_day == course_day)` and intervals overlap, record a room availability conflict.
6. **Suggest Alternative Slots & Generate Visual Grid**:
   - Build a 2D nested list (`weekly_matrix`) across `GRID_SLOTS` x `VALID_DAYS`.
   - For conflicting course codes, scan `CORE_DAYS` and `GRID_SLOTS` to find the first conflict-free time and available room.
   - Generate the loop-based ASCII timetable banner and grid.
7. **Output & Persist**: Display validation verdict, conflicts, suggestions, weekly matrix, optional SQLite save, and CSV export.
8. **End**.
