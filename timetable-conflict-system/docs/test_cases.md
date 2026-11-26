# Test Cases

All test cases are automated in [`tests/test_timetable.py`](../tests/test_timetable.py).

| Test ID | Scenario | Input / Condition | Expected Result |
|---|---|---|---|
| **TC-01** | Valid Schedule String Parsing | `"cs101 | Data Structures | Mon 09:00-10:30 | r-204"` | Parsed into tuple with `CS101`, `Mon`, `540..630`, `R-204`. |
| **TC-02** | Invalid Schedule Strings | Empty, bad day `"Fun"`, or `11:00-10:00` | Rejected with clear error message. |
| **TC-03** | Adjacent Back-to-Back Periods | `09:00-10:30` and `10:30-12:00` on `Mon` | `intervals_overlap` returns `False` (no conflict). |
| **TC-04** | Time & Same-Room Clash | `CS101` (`Mon 09:00-10:30`, `R-204`) & `CS109` (`Mon 09:30-11:00`, `R-204`) | Detects `TIME_AND_ROOM_CLASH` with window `09:30-10:30`. |
| **TC-05** | Unavailable / Unknown Rooms | `LAB-102` in `Maintenance` (`Wed 10:00-13:00`) & `Z-999` unknown | Flags both room issues with status and reason. |
| **TC-06** | Proposed Timetable Validation | Valid 2-course vs conflicting 2-course set | Returns `is_valid=True` for clean set; `is_valid=False` + suggestions for clash. |
| **TC-07** | Course Field Validation | Valid vs invalid form fields (`end <= start`, bad credits) | Rejects invalid inputs cleanly. |
| **TC-08** | All Routes HTTP 200 | GET `/`, `/validator`, `/courses`, `/rooms`, `/proposals`, `/reports` | All return HTTP `200`. |
| **TC-09** | Validator POST & Save Proposal | Submit raw schedule strings & save | Proposal stored in SQLite and marked Valid. |
| **TC-10** | Add Course & CSV Export | POST `/courses` (`CS299`) & GET `/reports/export-csv` | Course persisted and exported in CSV response. |
