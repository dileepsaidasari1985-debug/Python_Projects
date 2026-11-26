"""
SQLite Database Layer - Progressive Electricity Billing System
--------------------------------------------------------------
Automatically creates the SQLite database and tables, enforces uniqueness,
runs parameterized SQL queries, manages tariff rules & progressive slabs,
and loads idempotent sample household and monthly billing records.
"""

import os
import shutil
import sqlite3
import tempfile
from datetime import datetime

from billing_logic import (
    DEFAULT_RULES,
    DEFAULT_SLABS,
    calculate_full_bill,
    generate_bill_number,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BUNDLED_DB_PATH = os.path.join(BASE_DIR, "database", "electricity.db")


def resolve_default_db_path():
    """
    Use database/electricity.db locally; on read-only serverless environments
    (such as Vercel), copy the seeded database into the writable temp directory.
    """
    db_dir = os.path.dirname(BUNDLED_DB_PATH)
    is_vercel = bool(os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV"))
    is_writable = os.path.isdir(db_dir) and os.access(db_dir, os.W_OK)

    if is_vercel or not is_writable:
        tmp_db = os.path.join(tempfile.gettempdir(), "electricity.db")
        if not os.path.exists(tmp_db) and os.path.exists(BUNDLED_DB_PATH):
            shutil.copy2(BUNDLED_DB_PATH, tmp_db)
        return tmp_db
    return BUNDLED_DB_PATH


DEFAULT_DB_PATH = resolve_default_db_path()


def get_connection(db_path=DEFAULT_DB_PATH):
    """Open a SQLite connection with Row mapping and foreign keys enabled."""
    db_dir = os.path.dirname(os.path.abspath(db_path))
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path=DEFAULT_DB_PATH, seed_if_empty=True):
    """Create all tables, seed default tariff rules/slabs, and optionally load sample data."""
    conn = get_connection(db_path)
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS households (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                household_id TEXT NOT NULL UNIQUE,
                consumer_name TEXT NOT NULL,
                meter_number TEXT NOT NULL UNIQUE,
                address TEXT NOT NULL,
                area TEXT NOT NULL,
                connection_type TEXT NOT NULL,
                meter_category TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS meter_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                household_ref_id INTEGER NOT NULL,
                billing_month TEXT NOT NULL,
                previous_reading REAL NOT NULL,
                current_reading REAL NOT NULL,
                consumption_units REAL NOT NULL,
                billing_date TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(household_ref_id, billing_month),
                FOREIGN KEY (household_ref_id) REFERENCES households(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS electricity_bills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bill_number TEXT NOT NULL UNIQUE,
                reading_id INTEGER NOT NULL UNIQUE,
                household_ref_id INTEGER NOT NULL,
                billing_month TEXT NOT NULL,
                previous_reading REAL NOT NULL,
                current_reading REAL NOT NULL,
                units_consumed REAL NOT NULL,
                energy_charge REAL NOT NULL,
                fixed_charge REAL NOT NULL,
                electricity_duty REAL NOT NULL,
                surcharge_amount REAL NOT NULL,
                rebate_amount REAL NOT NULL,
                late_penalty_amount REAL NOT NULL,
                final_payable REAL NOT NULL,
                payment_status TEXT NOT NULL DEFAULT 'Unpaid',
                is_late_payment INTEGER NOT NULL DEFAULT 0,
                billing_date TEXT NOT NULL,
                generated_at TEXT NOT NULL,
                UNIQUE(household_ref_id, billing_month),
                FOREIGN KEY (reading_id) REFERENCES meter_readings(id) ON DELETE CASCADE,
                FOREIGN KEY (household_ref_id) REFERENCES households(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS bill_slab_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bill_id INTEGER NOT NULL,
                slab_order INTEGER NOT NULL,
                slab_label TEXT NOT NULL,
                units_in_slab REAL NOT NULL,
                rate_per_unit REAL NOT NULL,
                slab_charge REAL NOT NULL,
                FOREIGN KEY (bill_id) REFERENCES electricity_bills(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS billing_rules (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                company_name TEXT NOT NULL,
                fixed_charge REAL NOT NULL,
                duty_percent REAL NOT NULL,
                surcharge_percent REAL NOT NULL,
                surcharge_threshold_units REAL NOT NULL,
                rebate_mode TEXT NOT NULL,
                rebate_value REAL NOT NULL,
                rebate_threshold_units REAL NOT NULL,
                late_payment_penalty REAL NOT NULL,
                unusual_increase_percent REAL NOT NULL,
                high_consumption_threshold REAL NOT NULL,
                high_bill_threshold REAL NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tariff_slabs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slab_order INTEGER NOT NULL UNIQUE,
                min_unit INTEGER NOT NULL,
                max_unit INTEGER,
                rate_per_unit REAL NOT NULL,
                label TEXT NOT NULL
            );
            """
        )

        # Ensure default billing rules row exists
        rule_row = conn.execute("SELECT id FROM billing_rules WHERE id = 1").fetchone()
        if not rule_row:
            _insert_default_rules(conn)

        # Ensure default progressive tariff slabs exist
        slab_count = conn.execute("SELECT COUNT(*) FROM tariff_slabs").fetchone()[0]
        if slab_count == 0:
            _insert_default_slabs(conn)

        conn.commit()
    finally:
        conn.close()

    if seed_if_empty:
        # Seed sample data only when households table is empty
        conn_check = get_connection(db_path)
        try:
            hh_count = conn_check.execute("SELECT COUNT(*) FROM households").fetchone()[0]
        finally:
            conn_check.close()
        if hh_count == 0:
            load_sample_data(db_path)


def _insert_default_rules(conn):
    """Insert or replace the single billing_rules configuration row."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        """
        INSERT OR REPLACE INTO billing_rules (
            id, company_name, fixed_charge, duty_percent, surcharge_percent,
            surcharge_threshold_units, rebate_mode, rebate_value,
            rebate_threshold_units, late_payment_penalty, unusual_increase_percent,
            high_consumption_threshold, high_bill_threshold, updated_at
        ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            DEFAULT_RULES["company_name"],
            DEFAULT_RULES["fixed_charge"],
            DEFAULT_RULES["duty_percent"],
            DEFAULT_RULES["surcharge_percent"],
            DEFAULT_RULES["surcharge_threshold_units"],
            DEFAULT_RULES["rebate_mode"],
            DEFAULT_RULES["rebate_value"],
            DEFAULT_RULES["rebate_threshold_units"],
            DEFAULT_RULES["late_payment_penalty"],
            DEFAULT_RULES["unusual_increase_percent"],
            DEFAULT_RULES["high_consumption_threshold"],
            DEFAULT_RULES["high_bill_threshold"],
            now_str,
        ),
    )


def _insert_default_slabs(conn):
    """Insert default academic progressive tariff slabs."""
    conn.execute("DELETE FROM tariff_slabs")
    for idx, slab_tuple in enumerate(DEFAULT_SLABS, start=1):
        low, high, rate, label = slab_tuple
        conn.execute(
            """
            INSERT INTO tariff_slabs (slab_order, min_unit, max_unit, rate_per_unit, label)
            VALUES (?, ?, ?, ?, ?)
            """,
            (idx, low, high, rate, label),
        )


def get_rules(db_path=DEFAULT_DB_PATH):
    """Fetch current billing rules as a dictionary."""
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT * FROM billing_rules WHERE id = 1").fetchone()
        return dict(row) if row else dict(DEFAULT_RULES)
    finally:
        conn.close()


def get_slabs(db_path=DEFAULT_DB_PATH):
    """Fetch progressive tariff slabs as a list of (min_unit, max_unit, rate, label) tuples."""
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT min_unit, max_unit, rate_per_unit, label FROM tariff_slabs ORDER BY slab_order ASC"
        ).fetchall()
        if not rows:
            return list(DEFAULT_SLABS)
        return [
            (r["min_unit"], r["max_unit"], r["rate_per_unit"], r["label"])
            for r in rows
        ]
    finally:
        conn.close()


def update_rules_and_slabs(rules_data, slabs_data, db_path=DEFAULT_DB_PATH):
    """Update configurable billing rules and tariff slabs in SQLite."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection(db_path)
    try:
        conn.execute(
            """
            UPDATE billing_rules SET
                company_name = ?,
                fixed_charge = ?,
                duty_percent = ?,
                surcharge_percent = ?,
                surcharge_threshold_units = ?,
                rebate_mode = ?,
                rebate_value = ?,
                rebate_threshold_units = ?,
                late_payment_penalty = ?,
                unusual_increase_percent = ?,
                high_consumption_threshold = ?,
                high_bill_threshold = ?,
                updated_at = ?
            WHERE id = 1
            """,
            (
                rules_data["company_name"],
                rules_data["fixed_charge"],
                rules_data["duty_percent"],
                rules_data["surcharge_percent"],
                rules_data["surcharge_threshold_units"],
                rules_data["rebate_mode"],
                rules_data["rebate_value"],
                rules_data["rebate_threshold_units"],
                rules_data["late_payment_penalty"],
                rules_data["unusual_increase_percent"],
                rules_data["high_consumption_threshold"],
                rules_data["high_bill_threshold"],
                now_str,
            ),
        )
        conn.execute("DELETE FROM tariff_slabs")
        for idx, slab_tuple in enumerate(slabs_data, start=1):
            low, high, rate, label = slab_tuple
            conn.execute(
                """
                INSERT INTO tariff_slabs (slab_order, min_unit, max_unit, rate_per_unit, label)
                VALUES (?, ?, ?, ?, ?)
                """,
                (idx, low, high, rate, label),
            )
        conn.commit()
    finally:
        conn.close()


def reset_rules_to_default(db_path=DEFAULT_DB_PATH):
    """Reset billing rules and tariff slabs back to academic defaults."""
    conn = get_connection(db_path)
    try:
        _insert_default_rules(conn)
        _insert_default_slabs(conn)
        conn.commit()
    finally:
        conn.close()


def add_household(data, db_path=DEFAULT_DB_PATH):
    """Insert a new household; raises ValueError on duplicate Household ID or Meter Number."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection(db_path)
    try:
        dup_hh = conn.execute(
            "SELECT id FROM households WHERE household_id = ?",
            (data["household_id"],),
        ).fetchone()
        if dup_hh:
            raise ValueError(f"Household ID '{data['household_id']}' already exists.")

        dup_meter = conn.execute(
            "SELECT id FROM households WHERE meter_number = ?",
            (data["meter_number"],),
        ).fetchone()
        if dup_meter:
            raise ValueError(f"Meter number '{data['meter_number']}' is already registered.")

        cursor = conn.execute(
            """
            INSERT INTO households (
                household_id, consumer_name, meter_number, address, area,
                connection_type, meter_category, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["household_id"],
                data["consumer_name"],
                data["meter_number"],
                data["address"],
                data["area"],
                data["connection_type"],
                data["meter_category"],
                now_str,
            ),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def update_household(record_id, data, db_path=DEFAULT_DB_PATH):
    """Update an existing household record while preventing duplicate IDs or meter numbers."""
    conn = get_connection(db_path)
    try:
        dup_hh = conn.execute(
            "SELECT id FROM households WHERE household_id = ? AND id != ?",
            (data["household_id"], record_id),
        ).fetchone()
        if dup_hh:
            raise ValueError(f"Household ID '{data['household_id']}' already belongs to another record.")

        dup_meter = conn.execute(
            "SELECT id FROM households WHERE meter_number = ? AND id != ?",
            (data["meter_number"], record_id),
        ).fetchone()
        if dup_meter:
            raise ValueError(f"Meter number '{data['meter_number']}' already belongs to another household.")

        conn.execute(
            """
            UPDATE households SET
                household_id = ?,
                consumer_name = ?,
                meter_number = ?,
                address = ?,
                area = ?,
                connection_type = ?,
                meter_category = ?
            WHERE id = ?
            """,
            (
                data["household_id"],
                data["consumer_name"],
                data["meter_number"],
                data["address"],
                data["area"],
                data["connection_type"],
                data["meter_category"],
                record_id,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def delete_household(record_id, db_path=DEFAULT_DB_PATH):
    """Delete a household and its associated readings/bills (cascade)."""
    conn = get_connection(db_path)
    try:
        conn.execute("DELETE FROM households WHERE id = ?", (record_id,))
        conn.commit()
    finally:
        conn.close()


def get_household_by_id(record_id, db_path=DEFAULT_DB_PATH):
    """Fetch one household by primary key."""
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT * FROM households WHERE id = ?", (record_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_all_households(search="", area="", connection_type="", db_path=DEFAULT_DB_PATH):
    """Fetch households with optional search (name/ID/meter) and area/connection filters."""
    conn = get_connection(db_path)
    try:
        query = """
            SELECT h.*,
                   COUNT(b.id) AS total_bills,
                   COALESCE(SUM(b.units_consumed), 0) AS total_units,
                   COALESCE(SUM(b.final_payable), 0) AS total_billed
            FROM households h
            LEFT JOIN electricity_bills b ON h.id = b.household_ref_id
            WHERE 1 = 1
        """
        params = []
        if search:
            like_val = f"%{search.strip()}%"
            query += " AND (h.consumer_name LIKE ? OR h.meter_number LIKE ? OR h.household_id LIKE ?)"
            params.extend([like_val, like_val, like_val])
        if area:
            query += " AND h.area = ?"
            params.append(area)
        if connection_type:
            query += " AND h.connection_type = ?"
            params.append(connection_type)

        query += " GROUP BY h.id ORDER BY h.household_id ASC"
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_distinct_areas(db_path=DEFAULT_DB_PATH):
    """Return sorted list of distinct household areas for filter dropdowns."""
    conn = get_connection(db_path)
    try:
        rows = conn.execute("SELECT DISTINCT area FROM households ORDER BY area ASC").fetchall()
        return [r["area"] for r in rows]
    finally:
        conn.close()


def get_latest_reading_for_household(household_ref_id, db_path=DEFAULT_DB_PATH):
    """Fetch the most recent current_reading for auto-filling next month's previous reading."""
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            """
            SELECT billing_month, current_reading
            FROM meter_readings
            WHERE household_ref_id = ?
            ORDER BY billing_month DESC
            LIMIT 1
            """,
            (household_ref_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def check_duplicate_billing_month(household_ref_id, billing_month, db_path=DEFAULT_DB_PATH):
    """Return True if a reading or bill already exists for this household and billing month."""
    conn = get_connection(db_path)
    try:
        existing = conn.execute(
            """
            SELECT id FROM meter_readings
            WHERE household_ref_id = ? AND billing_month = ?
            """,
            (household_ref_id, billing_month),
        ).fetchone()
        return existing is not None
    finally:
        conn.close()


def create_reading_and_bill(reading_data, payment_status="Unpaid", db_path=DEFAULT_DB_PATH):
    """
    Save a meter reading, compute progressive charges using current rules & slabs,
    generate a unique bill number, and store the bill + slab breakdown in SQLite.
    """
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rules = get_rules(db_path)
    slabs = get_slabs(db_path)

    conn = get_connection(db_path)
    try:
        household = conn.execute(
            "SELECT * FROM households WHERE id = ?",
            (reading_data["household_ref_id"],),
        ).fetchone()
        if not household:
            raise ValueError("Selected household does not exist.")

        dup = conn.execute(
            """
            SELECT id FROM meter_readings
            WHERE household_ref_id = ? AND billing_month = ?
            """,
            (reading_data["household_ref_id"], reading_data["billing_month"]),
        ).fetchone()
        if dup:
            raise ValueError(
                f"A meter reading and bill already exist for {household['household_id']} in {reading_data['billing_month']}."
            )

        consumption = round(
            float(reading_data["current_reading"]) - float(reading_data["previous_reading"]),
            2,
        )
        bill_calc = calculate_full_bill(
            consumption,
            slabs=slabs,
            rules=rules,
            is_late_payment=bool(reading_data.get("is_late_payment", False)),
        )

        # Insert meter reading
        reading_cur = conn.execute(
            """
            INSERT INTO meter_readings (
                household_ref_id, billing_month, previous_reading,
                current_reading, consumption_units, billing_date, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                reading_data["household_ref_id"],
                reading_data["billing_month"],
                reading_data["previous_reading"],
                reading_data["current_reading"],
                consumption,
                reading_data["billing_date"],
                now_str,
            ),
        )
        reading_id = reading_cur.lastrowid

        # Generate guaranteed-unique bill number
        next_seq = conn.execute(
            "SELECT COALESCE(MAX(id), 0) + 1 FROM electricity_bills"
        ).fetchone()[0]
        bill_number = generate_bill_number(
            reading_data["billing_month"], household["household_id"], next_seq
        )

        bill_cur = conn.execute(
            """
            INSERT INTO electricity_bills (
                bill_number, reading_id, household_ref_id, billing_month,
                previous_reading, current_reading, units_consumed,
                energy_charge, fixed_charge, electricity_duty,
                surcharge_amount, rebate_amount, late_penalty_amount,
                final_payable, payment_status, is_late_payment,
                billing_date, generated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                bill_number,
                reading_id,
                reading_data["household_ref_id"],
                reading_data["billing_month"],
                reading_data["previous_reading"],
                reading_data["current_reading"],
                bill_calc["units_consumed"],
                bill_calc["energy_charge"],
                bill_calc["fixed_charge"],
                bill_calc["electricity_duty"],
                bill_calc["surcharge_amount"],
                bill_calc["rebate_amount"],
                bill_calc["late_penalty_amount"],
                bill_calc["final_payable"],
                payment_status,
                1 if reading_data.get("is_late_payment") else 0,
                reading_data["billing_date"],
                now_str,
            ),
        )
        bill_id = bill_cur.lastrowid

        for idx, item in enumerate(bill_calc["slab_breakdown"], start=1):
            conn.execute(
                """
                INSERT INTO bill_slab_items (
                    bill_id, slab_order, slab_label, units_in_slab, rate_per_unit, slab_charge
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    bill_id,
                    idx,
                    item["label"],
                    item["units"],
                    item["rate"],
                    item["charge"],
                ),
            )

        conn.commit()
        return bill_id
    finally:
        conn.close()


def get_bill_by_id(bill_id, db_path=DEFAULT_DB_PATH):
    """Fetch a single electricity bill along with household details and slab breakdown."""
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            """
            SELECT b.*, h.household_id, h.consumer_name, h.meter_number,
                   h.address, h.area, h.connection_type, h.meter_category
            FROM electricity_bills b
            JOIN households h ON b.household_ref_id = h.id
            WHERE b.id = ?
            """,
            (bill_id,),
        ).fetchone()
        if not row:
            return None
        bill = dict(row)
        slab_rows = conn.execute(
            """
            SELECT slab_order, slab_label, units_in_slab, rate_per_unit, slab_charge
            FROM bill_slab_items
            WHERE bill_id = ?
            ORDER BY slab_order ASC
            """,
            (bill_id,),
        ).fetchall()
        bill["slab_items"] = [dict(s) for s in slab_rows]
        return bill
    finally:
        conn.close()


def get_all_bills(
    month="",
    search="",
    payment_status="",
    household_ref_id=None,
    sort_by="month_desc",
    db_path=DEFAULT_DB_PATH,
):
    """Fetch electricity bills joined with household details, supporting filtering and sorting."""
    conn = get_connection(db_path)
    try:
        query = """
            SELECT b.*, h.household_id, h.consumer_name, h.meter_number,
                   h.area, h.connection_type, h.meter_category
            FROM electricity_bills b
            JOIN households h ON b.household_ref_id = h.id
            WHERE 1 = 1
        """
        params = []
        if month:
            query += " AND b.billing_month = ?"
            params.append(month)
        if search:
            like_val = f"%{search.strip()}%"
            query += " AND (h.household_id LIKE ? OR h.consumer_name LIKE ? OR b.bill_number LIKE ? OR h.meter_number LIKE ?)"
            params.extend([like_val, like_val, like_val, like_val])
        if payment_status:
            query += " AND b.payment_status = ?"
            params.append(payment_status)
        if household_ref_id:
            query += " AND b.household_ref_id = ?"
            params.append(int(household_ref_id))

        sort_map = {
            "month_desc": "b.billing_month DESC, b.id DESC",
            "month_asc": "b.billing_month ASC, b.id ASC",
            "units_desc": "b.units_consumed DESC, b.billing_month DESC",
            "units_asc": "b.units_consumed ASC, b.billing_month DESC",
            "amount_desc": "b.final_payable DESC, b.billing_month DESC",
            "amount_asc": "b.final_payable ASC, b.billing_month DESC",
        }
        order_clause = sort_map.get(sort_by, "b.billing_month DESC, b.id DESC")
        query += f" ORDER BY {order_clause}"

        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_distinct_billing_months(db_path=DEFAULT_DB_PATH):
    """Return sorted billing months (newest first) present in bills."""
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT DISTINCT billing_month FROM electricity_bills ORDER BY billing_month DESC"
        ).fetchall()
        return [r["billing_month"] for r in rows]
    finally:
        conn.close()


def toggle_bill_payment_status(bill_id, db_path=DEFAULT_DB_PATH):
    """Toggle a bill's payment status between Paid and Unpaid."""
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT payment_status FROM electricity_bills WHERE id = ?",
            (bill_id,),
        ).fetchone()
        if not row:
            return None
        new_status = "Paid" if row["payment_status"] != "Paid" else "Unpaid"
        conn.execute(
            "UPDATE electricity_bills SET payment_status = ? WHERE id = ?",
            (new_status, bill_id),
        )
        conn.commit()
        return new_status
    finally:
        conn.close()


# Sample dataset definition (6 households, 22 monthly billing records)
SAMPLE_HOUSEHOLDS = (
    {
        "household_id": "HH-101",
        "consumer_name": "Aarav Sharma",
        "meter_number": "MTR-1001",
        "address": "14 Sunrise Residency, MG Road",
        "area": "Sector 14",
        "connection_type": "Domestic",
        "meter_category": "Single Phase",
    },
    {
        "household_id": "HH-102",
        "consumer_name": "Priya Nair",
        "meter_number": "MTR-1002",
        "address": "208 Maple Heights, Green Park",
        "area": "Green Park",
        "connection_type": "Domestic",
        "meter_category": "Three Phase",
    },
    {
        "household_id": "HH-103",
        "consumer_name": "Meera Patel",
        "meter_number": "MTR-1003",
        "address": "42 Lotus Villas, Lake View",
        "area": "Lake View",
        "connection_type": "Domestic",
        "meter_category": "Smart Digital",
    },
    {
        "household_id": "HH-104",
        "consumer_name": "Vikram Verma",
        "meter_number": "MTR-1004",
        "address": "77 Central Plaza, Market Road",
        "area": "Market Road",
        "connection_type": "Commercial",
        "meter_category": "Three Phase",
    },
    {
        "household_id": "HH-105",
        "consumer_name": "Rohan Kulkarni",
        "meter_number": "MTR-1005",
        "address": "Plot 9, Phase II Industrial Estate",
        "area": "Industrial Estate",
        "connection_type": "Small Industry",
        "meter_category": "Three Phase",
    },
    {
        "household_id": "HH-106",
        "consumer_name": "Ananya Iyer",
        "meter_number": "MTR-1006",
        "address": "Green Acres Farm, Riverdale",
        "area": "Riverdale",
        "connection_type": "Agricultural",
        "meter_category": "Single Phase",
    },
)

SAMPLE_BILLS = (
    # HH-101: Low/rebate months followed by unusual spike in 2026-09, then normalized
    ("HH-101", "2026-06", 1050, 1170, "2026-06-28", False, "Paid"),
    ("HH-101", "2026-07", 1170, 1300, "2026-07-28", False, "Paid"),
    ("HH-101", "2026-08", 1300, 1440, "2026-08-28", False, "Paid"),
    ("HH-101", "2026-09", 1440, 1760, "2026-09-28", False, "Paid"),
    ("HH-101", "2026-10", 1760, 1910, "2026-10-28", False, "Paid"),
    ("HH-101", "2026-11", 1910, 2035, "2026-11-25", False, "Unpaid"),
    # HH-102: Medium consumption (250 units example) + unusual spike in 2026-10
    ("HH-102", "2026-07", 2400, 2650, "2026-07-29", False, "Paid"),
    ("HH-102", "2026-08", 2650, 2920, "2026-08-29", False, "Paid"),
    ("HH-102", "2026-09", 2920, 3180, "2026-09-29", False, "Paid"),
    ("HH-102", "2026-10", 3180, 3640, "2026-10-29", False, "Paid"),
    ("HH-102", "2026-11", 3640, 3920, "2026-11-25", False, "Unpaid"),
    # HH-103: Zero consumption + low consumption (first slab + rebate)
    ("HH-103", "2026-08", 500, 500, "2026-08-27", False, "Paid"),
    ("HH-103", "2026-09", 500, 585, "2026-09-27", False, "Paid"),
    ("HH-103", "2026-10", 585, 680, "2026-10-27", False, "Paid"),
    ("HH-103", "2026-11", 680, 790, "2026-11-25", False, "Paid"),
    # HH-104: Commercial high consumption (>300 & >500 units, surcharge & late penalty)
    ("HH-104", "2026-09", 8100, 8580, "2026-09-30", True, "Paid"),
    ("HH-104", "2026-10", 8580, 9140, "2026-10-30", False, "Paid"),
    ("HH-104", "2026-11", 9140, 9760, "2026-11-25", False, "Unpaid"),
    # HH-105: Small industry with spike in 2026-11
    ("HH-105", "2026-10", 12000, 12310, "2026-10-30", False, "Paid"),
    ("HH-105", "2026-11", 12310, 12890, "2026-11-25", True, "Unpaid"),
    # HH-106: Agricultural steady low-medium consumption with rebate
    ("HH-106", "2026-10", 3100, 3240, "2026-10-28", False, "Paid"),
    ("HH-106", "2026-11", 3240, 3385, "2026-11-25", False, "Unpaid"),
)


def count_missing_sample_records(db_path=DEFAULT_DB_PATH):
    """Count how many sample households or sample bills are not yet loaded."""
    conn = get_connection(db_path)
    try:
        missing_hh = 0
        for hh in SAMPLE_HOUSEHOLDS:
            row = conn.execute(
                "SELECT id FROM households WHERE household_id = ?",
                (hh["household_id"],),
            ).fetchone()
            if not row:
                missing_hh += 1

        missing_bills = 0
        for hh_id, month, *_rest in SAMPLE_BILLS:
            row = conn.execute(
                """
                SELECT b.id FROM electricity_bills b
                JOIN households h ON b.household_ref_id = h.id
                WHERE h.household_id = ? AND b.billing_month = ?
                """,
                (hh_id, month),
            ).fetchone()
            if not row:
                missing_bills += 1
        return missing_hh, missing_bills
    finally:
        conn.close()


def load_sample_data(db_path=DEFAULT_DB_PATH):
    """
    Idempotently load sample households and 22 monthly billing records
    without creating duplicate households or duplicate billing months.
    Returns (added_households, added_bills).
    """
    added_hh = 0
    added_bills = 0

    conn = get_connection(db_path)
    hh_id_to_ref = {}
    try:
        for hh in SAMPLE_HOUSEHOLDS:
            existing = conn.execute(
                "SELECT id FROM households WHERE household_id = ?",
                (hh["household_id"],),
            ).fetchone()
            if existing:
                hh_id_to_ref[hh["household_id"]] = existing["id"]
            else:
                conn.close()
                new_id = add_household(hh, db_path=db_path)
                hh_id_to_ref[hh["household_id"]] = new_id
                added_hh += 1
                conn = get_connection(db_path)
    finally:
        conn.close()

    for hh_id, month, prev_r, curr_r, bill_date, is_late, status in SAMPLE_BILLS:
        ref_id = hh_id_to_ref.get(hh_id)
        if not ref_id:
            continue
        if check_duplicate_billing_month(ref_id, month, db_path=db_path):
            continue
        create_reading_and_bill(
            {
                "household_ref_id": ref_id,
                "billing_month": month,
                "previous_reading": float(prev_r),
                "current_reading": float(curr_r),
                "billing_date": bill_date,
                "is_late_payment": is_late,
            },
            payment_status=status,
            db_path=db_path,
        )
        added_bills += 1

    return added_hh, added_bills
