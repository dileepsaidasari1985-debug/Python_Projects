# Step-by-Step Algorithm

1. **Start** and load `menu_inventory` and `canteen_orders` from SQLite.
2. **Read Order Queue**: Accept one order or a list of `(customer_name, [(item_code, qty), ...])` tuples.
3. **For Each Order**:
   - Initialize `subtotal = 0`, `accepted_lines = []`, `rejected_lines = []`.
   - **For Each `(item_code, raw_qty)`**:
     1. Validate `qty` is an integer `> 0`.
     2. Find `item_code` in `working_inventory`; if missing, reject.
     3. If `qty > available_stock`, reject with available count.
     4. Otherwise deduct `stock -= qty`, add `unit_price * qty` to `subtotal`, and record accepted line.
   - Compute `gst = round(subtotal * 0.05, 2)` and `grand_total = round(subtotal + gst, 2)`.
   - Classify status as `COMPLETED`, `PARTIAL`, or `REJECTED`.
4. **Persist & Summarize**: Save updated inventory and order logs to SQLite, compute daily revenue and low-stock alerts, generate ASCII stock gauges, and support CSV export.
5. **End**.
