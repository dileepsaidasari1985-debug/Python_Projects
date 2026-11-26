"""Smart ATM Transaction and Banking Simulation System (Case Study #13).

Flask web application providing:
- Simulated Demo Account Dashboard
- Interactive ATM Menu Terminal
- Cash Deposit & Cash Withdrawal with Configurable Limits
- Balance Inquiry
- ATM Transaction Sequence Simulator (Loop + Tuple Unpacking)
- Searchable & Filterable Transaction History
- Financial Reports & Built-in Python CSV Export
- Configurable ATM Settings & Safe Account Reset
"""

import csv
from datetime import datetime
import hashlib
import hmac
import io
import os
import secrets

from flask import (
    Flask,
    Response,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from database import (
    DEFAULT_DB_PATH,
    get_atm_settings,
    get_daily_withdrawn_total,
    get_demo_account,
    get_last_transaction_date,
    get_transaction_by_id,
    get_transactions,
    init_db,
    record_single_transaction,
    record_transaction_sequence,
    reset_demo_account,
    update_atm_settings,
)
from transaction_logic import (
    DEPOSIT_PRESETS,
    EXAMPLE_SEQUENCE_TUPLES,
    WITHDRAWAL_PRESETS,
    calculate_transaction_summary,
    format_inr,
    generate_atm_receipt_pattern,
    generate_summary_pattern,
    parse_sequence_text,
    validate_atm_settings,
)


def create_app(db_path=None):
    """Application factory so tests can inject an isolated SQLite database path."""
    app = Flask(__name__)
    deployment_seed = os.environ.get("VERCEL_DEPLOYMENT_ID") or os.environ.get("VERCEL_URL")
    app.config["SECRET_KEY"] = (
        os.environ.get("FLASK_SECRET_KEY")
        or (hashlib.sha256(deployment_seed.encode("utf-8")).hexdigest() if deployment_seed else None)
        or secrets.token_hex(32)
    )
    app.config["DB_PATH"] = db_path or DEFAULT_DB_PATH

    # Initialize SQLite database and default demo account on startup
    init_db(app.config["DB_PATH"])

    # -----------------------------------------------------------------------
    # Jinja Filters & Global Template Helpers
    # -----------------------------------------------------------------------

    @app.template_filter("inr")
    def inr_filter(value):
        return format_inr(value)

    def get_csrf_token():
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_hex(24)
        return session["csrf_token"]

    app.jinja_env.globals["csrf_token"] = get_csrf_token

    @app.before_request
    def verify_csrf():
        if request.method == "POST":
            expected = session.get("csrf_token", "")
            submitted = request.form.get("csrf_token", "")
            if not expected or not hmac.compare_digest(expected, submitted):
                abort(400, description="Invalid or missing CSRF security token.")

    @app.context_processor
    def inject_atm_context():
        db = app.config["DB_PATH"]
        account = get_demo_account("DEMO1001", db_path=db)
        settings = get_atm_settings(db_path=db)
        daily_withdrawn = get_daily_withdrawn_total("DEMO1001", db_path=db)
        max_daily = float(settings["max_daily_withdrawal"]) if settings else 25000.0
        remaining_daily = max(0.0, round(max_daily - daily_withdrawn, 2))
        return {
            "active_account": account,
            "atm_settings": settings,
            "daily_withdrawn": daily_withdrawn,
            "remaining_daily": remaining_daily,
            "current_endpoint": request.endpoint or "",
        }

    # -----------------------------------------------------------------------
    # Routes
    # -----------------------------------------------------------------------

    @app.route("/")
    def dashboard():
        db = app.config["DB_PATH"]
        account = get_demo_account("DEMO1001", db_path=db)
        settings = get_atm_settings(db_path=db)
        all_txns = get_transactions("DEMO1001", sort_by="newest", db_path=db)
        summary = calculate_transaction_summary(
            all_txns,
            opening_balance=account["initial_balance"],
            current_balance=account["current_balance"],
        )
        recent_txns = all_txns[:8]
        daily_withdrawn = get_daily_withdrawn_total("DEMO1001", db_path=db)
        max_daily = float(settings["max_daily_withdrawal"])
        daily_pct = (
            min(100.0, round((daily_withdrawn / max_daily) * 100, 1))
            if max_daily > 0
            else 0.0
        )
        return render_template(
            "dashboard.html",
            account=account,
            summary=summary,
            recent_transactions=recent_txns,
            daily_pct=daily_pct,
        )

    @app.route("/atm")
    def atm_menu():
        db = app.config["DB_PATH"]
        account = get_demo_account("DEMO1001", db_path=db)
        all_txns = get_transactions("DEMO1001", sort_by="newest", db_path=db)
        summary = calculate_transaction_summary(
            all_txns,
            opening_balance=account["initial_balance"],
            current_balance=account["current_balance"],
        )
        exited = request.args.get("exit") == "1"
        last_txn_date = get_last_transaction_date("DEMO1001", db_path=db)
        return render_template(
            "atm_menu.html",
            account=account,
            summary=summary,
            exited=exited,
            last_txn_date=last_txn_date,
        )

    @app.route("/deposit", methods=["GET", "POST"])
    def deposit():
        db = app.config["DB_PATH"]
        account = get_demo_account("DEMO1001", db_path=db)
        outcome = None
        receipt_text = ""
        form_data = {
            "account_number": account["account_number"],
            "amount": "",
            "description": "",
        }

        if request.method == "POST":
            acct_num = request.form.get("account_number", "").strip().upper()
            raw_amt = request.form.get("amount", "").strip()
            desc = request.form.get("description", "").strip()
            form_data = {
                "account_number": acct_num,
                "amount": raw_amt,
                "description": desc,
            }

            is_ok, outcome, err_msg = record_single_transaction(
                account_number=acct_num,
                txn_type="DEPOSIT",
                raw_amount=raw_amt,
                description=desc,
                source="SINGLE",
                db_path=db,
            )

            account = get_demo_account("DEMO1001", db_path=db)
            if outcome is not None:
                receipt_text = generate_atm_receipt_pattern(account, outcome)

            if is_ok:
                flash(
                    f"Deposit successful! {format_inr(outcome['amount'])} credited. "
                    f"New balance: {format_inr(outcome['balance_after'])} (ID: {outcome['transaction_id']}).",
                    "success",
                )
            else:
                flash(f"Deposit rejected: {err_msg}", "error")

        return render_template(
            "deposit.html",
            account=account,
            presets=DEPOSIT_PRESETS,
            outcome=outcome,
            receipt_text=receipt_text,
            form_data=form_data,
        )

    @app.route("/withdrawal", methods=["GET", "POST"])
    def withdrawal():
        db = app.config["DB_PATH"]
        account = get_demo_account("DEMO1001", db_path=db)
        settings = get_atm_settings(db_path=db)
        outcome = None
        receipt_text = ""
        form_data = {
            "account_number": account["account_number"],
            "amount": "",
            "description": "",
        }

        if request.method == "POST":
            acct_num = request.form.get("account_number", "").strip().upper()
            raw_amt = request.form.get("amount", "").strip()
            desc = request.form.get("description", "").strip()
            form_data = {
                "account_number": acct_num,
                "amount": raw_amt,
                "description": desc,
            }

            is_ok, outcome, err_msg = record_single_transaction(
                account_number=acct_num,
                txn_type="WITHDRAWAL",
                raw_amount=raw_amt,
                description=desc,
                source="SINGLE",
                db_path=db,
            )

            account = get_demo_account("DEMO1001", db_path=db)
            if outcome is not None:
                receipt_text = generate_atm_receipt_pattern(account, outcome)

            if is_ok:
                flash(
                    f"Withdrawal successful! {format_inr(outcome['amount'])} dispensed. "
                    f"Remaining balance: {format_inr(outcome['balance_after'])} (ID: {outcome['transaction_id']}).",
                    "success",
                )
            else:
                flash(f"Withdrawal rejected: {err_msg}", "error")

        return render_template(
            "withdrawal.html",
            account=account,
            settings=settings,
            presets=WITHDRAWAL_PRESETS,
            outcome=outcome,
            receipt_text=receipt_text,
            form_data=form_data,
        )

    @app.route("/balance")
    def balance_inquiry():
        db = app.config["DB_PATH"]
        account = get_demo_account("DEMO1001", db_path=db)
        all_txns = get_transactions("DEMO1001", sort_by="newest", db_path=db)
        summary = calculate_transaction_summary(
            all_txns,
            opening_balance=account["initial_balance"],
            current_balance=account["current_balance"],
        )
        last_txn_date = get_last_transaction_date("DEMO1001", db_path=db)
        return render_template(
            "balance.html",
            account=account,
            summary=summary,
            last_txn_date=last_txn_date,
        )

    @app.route("/sequence", methods=["GET", "POST"])
    def transaction_sequence():
        db = app.config["DB_PATH"]
        account = get_demo_account("DEMO1001", db_path=db)
        simulation = None
        commit_to_db = True
        input_mode = "builder"

        # Default rows pre-populated with Case Study #13 example sequence
        builder_rows = [
            {"type": t, "amount": a, "description": d}
            for t, a, d in EXAMPLE_SEQUENCE_TUPLES
        ]
        sequence_text = "\n".join(
            f"{t} {a} | {d}" for t, a, d in EXAMPLE_SEQUENCE_TUPLES
        )

        if request.method == "POST":
            input_mode = request.form.get("input_mode", "builder")
            commit_to_db = request.form.get("commit_to_db") == "on"

            if input_mode == "text":
                sequence_text = request.form.get("sequence_text", "")
                sequence_items = parse_sequence_text(sequence_text)
                if sequence_items:
                    builder_rows = [
                        {"type": t, "amount": a, "description": d}
                        for t, a, d in sequence_items
                    ]
            else:
                types = request.form.getlist("txn_type[]")
                amounts = request.form.getlist("amount[]")
                descriptions = request.form.getlist("description[]")
                sequence_items = []
                new_builder_rows = []

                for idx in range(max(len(types), len(amounts))):
                    t_val = types[idx] if idx < len(types) else "DEPOSIT"
                    a_val = amounts[idx].strip() if idx < len(amounts) else ""
                    d_val = descriptions[idx].strip() if idx < len(descriptions) else ""
                    if not a_val and not d_val:
                        continue
                    sequence_items.append((t_val, a_val, d_val))
                    new_builder_rows.append(
                        {"type": t_val, "amount": a_val, "description": d_val}
                    )

                if new_builder_rows:
                    builder_rows = new_builder_rows
                    sequence_text = "\n".join(
                        f"{r['type']} {r['amount']}" + (f" | {r['description']}" if r["description"] else "")
                        for r in builder_rows
                    )

            if not sequence_items:
                flash("Please add at least one transaction to simulate.", "error")
            else:
                ok, simulation, err = record_transaction_sequence(
                    account_number="DEMO1001",
                    sequence_items=sequence_items,
                    commit_to_db=commit_to_db,
                    db_path=db,
                )
                account = get_demo_account("DEMO1001", db_path=db)
                if ok:
                    mode_label = "saved to SQLite" if commit_to_db else "previewed (not saved)"
                    s = simulation["summary"]
                    flash(
                        f"Sequence processed ({s['total_attempted']} steps, {mode_label}): "
                        f"{s['success_count']} succeeded, {s['rejected_count']} rejected. "
                        f"Closing balance: {format_inr(s['closing_balance'])}.",
                        "success" if s["rejected_count"] == 0 else "info",
                    )
                else:
                    flash(err or "Unable to process transaction sequence.", "error")

        return render_template(
            "transaction_sequence.html",
            account=account,
            builder_rows=builder_rows,
            sequence_text=sequence_text,
            input_mode=input_mode,
            commit_to_db=commit_to_db,
            simulation=simulation,
            example_tuples=EXAMPLE_SEQUENCE_TUPLES,
        )

    @app.route("/simulate-sample", methods=["POST"])
    def simulate_sample():
        """Run the Case Study #13 sample sequence directly from Dashboard."""
        db = app.config["DB_PATH"]
        ok, simulation, err = record_transaction_sequence(
            account_number="DEMO1001",
            sequence_items=EXAMPLE_SEQUENCE_TUPLES,
            commit_to_db=True,
            db_path=db,
        )
        if ok:
            s = simulation["summary"]
            flash(
                f"Sample ATM sequence executed via Python engine: {s['success_count']} successful, "
                f"{s['rejected_count']} rejected. Current balance: {format_inr(s['closing_balance'])}.",
                "success",
            )
        else:
            flash(err or "Could not run sample sequence.", "error")
        return redirect(url_for("dashboard"))

    @app.route("/history")
    def transaction_history():
        db = app.config["DB_PATH"]
        search_id = request.args.get("q", "").strip()
        txn_type = request.args.get("type", "").strip().upper()
        status = request.args.get("status", "").strip().upper()
        date_filter = request.args.get("date", "").strip()
        sort_by = request.args.get("sort", "newest").strip()

        transactions = get_transactions(
            account_number="DEMO1001",
            search_id=search_id,
            txn_type=txn_type,
            status=status,
            date_filter=date_filter,
            sort_by=sort_by,
            db_path=db,
        )

        return render_template(
            "transaction_history.html",
            transactions=transactions,
            filters={
                "q": search_id,
                "type": txn_type,
                "status": status,
                "date": date_filter,
                "sort": sort_by,
            },
        )

    @app.route("/transaction/<transaction_id>")
    def transaction_details(transaction_id):
        db = app.config["DB_PATH"]
        txn = get_transaction_by_id(transaction_id, db_path=db)
        if not txn:
            abort(404, description="Transaction not found.")
        account = get_demo_account(txn["account_number"], db_path=db)
        receipt_text = generate_atm_receipt_pattern(account, txn)
        return render_template(
            "transaction_details.html",
            txn=txn,
            account=account,
            receipt_text=receipt_text,
        )

    @app.route("/reports")
    def reports():
        db = app.config["DB_PATH"]
        account = get_demo_account("DEMO1001", db_path=db)
        all_txns = get_transactions("DEMO1001", sort_by="newest", db_path=db)
        summary = calculate_transaction_summary(
            all_txns,
            opening_balance=account["initial_balance"],
            current_balance=account["current_balance"],
        )
        summary_pattern = generate_summary_pattern(account, summary)
        return render_template(
            "reports.html",
            account=account,
            summary=summary,
            summary_pattern=summary_pattern,
            transactions=all_txns,
        )

    @app.route("/reports/export-csv")
    def export_csv():
        """Export transaction records using Python's built-in csv module."""
        db = app.config["DB_PATH"]
        search_id = request.args.get("q", "").strip()
        txn_type = request.args.get("type", "").strip().upper()
        status = request.args.get("status", "").strip().upper()
        date_filter = request.args.get("date", "").strip()
        sort_by = request.args.get("sort", "newest").strip()

        transactions = get_transactions(
            account_number="DEMO1001",
            search_id=search_id,
            txn_type=txn_type,
            status=status,
            date_filter=date_filter,
            sort_by=sort_by,
            db_path=db,
        )

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "Transaction ID",
                "Account Number",
                "Date & Time",
                "Transaction Type",
                "Amount (INR)",
                "Balance Before (INR)",
                "Balance After (INR)",
                "Status",
                "Rejection Reason",
                "Description",
                "Source",
            ]
        )

        for txn in transactions:
            writer.writerow(
                [
                    txn["transaction_id"],
                    txn["account_number"],
                    txn["created_at"],
                    txn["transaction_type"],
                    f"{float(txn['amount']):.2f}",
                    f"{float(txn['balance_before']):.2f}",
                    f"{float(txn['balance_after']):.2f}",
                    txn["status"],
                    txn["rejection_reason"],
                    txn["description"],
                    txn["source"],
                ]
            )

        csv_content = output.getvalue()
        filename = f"atm_transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return Response(
            csv_content,
            mimetype="text/csv; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    @app.route("/settings", methods=["GET", "POST"])
    def settings():
        db = app.config["DB_PATH"]
        current_settings = get_atm_settings(db_path=db)
        account = get_demo_account("DEMO1001", db_path=db)
        errors = []

        if request.method == "POST":
            ok, validated, errors = validate_atm_settings(
                raw_max_per_txn=request.form.get("max_per_transaction", ""),
                raw_max_daily=request.form.get("max_daily_withdrawal", ""),
                raw_min_wd=request.form.get("min_withdrawal", ""),
                raw_denom=request.form.get("withdrawal_denomination", ""),
                raw_initial_balance=request.form.get("initial_demo_balance", ""),
            )
            if ok:
                update_atm_settings(validated, db_path=db)
                current_settings = get_atm_settings(db_path=db)
                flash(
                    "ATM rules updated successfully! All new withdrawals and sequences will enforce these limits.",
                    "success",
                )
            else:
                for msg in errors:
                    flash(msg, "error")

        return render_template(
            "settings.html",
            settings=current_settings,
            account=account,
            errors=errors,
        )

    @app.route("/settings/reset", methods=["POST"])
    def reset_account():
        db = app.config["DB_PATH"]
        restored_balance = reset_demo_account("DEMO1001", db_path=db)
        flash(
            f"Demo account DEMO1001 reset cleanly. All transactions cleared and balance restored to {format_inr(restored_balance)}.",
            "info",
        )
        return redirect(url_for("dashboard"))

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="127.0.0.1", port=port)
