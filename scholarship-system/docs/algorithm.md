# Step-by-Step Algorithm

1. **Start** the application and initialize the SQLite database (`students` and `scholarship_rules` tables).
2. **Load Active Rules** from `scholarship_rules` (minimum aggregate, minimum subject marks, minimum attendance, maximum income, certificate requirement, quota, weights, and income merit slabs).
3. **Input Student Data** (Student ID, personal details, 5 subject marks, attendance %, annual income, certificate status, category, date).
4. **Validate Input Data**:
   - Check required fields are non-empty.
   - Normalize `student_id` (uppercase, trimmed) and verify uniqueness.
   - Verify marks and attendance are numeric and within `[0, 100]`.
   - Verify income is numeric and `>= 0`.
   - If invalid, return descriptive error messages and stop saving.
5. **Calculate Academic Totals**:
   - `total_marks = math + physics + chemistry + english + cs`
   - `aggregate_percentage = total_marks / 5`
6. **Evaluate Eligibility Conditions** for each student:
   - Check `aggregate_percentage >= min_aggregate`.
   - Loop over all 5 subjects and check each `subject_mark >= min_subject_marks`.
   - Check `attendance_percentage >= min_attendance`.
   - Check `annual_income <= max_family_income`.
   - If `income_certificate_required` is enabled, check `income_certificate_status == "Available"`.
   - Collect all failed conditions into `rejection_reasons`.
7. **Separate Eligible and Rejected Students**:
   - If `rejection_reasons` is empty, add student to `eligible_students` list.
   - Otherwise, set `scholarship_score = 0.00` and add student to `rejected_students` list.
8. **Calculate Scholarship Score** for each eligible student:
   - Determine `income_merit_score` by matching `annual_income` against the ordered `(limit, points)` slab tuples.
   - Compute `scholarship_score = round((aggregate * w_agg) + (attendance * w_att) + (income_merit * w_inc), 2)`.
9. **Rank Eligible Students & Apply Tie-Breaking**:
   - Build a sorting key tuple for each eligible student:
     `(-scholarship_score, -aggregate_percentage, -attendance_percentage, annual_income, -total_marks, student_id)`
   - Sort `eligible_students` using this tuple key.
   - Assign sequential ranks `1, 2, ..., N`.
10. **Allocate Scholarships**:
    - For `rank <= scholarship_quota`, mark status as `Eligible & Selected` and generate merit pattern/award banner.
    - For `rank > scholarship_quota`, mark status as `Eligible (Waitlisted)`.
11. **Generate Reports & CSV Export**:
    - Build nested department summary list `[department, total, eligible, selected, avg_aggregate]`.
    - Compute dashboard totals and export ranked records via Python's built-in `csv` module.
12. **End**.
