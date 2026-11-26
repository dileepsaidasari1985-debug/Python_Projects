# Problem Statement

## Case Study #26: Nested Loop Examination Seating Generator

Organizing university examinations requires fair, deterministic seating plans that prevent malpractice, honor reserved seats for proctors or differently abled candidates, and never exceed fixed classroom capacities. Manual spreadsheet seating charts break down when alternate-seat spacing or reserved desks vary across rooms.

**Problem Statement:**
Design and implement a **Nested Loop Examination Seating Generator** in Python that creates a 2D classroom seating arrangement with row/column identifiers (`A1`, `B2`), blocks reserved positions, enforces alternate seating restrictions, respects fixed classroom capacities, reports overflow students, renders an interactive seat map and ASCII pattern, persists plans in SQLite, and exports CSV charts.
