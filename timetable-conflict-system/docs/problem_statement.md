# Problem Statement

## Case Study #23: Student Timetable Conflict Detection

Students and academic coordinators regularly assemble proposed course timetables from diverse department offerings. When course timings are entered manually as text schedules or selected across electives, two critical errors frequently occur:
1. **Overlapping Class Periods**: Two selected courses occur on the same weekday with intersecting start and end times.
2. **Unavailable or Double-Booked Classrooms**: A scheduled course is assigned to a room undergoing maintenance, reserved for special campus events, or simultaneously booked by another course.

**Problem Statement:**
Design and implement a **Student Timetable Conflict Detection System** in Python that parses course schedules represented as formatted strings and immutable tuples, detects all overlapping time intervals and unavailable/double-booked rooms, proposes conflict-free alternative slots, renders a visual weekly timetable grid and ASCII pattern, persists courses/rooms/proposals in SQLite, and exports conflict audit reports to CSV.
