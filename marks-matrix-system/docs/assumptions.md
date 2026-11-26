# Project Assumptions & Business Rules

1. **Fixed Subject Columns**: Each student record contains 5 subject scores (`Mathematics`, `Physics`, `Chemistry`, `English`, `Computer Science`) on a `0–100` scale.
2. **Default Thresholds**: `pass_mark = 40.0` per subject and `low_avg_threshold = 60.0` per subject average (both configurable).
3. **Tie-Breaking Rule**: Equal student averages are broken by higher total marks, higher minimum subject score, and ascending Student ID.
