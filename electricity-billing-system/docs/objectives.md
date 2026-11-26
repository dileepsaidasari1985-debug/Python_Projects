# Project Objectives

1. **Progressive Slab Billing**: Implement `calculate_energy_charge(consumption, slabs)` to compute energy charges slab by slab rather than applying the highest rate to all units.
2. **Itemized Tariff Charges**: Separate and display Energy Charge, Fixed Charge, Electricity Duty, Surcharge, Rebate, Late Payment Penalty, and Final Payable Amount.
3. **Configurable Billing Rules**: Provide an administrator interface to update slab limits, rates, surcharges, rebates, and anomaly thresholds in SQLite.
4. **Accurate Meter Reading Management**: Validate non-negative readings, ensure `Current Reading >= Previous Reading`, and prevent duplicate household billing months.
5. **Persistent SQLite Storage**: Automatically initialize `database/electricity.db` with normalized tables (`households`, `meter_readings`, `electricity_bills`, `bill_slab_items`, `billing_rules`, `tariff_slabs`) using parameterized SQL queries.
6. **Monthly Consumption Comparison**: Track month-over-month unit and bill percentage changes and identify the highest, lowest, average, and total consumption.
7. **Rule-Based Unusual Consumption Detection**: Flag consumption increases above 50% month-over-month or above the previous 3-month average, as well as high usage and high bill breaches.
8. **Printable Statements & CSV Exports**: Generate unique bill numbers, print-ready bill layouts, and CSV downloads using Python's built-in `csv` module.
9. **Syllabus Demonstration**: Apply core Python concepts—variables, operators, conditionals, loops, strings, pattern generation, lists, nested lists, tuples, and tuple unpacking—in clean, readable code.
