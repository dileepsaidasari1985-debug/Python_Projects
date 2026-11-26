# Nested Loop Examination Seating Generator

**Case Study #26:** *Generate a seating arrangement with row and column identifiers, reserved positions, alternate seating restrictions, and fixed classroom capacities.*

## Key Features
- **Nested Loop 2D Matrix Engine**: Traverses rows and columns to assign alphanumeric (`A1`, `B3`) and coordinate (`R1C1`) seat identifiers.
- **Reserved Position Enforcement**: Reserves explicit seats for proctors, accessibility needs, or broken desks.
- **Alternate Seating Modes**: Supports Checkerboard (`(r + c) % 2 == 0`), Alternate Column (`c % 2 == 0`), and Full Capacity layouts.
- **Fixed Classroom Capacity & Overflow Tracking**: Caps usable seats at `fixed_capacity` and lists any overflow candidates.
- **SQLite Persistence, ASCII Map & CSV Export**: Saves halls and seating plans in SQLite and exports seating sheets to CSV.
