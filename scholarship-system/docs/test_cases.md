# Test Cases

All 15+ test cases below are automated in [`tests/test_scholarship.py`](../tests/test_scholarship.py) using Python's built-in `unittest` module.

| Test ID | Scenario | Input / Condition | Expected Result |
| :--- | :--- | :--- | :--- |
| **TC-01** | Valid Student Application | Valid ID `STU901`, marks `[90, 85, 88, 92, 95]`, attendance `92%`, income `₹1,20,000`, certificate `Available` | Validation passes; `total_marks = 450`, `aggregate = 90.00%`, saved to SQLite, marked Eligible. |
| **TC-02** | Invalid Marks | Mathematics mark `-5` or `105` | Validation fails with message `"Mathematics marks must be between 0 and 100."` |
| **TC-03** | Invalid Attendance | Attendance `-1` or `101.5` | Validation fails with message `"Attendance percentage must be between 0 and 100."` |
| **TC-04** | Negative Family Income | Annual family income `-5000` | Validation fails with message `"Annual family income cannot be negative."` |
| **TC-05** | Duplicate Student ID | Submitting `stu901` when `STU901` already exists | Duplicate blocked with message `"Student ID 'STU901' already exists."` |
| **TC-06** | Minimum Aggregate Boundary | Marks `[75, 75, 75, 75, 75]` (75.00%) vs `[74, 75, 75, 75, 75]` (74.80%) | `75.00%` is Eligible; `74.80%` is Rejected with `"Aggregate percentage below minimum"`. |
| **TC-07** | Minimum Subject Boundary | Marks `[95, 95, 95, 95, 49]` (85.80% aggregate, CS = 49) vs `[95, 95, 95, 95, 50]` | `49` is Rejected with `"Subject marks below minimum (50): Computer Science (49)"`; `50` is Eligible. |
| **TC-08** | Minimum Attendance Boundary | Attendance `75.00%` vs `74.99%` | `75.00%` is Eligible; `74.99%` is Rejected with `"Attendance below minimum"`. |
| **TC-09** | Maximum Income Boundary | Income `₹2,50,000` vs `₹2,50,001` | `₹2,50,000` is Eligible (40 income merit points); `₹2,50,001` is Rejected with `"Family income exceeds limit"`. |
| **TC-10** | Missing Income Certificate | `income_certificate_status = "Missing"` | Rejected with `"Income certificate missing"` when certificate is required; Eligible when rule is disabled. |
| **TC-11** | Scholarship Score Calculation | Aggregate `90%`, Attendance `80%`, Income `₹1,00,000` (100 pts) with weights `(0.70, 0.20, 0.10)` | Score = `(90*0.70) + (80*0.20) + (100*0.10) = 63.0 + 16.0 + 10.0 = 89.00`. |
| **TC-12** | Merit Ranking | Multiple eligible & rejected students | Only eligible students receive ranks `1..N` sorted descending by `scholarship_score`; rejected have `rank = None`. |
| **TC-13** | Tie-Breaking Rules | Pairs of eligible students with identical `scholarship_score` | Resolved strictly by: (1) higher aggregate %, (2) higher attendance %, (3) lower income, (4) higher total marks, (5) alphabetical Student ID. |
| **TC-14** | Scholarship Quota Allocation | 4 eligible students with `scholarship_quota = 2` | Ranks #1 and #2 marked `"Eligible & Selected"`; Ranks #3 and #4 marked `"Eligible (Waitlisted)"`. |
| **TC-15** | CSV Report Generation | `GET /reports/export-csv` | Returns HTTP `200`, `text/csv`, header columns + accurate ranked rows generated with built-in `csv`. |
| **TC-16** | Rule Change Recalculation & CRUD | Update quota/thresholds, edit student, delete student, idempotent sample load | Rankings update immediately; duplicate sample records never created. |
