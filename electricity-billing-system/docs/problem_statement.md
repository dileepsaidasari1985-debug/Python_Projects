# Problem Statement

## Project Title
**Progressive Electricity Billing and Monthly Consumption Analysis System** (Case Study #2)

## Background
Manual or flat-rate electricity billing creates several operational and analytical challenges for residential utilities and consumers:
1. **Unfair Flat Pricing**: Applying a single tariff rate to all units penalizes low-consumption households and fails to encourage energy conservation.
2. **Error-Prone Manual Calculations**: Computing slab-by-slab progressive charges, fixed monthly charges, electricity duty, surcharges, rebates, and late payment penalties manually often leads to arithmetic mistakes.
3. **Lack of Historical Comparison**: Households and administrators struggle to compare electricity consumption across multiple months or calculate percentage increases/decreases accurately.
4. **Delayed Anomaly Detection**: Sudden spikes in meter usage—caused by faulty appliances, meter errors, or abnormal load—often go unnoticed until a high bill arrives.

## Problem Definition
Design and implement a full-stack Python web application that:
- Registers households with unique Household IDs and Meter Numbers.
- Validates monthly meter readings (`Consumption = Current Reading - Previous Reading`) and prevents duplicate billing months.
- Computes electricity energy charges progressively across configurable consumption slabs.
- Applies fixed charges, electricity duty, surcharges, rebates, and late payment penalties while preventing negative final bills.
- Persists all records in a relational SQLite database.
- Compares monthly consumption and bill amounts with safe zero-division handling.
- Detects unusual consumption spikes using transparent, rule-based Python logic.
- Generates print-friendly bills and downloadable CSV reports.
