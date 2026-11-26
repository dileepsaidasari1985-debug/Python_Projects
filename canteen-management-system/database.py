"""SQLite Persistence Layer for Smart Canteen Order and Stock Management (Case Study #57)."""

import os
import shutil
import sqlite3

from canteen_logic import SAMPLE_SUCCESSIVE_ORDERS, process_successive_orders

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "database", "canteen.db")

SAMPLE_MENU = (
    ("ITM101", "Masala Dosa", "Breakfast", 55.0, 25, 6),
    ("ITM102", "Veg Pulao Bowl", "Meals", 85.0, 20, 5),
    ("ITM103", "Paneer Tikka Roll", "Snacks", 70.0, 12, 5),
    ("ITM104", "Crispy Samosa (2 pcs)", "Snacks", 30.0, 35, 8),
    ("ITM105", "Cold Coffee", "Beverages", 45.0, 18, 5),
    ("ITM106", "Filter Coffee", "Beverages", 25.0, 30, 8),
    ("ITM107", "Fresh Watermelon Juice", "Beverages", 40.0, 4, 5),
    ("ITM108", "Grilled Cheese Sandwich", "Snacks", 60.0, 15, 5),
)


def _resolve_db_path(db_path):
    target = db_path or DEFAULT_DB_PATH
    if os.environ.get("VERCEL") and not str(target).startswith("/tmp"):
        tmp_path = os.path.join("/tmp", os.path.basename(target))
        if not os.path.exists(tmp_path) and os.path.exists(target):
            shutil.copyfile(target, tmp_path)
        return tmp_path
    return target


def get_connection(db_path=None):
    resolved = _resolve_db_path(db_path)
    parent = os.path.dirname(resolved)
    if parent:
        os.makedirs(parent, exist_ok=True)
    conn = sqlite3.connect(resolved)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path=None, seed_if_empty=True):
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS menu_inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_code TEXT UNIQUE NOT NULL,
                item_name TEXT NOT NULL,
                category TEXT NOT NULL,
                unit_price REAL NOT NULL,
                stock INTEGER NOT NULL,
                reorder_level INTEGER NOT NULL DEFAULT 5,
                sold_today INTEGER NOT NULL DEFAULT 0
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS canteen_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_number TEXT UNIQUE NOT NULL,
                customer_name TEXT NOT NULL,
                status TEXT NOT NULL,
                items_count INTEGER NOT NULL,
                subtotal REAL NOT NULL,
                gst_amount REAL NOT NULL,
                grand_total REAL NOT NULL,
                summary_text TEXT NOT NULL,
                rejection_notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            )
        """)
        conn.commit()
        if seed_if_empty and cur.execute("SELECT COUNT(*) FROM menu_inventory").fetchone()[0] == 0:
            load_sample_data(db_path)
    finally:
        conn.close()


def load_sample_data(db_path=None):
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        for code, name, cat, price, stock, reorder in SAMPLE_MENU:
            cur.execute(
                "INSERT OR IGNORE INTO menu_inventory (item_code, item_name, category, unit_price, stock, reorder_level, sold_today) VALUES (?, ?, ?, ?, ?, ?, 0)",
                (code, name, cat, price, stock, reorder),
            )
        conn.commit()

        if cur.execute("SELECT COUNT(*) FROM canteen_orders").fetchone()[0] == 0:
            inv = get_inventory(db_path)
            batch_res = process_successive_orders(SAMPLE_SUCCESSIVE_ORDERS, inv)
            save_updated_inventory(batch_res["updated_inventory"], db_path)
            for res in batch_res["orders"]:
                save_order_record(res, db_path)
    finally:
        conn.close()


def get_inventory(db_path=None):
    conn = get_connection(db_path)
    try:
        return [dict(r) for r in conn.execute("SELECT * FROM menu_inventory ORDER BY item_code ASC").fetchall()]
    finally:
        conn.close()


def save_updated_inventory(updated_inv, db_path=None):
    conn = get_connection(db_path)
    try:
        for row in updated_inv:
            conn.execute(
                "UPDATE menu_inventory SET stock = ?, sold_today = ? WHERE item_code = ?",
                (int(row["stock"]), int(row.get("sold_today", 0)), row["item_code"]),
            )
        conn.commit()
    finally:
        conn.close()


def restock_item(item_code, add_qty, db_path=None):
    conn = get_connection(db_path)
    try:
        conn.execute("UPDATE menu_inventory SET stock = stock + ? WHERE item_code = ?", (int(add_qty), item_code))
        conn.commit()
    finally:
        conn.close()


def add_menu_item(item_code, item_name, category, unit_price, stock, reorder_level, db_path=None):
    conn = get_connection(db_path)
    try:
        if conn.execute("SELECT 1 FROM menu_inventory WHERE UPPER(item_code) = ?", (item_code.upper(),)).fetchone():
            return (False, f"Item '{item_code}' already exists.")
        conn.execute(
            "INSERT INTO menu_inventory (item_code, item_name, category, unit_price, stock, reorder_level) VALUES (?, ?, ?, ?, ?, ?)",
            (item_code.upper(), item_name, category, float(unit_price), int(stock), int(reorder_level)),
        )
        conn.commit()
        return (True, f"Item '{item_code.upper()}' added.")
    finally:
        conn.close()


def get_orders(db_path=None):
    conn = get_connection(db_path)
    try:
        return [dict(r) for r in conn.execute("SELECT * FROM canteen_orders ORDER BY id DESC").fetchall()]
    finally:
        conn.close()


def save_order_record(res, db_path=None):
    conn = get_connection(db_path)
    try:
        cnt = conn.execute("SELECT COUNT(*) FROM canteen_orders").fetchone()[0]
        order_no = f"ORD-2026-{cnt + 1:03d}"
        while conn.execute("SELECT 1 FROM canteen_orders WHERE order_number = ?", (order_no,)).fetchone():
            cnt += 1
            order_no = f"ORD-2026-{cnt + 1:03d}"

        summary = ", ".join(f"{l['qty']}x {l['item_name']}" for l in res["accepted_lines"]) or "No items fulfilled"
        rej_notes = " | ".join(r[2] for r in res["rejected_lines"])
        conn.execute(
            """
            INSERT INTO canteen_orders
            (order_number, customer_name, status, items_count, subtotal, gst_amount, grand_total, summary_text, rejection_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order_no,
                res["customer_name"],
                res["status"],
                res["items_accepted_count"],
                res["subtotal"],
                res["gst_amount"],
                res["grand_total"],
                summary,
                rej_notes,
            ),
        )
        conn.commit()
        return order_no
    finally:
        conn.close()
