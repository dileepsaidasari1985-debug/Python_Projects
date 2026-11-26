# Project Assumptions & Business Rules

1. **Academic Week & Hours**: Classes run Monday through Saturday (`VALID_DAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat")`) between `07:00` and `21:00` (420 to 1260 minutes since midnight).
2. **Time Representation**: All times use 24-hour `HH:MM` notation and are converted to integer minutes since midnight for exact arithmetic comparison.
3. **Half-Open Interval Rule**: A class running `[start_a, end_a)` overlaps `[start_b, end_b)` if and only if `start_a < end_b and start_b < end_a`. Back-to-back classes (e.g., `09:00-10:30` and `10:30-12:00`) do **not** overlap.
4. **Room Registry**: Every scheduled course must reference a known campus room. A room marked `Maintenance` or `Reserved` blocks classes whose weekday matches `unavailable_day` (or `ALL`) and whose time window overlaps the blocked interval.
5. **Double-Booking**: Two different courses overlapping on the same day in the same room trigger a `TIME_AND_ROOM_CLASH` conflict.
6. **Valid Timetable Definition**: A proposed timetable is valid only when both `time_conflicts` and `room_issues` are empty.
