# Project Assumptions & Business Rules

1. **Attendance Threshold**: Students below `75.0%` attendance are flagged with `Shortage`.
2. **Marks & Pass Criteria**: Subject scores range `0–100`; passing all subjects requires `>= 40.0` in each.
3. **Event Rules**: A student may register at most once per event, and total registrations cannot exceed `event.capacity`.
4. **Resource Rules**: Resources not marked `Available` (e.g., `Maintenance`) or already allocated for the requested `slot_label` cannot be booked.
