# Academic Assumptions & Default Tariff Rules

> **Note**: All rates and thresholds below are academic example values for this college assignment and do not represent official electricity board tariffs. Every parameter is configurable on the **Tariff & Billing Rules** page.

## 1. Progressive Consumption Slabs

| Slab # | Consumption Range | Capacity | Rate per Unit (₹) |
|--------|-------------------|----------|-------------------|
| 1 | 0–100 units | 100 units | ₹2.00 |
| 2 | 101–200 units | 100 units | ₹3.00 |
| 3 | 201–300 units | 100 units | ₹5.00 |
| 4 | 301–500 units | 200 units | ₹7.00 |
| 5 | Above 500 units | Unlimited | ₹8.00 |

### Worked Example (250 Units)
- First 100 units × ₹2.00 = ₹200.00
- Next 100 units × ₹3.00 = ₹300.00
- Remaining 50 units × ₹5.00 = ₹250.00
- **Total Energy Charge = ₹750.00**

## 2. Fixed Charges, Duty, Surcharges & Rebates
- **Fixed Monthly Charge**: ₹50.00 per bill (charged even when consumption is 0 units).
- **Electricity Duty**: 5% of total Energy Charge.
- **Surcharge**: 10% of Energy Charge when monthly consumption exceeds 300 units (configurable threshold; `0` applies to all bills).
- **Rebate**: Configurable mode (`percent` or `fixed`). Default is 5% of Energy Charge for non-zero consumption up to 150 units. Rebate is capped at the pre-rebate subtotal so the final payable amount is never negative.
- **Late Payment Penalty**: ₹100.00 when late payment is marked on the reading.

## 3. Final Bill Formula
```text
Final Payable = Energy Charge
              + Fixed Charge
              + Electricity Duty
              + Surcharge
              - Rebate
              + Late Payment Penalty
```

## 4. Unusual Consumption Detection Rules
- **Month-over-Month Increase**: Flagged if `((Current - Previous) / Previous) × 100 > 50%`.
- **3-Month Average Spike**: When at least 3 prior months exist for the household, flagged if consumption exceeds the 3-month average by more than `50%`.
- **High Usage Threshold**: Flagged if consumption exceeds `400 kWh`.
- **High Bill Threshold**: Flagged if final payable amount exceeds `₹2,500.00`.
