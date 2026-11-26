# Step-by-Step Billing & Analysis Algorithm

## Algorithm: Progressive Electricity Billing System

1. **Start** and initialize the SQLite database (`households`, `meter_readings`, `electricity_bills`, `bill_slab_items`, `billing_rules`, `tariff_slabs`).
2. **Register Household**:
   - Accept Household ID, Consumer Name, Meter Number, Address, Area, Connection Type, and Meter Category.
   - Normalize identifiers to uppercase and validate lengths and allowed characters.
   - Verify uniqueness of Household ID and Meter Number in SQLite; store record.
3. **Enter & Validate Meter Reading**:
   - Select a registered household and enter Billing Month (`YYYY-MM`), Previous Reading, Current Reading, and Billing Date.
   - Verify readings are `>= 0` and `Current Reading >= Previous Reading`.
   - Verify no duplicate bill exists for `(household_ref_id, billing_month)`.
   - Compute `Consumption = Current Reading - Previous Reading`.
4. **Calculate Progressive Slab Energy Charge**:
   - Set `remaining = Consumption` and `energy_charge = 0.0`.
   - For each tuple `(low, high, rate, label)` in sorted `slabs`:
     - If `remaining <= 0`, `slab_units = 0`.
     - Else if `high is None`, `slab_units = remaining`.
     - Else compute slab `capacity` (`high` if `low == 0`, else `high - low + 1`) and set `slab_units = min(remaining, capacity)`.
     - Compute `slab_charge = slab_units * rate`.
     - Add `slab_charge` to `energy_charge` and subtract `slab_units` from `remaining`.
     - Append slab details to the breakdown list.
5. **Apply Fixed Charges, Duty, Surcharge, Rebate & Penalty**:
   - `electricity_duty = energy_charge * (duty_percent / 100)`.
   - If `Consumption > surcharge_threshold_units`, `surcharge = energy_charge * (surcharge_percent / 100)`, else `0`.
   - If `0 < Consumption <= rebate_threshold_units`, calculate percentage or fixed `rebate`, else `0`.
   - Cap `rebate` at `(energy_charge + fixed_charge + electricity_duty + surcharge)` to prevent negative bills.
   - Add `late_payment_penalty` if flagged as late.
   - Compute `final_payable = energy_charge + fixed_charge + electricity_duty + surcharge - rebate + late_penalty`.
6. **Generate & Persist Bill**:
   - Generate unique bill number (`BILL-YYYYMM-HHID-SEQ`).
   - Save meter reading, electricity bill, and slab breakdown rows inside SQLite.
7. **Monthly Comparison & Unusual Consumption Detection**:
   - Group bills chronologically by month and compute `Percentage Change = ((Current - Previous) / Previous) * 100` (returning `None` if `Previous == 0`).
   - Identify highest, lowest, average, and total consumption.
   - For each household's chronological bills, compare current units against previous month, 3-month average, high consumption limit, and high bill limit to raise rule-based warnings.
8. **Export Reports**:
   - Render printable bill/report views and write CSV files using Python's built-in `csv` module.
9. **End**.
