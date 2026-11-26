# Project Objectives

1. **Automate Student Application Intake & Validation:** Provide an intuitive web form with strict client-side UX hints and authoritative server-side validation (marks 0–100, attendance 0–100, non-negative income, unique Student ID).
2. **Enforce Multi-Criteria Scholarship Eligibility:** Evaluate every applicant against minimum aggregate marks, subject-wise minimum scores, attendance, maximum annual family income, and income certificate availability—reporting exact rejection reasons for ineligible applicants.
3. **Compute Transparent Merit-cum-Means Scores:** Calculate a composite Scholarship Score using configurable weights (default: 70% Aggregate, 20% Attendance, 10% Income Merit Score).
4. **Implement Deterministic Ranking & Tie-Breaking:** Separate eligible and rejected students, rank eligible applicants in descending score order, and break ties fairly using a 5-level tuple ordering (aggregate %, attendance %, lower income, total marks, alphabetical Student ID).
5. **Support Configurable Policy Rules:** Allow administrators to modify thresholds, quota, weights, and income slabs and immediately recalculate all rankings.
6. **Persist & Manage Records Safely:** Store student records and rules in SQLite using parameterized queries to prevent SQL injection, supporting search, filter, sort, edit, and confirmed delete.
7. **Generate Submission-Ready Reports:** Provide summary analytics, department-wise breakdowns, print-ready views, and CSV downloads using Python's built-in `csv` module.
8. **Demonstrate Core Python Syllabus Concepts:** Naturally apply computational thinking, algorithms, flowcharts, pseudocode, variables, data types, operators, conditionals, loops, strings, pattern generation, lists, nested lists, tuples, tuple operations, and tuple unpacking.
