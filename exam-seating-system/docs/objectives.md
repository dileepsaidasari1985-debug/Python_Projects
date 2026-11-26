# Project Objectives

1. **Generate 2D Seating Grids via Nested Loops**: Iterate across `rows` and `cols` to produce structured row/column seat IDs (`A1`, `R1C1`).
2. **Enforce Reserved Positions**: Parse and block reserved seats (`PROCTOR`, `ACCESSIBLE`, `BROKEN`) prior to student allocation.
3. **Apply Alternate Seating Restrictions**: Support Checkerboard (`(r + c) % 2 == 1` gap), Alternate Column (`c % 2 == 1` gap), and Full Capacity rules.
4. **Respect Fixed Classroom Capacities**: Limit assignable seats to `fixed_capacity` and isolate overflow roll numbers cleanly.
5. **Visualize & Export**: Render color-coded classroom grids, ASCII charts, SQLite plan storage, and CSV exports.
