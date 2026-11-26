# Project Objectives

1. **Parse Schedule Strings into Tuples**: Convert human-readable schedule strings (`CODE | TITLE | Day HH:MM-HH:MM | ROOM`) into structured, validated tuples using string splitting, stripping, slicing, and case normalization.
2. **Detect Overlapping Time Intervals**: Compare all pairs of courses in a proposed timetable using nested loops and tuple unpacking to detect overlapping durations while allowing adjacent back-to-back classes.
3. **Verify Room Availability**: Cross-check every course's room assignment against campus room statuses (`Available`, `Maintenance`, `Reserved`) and blocked weekday/time windows, plus detect room double-bookings.
4. **Validate Proposed Timetables**: Classify a proposed schedule as Valid (0 conflicts) or Invalid, and compute conflict-free alternative slots for clashing courses.
5. **Visualize & Persist Schedules**: Render an interactive 2D weekly matrix (nested lists), a loop-generated ASCII timetable pattern, SQLite persistence, and downloadable CSV reports.
6. **Demonstrate Python Syllabus Concepts**: Strictly apply variables, operators, conditionals, loops, strings, pattern generation, lists, nested lists, tuples, tuple operations, and tuple unpacking.
