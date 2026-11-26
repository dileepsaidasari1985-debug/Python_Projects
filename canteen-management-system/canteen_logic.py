"""Core Smart Canteen Order and Stock Management logic (Case Study #57).

Demonstrates Python syllabus concepts:
- Variables, data types, arithmetic & relational/logical operators
- Conditional statements (if / elif / else) and loops (for, while)
- Strings and ASCII inventory/sales bar pattern generation
- Lists and nested lists (order queues, line breakdowns, low-stock alerts)
- Tuples, tuple operations, and tuple unpacking ((item_code, qty))
"""

CANTEEN_CATEGORIES = ("Breakfast", "Meals", "Snacks", "Beverages")
DEFAULT_GST_RATE = 0.05

# Sample successive order queue: (customer_name, [(item_code, qty), ...])
SAMPLE_SUCCESSIVE_ORDERS = (
    ("Aarav (CS-2A)", (("ITM101", 2), ("ITM105", 2))),
    ("Diya (IT-3B)", (("ITM102", 1), ("ITM104", 4))),
    ("Rohan (ME-1A)", (("ITM103", 50), ("ITM106", 1))),
)


def format_inr(amount):
    """Format numeric value as ₹X,XXX.XX."""
    val = round(float(amount), 2)
    return f"₹{val:,.2f}"


def generate_stock_bar(stock, max_cap=40, width=10):
    """Generate an ASCII remaining stock gauge using a loop."""
    if max_cap <= 0:
        max_cap = 1
    ratio = stock / max_cap
    if ratio > 1.0:
        ratio = 1.0
    elif ratio < 0.0:
        ratio = 0.0
    filled = int(round(ratio * width))
    bar = ""
    i = 0
    while i < width:
        bar += "█" if i < filled else "░"
        i += 1
    return f"[{bar}]"


def process_single_order(customer_name, order_items, inventory_list, gst_rate=DEFAULT_GST_RATE):
    """Process one customer order against mutable inventory list.

    order_items: sequence of (item_code, raw_qty) tuples
    inventory_list: list of dicts with keys item_code, item_name, category, unit_price, stock, reorder_level
    Returns (order_result_dict, updated_inventory_list)
    """
    clean_customer = " ".join(str(customer_name or "").strip().split()) or "Walk-in Student"
    working_inv = [dict(row) for row in inventory_list]

    accepted_lines = []
    rejected_lines = []
    subtotal = 0.0

    for item_code_raw, raw_qty in order_items:
        code = str(item_code_raw or "").strip().upper()
        try:
            qty = int(str(raw_qty).strip())
        except (ValueError, TypeError):
            rejected_lines.append((code or "UNKNOWN", raw_qty, f"Invalid non-integer quantity '{raw_qty}'."))
            continue

        if qty <= 0:
            rejected_lines.append((code or "UNKNOWN", qty, "Quantity must be greater than zero."))
            continue

        matched = None
        for inv in working_inv:
            if inv["item_code"].upper() == code:
                matched = inv
                break

        if matched is None:
            rejected_lines.append((code, qty, f"Item '{code}' not found in canteen menu."))
            continue

        available = int(matched["stock"])
        if available == 0:
            rejected_lines.append((code, qty, f"{matched['item_name']} is out of stock (0 remaining)."))
            continue

        if qty > available:
            rejected_lines.append((
                code,
                qty,
                f"Requested {qty} x {matched['item_name']}, but only {available} available in stock.",
            ))
            continue

        unit_price = float(matched["unit_price"])
        line_total = round(unit_price * qty, 2)
        matched["stock"] = available - qty
        matched["sold_today"] = int(matched.get("sold_today", 0)) + qty
        subtotal = round(subtotal + line_total, 2)
        accepted_lines.append({
            "item_code": code,
            "item_name": matched["item_name"],
            "qty": qty,
            "unit_price": unit_price,
            "line_total": line_total,
            "remaining_stock": matched["stock"],
        })

    gst_amount = round(subtotal * gst_rate, 2)
    grand_total = round(subtotal + gst_amount, 2)

    if accepted_lines and not rejected_lines:
        status = "COMPLETED"
    elif accepted_lines and rejected_lines:
        status = "PARTIAL"
    else:
        status = "REJECTED"

    return {
        "customer_name": clean_customer,
        "status": status,
        "accepted_lines": accepted_lines,
        "rejected_lines": rejected_lines,
        "subtotal": subtotal,
        "gst_amount": gst_amount,
        "grand_total": grand_total,
        "items_accepted_count": sum(l["qty"] for l in accepted_lines),
    }, working_inv


def process_successive_orders(order_queue, inventory_list, gst_rate=DEFAULT_GST_RATE):
    """Process successive customer orders sequentially using a loop and tuple unpacking."""
    current_inv = [dict(row) for row in inventory_list]
    processed_orders = []
    total_batch_revenue = 0.0

    for step_idx, (customer_name, item_tuples) in enumerate(order_queue, start=1):
        res, current_inv = process_single_order(customer_name, item_tuples, current_inv, gst_rate)
        res["step"] = step_idx
        total_batch_revenue = round(total_batch_revenue + res["grand_total"], 2)
        processed_orders.append(res)

    return {
        "orders": processed_orders,
        "updated_inventory": current_inv,
        "total_batch_revenue": total_batch_revenue,
    }


def summarize_daily_sales(orders_history, inventory_list):
    """Summarize daily sales revenue, item counts, low-stock alerts, and ASCII report."""
    total_revenue = 0.0
    completed_count = 0
    partial_count = 0
    rejected_count = 0
    total_units_sold = 0

    for ord_row in orders_history:
        total_revenue = round(total_revenue + float(ord_row["grand_total"]), 2)
        st = ord_row["status"]
        if st == "COMPLETED":
            completed_count += 1
        elif st == "PARTIAL":
            partial_count += 1
        else:
            rejected_count += 1
        total_units_sold += int(ord_row["items_count"])

    low_stock_items = []
    stock_rows = []
    for inv in inventory_list:
        stk = int(inv["stock"])
        reorder = int(inv["reorder_level"])
        is_low = stk <= reorder
        if is_low:
            low_stock_items.append(inv)
        stock_rows.append({
            **inv,
            "is_low": is_low,
            "stock_bar": generate_stock_bar(stk, max(30, stk)),
        })

    ascii_summary = generate_ascii_daily_summary(total_revenue, completed_count, partial_count, rejected_count, stock_rows)
    return {
        "total_revenue": total_revenue,
        "total_orders": len(orders_history),
        "completed_count": completed_count,
        "partial_count": partial_count,
        "rejected_count": rejected_count,
        "total_units_sold": total_units_sold,
        "low_stock_items": low_stock_items,
        "stock_rows": stock_rows,
        "ascii_summary": ascii_summary,
    }


def generate_ascii_daily_summary(revenue, completed, partial, rejected, stock_rows):
    """Generate an ASCII daily canteen sales & remaining stock report."""
    lines = [
        "+" + "-" * 64 + "+",
        "| SMART CANTEEN DAILY SALES & REMAINING STOCK SUMMARY".ljust(65) + "|",
        "+" + "-" * 64 + "+",
        f"| Revenue: {format_inr(revenue):<16} | Completed: {completed:<3} Partial: {partial:<3} Rejected: {rejected:<3}|",
        "+" + "-" * 64 + "+",
        f"| {'Code':<7} {'Item Name':<22} {'Price':>8} {'Stock':>6} {'Gauge':<14} |",
        "|" + "-" * 64 + "|",
    ]
    for r in stock_rows:
        lines.append(
            f"| {r['item_code']:<7} {r['item_name'][:22]:<22} {r['unit_price']:8.2f} {r['stock']:6d} {r['stock_bar']:<14} |"
        )
    lines.append("+" + "-" * 64 + "+")
    return "\n".join(lines)
