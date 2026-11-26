# Problem Statement

## Case Study #42: Student Marks Matrix Analysis

Academic departments routinely collect multi-subject marks across entire student cohorts. Manually computing individual student aggregates, per-subject averages, pass rates, top performers, and underperforming subjects from raw tabular mark sheets is slow and error-prone.

**Problem Statement:**
Design and implement a **Student Marks Matrix Analysis System** in Python that represents cohort marks as a 2D nested-list matrix, computes row-wise student statistics and column-wise subject statistics using nested loops, identifies top performers with deterministic tie-breaking, flags subjects below a configurable low-average threshold, persists cohort records in SQLite, and exports CSV reports.
