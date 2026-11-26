# Test Cases

Automated in [`tests/test_seating.py`](../tests/test_seating.py).

| Test ID | Scenario | Input / Condition | Expected Result |
|---|---|---|---|
| **TC-01** | Seat ID Generation | `(0, 0)` and `(2, 4)` | `("A", 1, "A1")` and `("C", 5, "C5")`. |
| **TC-02** | Reserved Bounds Validation | `"a1:proctor, b3"` vs `"Z9:PROCTOR"` in 4x4 | Valid parses cleanly; out-of-bounds `Z9` rejected. |
| **TC-03** | Checkerboard + Reserved | 3x4 hall, `A1:PROCTOR`, 6 students | `A1` RESERVED, `A2` GAP, 5 seated, 1 overflow. |
| **TC-04** | Fixed Capacity Cap | 3x4 hall with `fixed_capacity = 5`, 10 students | 5 seated, 7 `CAP_LIMIT`, 5 overflow. |
| **TC-05** | Hall Input Validation | Empty name, `0` rows, `cap > rows*cols` | Rejected with explicit validation errors. |
| **TC-06** | Web Routes & CSV Export | GET `/`, `/generator`, `/halls`, `/plans`, `/reports/export-csv` | HTTP `200` and valid CSV seating sheet. |
| **TC-07** | Save Seating Plan Route | POST `/generator` with `action=save` | Plan persisted in SQLite (`PLAN-2026-003`). |
