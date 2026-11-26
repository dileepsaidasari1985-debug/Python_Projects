# Pseudocode

## 1. Meter Reading Calculation & Validation
```text
FUNCTION calculate_consumption(previous_reading, current_reading):
    IF previous_reading < 0 OR current_reading < 0 THEN
        RETURN ERROR "Readings must not be negative"
    END IF
    IF current_reading < previous_reading THEN
        RETURN ERROR "Current reading cannot be less than previous reading"
    END IF
    consumption = current_reading - previous_reading
    RETURN ROUND(consumption, 2)
END FUNCTION
```

## 2. Progressive Slab Billing
```text
FUNCTION calculate_energy_charge(consumption, slabs):
    remaining = consumption
    total_charge = 0
    breakdown = EMPTY LIST

    FOR EACH (low, high, rate, label) IN SORTED(slabs):
        IF remaining <= 0 THEN
            slab_units = 0
        ELSE IF high IS NULL THEN
            slab_units = remaining
        ELSE
            IF low == 0 THEN
                capacity = high
            ELSE
                capacity = high - low + 1
            END IF
            slab_units = MIN(remaining, capacity)
        END IF

        slab_charge = slab_units * rate
        total_charge = total_charge + slab_charge
        remaining = remaining - slab_units
        APPEND [label, slab_units, rate, slab_charge] TO breakdown
    END FOR

    RETURN total_charge, breakdown
END FUNCTION
```

## 3. Final Bill Calculation
```text
FUNCTION calculate_final_bill(consumption, slabs, rules, is_late):
    energy_charge, breakdown = calculate_energy_charge(consumption, slabs)
    fixed_charge = rules.fixed_charge
    duty = energy_charge * (rules.duty_percent / 100)

    IF consumption > rules.surcharge_threshold_units THEN
        surcharge = energy_charge * (rules.surcharge_percent / 100)
    ELSE
        surcharge = 0
    END IF

    IF consumption > 0 AND consumption <= rules.rebate_threshold_units THEN
        IF rules.rebate_mode == "fixed" THEN
            raw_rebate = rules.rebate_value
        ELSE
            raw_rebate = energy_charge * (rules.rebate_value / 100)
        END IF
    ELSE
        raw_rebate = 0
    END IF

    subtotal = energy_charge + fixed_charge + duty + surcharge
    rebate = MIN(raw_rebate, subtotal)
    penalty = rules.late_payment_penalty IF is_late ELSE 0
    final_payable = MAX(0, subtotal - rebate + penalty)

    RETURN final_payable
END FUNCTION
```

## 4. Monthly Comparison
```text
FUNCTION analyze_monthly_consumption(bills):
    GROUP bills BY billing_month INTO month_totals
    prev_units = NULL

    FOR EACH month IN SORTED(month_totals):
        units = month_totals[month].units
        IF prev_units IS NULL OR prev_units == 0 THEN
            pct_change = NULL
        ELSE
            pct_change = ((units - prev_units) / prev_units) * 100
        END IF
        RECORD [month, units, pct_change]
        prev_units = units
    END FOR
END FUNCTION
```

## 5. Unusual Consumption Detection
```text
FUNCTION detect_unusual_consumption(household_bills, rules):
    history = EMPTY LIST
    FOR EACH bill IN SORTED_BY_MONTH(household_bills):
        reasons = EMPTY LIST
        IF LENGTH(history) >= 1 THEN
            prev = LAST(history)
            IF prev > 0 AND ((bill.units - prev) / prev) * 100 > rules.unusual_increase_percent THEN
                APPEND "Unusual consumption increase" TO reasons
            END IF
        END IF
        IF LENGTH(history) >= 3 THEN
            avg3 = SUM(LAST_3(history)) / 3
            IF avg3 > 0 AND ((bill.units - avg3) / avg3) * 100 > rules.unusual_increase_percent THEN
                APPEND "Sudden increase vs 3-month average" TO reasons
            END IF
        END IF
        IF bill.units > rules.high_consumption_threshold THEN
            APPEND "Consumption above configured threshold" TO reasons
        END IF
        IF bill.final_payable > rules.high_bill_threshold THEN
            APPEND "High electricity bill" TO reasons
        END IF
        APPEND bill.units TO history
    END FOR
END FUNCTION
```
