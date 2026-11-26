# Test Cases

Automated in [`tests/test_campus.py`](../tests/test_campus.py).

| Test ID | Scenario | Input / Condition | Expected Result |
|---|---|---|---|
| **TC-01** | Student Record Validation | Valid `(CAMP201, "ananya rao", ...)` vs invalid fields | Normalizes valid tuple; catches all 4 invalid fields. |
| **TC-02** | Attendance & Marks | `36/48` vs `50/48`; marks `(90, 95, 85)` | `75.0%` valid, `50/48` rejected; marks avg `90.0` (`A+`). |
| **TC-03** | Event Duplicate & Capacity | Duplicate `CAMP101`, then 3rd registration on cap-2 event | Rejects duplicate and full-capacity attempts. |
| **TC-04** | Resource Slot Conflict | Maintenance `RES-CONF` & booked slot `Mon 14:00-16:00` | Rejects maintenance & clashing slot; allows free slot. |
| **TC-05** | Web Routes & CSV Export | GET `/`, `/students`, `/academics`, `/events`, `/resources`, `/reports`, `/reports/export-csv` | HTTP `200` and valid CSV export. |
| **TC-06** | Add Student Route | POST `/students` with `CAMP901` | Student saved and rendered in directory. |
