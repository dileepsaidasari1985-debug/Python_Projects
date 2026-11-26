# Comprehensive Smart Campus Management Simulation

**Case Study #100:** *Develop a menu-driven program that integrates student records, attendance, marks, event registration, resource allocation, and summary reporting using conditional statements, loops, strings, lists, nested lists, tuples, and tuple unpacking.*

## Key Features
- **Dual Interface (Interactive CLI Menu + Flask Web UI)**: Run `python cli_menu.py` for the terminal `while True` menu loop OR `python app.py` for the full SQLite-backed web application.
- **6 Integrated Campus Modules**:
  1. Student Records (validation, ID normalization, department & year tracking)
  2. Attendance Tracking (attended/total evaluation & `< 75%` shortage alerts)
  3. Marks & Grading (subject tuples, averages, letter grades)
  4. Event Registration (capacity limits & duplicate prevention)
  5. Resource Allocation (maintenance blocking & slot conflict detection)
  6. Summary Reporting (campus-wide KPIs, ASCII Executive Summary & CSV export)
