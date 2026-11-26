"""Smart Canteen Order and Stock Management (Case Study #57) - Flask Application."""

import csv
import io
import os
import secrets

from flask import Flask, Response, abort, flash, redirect, render_template, request, session, url_for

from canteen_logic import (
    CANTEEN_CATEGORIES,
    format_inr,
    process_single_order,
    process_successive_orders,
    summarize_daily_sales,
)
from database import (
    DEFAULT_DB_PATH,
    add_menu_item,
    get_inventory,
    get_orders,
    init_db,
    restock_item,
    save_order_record,
    save_updated_inventory,
)


def create_app(db_path=None, seed_if_empty=True):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)
    app.config["DB_PATH"] = db_path or DEFAULT_DB_PATH
    init_db(app.config["DB_PATH"], seed_if_empty=seed_if_empty)

    def get_csrf_token():
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_hex(24)
        return session["csrf_token"]

    app.jinja_env.globals["csrf_token"] = get_csrf_token
    app.template_filter("inr")(format_inr)

    @app.before_request
    def verify_csrf():
        if request.method == "POST":
            expected = session.get("csrf_token", "")
            submitted = request.form.get("csrf_token", "")
            if not expected or not secrets.compare_digest(expected, submitted):
                abort(400, description="Invalid or missing CSRF token.")

    @app.context_processor
    def inject_nav():
        db = app.config["DB_PATH"]
        inv = get_inventory(db)
        orders = get_orders(db)
        low_count = sum(1 for i in inv if i["stock"] <= i["reorder_level"])
        return {
            "current_endpoint": request.endpoint or "dashboard",
            "nav_items": len(inv),
            "nav_orders": len(orders),
            "nav_low_stock": low_count,
            "categories": CANTEEN_CATEGORIES,
        }

    @app.route("/")
    def dashboard():
        db = app.config["DB_PATH"]
        inv = get_inventory(db)
        orders = get_orders(db)
        summary = summarize_daily_sales(orders, inv)
        return render_template("dashboard.html", summary=summary, orders=orders[:6])

    @app.route("/order", methods=["GET", "POST"])
    def order_counter():
        db = app.config["DB_PATH"]
        inv = get_inventory(db)
        last_result = None

        if request.method == "POST":
            customer = request.form.get("customer_name", "").strip()
            order_items = []
            for item in inv:
                raw_q = request.form.get(f"qty_{item['item_code']}", "0").strip()
                if raw_q and raw_q != "0":
                    order_items.append((item["item_code"], raw_q))

            if not order_items:
                flash("Enter a quantity for at least one canteen item.", "danger")
            else:
                last_result, updated_inv = process_single_order(customer, order_items, inv)
                save_updated_inventory(updated_inv, db)
                order_no = save_order_record(last_result, db)
                if last_result["status"] == "COMPLETED":
                    flash(f"Order {order_no} completed! Total: {format_inr(last_result['grand_total'])}.", "success")
                elif last_result["status"] == "PARTIAL":
                    flash(f"Order {order_no} partially fulfilled (some quantities rejected).", "warning")
                else:
                    flash(f"Order {order_no} rejected due to unavailable stock or invalid quantities.", "danger")
                inv = get_inventory(db)

        return render_template("order.html", inventory=inv, last_result=last_result)

    @app.route("/queue", methods=["GET", "POST"])
    def order_queue():
        db = app.config["DB_PATH"]
        inv = get_inventory(db)
        default_queue = "\n".join([
            "Kiran (CS) | ITM101:2, ITM105:1",
            "Sneha (EC) | ITM107:3, ITM104:5",
            "Arjun (ME) | ITM107:5, ITM106:2",
        ])
        raw_queue = default_queue
        batch_result = None

        if request.method == "POST":
            raw_queue = request.form.get("queue_text", "").strip()
            parsed_queue = []
            for line in raw_queue.splitlines():
                if not line.strip() or "|" not in line:
                    continue
                cust, items_part = [p.strip() for p in line.split("|", 1)]
                item_tuples = []
                for pair in items_part.split(","):
                    if ":" in pair:
                        code, qty = [x.strip() for x in pair.split(":", 1)]
                        item_tuples.append((code, qty))
                if item_tuples:
                    parsed_queue.append((cust, item_tuples))

            if parsed_queue:
                batch_result = process_successive_orders(parsed_queue, inv)
                if request.form.get("commit_queue") == "1":
                    save_updated_inventory(batch_result["updated_inventory"], db)
                    for ord_res in batch_result["orders"]:
                        save_order_record(ord_res, db)
                    flash(f"Committed {len(batch_result['orders'])} successive orders to SQLite!", "success")

        return render_template("queue.html", raw_queue=raw_queue, batch_result=batch_result, inventory=inv)

    @app.route("/inventory", methods=["GET", "POST"])
    def inventory():
        db = app.config["DB_PATH"]
        if request.method == "POST":
            action = request.form.get("action", "restock")
            if action == "restock":
                code = request.form.get("item_code", "")
                try:
                    qty = int(request.form.get("add_qty", "0"))
                    if qty <= 0:
                        flash("Restock quantity must be positive.", "danger")
                    else:
                        restock_item(code, qty, db)
                        flash(f"Added {qty} units to {code}.", "success")
                except ValueError:
                    flash("Invalid restock quantity.", "danger")
            elif action == "add_item":
                try:
                    code = request.form.get("item_code", "").strip().upper()
                    name = request.form.get("item_name", "").strip()
                    cat = request.form.get("category", "Snacks")
                    price = float(request.form.get("unit_price", "0"))
                    stock = int(request.form.get("stock", "0"))
                    reorder = int(request.form.get("reorder_level", "5"))
                    if not code or not name or price <= 0 or stock < 0:
                        flash("Valid code, name, positive price, and non-negative stock required.", "danger")
                    else:
                        ok, msg = add_menu_item(code, name, cat, price, stock, reorder, db)
                        flash(msg, "success" if ok else "danger")
                except ValueError:
                    flash("Invalid numeric values for new menu item.", "danger")
            return redirect(url_for("inventory"))

        inv = get_inventory(db)
        orders = get_orders(db)
        summary = summarize_daily_sales(orders, inv)
        return render_template("inventory.html", stock_rows=summary["stock_rows"])

    @app.route("/reports")
    def reports():
        db = app.config["DB_PATH"]
        inv = get_inventory(db)
        orders = get_orders(db)
        summary = summarize_daily_sales(orders, inv)
        return render_template("reports.html", summary=summary, orders=orders)

    @app.route("/reports/export-csv")
    def export_csv():
        db = app.config["DB_PATH"]
        inv = get_inventory(db)
        orders = get_orders(db)
        out = io.StringIO()
        writer = csv.writer(out)
        writer.writerow(["Order #", "Customer", "Status", "Items Sold", "Subtotal", "GST", "Grand Total", "Summary", "Rejections"])
        for o in orders:
            writer.writerow([o["order_number"], o["customer_name"], o["status"], o["items_count"], o["subtotal"], o["gst_amount"], o["grand_total"], o["summary_text"], o["rejection_notes"]])
        writer.writerow([])
        writer.writerow(["Item Code", "Item Name", "Category", "Unit Price", "Remaining Stock", "Sold Today"])
        for i in inv:
            writer.writerow([i["item_code"], i["item_name"], i["category"], i["unit_price"], i["stock"], i["sold_today"]])
        return Response(out.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=canteen_sales_stock.csv"})

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5057)
