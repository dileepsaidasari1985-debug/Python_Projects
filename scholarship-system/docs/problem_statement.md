# Problem Statement

## Case Study #1: University Scholarship Allocation System

Universities receive a large number of scholarship applications every academic year from students across multiple departments and income backgrounds. Evaluating applications manually using spreadsheets is slow, error-prone, and lacks transparency—especially when multiple eligibility thresholds, subject-wise minimum scores, attendance rules, family income slabs, and tie-breaking conditions must be enforced consistently.

**Problem Statement:**
Design and implement a **University Scholarship Allocation System** that evaluates student applicants using aggregate marks, subject-wise minimum scores, attendance percentage, annual family income, and income certificate status; calculates weighted scholarship scores; ranks eligible candidates; resolves ties using predefined deterministic rules; allocates limited scholarship seats according to a configurable quota; persists records in a SQLite database; and generates printable and CSV-exportable allocation reports.
