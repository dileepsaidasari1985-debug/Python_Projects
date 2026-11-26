"""SQLite Persistence Layer for Password Policy Validation Engine (Case Study #29)."""

import os
import shutil
import sqlite3

from password_logic import DEFAULT_POLICY, SAMPLE_PASSWORD_TUPLES, evaluate_password

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "database", "password_policy.db")


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
            CREATE TABLE IF NOT EXISTS policy_settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                min_length INTEGER NOT NULL,
                min_upper INTEGER NOT NULL,
                min_lower INTEGER NOT NULL,
                min_digits INTEGER NOT NULL,
                min_special INTEGER NOT NULL,
                max_consecutive_repeat INTEGER NOT NULL,
                disallow_spaces INTEGER NOT NULL,
                prohibited_csv TEXT NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS validation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sample_label TEXT NOT NULL,
                username TEXT NOT NULL,
                masked_preview TEXT NOT NULL,
                pw_length INTEGER NOT NULL,
                verdict TEXT NOT NULL,
                score INTEGER NOT NULL,
                strength_label TEXT NOT NULL,
                failed_reasons TEXT NOT NULL,
                evaluated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            )
        """)
        conn.commit()
        if seed_if_empty:
            if cur.execute("SELECT COUNT(*) FROM policy_settings").fetchone()[0] == 0:
                load_sample_data(db_path)
    finally:
        conn.close()


def load_sample_data(db_path=None):
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT OR IGNORE INTO policy_settings
            (id, min_length, min_upper, min_lower, min_digits, min_special, max_consecutive_repeat, disallow_spaces, prohibited_csv)
            VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                DEFAULT_POLICY["min_length"],
                DEFAULT_POLICY["min_upper"],
                DEFAULT_POLICY["min_lower"],
                DEFAULT_POLICY["min_digits"],
                DEFAULT_POLICY["min_special"],
                DEFAULT_POLICY["max_consecutive_repeat"],
                DEFAULT_POLICY["disallow_spaces"],
                DEFAULT_POLICY["prohibited_csv"],
            ),
        )
        if cur.execute("SELECT COUNT(*) FROM validation_logs").fetchone()[0] == 0:
            for label, pw, user in SAMPLE_PASSWORD_TUPLES:
                res = evaluate_password(pw, user, DEFAULT_POLICY)
                reasons = " | ".join(res["failed_explanations"]) if res["failed_explanations"] else "All rules satisfied."
                cur.execute(
                    """
                    INSERT INTO validation_logs
                    (sample_label, username, masked_preview, pw_length, verdict, score, strength_label, failed_reasons)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (label, user, res["masked_password"], res["length"], res["verdict"], res["score"], res["strength_label"], reasons),
                )
        conn.commit()
    finally:
        conn.close()


def get_policy(db_path=None):
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT * FROM policy_settings WHERE id = 1").fetchone()
        return dict(row) if row else dict(DEFAULT_POLICY)
    finally:
        conn.close()


def update_policy(cleaned, db_path=None):
    conn = get_connection(db_path)
    try:
        conn.execute(
            """
            UPDATE policy_settings
            SET min_length = ?, min_upper = ?, min_lower = ?, min_digits = ?, min_special = ?,
                max_consecutive_repeat = ?, disallow_spaces = ?, prohibited_csv = ?
            WHERE id = 1
            """,
            (
                cleaned["min_length"],
                cleaned["min_upper"],
                cleaned["min_lower"],
                cleaned["min_digits"],
                cleaned["min_special"],
                cleaned["max_consecutive_repeat"],
                cleaned["disallow_spaces"],
                cleaned["prohibited_csv"],
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_logs(db_path=None):
    conn = get_connection(db_path)
    try:
        return [dict(r) for r in conn.execute("SELECT * FROM validation_logs ORDER BY id DESC").fetchall()]
    finally:
        conn.close()


def add_log(sample_label, username, eval_res, db_path=None):
    conn = get_connection(db_path)
    try:
        reasons = " | ".join(eval_res["failed_explanations"]) if eval_res["failed_explanations"] else "All rules satisfied."
        conn.execute(
            """
            INSERT INTO validation_logs
            (sample_label, username, masked_preview, pw_length, verdict, score, strength_label, failed_reasons)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (sample_label, username, eval_res["masked_password"], eval_res["length"], eval_res["verdict"], eval_res["score"], eval_res["strength_label"], reasons),
        )
        conn.commit()
    finally:
        conn.close()
