# Test Cases (20 Documented Academic Cases)

| TC # | Scenario | Input | Expected Output |
|------|----------|-------|-----------------|
| TC-01 | Zero consumption | `consumption = 0` | Energy charge `₹0.00`, fixed charge `₹50.00`, final bill `₹50.00` |
| TC-02 | Consumption within first slab | `consumption = 60` | `60 × ₹2 = ₹120.00` energy charge |
| TC-03 | Consumption at slab boundary (100 units) | `consumption = 100` | `100 × ₹2 = ₹200.00` energy charge |
| TC-04 | Consumption at slab boundary crossing (101 units) | `consumption = 101` | `100 × ₹2 + 1 × ₹3 = ₹203.00` |
| TC-05 | Consumption across multiple slabs (250 units) | `consumption = 250` | `100×₹2 + 100×₹3 + 50×₹5 = ₹750.00` |
| TC-06 | Consumption above 500 units (600 units) | `consumption = 600` | `200 + 300 + 500 + 1400 + 800 = ₹3,200.00` |
| TC-07 | Invalid meter reading (current < previous) | `prev = 500, curr = 420` | Validation fails with clear error |
| TC-08 | Negative meter reading | `prev = -10, curr = 50` | Validation fails (`cannot be negative`) |
| TC-09 | Duplicate billing month for household | `HH-101` + `2026-11` twice | Duplicate rejected by validation and SQLite constraint |
| TC-10 | Fixed charge & electricity duty | `units = 250`, duty `5%`, fixed `₹50` | Duty = `₹37.50`, fixed = `₹50.00` |
| TC-11 | Surcharge calculation (>300 units) | `units = 350`, surcharge `10%` | Energy = `₹1,350`, surcharge = `₹135.00` |
| TC-12 | Rebate calculation & negative-bill prevention | Fixed rebate `₹500` on `₹50` bill | Rebate capped at `₹50.00`; final bill = `₹0.00` (never negative) |
| TC-13 | Final bill with late payment penalty | `units = 250, is_late_payment = True` | `750 + 50 + 37.50 + 100 = ₹937.50` |
| TC-14 | Zero previous consumption % change | `prev = 0, curr = 85` | Returns `None` safely (no `ZeroDivisionError`) |
| TC-15 | Monthly percentage change calculation | `prev = 100, curr = 150` | Returns `+50.0%` |
| TC-16 | Unusual consumption increase (>50% MoM) | `140 -> 320` (+128.57%) | Flagged with `"Unusual consumption increase"` |
| TC-17 | Normal consumption (<=50% change) | `120 -> 130 -> 140` | Not flagged as unusual |
| TC-18 | CSV report generation | `GET /reports/export-csv?type=all_bills` | HTTP 200, `text/csv`, valid header & rows |
| TC-19 | Tariff rule modification & invalid rule block | Negative surcharge or >100% rebate | Rejected; valid updates persist in SQLite |
| TC-20 | Household registration & duplicate prevention | Duplicate `HH-101` or `MTR-1001` | Rejected; unique household persists in SQLite |
