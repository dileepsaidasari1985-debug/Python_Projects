"""SQLite database operations for the Smart ATM Transaction & Banking Simulation.

Tables:
1. demo_accounts - Simulated student/demo account (no real banking info)
2. transactions  - Persistent ledger of successful and rejected ATM transactions
3. atm_settings  - Configurable withdrawal limits, denomination, and initial balance

All queries use parameterized SQL placeholders (?) for safety.
"""

from datetime import datetime
import os
import shutil
import sqlite3
import tempfile

from transaction_logic import (
    DEFAULT_ACCOUNT_TUPLE,
    DEFAULT_SETTINGS_TUPLE,
    execute_single_transaction,
    process_transaction_sequence,
)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BUNDLED_DB_PATH = os.path.join(BASE_DIR, "database", "atm.db")


def resolve_default_db_path():
    """Use database/atm.db locally; on read-only serverless hosts (e.g. Vercel), use temp dir."""
    db_dir = os.path.dirname(BUNDLED_DB_PATH)
    is_vercel = bool(os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV"))
    is_writable = os.path.isdir(db_dir) and os.access(db_dir, os.W_OK)

    if is_vercel or not is_writable:
        tmp_db = os.path.join(tempfile.gettempdir(), "atm.db")
        if not os.path.exists(tmp_db) and os.path.exists(BUNDLED_DB_PATH):
            shutil.copy2(BUNDLED_DB_PATH, tmp_db)
        return tmp_db
    return BUNDLED_DB_PATH


DEFAULT_DB_PATH = resolve_default_db_path()


def get_connection(db_path=None):
    """Open a SQLite connection with row dictionary access."""
    target_path = db_path or DEFAULT_DB_PATH
    parent_dir = os.path.dirname(target_path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path=None):
    """Automatically create tables and seed default demo account and ATM settings."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS demo_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_number TEXT NOT NULL UNIQUE,
                holder_name TEXT NOT NULL,
                initial_balance REAL NOT NULL,
                current_balance REAL NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT NOT NULL UNIQUE,
                account_number TEXT NOT NULL,
                transaction_type TEXT NOT NULL,
                amount REAL NOT NULL,
                balance_before REAL NOT NULL,
                balance_after REAL NOT NULL,
                status TEXT NOT NULL,
                rejection_reason TEXT NOT NULL DEFAULT '',
                description TEXT NOT NULL DEFAULT '',
                source TEXT NOT NULL DEFAULT 'SINGLE',
                created_at TEXT NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS atm_settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                max_per_transaction REAL NOT NULL,
                max_daily_withdrawal REAL NOT NULL,
                min_withdrawal REAL NOT NULL,
                withdrawal_denomination INTEGER NOT NULL,
                initial_demo_balance REAL NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Seed default ATM settings if missing (tuple unpacking)
        existing_settings = cursor.execute(
            "SELECT id FROM atm_settings WHERE id = 1"
        ).fetchone()
        if not existing_settings:
            max_txn, max_daily, min_wd, denom, init_bal = DEFAULT_SETTINGS_TUPLE
            cursor.execute(
                """
                INSERT INTO atm_settings (
                    id, max_per_transaction, max_daily_withdrawal,
                    min_withdrawal, withdrawal_denomination,
                    initial_demo_balance, updated_at
                )
                VALUES (1, ?, ?, ?, ?, ?, ?)
                """,
                (max_txn, max_daily, min_wd, denom, init_bal, now_str),
            )

        # Seed default simulated demo account if missing (tuple unpacking)
        acct_no, holder_name, acct_init_bal = DEFAULT_ACCOUNT_TUPLE
        existing_account = cursor.execute(
            "SELECT id FROM demo_accounts WHERE account_number = ?",
            (acct_no,),
        ).fetchone()
        if not existing_account:
            cursor.execute(
                """
                INSERT INTO demo_accounts (
                    account_number, holder_name, initial_balance,
                    current_balance, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (acct_no, holder_name, acct_init_bal, acct_init_bal, now_str, now_str),
            )

        conn.commit()
    finally:
        conn.close()


def get_atm_settings(db_path=None):
    """Fetch the active ATM simulation rules dictionary."""
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT * FROM atm_settings WHERE id = 1").fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_atm_settings(validated_settings, db_path=None):
    """Persist validated ATM rule settings."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection(db_path)
    try:
        conn.execute(
            """
            UPDATE atm_settings
            SET max_per_transaction = ?,
                max_daily_withdrawal = ?,
                min_withdrawal = ?,
                withdrawal_denomination = ?,
                initial_demo_balance = ?,
                updated_at = ?
            WHERE id = 1
            """,
            (
                validated_settings["max_per_transaction"],
                validated_settings["max_daily_withdrawal"],
                validated_settings["min_withdrawal"],
                validated_settings["withdrawal_denomination"],
                validated_settings["initial_demo_balance"],
                now_str,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_demo_account(account_number="DEMO1001", db_path=None):
    """Fetch a simulated demo account by account number."""
    clean_acct = str(account_number or "").strip().upper()
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM demo_accounts WHERE account_number = ?",
            (clean_acct,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_all_demo_accounts(db_path=None):
    """Return all simulated demo accounts."""
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM demo_accounts ORDER BY id ASC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_daily_withdrawn_total(account_number="DEMO1001", target_date=None, db_path=None):
    """Calculate total successful withdrawals made on target_date (default today)."""
    date_prefix = target_date or datetime.now().strftime("%Y-%m-%d")
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            """
            SELECT COALESCE(SUM(amount), 0.0) AS total_today
            FROM transactions
            WHERE account_number = ?
              AND transaction_type = 'WITHDRAWAL'
              AND status = 'SUCCESS'
              AND created_at LIKE ?
            """,
            (account_number, f"{date_prefix}%"),
        ).fetchone()
        return round(float(row["total_today"]), 2) if row else 0.0
    finally:
        conn.close()


def get_last_transaction_date(account_number="DEMO1001", db_path=None):
    """Return timestamp of the latest transaction for the account, or None."""
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            """
            SELECT created_at FROM transactions
            WHERE account_number = ?
            ORDER BY id DESC LIMIT 1
            """,
            (account_number,),
        ).fetchone()
        return row["created_at"] if row else None
    finally:
        conn.close()


def _insert_transaction_row(cursor, account_number, outcome):
    """Insert a single transaction outcome row using an open DB cursor."""
    cursor.execute(
        """
        INSERT INTO transactions (
            transaction_id, account_number, transaction_type,
            amount, balance_before, balance_after, status,
            rejection_reason, description, source, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            outcome["transaction_id"],
            account_number,
            outcome["transaction_type"],
            outcome["amount"],
            outcome["balance_before"],
            outcome["balance_after"],
            outcome["status"],
            outcome["rejection_reason"],
            outcome["description"],
            outcome["source"],
            outcome["created_at"],
        ),
    )


def record_single_transaction(
    account_number, txn_type, raw_amount, description="", source="SINGLE", db_path=None
):
    """Process one transaction via Python engine and persist both ledger & balance."""
    clean_acct = str(account_number or "").strip().upper()
    conn = get_connection(db_path)
    try:
        account_row = conn.execute(
            "SELECT * FROM demo_accounts WHERE account_number = ?",
            (clean_acct,),
        ).fetchone()
        if not account_row:
            return (False, None, f"Simulated account '{clean_acct}' not found.")

        settings_row = conn.execute("SELECT * FROM atm_settings WHERE id = 1").fetchone()
        settings = dict(settings_row)

        today_prefix = datetime.now().strftime("%Y-%m-%d")
        daily_row = conn.execute(
            """
            SELECT COALESCE(SUM(amount), 0.0) AS total_today
            FROM transactions
            WHERE account_number = ?
              AND transaction_type = 'WITHDRAWAL'
              AND status = 'SUCCESS'
              AND created_at LIKE ?
            """,
            (clean_acct, f"{today_prefix}%"),
        ).fetchone()
        daily_withdrawn = round(float(daily_row["total_today"]), 2)

        outcome = execute_single_transaction(
            txn_type=txn_type,
            raw_amount=raw_amount,
            current_balance=account_row["current_balance"],
            daily_withdrawn=daily_withdrawn,
            settings=settings,
            description=description,
            source=source,
        )

        cursor = conn.cursor()
        _insert_transaction_row(cursor, clean_acct, outcome)

        if outcome["status"] == "SUCCESS":
            cursor.execute(
                """
                UPDATE demo_accounts
                SET current_balance = ?, updated_at = ?
                WHERE account_number = ?
                """,
                (outcome["balance_after"], outcome["created_at"], clean_acct),
            )

        conn.commit()
        return (outcome["status"] == "SUCCESS", outcome, outcome["rejection_reason"])
    finally:
        conn.close()


def record_transaction_sequence(
    account_number, sequence_items, commit_to_db=True, db_path=None
):
    """Run a multi-transaction sequence through Python engine and optionally persist to SQLite."""
    clean_acct = str(account_number or "").strip().upper()
    conn = get_connection(db_path)
    try:
        account_row = conn.execute(
            "SELECT * FROM demo_accounts WHERE account_number = ?",
            (clean_acct,),
        ).fetchone()
        if not account_row:
            return (False, None, f"Simulated account '{clean_acct}' not found.")

        settings_row = conn.execute("SELECT * FROM atm_settings WHERE id = 1").fetchone()
        settings = dict(settings_row)

        today_prefix = datetime.now().strftime("%Y-%m-%d")
        daily_row = conn.execute(
            """
            SELECT COALESCE(SUM(amount), 0.0) AS total_today
            FROM transactions
            WHERE account_number = ?
              AND transaction_type = 'WITHDRAWAL'
              AND status = 'SUCCESS'
              AND created_at LIKE ?
            """,
            (clean_acct, f"{today_prefix}%"),
        ).fetchone()
        daily_withdrawn = round(float(daily_row["total_today"]), 2)

        simulation = process_transaction_sequence(
            sequence_items=sequence_items,
            starting_balance=account_row["current_balance"],
            starting_daily_withdrawn=daily_withdrawn,
            settings=settings,
        )

        if commit_to_db and simulation["results"]:
            cursor = conn.cursor()
            for outcome in simulation["results"]:
                _insert_transaction_row(cursor, clean_acct, outcome)

            final_balance = simulation["summary"]["closing_balance"]
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                """
                UPDATE demo_accounts
                SET current_balance = ?, updated_at = ?
                WHERE account_number = ?
                """,
                (final_balance, now_str, clean_acct),
            )
            conn.commit()

        return (True, simulation, "")
    finally:
        conn.close()


def get_transactions(
    account_number="DEMO1001",
    search_id="",
    txn_type="",
    status="",
    date_filter="",
    sort_by="newest",
    limit=None,
    db_path=None,
):
    """Query transactions with parameterized filtering and sorting."""
    query = "SELECT * FROM transactions WHERE account_number = ?"
    params = [account_number]

    if search_id:
        clean_search = f"%{search_id.strip()}%"
        query += " AND (transaction_id LIKE ? OR description LIKE ?)"
        params.extend([clean_search, clean_search])

    if txn_type in ("DEPOSIT", "WITHDRAWAL"):
        query += " AND transaction_type = ?"
        params.append(txn_type)

    if status in ("SUCCESS", "REJECTED"):
        query += " AND status = ?"
        params.append(status)

    if date_filter:
        query += " AND created_at LIKE ?"
        params.append(f"{date_filter.strip()}%")

    sort_clauses = {
        "newest": "ORDER BY id DESC",
        "oldest": "ORDER BY id ASC",
        "amount_desc": "ORDER BY amount DESC, id DESC",
        "amount_asc": "ORDER BY amount ASC, id DESC",
    }
    query += " " + sort_clauses.get(sort_by, "ORDER BY id DESC")

    if limit is not None and int(limit) > 0:
        query += " LIMIT ?"
        params.append(int(limit))

    conn = get_connection(db_path)
    try:
        rows = conn.execute(query, tuple(params)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_transaction_by_id(transaction_id, db_path=None):
    """Fetch a single transaction record by its unique transaction ID."""
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM transactions WHERE transaction_id = ?",
            (transaction_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def reset_demo_account(account_number="DEMO1001", db_path=None):
    """Reset the simulated demo account balance to initial_demo_balance and clear transactions."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection(db_path)
    try:
        settings_row = conn.execute("SELECT * FROM atm_settings WHERE id = 1").fetchone()
        init_bal = (
            float(settings_row["initial_demo_balance"])
            if settings_row
            else DEFAULT_ACCOUNT_TUPLE[2]
        )

        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM transactions WHERE account_number = ?",
            (account_number,),
        )
        cursor.execute(
            """
            UPDATE demo_accounts
            SET initial_balance = ?, current_balance = ?, updated_at = ?
            WHERE account_number = ?
            """,
            (init_bal, init_bal, now_str, account_number),
        )
        conn.commit()
        return init_bal
    finally:
        conn.close()
