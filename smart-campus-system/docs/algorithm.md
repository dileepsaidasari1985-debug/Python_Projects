# Step-by-Step Algorithm

1. **Start** and initialize SQLite tables (`students`, `events`, `event_registrations`, `resources`, `resource_allocations`).
2. **Display Menu (`MENU_OPTIONS` tuple)**: Present options `1..6` and `0` (Exit).
3. **Branch on Choice (`if / elif / else`)**:
   - **1 (Student Records)**: Validate `(student_id, name, department, year)` tuple and insert/list records.
   - **2 (Attendance)**: Validate `0 <= attended <= total` and compute `pct = (attended / total) * 100`.
   - **3 (Marks)**: Unpack `(math, cs, eng)` marks, calculate average and letter grade.
   - **4 (Event Registration)**: Check event exists, student not already registered, and `count < capacity`.
   - **5 (Resource Allocation)**: Verify resource status is `Available` and no existing allocation matches `(resource_code, slot_label)`.
   - **6 (Summary Reporting)**: Loop through all tables to compute campus averages, shortages, honors scholars, ASCII report, and CSV export.
4. **Repeat** until user chooses `0` (Exit).
5. **End**.
