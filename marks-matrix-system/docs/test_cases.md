# Test Cases

Automated in [`tests/test_matrix.py`](../tests/test_matrix.py).

| Test ID | Scenario | Input / Condition | Expected Result |
|---|---|---|---|
| **TC-01** | Row & Column Stats | 2 students across 5 subjects | Exact row totals/averages and Physics flagged low (`45.0 < 60.0`). |
| **TC-02** | Top Performer Tie-Breaking | Equal `80.0` averages (`min_mark 80` vs `70`) | Higher minimum subject score (`S02`) ranks #1. |
| **TC-03** | Grade & Input Bounds | `92.0 -> A+`, `35.0 -> F`, mark `105` | Rejects mark `105` cleanly. |
| **TC-04** | Matrix Text Parsing | Multi-line CSV student rows | Parses into validated tuples. |
| **TC-05** | Web Routes & CSV Export | GET `/`, `/matrix`, `/sandbox`, `/reports/export-csv` | HTTP `200` and valid CSV summary. |
| **TC-06** | Add Student POST | POST `/matrix` with `STU4299` | Student persisted and ranked in matrix. |
