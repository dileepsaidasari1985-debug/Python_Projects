"""Core ATM Transaction Sequence Simulation logic.

Educational simulation only (Case Study #13):
Demonstrates Python syllabus concepts naturally:
- Variables, data types, arithmetic & logical operators
- Conditional statements and loops
- Strings and ASCII pattern generation
- Lists, nested lists, tuples, tuple operations, and tuple unpacking
"""

from datetime import datetime
import math
import secrets


# ---------------------------------------------------------------------------
# Tuples & Constants (demonstrating Tuple Creation and Tuple Operations)
# ---------------------------------------------------------------------------

TRANSACTION_TYPES = ("DEPOSIT", "WITHDRAWAL")
TRANSACTION_STATUSES = ("SUCCESS", "REJECTED")

# Tuple: (account_number, holder_name, initial_balance)
DEFAULT_ACCOUNT_TUPLE = ("DEMO1001", "Demo Student", 10000.0)

# Tuple: (max_per_transaction, max_daily_withdrawal, min_withdrawal, denomination, initial_demo_balance)
DEFAULT_SETTINGS_TUPLE = (10000.0, 25000.0, 100.0, 100, 10000.0)

# Tuple of tuples for the Case Study #13 default example sequence
EXAMPLE_SEQUENCE_TUPLES = (
    ("DEPOSIT", "2000", "Allowance Deposit"),
    ("WITHDRAWAL", "500", "ATM Cash Withdrawal"),
    ("DEPOSIT", "1000", "Refund Credit"),
    ("WITHDRAWAL", "3000", "Bookstore Cash"),
    ("WITHDRAWAL", "15000", "High-Value Attempt (Exceeds Limit)"),
)

# Tuple slicing & concatenation demonstration for UI quick-amount presets
DEPOSIT_PRESETS = (500, 1000, 2000) + (5000,)
WITHDRAWAL_PRESETS = (500, 1000, 2000, 5000, 10000)


def settings_to_tuple(settings):
    """Convert an ATM settings dictionary into an ordered configuration tuple."""
    return (
        float(settings["max_per_transaction"]),
        float(settings["max_daily_withdrawal"]),
        float(settings["min_withdrawal"]),
        int(settings["withdrawal_denomination"]),
        float(settings["initial_demo_balance"]),
    )


def format_inr(amount):
    """Format a numeric amount as Indian Rupee string with 2 decimals."""
    value = round(float(amount), 2)
    is_negative = value < 0
    abs_val = abs(value)
    whole_part = int(abs_val)
    decimal_part = f"{abs_val:.2f}".split(".")[1]

    digits = str(whole_part)
    if len(digits) <= 3:
        grouped = digits
    else:
        last_three = digits[-3:]
        remaining = digits[:-3]
        groups = []
        while len(remaining) > 2:
            groups.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            groups.insert(0, remaining)
        grouped = ",".join(groups) + "," + last_three

    prefix = "-₹" if is_negative else "₹"
    return f"{prefix}{grouped}.{decimal_part}"


def generate_transaction_id(now=None):
    """Generate a unique string transaction ID in TXN-YYYYMMDD-XXXXXX format."""
    current_time = now if now is not None else datetime.now()
    date_part = current_time.strftime("%Y%m%d")
    time_part = current_time.strftime("%H%M%S")
    random_hex = secrets.token_hex(2).upper()
    return f"TXN-{date_part}-{time_part}{random_hex}"


def parse_amount(raw_value):
    """Validate and convert a raw numeric input into a rounded float amount.

    Returns a tuple: (is_valid, parsed_float, error_message)
    """
    if raw_value is None:
        return (False, 0.0, "Amount is required.")

    cleaned = str(raw_value).strip().replace(",", "").replace("₹", "")
    if not cleaned:
        return (False, 0.0, "Amount cannot be empty.")

    try:
        numeric_value = float(cleaned)
    except ValueError:
        return (False, 0.0, "Invalid numeric amount. Please enter numbers only.")

    if math.isnan(numeric_value) or math.isinf(numeric_value):
        return (False, 0.0, "Amount must be a finite number.")

    rounded_value = round(numeric_value, 2)
    return (True, rounded_value, "")


def validate_deposit(raw_amount):
    """Validate a simulated cash deposit amount.

    Rules:
    - Must be a valid number
    - Must be strictly greater than zero (no zero or negative deposits)
    """
    is_num, amount, parse_err = parse_amount(raw_amount)
    if not is_num:
        return (False, 0.0, parse_err)

    if amount < 0:
        return (False, amount, "Deposit amount cannot be negative.")
    if amount == 0:
        return (False, amount, "Deposit amount must be greater than ₹0.00.")

    return (True, amount, "")


def validate_withdrawal(raw_amount, current_balance, daily_withdrawn, settings):
    """Validate a simulated cash withdrawal against ATM rules and balance.

    Rules checked in order:
    1. Valid numeric input
    2. Positive (> 0)
    3. At least minimum withdrawal amount
    4. At most maximum per-transaction limit
    5. Multiple of configured denomination (e.g., ₹100)
    6. Sufficient simulated account balance (never allow negative balance)
    7. Within maximum daily withdrawal limit
    """
    # Tuple unpacking of active ATM rules
    max_per_txn, max_daily, min_wd, denom, _ = settings_to_tuple(settings)

    is_num, amount, parse_err = parse_amount(raw_amount)
    if not is_num:
        return (False, 0.0, parse_err)

    if amount < 0:
        return (False, amount, "Withdrawal amount cannot be negative.")
    if amount == 0:
        return (False, amount, "Withdrawal amount must be greater than ₹0.00.")
    if amount < min_wd:
        return (
            False,
            amount,
            f"Minimum withdrawal amount is {format_inr(min_wd)}.",
        )
    if amount > max_per_txn:
        return (
            False,
            amount,
            f"Exceeds per-transaction withdrawal limit of {format_inr(max_per_txn)}.",
        )

    # Denomination check: ATM dispenses whole integer multiples only
    if amount != int(amount) or int(amount) % denom != 0:
        return (
            False,
            amount,
            f"Withdrawal amount must be a multiple of ₹{denom}.",
        )

    if amount > float(current_balance):
        return (
            False,
            amount,
            f"Insufficient balance. Available balance is {format_inr(current_balance)}.",
        )

    if round(float(daily_withdrawn) + amount, 2) > max_daily:
        remaining = max(0.0, round(max_daily - float(daily_withdrawn), 2))
        return (
            False,
            amount,
            f"Exceeds daily withdrawal limit of {format_inr(max_daily)} "
            f"(Remaining today: {format_inr(remaining)}).",
        )

    return (True, amount, "")


def execute_single_transaction(
    txn_type,
    raw_amount,
    current_balance,
    daily_withdrawn,
    settings,
    description="",
    source="SINGLE",
    timestamp_str=None,
):
    """Execute one simulated ATM transaction and return full result dictionary."""
    normalized_type = str(txn_type or "").strip().upper()
    balance_before = round(float(current_balance), 2)
    daily_before = round(float(daily_withdrawn), 2)
    clean_desc = " ".join(str(description or "").strip().split())[:140]
    created_at = timestamp_str or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    txn_id = generate_transaction_id()

    if normalized_type not in TRANSACTION_TYPES:
        return {
            "transaction_id": txn_id,
            "transaction_type": normalized_type or "UNKNOWN",
            "amount": 0.0,
            "balance_before": balance_before,
            "balance_after": balance_before,
            "daily_withdrawn_after": daily_before,
            "status": "REJECTED",
            "rejection_reason": "Unsupported transaction type. Use DEPOSIT or WITHDRAWAL.",
            "description": clean_desc or "Invalid Transaction Type",
            "source": source,
            "created_at": created_at,
        }

    if normalized_type == "DEPOSIT":
        is_valid, parsed_amt, reason = validate_deposit(raw_amount)
        default_desc = "ATM Cash Deposit"
    else:
        is_valid, parsed_amt, reason = validate_withdrawal(
            raw_amount, balance_before, daily_before, settings
        )
        default_desc = "ATM Cash Withdrawal"

    if is_valid:
        if normalized_type == "DEPOSIT":
            balance_after = round(balance_before + parsed_amt, 2)
            daily_after = daily_before
        else:
            balance_after = round(balance_before - parsed_amt, 2)
            daily_after = round(daily_before + parsed_amt, 2)
        status = "SUCCESS"
    else:
        # Rejected transactions never mutate the simulated balance
        balance_after = balance_before
        daily_after = daily_before
        status = "REJECTED"

    return {
        "transaction_id": txn_id,
        "transaction_type": normalized_type,
        "amount": round(parsed_amt, 2),
        "balance_before": balance_before,
        "balance_after": balance_after,
        "daily_withdrawn_after": daily_after,
        "status": status,
        "rejection_reason": reason,
        "description": clean_desc or default_desc,
        "source": source,
        "created_at": created_at,
    }


def parse_sequence_text(raw_text):
    """Parse multi-line text input into a list of (txn_type, amount_str, description) tuples.

    Accepted line formats:
    - DEPOSIT 2000
    - WITHDRAWAL 500 | Bookstore
    - Withdraw 15000 - Limit test
    """
    alias_deposit = ("DEPOSIT", "DEP", "CREDIT", "+")
    alias_withdrawal = ("WITHDRAWAL", "WITHDRAW", "WD", "DEBIT", "-")

    parsed_items = []
    if not raw_text:
        return parsed_items

    lines = str(raw_text).splitlines()
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        description = ""
        main_part = stripped
        if "|" in stripped:
            parts = stripped.split("|", 1)
            main_part = parts[0].strip()
            description = parts[1].strip()

        tokens = main_part.split()
        if len(tokens) < 2:
            parsed_items.append((tokens[0].upper(), "", description))
            continue

        raw_action = tokens[0].upper()
        raw_amount = tokens[1]
        if not description and len(tokens) > 2:
            description = " ".join(tokens[2:]).lstrip("-: ").strip()

        if raw_action in alias_deposit:
            action = "DEPOSIT"
        elif raw_action in alias_withdrawal:
            action = "WITHDRAWAL"
        else:
            action = raw_action

        parsed_items.append((action, raw_amount, description))

    return parsed_items


def process_transaction_sequence(
    sequence_items, starting_balance, starting_daily_withdrawn, settings
):
    """Process a sequence of deposits and withdrawals sequentially using a loop.

    Demonstrates:
    - Loops (`for` with `enumerate`)
    - Tuple unpacking (`txn_type, raw_amount, description = item`)
    - Nested lists for tabular sequence summary

    Returns a dictionary with:
    - `results`: list of transaction dicts (with `step_number`)
    - `nested_rows`: nested list `[step, txn_id, type, amount, before, after, status, reason]`
    - `summary`: sequence-level totals and net change
    """
    running_balance = round(float(starting_balance), 2)
    running_daily = round(float(starting_daily_withdrawn), 2)
    opening_balance = running_balance

    results = []
    nested_rows = []
    success_count = 0
    rejected_count = 0
    total_deposited = 0.0
    total_withdrawn = 0.0

    for step_number, item in enumerate(sequence_items, start=1):
        # Tuple unpacking
        txn_type, raw_amount, description = item

        outcome = execute_single_transaction(
            txn_type=txn_type,
            raw_amount=raw_amount,
            current_balance=running_balance,
            daily_withdrawn=running_daily,
            settings=settings,
            description=description or f"Sequence Step #{step_number}",
            source="SEQUENCE",
        )
        outcome["step_number"] = step_number

        # Advance running state from transaction outcome
        running_balance = outcome["balance_after"]
        running_daily = outcome["daily_withdrawn_after"]

        if outcome["status"] == "SUCCESS":
            success_count += 1
            if outcome["transaction_type"] == "DEPOSIT":
                total_deposited = round(total_deposited + outcome["amount"], 2)
            elif outcome["transaction_type"] == "WITHDRAWAL":
                total_withdrawn = round(total_withdrawn + outcome["amount"], 2)
        else:
            rejected_count += 1

        results.append(outcome)
        # Nested list row
        nested_rows.append(
            [
                step_number,
                outcome["transaction_id"],
                outcome["transaction_type"],
                outcome["amount"],
                outcome["balance_before"],
                outcome["balance_after"],
                outcome["status"],
                outcome["rejection_reason"],
            ]
        )

    summary = {
        "opening_balance": opening_balance,
        "closing_balance": running_balance,
        "net_change": round(running_balance - opening_balance, 2),
        "total_attempted": len(results),
        "success_count": success_count,
        "rejected_count": rejected_count,
        "total_deposited": total_deposited,
        "total_withdrawn": total_withdrawn,
        "daily_withdrawn_after": running_daily,
    }

    return {
        "results": results,
        "nested_rows": nested_rows,
        "summary": summary,
    }


def calculate_transaction_summary(transactions, opening_balance, current_balance):
    """Compute complete financial and statistical summary from transaction records.

    All metrics are calculated in pure Python using loops, conditionals,
    lists, nested lists, and tuples.
    """
    opening = round(float(opening_balance), 2)
    closing = round(float(current_balance), 2)

    total_transactions = len(transactions)
    successful_count = 0
    rejected_count = 0
    deposit_count = 0
    withdrawal_count = 0
    total_deposited = 0.0
    total_withdrawn = 0.0
    largest_deposit = 0.0
    largest_withdrawal = 0.0

    successful_amounts = []
    rejection_counts = {}

    for txn in transactions:
        # Unpack key fields into a tuple to compute metrics cleanly
        record_tuple = (
            txn["transaction_type"],
            float(txn["amount"]),
            txn["status"],
            txn.get("rejection_reason") or "",
        )
        t_type, amt, status, reason = record_tuple

        if status == "SUCCESS":
            successful_count += 1
            successful_amounts.append(amt)
            if t_type == "DEPOSIT":
                deposit_count += 1
                total_deposited = round(total_deposited + amt, 2)
                if amt > largest_deposit:
                    largest_deposit = amt
            elif t_type == "WITHDRAWAL":
                withdrawal_count += 1
                total_withdrawn = round(total_withdrawn + amt, 2)
                if amt > largest_withdrawal:
                    largest_withdrawal = amt
        else:
            rejected_count += 1
            reason_label = reason.strip() or "Validation Failed"
            rejection_counts[reason_label] = rejection_counts.get(reason_label, 0) + 1

    if successful_amounts:
        avg_txn_amount = round(sum(successful_amounts) / len(successful_amounts), 2)
    else:
        avg_txn_amount = 0.0

    net_balance_change = round(closing - opening, 2)

    # Nested list: [[reason, count], ...] sorted by highest frequency
    rejection_breakdown = sorted(
        [[reason, count] for reason, count in rejection_counts.items()],
        key=lambda pair: pair[1],
        reverse=True,
    )

    # Activity chart points (up to 12 most recent transactions in chronological order)
    recent_chronological = list(reversed(transactions[:12]))
    max_chart_val = 1.0
    for item in recent_chronological:
        val = float(item["amount"])
        if val > max_chart_val:
            max_chart_val = val

    chart_bars = []
    for item in recent_chronological:
        amt = float(item["amount"])
        pct = round((amt / max_chart_val) * 100, 1) if max_chart_val > 0 else 0.0
        chart_bars.append(
            {
                "id": item["transaction_id"],
                "short_id": item["transaction_id"][-6:],
                "type": item["transaction_type"],
                "status": item["status"],
                "amount": amt,
                "height_pct": max(pct, 8.0) if amt > 0 else 4.0,
                "balance_after": float(item["balance_after"]),
            }
        )

    return {
        "opening_balance": opening,
        "closing_balance": closing,
        "current_balance": closing,
        "total_transactions": total_transactions,
        "total_successful": successful_count,
        "total_rejected": rejected_count,
        "total_deposits_count": deposit_count,
        "total_withdrawals_count": withdrawal_count,
        "total_money_deposited": total_deposited,
        "total_money_withdrawn": total_withdrawn,
        "net_balance_change": net_balance_change,
        "largest_deposit": round(largest_deposit, 2),
        "largest_withdrawal": round(largest_withdrawal, 2),
        "average_transaction_amount": avg_txn_amount,
        "rejection_breakdown": rejection_breakdown,
        "chart_bars": chart_bars,
    }


def validate_atm_settings(
    raw_max_per_txn, raw_max_daily, raw_min_wd, raw_denom, raw_initial_balance
):
    """Validate configurable ATM rule settings submitted by the user."""
    errors = []

    ok_max_txn, max_per_txn, err1 = parse_amount(raw_max_per_txn)
    ok_max_daily, max_daily, err2 = parse_amount(raw_max_daily)
    ok_min_wd, min_wd, err3 = parse_amount(raw_min_wd)
    ok_init, initial_bal, err4 = parse_amount(raw_initial_balance)

    if not ok_max_txn:
        errors.append(f"Max withdrawal per transaction: {err1}")
    if not ok_max_daily:
        errors.append(f"Max daily withdrawal: {err2}")
    if not ok_min_wd:
        errors.append(f"Minimum withdrawal: {err3}")
    if not ok_init:
        errors.append(f"Initial demo balance: {err4}")

    try:
        denom = int(str(raw_denom).strip())
    except (ValueError, TypeError):
        denom = 0
        errors.append("Withdrawal denomination must be a positive whole number.")

    if not errors:
        if denom <= 0:
            errors.append("Withdrawal denomination must be greater than ₹0.")
        if min_wd <= 0:
            errors.append("Minimum withdrawal must be greater than ₹0.")
        if denom > 0 and (min_wd != int(min_wd) or int(min_wd) % denom != 0):
            errors.append(
                f"Minimum withdrawal ({format_inr(min_wd)}) must be a multiple of denomination (₹{denom})."
            )
        if max_per_txn < min_wd:
            errors.append(
                "Maximum withdrawal per transaction cannot be less than minimum withdrawal."
            )
        if denom > 0 and (max_per_txn != int(max_per_txn) or int(max_per_txn) % denom != 0):
            errors.append(
                f"Maximum withdrawal per transaction must be a multiple of denomination (₹{denom})."
            )
        if max_daily < max_per_txn:
            errors.append(
                "Maximum daily withdrawal cannot be less than per-transaction limit."
            )
        if initial_bal < 0:
            errors.append("Initial demo balance cannot be negative.")

    if errors:
        return (False, {}, errors)

    validated = {
        "max_per_transaction": round(max_per_txn, 2),
        "max_daily_withdrawal": round(max_daily, 2),
        "min_withdrawal": round(min_wd, 2),
        "withdrawal_denomination": denom,
        "initial_demo_balance": round(initial_bal, 2),
    }
    return (True, validated, [])


def generate_atm_receipt_pattern(account, txn):
    """Generate an ASCII ATM receipt using Python string formatting and loops."""
    border_thick = "=" * 46
    border_thin = "-" * 46

    rows = [
        ("Txn ID", txn["transaction_id"]),
        ("Date/Time", txn["created_at"]),
        ("Account", f"{account['account_number']} ({account['holder_name']})"),
        ("Type", txn["transaction_type"]),
        ("Status", txn["status"]),
        ("Amount", format_inr(txn["amount"])),
        ("Prev Bal", format_inr(txn["balance_before"])),
        ("New Bal", format_inr(txn["balance_after"])),
    ]
    if txn.get("rejection_reason"):
        rows.append(("Reason", txn["rejection_reason"]))

    lines = [
        border_thick,
        "       SMART ATM SIMULATION - RECEIPT",
        "     (Educational Demo - Not Real Banking)",
        border_thick,
    ]
    for label, value in rows:
        lines.append(f"{label:<11}: {value}")
    lines.append(border_thin)
    lines.append(f"Note       : {txn.get('description', 'N/A')}")
    lines.append(border_thick)
    return "\n".join(lines)


def generate_summary_pattern(account, summary):
    """Generate an ASCII transaction summary pattern for reports & printing."""
    line_eq = "=" * 52
    line_dash = "-" * 52

    metrics = [
        ("Account Holder", account["holder_name"]),
        ("Account Number", account["account_number"]),
        ("Opening Balance", format_inr(summary["opening_balance"])),
        ("Closing Balance", format_inr(summary["closing_balance"])),
        ("Net Balance Change", format_inr(summary["net_balance_change"])),
        ("Total Transactions", str(summary["total_transactions"])),
        ("Successful Txns", str(summary["total_successful"])),
        ("Rejected Txns", str(summary["total_rejected"])),
        ("Total Deposited", format_inr(summary["total_money_deposited"])),
        ("Total Withdrawn", format_inr(summary["total_money_withdrawn"])),
        ("Largest Deposit", format_inr(summary["largest_deposit"])),
        ("Largest Withdrawal", format_inr(summary["largest_withdrawal"])),
        ("Avg Txn Amount", format_inr(summary["average_transaction_amount"])),
    ]

    output = [
        line_eq,
        "     SMART ATM TRANSACTION SUMMARY REPORT",
        line_eq,
    ]
    for label, val in metrics:
        output.append(f"  {label:<22} : {val}")
    output.append(line_dash)
    output.append("  Generated by Python ATM Simulation Engine")
    output.append(line_eq)
    return "\n".join(output)
