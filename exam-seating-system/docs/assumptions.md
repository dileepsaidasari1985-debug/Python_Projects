# Project Assumptions & Business Rules

1. **Grid Dimensions**: Rows range from `1..20` (labeled `A..T`) and columns from `1..15` (`1..15`).
2. **Fixed Capacity Bound**: `1 <= fixed_capacity <= rows * cols`. Even if physical grid slots remain, allocation stops once `fixed_capacity` usable seats are reached.
3. **Priority Order per Cell**: A seat is evaluated in strict order: (1) Reserved Position, (2) Alternate Gap Restriction, (3) Fixed Capacity Limit, (4) Student Roll Allocation or Open Seat.
4. **Duplicate Roll Removal**: Duplicate roll numbers in the candidate input list are deduplicated while preserving arrival order.
