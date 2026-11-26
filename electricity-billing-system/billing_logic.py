"""
Progressive Electricity Billing & Consumption Analysis Engine
-----------------------------------------------------------
Implements progressive tariff slab calculations, fixed charges, electricity duty,
surcharges, rebates, late penalties, monthly comparisons, rule-based unusual
consumption detection, input validation, and text pattern generation.

Uses beginner-friendly Python 3 syllabus concepts: variables, data types,
operators, conditional statements, loops, strings, pattern generation,
lists, nested lists, tuples, tuple operations, and tuple unpacking.
"""

from datetime import datetime

# Immutable tuple of default academic tariff slabs:
# (min_unit, max_unit, rate_per_unit, label)
DEFAULT_SLABS = (
    (0, 100, 2.0, "0-100 units"),
    (101, 200, 3.0, "101-200 units"),
    (201, 300, 5.0, "201-300 units"),
    (301, 500, 7.0, "301-500 units"),
    (501, None, 8.0, "Above 500 units"),
)

# Tuple constants for dropdown options and validation
CONNECTION_TYPES = ("Domestic", "Commercial", "Agricultural", "Small Industry")
METER_CATEGORIES = ("Single Phase", "Three Phase", "Smart Digital")
PAYMENT_STATUSES = ("Unpaid", "Paid")
REBATE_MODES = ("percent", "fixed")

# Default academic billing rules
DEFAULT_RULES = {
    "company_name": "VoltGrid Municipal Power Utility",
    "fixed_charge": 50.0,
    "duty_percent": 5.0,
    "surcharge_percent": 10.0,
    "surcharge_threshold_units": 300.0,
    "rebate_mode": "percent",
    "rebate_value": 5.0,
    "rebate_threshold_units": 150.0,
    "late_payment_penalty": 100.0,
    "unusual_increase_percent": 50.0,
    "high_consumption_threshold": 400.0,
    "high_bill_threshold": 2500.0,
}


def format_inr(amount):
    """Format a numeric amount as Indian Rupee currency string."""
    value = float(amount or 0.0)
    return f"₹{value:,.2f}"


def normalize_identifier(text):
    """Clean and uppercase identifiers such as Household ID or Meter Number."""
    return str(text or "").strip().upper()


def is_valid_identifier(text, min_len=3, max_len=24):
    """
    Validate an identifier string using string operations.
    Allowed characters: letters, digits, hyphens, underscores.
    """
    cleaned = normalize_identifier(text)
    if len(cleaned) < min_len or len(cleaned) > max_len:
        return False

    has_alnum = False
    for ch in cleaned:
        if ch.isalnum():
            has_alnum = True
        elif ch not in ("-", "_"):
            return False
    return has_alnum


def is_valid_billing_month(month_str):
    """Validate billing month strictly in YYYY-MM format."""
    cleaned = str(month_str or "").strip()
    if len(cleaned) != 7 or cleaned[4] != "-":
        return False
    parts = cleaned.split("-")
    year_str, month_part = parts[0], parts[1]
    if not (year_str.isdigit() and month_part.isdigit()):
        return False
    year_val = int(year_str)
    month_val = int(month_part)
    return 2000 <= year_val <= 2100 and 1 <= month_val <= 12


def format_month_label(month_str):
    """Convert 'YYYY-MM' into a readable label like 'Nov 2026'."""
    if not is_valid_billing_month(month_str):
        return str(month_str or "")
    dt = datetime.strptime(month_str.strip(), "%Y-%m")
    return dt.strftime("%b %Y")


def generate_bill_number(billing_month, household_id, sequence_num):
    """
    Generate a unique formatted bill number using string operations.
    Example: BILL-202611-HH101-001
    """
    compact_month = str(billing_month).replace("-", "")
    compact_hh = normalize_identifier(household_id).replace("-", "").replace("_", "")
    seq_padded = str(int(sequence_num)).zfill(3)
    return f"BILL-{compact_month}-{compact_hh}-{seq_padded}"


def calculate_energy_charge(consumption, slabs=DEFAULT_SLABS):
    """
    Calculate progressive electricity energy charge slab by slab.

    Args:
        consumption (float | int): Total electricity units consumed (>= 0).
        slabs (list | tuple): Sequence of (min_unit, max_unit, rate_per_unit, label) tuples.

    Returns:
        tuple: (total_energy_charge, breakdown_list)
            total_energy_charge (float): Sum of all slab charges rounded to 2 decimals.
            breakdown_list (list[dict]): Slab-wise unit and charge breakdown.
    """
    units = float(consumption)
    if units < 0:
        raise ValueError("Consumption units cannot be negative.")

    remaining = units
    total_charge = 0.0
    breakdown = []

    # Sort slabs by minimum unit limit safely
    sorted_slabs = sorted(slabs, key=lambda item: float(item[0]))

    for slab_tuple in sorted_slabs:
        # Tuple unpacking to extract slab details
        low, high, rate, label = slab_tuple
        low_val = float(low)
        rate_val = float(rate)

        if remaining <= 0:
            slab_units = 0.0
        elif high is None:
            slab_units = remaining
        else:
            high_val = float(high)
            # First slab starting at 0 holds `high` units (0-100 = 100 units);
            # subsequent slabs like 101-200 hold (200 - 101 + 1) = 100 units.
            if low_val == 0:
                capacity = high_val
            else:
                capacity = high_val - low_val + 1.0
            if capacity < 0:
                capacity = 0.0
            slab_units = min(remaining, capacity)

        slab_units_rounded = round(slab_units, 2)
        slab_charge = round(slab_units * rate_val, 2)
        total_charge = round(total_charge + slab_charge, 2)
        remaining = round(remaining - slab_units, 4)
        if remaining < 0:
            remaining = 0.0

        breakdown.append(
            {
                "label": label,
                "min_unit": int(low_val),
                "max_unit": int(high) if high is not None else None,
                "rate": round(rate_val, 2),
                "units": slab_units_rounded,
                "charge": slab_charge,
            }
        )

    return round(total_charge, 2), breakdown


def build_slab_nested_list(breakdown):
    """Convert slab breakdown dictionaries into a nested list representation."""
    nested_rows = []
    for item in breakdown:
        nested_rows.append(
            [item["label"], item["units"], item["rate"], item["charge"]]
        )
    return nested_rows


def calculate_full_bill(consumption, slabs=DEFAULT_SLABS, rules=None, is_late_payment=False):
    """
    Calculate the complete electricity bill with all components:
    Energy Charge + Fixed Charge + Electricity Duty + Surcharge - Rebate + Late Penalty.
    Prevents negative final bills by capping rebate at subtotal.
    """
    active_rules = dict(DEFAULT_RULES)
    if rules:
        active_rules.update(rules)

    units = round(float(consumption), 2)
    energy_charge, breakdown = calculate_energy_charge(units, slabs)

    fixed_charge = round(float(active_rules["fixed_charge"]), 2)
    duty_percent = float(active_rules["duty_percent"])
    electricity_duty = round(energy_charge * (duty_percent / 100.0), 2)

    # Surcharge applies when consumption exceeds the configured threshold (0 = always apply)
    surcharge_percent = float(active_rules["surcharge_percent"])
    surcharge_threshold = float(active_rules["surcharge_threshold_units"])
    if surcharge_percent > 0 and (surcharge_threshold <= 0 or units > surcharge_threshold):
        surcharge_amount = round(energy_charge * (surcharge_percent / 100.0), 2)
    else:
        surcharge_amount = 0.0

    # Rebate applies for non-zero consumption within the configured unit threshold (0 = all)
    rebate_mode = str(active_rules.get("rebate_mode", "percent")).strip().lower()
    rebate_value = float(active_rules["rebate_value"])
    rebate_threshold = float(active_rules["rebate_threshold_units"])
    if units > 0 and rebate_value > 0 and (rebate_threshold <= 0 or units <= rebate_threshold):
        if rebate_mode == "fixed":
            raw_rebate = round(rebate_value, 2)
        else:
            raw_rebate = round(energy_charge * (rebate_value / 100.0), 2)
    else:
        raw_rebate = 0.0

    subtotal_before_rebate = round(
        energy_charge + fixed_charge + electricity_duty + surcharge_amount, 2
    )
    # Prevent negative final bills by capping rebate
    rebate_amount = round(min(raw_rebate, subtotal_before_rebate), 2)

    late_penalty_amount = (
        round(float(active_rules["late_payment_penalty"]), 2) if is_late_payment else 0.0
    )

    final_payable = round(
        subtotal_before_rebate - rebate_amount + late_penalty_amount, 2
    )
    if final_payable < 0:
        final_payable = 0.0

    return {
        "units_consumed": units,
        "energy_charge": energy_charge,
        "fixed_charge": fixed_charge,
        "electricity_duty": electricity_duty,
        "surcharge_amount": surcharge_amount,
        "rebate_amount": rebate_amount,
        "late_penalty_amount": late_penalty_amount,
        "final_payable": final_payable,
        "slab_breakdown": breakdown,
        "slab_nested_list": build_slab_nested_list(breakdown),
        "surcharge_applied": surcharge_amount > 0,
        "rebate_applied": rebate_amount > 0,
    }


def validate_household_data(form_data):
    """Validate household registration or update input."""
    errors = []

    household_id = normalize_identifier(form_data.get("household_id"))
    consumer_name = str(form_data.get("consumer_name") or "").strip()
    meter_number = normalize_identifier(form_data.get("meter_number"))
    address = str(form_data.get("address") or "").strip()
    area = str(form_data.get("area") or "").strip()
    connection_type = str(form_data.get("connection_type") or "").strip()
    meter_category = str(form_data.get("meter_category") or "").strip()

    if not is_valid_identifier(household_id, 3, 24):
        errors.append(
            "Household ID must be 3-24 characters using letters, numbers, hyphens, or underscores."
        )
    if len(consumer_name) < 2 or len(consumer_name) > 80:
        errors.append("Consumer name must be between 2 and 80 characters.")
    if not is_valid_identifier(meter_number, 3, 24):
        errors.append(
            "Meter number must be 3-24 characters using letters, numbers, hyphens, or underscores."
        )
    if len(address) < 4 or len(address) > 200:
        errors.append("Address must be between 4 and 200 characters.")
    if len(area) < 2 or len(area) > 60:
        errors.append("Area / locality must be between 2 and 60 characters.")
    if connection_type not in CONNECTION_TYPES:
        errors.append("Please select a valid connection type.")
    if meter_category not in METER_CATEGORIES:
        errors.append("Please select a valid meter category.")

    cleaned = {
        "household_id": household_id,
        "consumer_name": consumer_name,
        "meter_number": meter_number,
        "address": address,
        "area": area,
        "connection_type": connection_type,
        "meter_category": meter_category,
    }
    return len(errors) == 0, errors, cleaned


def validate_meter_reading_data(form_data):
    """
    Validate meter reading inputs and compute consumption.
    Ensures non-negative readings, current >= previous, valid billing month and date.
    """
    errors = []

    household_ref_id_raw = str(form_data.get("household_ref_id") or "").strip()
    billing_month = str(form_data.get("billing_month") or "").strip()
    prev_raw = str(form_data.get("previous_reading") or "").strip()
    curr_raw = str(form_data.get("current_reading") or "").strip()
    billing_date = str(form_data.get("billing_date") or "").strip()
    is_late_payment = str(form_data.get("is_late_payment") or "").lower() in (
        "1",
        "true",
        "on",
        "yes",
    )

    try:
        household_ref_id = int(household_ref_id_raw)
        if household_ref_id <= 0:
            errors.append("Please select a valid household.")
            household_ref_id = None
    except ValueError:
        errors.append("Please select a registered household.")
        household_ref_id = None

    if not is_valid_billing_month(billing_month):
        errors.append("Billing month must be valid in YYYY-MM format.")

    prev_val = None
    curr_val = None
    try:
        prev_val = round(float(prev_raw), 2)
        if prev_val < 0:
            errors.append("Previous meter reading cannot be negative.")
    except ValueError:
        errors.append("Previous meter reading must be a valid number.")

    try:
        curr_val = round(float(curr_raw), 2)
        if curr_val < 0:
            errors.append("Current meter reading cannot be negative.")
    except ValueError:
        errors.append("Current meter reading must be a valid number.")

    consumption = None
    if prev_val is not None and curr_val is not None:
        if curr_val < prev_val:
            errors.append(
                "Current meter reading cannot be less than previous meter reading."
            )
        else:
            consumption = round(curr_val - prev_val, 2)

    if not billing_date:
        errors.append("Billing date is required.")
    else:
        try:
            datetime.strptime(billing_date, "%Y-%m-%d")
        except ValueError:
            errors.append("Billing date must be valid in YYYY-MM-DD format.")

    cleaned = {
        "household_ref_id": household_ref_id,
        "billing_month": billing_month,
        "previous_reading": prev_val,
        "current_reading": curr_val,
        "consumption_units": consumption,
        "billing_date": billing_date,
        "is_late_payment": is_late_payment,
    }
    return len(errors) == 0, errors, cleaned


def validate_rules_and_slabs(form_data):
    """Validate configurable tariff rules and progressive slab inputs."""
    errors = []
    cleaned_rules = {}
    cleaned_slabs = []

    numeric_fields = (
        ("fixed_charge", "Fixed monthly charge", 0.0, 10000.0),
        ("duty_percent", "Electricity duty (%)", 0.0, 100.0),
        ("surcharge_percent", "Surcharge (%)", 0.0, 100.0),
        ("surcharge_threshold_units", "Surcharge threshold units", 0.0, 100000.0),
        ("rebate_value", "Rebate value", 0.0, 100000.0),
        ("rebate_threshold_units", "Rebate threshold units", 0.0, 100000.0),
        ("late_payment_penalty", "Late payment penalty", 0.0, 50000.0),
        ("unusual_increase_percent", "Unusual increase threshold (%)", 5.0, 500.0),
        ("high_consumption_threshold", "High consumption threshold (units)", 10.0, 100000.0),
        ("high_bill_threshold", "High bill threshold (₹)", 50.0, 1000000.0),
    )

    company_name = str(form_data.get("company_name") or "").strip()
    if len(company_name) < 3 or len(company_name) > 100:
        errors.append("Electricity company name must be between 3 and 100 characters.")
    cleaned_rules["company_name"] = company_name

    rebate_mode = str(form_data.get("rebate_mode") or "percent").strip().lower()
    if rebate_mode not in REBATE_MODES:
        errors.append("Rebate mode must be either percentage or fixed amount.")
    cleaned_rules["rebate_mode"] = rebate_mode

    for field_key, label, min_val, max_val in numeric_fields:
        raw_val = str(form_data.get(field_key) or "").strip()
        try:
            num_val = round(float(raw_val), 2)
            if num_val < min_val or num_val > max_val:
                errors.append(f"{label} must be between {min_val} and {max_val}.")
            cleaned_rules[field_key] = num_val
        except ValueError:
            errors.append(f"{label} must be a valid number.")

    if rebate_mode == "percent" and cleaned_rules.get("rebate_value", 0) > 100:
        errors.append("Percentage rebate cannot exceed 100%.")

    # Validate 5 progressive slabs
    prev_max = -1
    for idx in range(1, 6):
        min_raw = str(form_data.get(f"slab_min_{idx}") or "").strip()
        max_raw = str(form_data.get(f"slab_max_{idx}") or "").strip()
        rate_raw = str(form_data.get(f"slab_rate_{idx}") or "").strip()
        label_val = str(form_data.get(f"slab_label_{idx}") or "").strip()

        try:
            min_u = int(min_raw)
            if min_u < 0:
                errors.append(f"Slab {idx} minimum units cannot be negative.")
        except ValueError:
            errors.append(f"Slab {idx} minimum units must be a whole number.")
            min_u = 0

        if idx == 5 and max_raw == "":
            max_u = None
        elif max_raw == "":
            errors.append(f"Slab {idx} maximum units is required (only last slab can be open-ended).")
            max_u = None
        else:
            try:
                max_u = int(max_raw)
                if max_u < min_u:
                    errors.append(f"Slab {idx} maximum units cannot be less than minimum units.")
            except ValueError:
                errors.append(f"Slab {idx} maximum units must be a whole number.")
                max_u = None

        try:
            rate_u = round(float(rate_raw), 2)
            if rate_u < 0:
                errors.append(f"Slab {idx} rate per unit cannot be negative.")
        except ValueError:
            errors.append(f"Slab {idx} rate per unit must be a valid number.")
            rate_u = 0.0

        if prev_max is not None and min_u <= prev_max:
            errors.append(f"Slab {idx} minimum units must be greater than previous slab maximum ({prev_max}).")
        prev_max = max_u

        if not label_val:
            label_val = f"{min_u}-{max_u} units" if max_u is not None else f"Above {min_u - 1} units"

        cleaned_slabs.append((min_u, max_u, rate_u, label_val))

    return len(errors) == 0, errors, cleaned_rules, cleaned_slabs


def calculate_percentage_change(current_value, previous_value):
    """
    Calculate percentage change: ((Current - Previous) / Previous) * 100.
    Safely handles zero or None previous values without division by zero.
    """
    if previous_value is None:
        return None
    prev = float(previous_value)
    curr = float(current_value)
    if prev == 0:
        return None
    return round(((curr - prev) / prev) * 100.0, 2)


def analyze_monthly_consumption(bills):
    """
    Aggregate and compare electricity consumption and bills month by month.
    Uses Python loops, lists, nested lists, and tuple unpacking.

    Returns a dictionary containing:
        - monthly_rows: list of dicts sorted chronologically
        - nested_records: nested list [[month, label, units, energy, total, pct_units, pct_bill], ...]
        - total_consumption, total_billing, avg_consumption
        - highest_month, lowest_month (tuples unpacked cleanly)
    """
    if not bills:
        return {
            "monthly_rows": [],
            "nested_records": [],
            "total_consumption": 0.0,
            "total_billing": 0.0,
            "avg_consumption": 0.0,
            "highest_month": None,
            "lowest_month": None,
        }

    # Aggregate totals per billing_month
    month_buckets = {}
    for bill in bills:
        month = bill["billing_month"]
        if month not in month_buckets:
            month_buckets[month] = [0.0, 0.0, 0.0, 0]
        month_buckets[month][0] += float(bill["units_consumed"])
        month_buckets[month][1] += float(bill["energy_charge"])
        month_buckets[month][2] += float(bill["final_payable"])
        month_buckets[month][3] += 1

    sorted_months = sorted(month_buckets.keys())
    monthly_rows = []
    nested_records = []

    prev_units = None
    prev_bill = None
    total_consumption = 0.0
    total_billing = 0.0

    # Track extremes as (month, label, units, bill_total) tuples
    highest_tuple = None
    lowest_tuple = None

    for month in sorted_months:
        units_sum, energy_sum, bill_sum, count = month_buckets[month]
        units_sum = round(units_sum, 2)
        energy_sum = round(energy_sum, 2)
        bill_sum = round(bill_sum, 2)
        month_label = format_month_label(month)

        pct_units = calculate_percentage_change(units_sum, prev_units)
        pct_bill = calculate_percentage_change(bill_sum, prev_bill)

        total_consumption = round(total_consumption + units_sum, 2)
        total_billing = round(total_billing + bill_sum, 2)

        row_dict = {
            "month": month,
            "month_label": month_label,
            "bill_count": count,
            "units_consumed": units_sum,
            "energy_charge": energy_sum,
            "total_bill": bill_sum,
            "pct_change_units": pct_units,
            "pct_change_bill": pct_bill,
            "prev_units": prev_units,
        }
        monthly_rows.append(row_dict)

        # Nested list entry for syllabus demonstration & tabular export
        nested_records.append(
            [month, month_label, units_sum, energy_sum, bill_sum, pct_units, pct_bill]
        )

        current_tuple = (month, month_label, units_sum, bill_sum)
        if highest_tuple is None or current_tuple[2] > highest_tuple[2]:
            highest_tuple = current_tuple
        if lowest_tuple is None or current_tuple[2] < lowest_tuple[2]:
            lowest_tuple = current_tuple

        prev_units = units_sum
        prev_bill = bill_sum

    avg_consumption = round(total_consumption / len(sorted_months), 2)

    # Tuple unpacking for highest and lowest consumption months
    high_m, high_lbl, high_u, high_b = highest_tuple
    low_m, low_lbl, low_u, low_b = lowest_tuple

    return {
        "monthly_rows": monthly_rows,
        "nested_records": nested_records,
        "total_consumption": total_consumption,
        "total_billing": total_billing,
        "avg_consumption": avg_consumption,
        "highest_month": {
            "month": high_m,
            "month_label": high_lbl,
            "units": high_u,
            "total_bill": high_b,
        },
        "lowest_month": {
            "month": low_m,
            "month_label": low_lbl,
            "units": low_u,
            "total_bill": low_b,
        },
    }


def detect_unusual_consumption(bills, rules=None):
    """
    Rule-based unusual consumption detector (no machine learning).
    Checks per-household chronological history for:
      1. Month-over-month spike (> unusual_increase_percent, default 50%)
      2. Spike above previous 3-month average (when >= 3 prior months exist)
      3. Consumption above configured high threshold
      4. Final bill above configured high bill threshold
    """
    active_rules = dict(DEFAULT_RULES)
    if rules:
        active_rules.update(rules)

    increase_limit = float(active_rules["unusual_increase_percent"])
    high_units_limit = float(active_rules["high_consumption_threshold"])
    high_bill_limit = float(active_rules["high_bill_threshold"])

    # Group bills by household_ref_id using lists
    grouped = {}
    for bill in bills:
        hh_ref = bill["household_ref_id"]
        if hh_ref not in grouped:
            grouped[hh_ref] = []
        grouped[hh_ref].append(bill)

    warnings_list = []

    for hh_ref in grouped:
        hh_bills = sorted(grouped[hh_ref], key=lambda item: item["billing_month"])
        history_units = []

        for idx, bill in enumerate(hh_bills):
            current_units = float(bill["units_consumed"])
            final_bill = float(bill["final_payable"])
            prev_units = history_units[-1] if idx > 0 else None

            reasons = []
            severity = "warning"
            pct_increase = None
            diff_units = None
            three_month_avg = None

            if prev_units is not None:
                diff_units = round(current_units - prev_units, 2)
                if prev_units > 0:
                    pct_increase = calculate_percentage_change(current_units, prev_units)
                    if pct_increase is not None and pct_increase > increase_limit:
                        reasons.append("Unusual consumption increase")
                        severity = "critical"
                elif current_units > high_units_limit:
                    reasons.append("Sudden increase in meter usage")
                    severity = "critical"

            # Compare with previous 3-month average when sufficient history exists
            if len(history_units) >= 3:
                last_three = history_units[-3:]
                three_month_avg = round(sum(last_three) / 3.0, 2)
                if three_month_avg > 0:
                    avg_pct = calculate_percentage_change(current_units, three_month_avg)
                    if avg_pct is not None and avg_pct > increase_limit:
                        reasons.append("Sudden increase in meter usage (vs 3-month avg)")
                        if pct_increase is None:
                            pct_increase = avg_pct
                            diff_units = round(current_units - three_month_avg, 2)
                        severity = "critical"

            if current_units > high_units_limit:
                reasons.append("Consumption above configured threshold")

            if final_bill > high_bill_limit:
                reasons.append("High electricity bill")

            if reasons:
                warnings_list.append(
                    {
                        "bill_id": bill["id"],
                        "bill_number": bill["bill_number"],
                        "household_ref_id": hh_ref,
                        "household_id": bill["household_id"],
                        "consumer_name": bill["consumer_name"],
                        "meter_number": bill["meter_number"],
                        "billing_month": bill["billing_month"],
                        "month_label": format_month_label(bill["billing_month"]),
                        "previous_consumption": prev_units,
                        "three_month_avg": three_month_avg,
                        "current_consumption": current_units,
                        "difference_units": diff_units,
                        "percentage_increase": pct_increase,
                        "final_payable": final_bill,
                        "reasons": reasons,
                        "reason_text": " • ".join(reasons),
                        "severity": severity,
                    }
                )

            history_units.append(current_units)

    # Sort warnings newest month first, then highest consumption
    warnings_list.sort(
        key=lambda w: (w["billing_month"], w["current_consumption"]),
        reverse=True,
    )
    return warnings_list


def generate_text_pattern_summary(monthly_rows, company_name):
    """
    Generate a formatted ASCII/Unicode text summary report using loops and
    string pattern generation (demonstrating syllabus pattern generation).
    """
    border = "=" * 62
    divider = "-" * 62
    lines = [
        border,
        f"  {company_name.upper()} - CONSUMPTION PATTERN",
        border,
    ]
    if not monthly_rows:
        lines.append("  No billing records available.")
        lines.append(border)
        return "\n".join(lines)

    max_units = max(row["units_consumed"] for row in monthly_rows) or 1.0
    bar_width = 24

    for row in monthly_rows:
        units = row["units_consumed"]
        filled = int(round((units / max_units) * bar_width))
        if units > 0 and filled == 0:
            filled = 1
        bar = "#" * filled + "." * (bar_width - filled)
        lines.append(
            f"  {row['month']} | [{bar}] {units:8.1f} kWh | ₹{row['total_bill']:9,.2f}"
        )
    lines.append(divider)
    return "\n".join(lines)
