"""
Progressive Electricity Billing & Monthly Consumption Analysis System
-------------------------------------------------------------------
Main Flask web application serving the dashboard, household registration and
management, meter reading calculator, progressive bill generator, billing history,
monthly comparisons, rule-based unusual consumption detection, configurable
tariff rules, and CSV/print reports.
"""

import csv
import io
import os
import secrets
from datetime import date

from flask import (
    Flask,
    Response,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from billing_logic import (
    CONNECTION_TYPES,
    METER_CATEGORIES,
    PAYMENT_STATUSES,
    REBATE_MODES,
    analyze_monthly_consumption,
    calculate_full_bill,
    detect_unusual_consumption,
    format_inr,
    format_month_label,
    generate_text_pattern_summary,
    validate_household_data,
    validate_meter_reading_data,
    validate_rules_and_slabs,
)
from database import (
    DEFAULT_DB_PATH,
    add_household,
    check_duplicate_billing_month,
    count_missing_sample_records,
    create_reading_and_bill,
    delete_household,
    get_all_bills,
    get_all_households,
    get_bill_by_id,
    get_distinct_areas,
    get_distinct_billing_months,
    get_household_by_id,
    get_latest_reading_for_household,
    get_rules,
    get_slabs,
    init_db,
    load_sample_data,
    reset_rules_to_default,
    toggle_bill_payment_status,
    update_household,
    update_rules_and_slabs,
)


def create_app(db_path=None, seed_if_empty=True):
    """Create and configure the Flask application instance."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, "templates"),
        static_folder=os.path.join(base_dir, "static"),
    )

    # Read secret key from environment or generate a secure runtime key
    app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)
    app.config["DB_PATH"] = db_path or DEFAULT_DB_PATH
    app.config["SEED_IF_EMPTY"] = seed_if_empty

    # Automatically create SQLite database, tables, and sample data on startup
    init_db(app.config["DB_PATH"], seed_if_empty=seed_if_empty)

    @app.before_request
    def ensure_db_exists():
        """Ensure SQLite database exists before handling requests."""
        if not os.path.exists(app.config["DB_PATH"]):
            init_db(app.config["DB_PATH"], seed_if_empty=app.config["SEED_IF_EMPTY"])

    def get_csrf_token():
        """Return a stable CSRF token stored in session and double-submit cookie."""
        cached = getattr(g, "_csrf_token", None)
        if cached:
            return cached
        token = request.cookies.get("csrf_cookie") or session.get("csrf_token")
        if not token:
            token = secrets.token_hex(24)
        session["csrf_token"] = token
        g._csrf_token = token
        return token

    @app.after_request
    def attach_csrf_cookie(response):
        """Set CSRF double-submit cookie on responses if not yet present."""
        token = getattr(g, "_csrf_token", None)
        if token and not request.cookies.get("csrf_cookie"):
            response.set_cookie(
                "csrf_cookie",
                token,
                httponly=True,
                samesite="Lax",
            )
        return response

    def verify_csrf():
        """Verify CSRF token on mutating POST requests."""
        submitted = request.form.get("csrf_token", "")
        cookie_token = request.cookies.get("csrf_cookie", "")
        session_token = session.get("csrf_token", "")
        if not submitted:
            abort(400, description="Missing CSRF token.")
        if not (
            (cookie_token and secrets.compare_digest(submitted, cookie_token))
            or (session_token and secrets.compare_digest(submitted, session_token))
        ):
            abort(400, description="Invalid CSRF token.")

    @app.context_processor
    def inject_globals():
        """Inject utility helpers, company name, and active page context into templates."""
        active_rules = get_rules(app.config["DB_PATH"])
        return {
            "csrf_token": get_csrf_token,
            "format_inr": format_inr,
            "format_month_label": format_month_label,
            "company_name": active_rules.get(
                "company_name", "VoltGrid Municipal Power Utility"
            ),
            "connection_types": CONNECTION_TYPES,
            "meter_categories": METER_CATEGORIES,
            "payment_statuses": PAYMENT_STATUSES,
            "rebate_modes": REBATE_MODES,
        }

    # ------------------------------------------------------------------
    # A. Dashboard
    # ------------------------------------------------------------------
    @app.route("/")
    def dashboard():
        db = app.config["DB_PATH"]
        households = get_all_households(db_path=db)
        bills = get_all_bills(sort_by="month_desc", db_path=db)
        rules = get_rules(db)

        analysis = analyze_monthly_consumption(bills)
        warnings = detect_unusual_consumption(bills, rules)
        missing_hh, missing_bills = count_missing_sample_records(db)

        # Determine current (latest) billing month from actual database records
        if analysis["monthly_rows"]:
            latest_month_row = analysis["monthly_rows"][-1]
            current_month_label = latest_month_row["month_label"]
            current_month_units = latest_month_row["units_consumed"]
            current_month_charges = latest_month_row["total_bill"]
        else:
            current_month_label = "No Data"
            current_month_units = 0.0
            current_month_charges = 0.0

        total_surcharges = round(sum(b["surcharge_amount"] for b in bills), 2)
        total_rebates = round(sum(b["rebate_amount"] for b in bills), 2)

        stats = {
            "total_households": len(households),
            "total_bills": len(bills),
            "current_month_label": current_month_label,
            "current_month_units": current_month_units,
            "current_month_charges": current_month_charges,
            "avg_monthly_consumption": analysis["avg_consumption"],
            "highest_month": analysis["highest_month"],
            "lowest_month": analysis["lowest_month"],
            "total_surcharges": total_surcharges,
            "total_rebates": total_rebates,
            "warning_count": len(warnings),
        }

        chart_payload = {
            "labels": [row["month_label"] for row in analysis["monthly_rows"]],
            "units": [row["units_consumed"] for row in analysis["monthly_rows"]],
            "bills": [row["total_bill"] for row in analysis["monthly_rows"]],
        }

        return render_template(
            "dashboard.html",
            active_page="dashboard",
            stats=stats,
            chart_payload=chart_payload,
            recent_bills=bills[:6],
            warning_cards=warnings[:4],
            missing_sample_count=missing_hh + missing_bills,
        )

    @app.route("/load-sample-data", methods=["POST"])
    def load_sample_route():
        verify_csrf()
        added_hh, added_bills = load_sample_data(app.config["DB_PATH"])
        if added_hh == 0 and added_bills == 0:
            flash("All sample households and billing records are already loaded.", "info")
        else:
            flash(
                f"Loaded {added_hh} sample household(s) and {added_bills} monthly bill(s).",
                "success",
            )
        return redirect(request.referrer or url_for("dashboard"))

    # ------------------------------------------------------------------
    # B & I. Household Registration & Management
    # ------------------------------------------------------------------
    @app.route("/households")
    def households_page():
        db = app.config["DB_PATH"]
        search = request.args.get("search", "").strip()
        area = request.args.get("area", "").strip()
        connection_type = request.args.get("connection_type", "").strip()

        households = get_all_households(
            search=search,
            area=area,
            connection_type=connection_type,
            db_path=db,
        )
        areas = get_distinct_areas(db)
        missing_hh, missing_bills = count_missing_sample_records(db)

        return render_template(
            "households.html",
            active_page="households",
            households=households,
            areas=areas,
            search=search,
            selected_area=area,
            selected_connection=connection_type,
            missing_sample_count=missing_hh + missing_bills,
        )

    @app.route("/households/add", methods=["GET", "POST"])
    def add_household_page():
        db = app.config["DB_PATH"]
        form_values = {
            "household_id": "",
            "consumer_name": "",
            "meter_number": "",
            "address": "",
            "area": "",
            "connection_type": "Domestic",
            "meter_category": "Single Phase",
        }
        errors = []

        if request.method == "POST":
            verify_csrf()
            form_values = request.form.to_dict()
            is_valid, errors, cleaned = validate_household_data(form_values)
            if is_valid:
                try:
                    add_household(cleaned, db_path=db)
                    flash(
                        f"Household {cleaned['household_id']} ({cleaned['consumer_name']}) registered successfully.",
                        "success",
                    )
                    return redirect(url_for("households_page"))
                except ValueError as exc:
                    errors.append(str(exc))

        return render_template(
            "add_household.html",
            active_page="add_household",
            form_values=form_values,
            errors=errors,
            is_edit=False,
        )

    @app.route("/households/<int:record_id>/edit", methods=["GET", "POST"])
    def edit_household_page(record_id):
        db = app.config["DB_PATH"]
        household = get_household_by_id(record_id, db_path=db)
        if not household:
            abort(404)

        form_values = dict(household)
        errors = []

        if request.method == "POST":
            verify_csrf()
            form_values = request.form.to_dict()
            is_valid, errors, cleaned = validate_household_data(form_values)
            if is_valid:
                try:
                    update_household(record_id, cleaned, db_path=db)
                    flash(
                        f"Household {cleaned['household_id']} updated successfully.",
                        "success",
                    )
                    return redirect(url_for("households_page"))
                except ValueError as exc:
                    errors.append(str(exc))

        return render_template(
            "add_household.html",
            active_page="households",
            form_values=form_values,
            errors=errors,
            is_edit=True,
            record_id=record_id,
        )

    @app.route("/households/<int:record_id>/delete", methods=["POST"])
    def delete_household_route(record_id):
        verify_csrf()
        db = app.config["DB_PATH"]
        household = get_household_by_id(record_id, db_path=db)
        if not household:
            abort(404)
        delete_household(record_id, db_path=db)
        flash(
            f"Household {household['household_id']} ({household['consumer_name']}) and its billing records were deleted.",
            "info",
        )
        return redirect(url_for("households_page"))

    # ------------------------------------------------------------------
    # C, D, F. Meter Reading & Progressive Bill Generation
    # ------------------------------------------------------------------
    @app.route("/meter-reading", methods=["GET", "POST"])
    def meter_reading_page():
        db = app.config["DB_PATH"]
        households = get_all_households(db_path=db)
        rules = get_rules(db)
        slabs = get_slabs(db)

        # Map latest meter reading for each household so JS can pre-fill Previous Reading
        latest_readings = {}
        for hh in households:
            latest = get_latest_reading_for_household(hh["id"], db_path=db)
            latest_readings[str(hh["id"])] = latest["current_reading"] if latest else 0

        preselect_id = request.args.get("household_ref_id", "")
        default_prev = latest_readings.get(preselect_id, "")
        form_values = {
            "household_ref_id": preselect_id,
            "billing_month": date.today().strftime("%Y-%m"),
            "previous_reading": default_prev,
            "current_reading": "",
            "billing_date": date.today().strftime("%Y-%m-%d"),
            "is_late_payment": False,
        }
        errors = []
        preview_calc = None

        if request.method == "POST":
            verify_csrf()
            form_values = {
                "household_ref_id": request.form.get("household_ref_id", ""),
                "billing_month": request.form.get("billing_month", ""),
                "previous_reading": request.form.get("previous_reading", ""),
                "current_reading": request.form.get("current_reading", ""),
                "billing_date": request.form.get("billing_date", ""),
                "is_late_payment": bool(request.form.get("is_late_payment")),
            }
            is_valid, errors, cleaned = validate_meter_reading_data(request.form)
            if is_valid:
                if check_duplicate_billing_month(
                    cleaned["household_ref_id"], cleaned["billing_month"], db_path=db
                ):
                    errors.append(
                        f"A bill for billing month {cleaned['billing_month']} already exists for this household."
                    )
                else:
                    # Save validated reading preview in session and pass params for stateless serverless compatibility
                    session["pending_reading"] = cleaned
                    return redirect(
                        url_for(
                            "generate_bill_page",
                            household_ref_id=cleaned["household_ref_id"],
                            billing_month=cleaned["billing_month"],
                            previous_reading=cleaned["previous_reading"],
                            current_reading=cleaned["current_reading"],
                            billing_date=cleaned["billing_date"],
                            is_late_payment="1" if cleaned["is_late_payment"] else "0",
                        )
                    )

        return render_template(
            "meter_reading.html",
            active_page="meter_reading",
            households=households,
            latest_readings=latest_readings,
            form_values=form_values,
            errors=errors,
            preview_calc=preview_calc,
            rules=rules,
            slabs=slabs,
        )

    @app.route("/generate-bill", methods=["GET", "POST"])
    def generate_bill_page():
        db = app.config["DB_PATH"]
        households = get_all_households(db_path=db)
        rules = get_rules(db)
        slabs = get_slabs(db)
        errors = []

        pending = session.get("pending_reading")
        if not pending and request.method == "GET" and request.args.get("household_ref_id"):
            ok_q, errs_q, cleaned_q = validate_meter_reading_data(request.args)
            if ok_q and not check_duplicate_billing_month(
                cleaned_q["household_ref_id"], cleaned_q["billing_month"], db_path=db
            ):
                pending = cleaned_q
            else:
                errors.extend(errs_q)

        if request.method == "POST":
            verify_csrf()
            action = request.form.get("action", "confirm")
            if action == "preview":
                is_valid, errors, cleaned = validate_meter_reading_data(request.form)
                if is_valid:
                    if check_duplicate_billing_month(
                        cleaned["household_ref_id"], cleaned["billing_month"], db_path=db
                    ):
                        errors.append(
                            f"A bill for billing month {cleaned['billing_month']} already exists for this household."
                        )
                    else:
                        session["pending_reading"] = cleaned
                        pending = cleaned
            elif action == "confirm":
                is_valid, errors, cleaned = validate_meter_reading_data(request.form)
                payment_status = request.form.get("payment_status", "Unpaid")
                if payment_status not in PAYMENT_STATUSES:
                    payment_status = "Unpaid"
                if is_valid:
                    try:
                        bill_id = create_reading_and_bill(
                            cleaned, payment_status=payment_status, db_path=db
                        )
                        session.pop("pending_reading", None)
                        flash("Electricity bill generated and saved to SQLite.", "success")
                        return redirect(url_for("bill_details_page", bill_id=bill_id))
                    except ValueError as exc:
                        errors.append(str(exc))

        preview_data = None
        selected_household = None
        if pending and pending.get("household_ref_id"):
            selected_household = get_household_by_id(pending["household_ref_id"], db_path=db)
            if selected_household:
                preview_data = calculate_full_bill(
                    pending["consumption_units"],
                    slabs=slabs,
                    rules=rules,
                    is_late_payment=bool(pending.get("is_late_payment", False)),
                )

        latest_readings = {}
        for hh in households:
            latest = get_latest_reading_for_household(hh["id"], db_path=db)
            latest_readings[str(hh["id"])] = latest["current_reading"] if latest else 0

        return render_template(
            "generate_bill.html",
            active_page="generate_bill",
            households=households,
            latest_readings=latest_readings,
            pending=pending,
            selected_household=selected_household,
            preview_data=preview_data,
            rules=rules,
            slabs=slabs,
            errors=errors,
            default_month=date.today().strftime("%Y-%m"),
            default_date=date.today().strftime("%Y-%m-%d"),
        )

    @app.route("/bill/<int:bill_id>")
    def bill_details_page(bill_id):
        db = app.config["DB_PATH"]
        bill = get_bill_by_id(bill_id, db_path=db)
        if not bill:
            abort(404)
        rules = get_rules(db)
        previous_bills = get_all_bills(
            household_ref_id=bill["household_ref_id"],
            sort_by="month_desc",
            db_path=db,
        )
        return render_template(
            "bill_details.html",
            active_page="billing_history",
            bill=bill,
            rules=rules,
            previous_bills=previous_bills,
            auto_print=request.args.get("print") == "1",
        )

    @app.route("/bill/<int:bill_id>/toggle-status", methods=["POST"])
    def toggle_bill_status_route(bill_id):
        verify_csrf()
        new_status = toggle_bill_payment_status(bill_id, db_path=app.config["DB_PATH"])
        if new_status is None:
            abort(404)
        flash(f"Bill payment status updated to {new_status}.", "success")
        return redirect(request.referrer or url_for("bill_details_page", bill_id=bill_id))

    @app.route("/bill/<int:bill_id>/csv")
    def download_single_bill_csv(bill_id):
        db = app.config["DB_PATH"]
        bill = get_bill_by_id(bill_id, db_path=db)
        if not bill:
            abort(404)
        rules = get_rules(db)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([rules["company_name"], "Official Electricity Bill"])
        writer.writerow(["Bill Number", bill["bill_number"]])
        writer.writerow(["Billing Month", bill["billing_month"]])
        writer.writerow(["Billing Date", bill["billing_date"]])
        writer.writerow(["Payment Status", bill["payment_status"]])
        writer.writerow(["Household ID", bill["household_id"]])
        writer.writerow(["Consumer Name", bill["consumer_name"]])
        writer.writerow(["Meter Number", bill["meter_number"]])
        writer.writerow(["Connection Type", bill["connection_type"]])
        writer.writerow(["Meter Category", bill["meter_category"]])
        writer.writerow(["Previous Reading", bill["previous_reading"]])
        writer.writerow(["Current Reading", bill["current_reading"]])
        writer.writerow(["Units Consumed", bill["units_consumed"]])
        writer.writerow([])
        writer.writerow(["Slab Range", "Units in Slab", "Rate per Unit (INR)", "Charge (INR)"])
        for item in bill["slab_items"]:
            writer.writerow(
                [
                    item["slab_label"],
                    item["units_in_slab"],
                    f"{item['rate_per_unit']:.2f}",
                    f"{item['slab_charge']:.2f}",
                ]
            )
        writer.writerow([])
        writer.writerow(["Energy Charge", f"{bill['energy_charge']:.2f}"])
        writer.writerow(["Fixed Monthly Charge", f"{bill['fixed_charge']:.2f}"])
        writer.writerow(["Electricity Duty", f"{bill['electricity_duty']:.2f}"])
        writer.writerow(["Surcharge", f"{bill['surcharge_amount']:.2f}"])
        writer.writerow(["Rebate", f"-{bill['rebate_amount']:.2f}"])
        writer.writerow(["Late Payment Penalty", f"{bill['late_penalty_amount']:.2f}"])
        writer.writerow(["Final Payable Amount", f"{bill['final_payable']:.2f}"])

        filename = f"{bill['bill_number']}.csv"
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    # ------------------------------------------------------------------
    # J. Billing History
    # ------------------------------------------------------------------
    @app.route("/billing-history")
    def billing_history_page():
        db = app.config["DB_PATH"]
        month = request.args.get("month", "").strip()
        search = request.args.get("search", "").strip()
        payment_status = request.args.get("payment_status", "").strip()
        household_ref_id = request.args.get("household_ref_id", "").strip()
        sort_by = request.args.get("sort_by", "month_desc").strip()

        bills = get_all_bills(
            month=month,
            search=search,
            payment_status=payment_status,
            household_ref_id=household_ref_id or None,
            sort_by=sort_by,
            db_path=db,
        )
        months = get_distinct_billing_months(db)
        households = get_all_households(db_path=db)

        return render_template(
            "billing_history.html",
            active_page="billing_history",
            bills=bills,
            months=months,
            households=households,
            selected_month=month,
            search=search,
            selected_status=payment_status,
            selected_household=household_ref_id,
            sort_by=sort_by,
        )

    # ------------------------------------------------------------------
    # G. Monthly Consumption Comparison
    # ------------------------------------------------------------------
    @app.route("/monthly-analysis")
    def monthly_analysis_page():
        db = app.config["DB_PATH"]
        household_ref_id = request.args.get("household_ref_id", "").strip()
        households = get_all_households(db_path=db)

        selected_household = None
        if household_ref_id:
            selected_household = get_household_by_id(int(household_ref_id), db_path=db)

        bills = get_all_bills(
            household_ref_id=household_ref_id or None,
            sort_by="month_asc",
            db_path=db,
        )
        analysis = analyze_monthly_consumption(bills)

        chart_payload = {
            "labels": [row["month_label"] for row in analysis["monthly_rows"]],
            "units": [row["units_consumed"] for row in analysis["monthly_rows"]],
            "bills": [row["total_bill"] for row in analysis["monthly_rows"]],
        }

        return render_template(
            "monthly_analysis.html",
            active_page="monthly_analysis",
            households=households,
            selected_household=selected_household,
            selected_household_id=household_ref_id,
            analysis=analysis,
            chart_payload=chart_payload,
        )

    # ------------------------------------------------------------------
    # H. Unusual Consumption Detection
    # ------------------------------------------------------------------
    @app.route("/unusual-consumption")
    def unusual_consumption_page():
        db = app.config["DB_PATH"]
        rules = get_rules(db)
        bills = get_all_bills(sort_by="month_asc", db_path=db)
        warnings = detect_unusual_consumption(bills, rules)

        return render_template(
            "unusual_consumption.html",
            active_page="unusual_consumption",
            warnings=warnings,
            rules=rules,
            total_bills_checked=len(bills),
        )

    # ------------------------------------------------------------------
    # E. Tariff & Billing Rules Configuration
    # ------------------------------------------------------------------
    @app.route("/tariff-rules", methods=["GET", "POST"])
    def tariff_rules_page():
        db = app.config["DB_PATH"]
        errors = []
        rules = get_rules(db)
        slabs = get_slabs(db)

        if request.method == "POST":
            verify_csrf()
            is_valid, errors, cleaned_rules, cleaned_slabs = validate_rules_and_slabs(
                request.form
            )
            if is_valid:
                update_rules_and_slabs(cleaned_rules, cleaned_slabs, db_path=db)
                flash(
                    "Tariff slabs and billing rules saved successfully. New bills will use these rates.",
                    "success",
                )
                return redirect(url_for("tariff_rules_page"))
            rules = {**rules, **cleaned_rules}
            slabs = cleaned_slabs

        return render_template(
            "tariff_rules.html",
            active_page="tariff_rules",
            rules=rules,
            slabs=slabs,
            errors=errors,
        )

    @app.route("/tariff-rules/reset", methods=["POST"])
    def reset_tariff_rules_route():
        verify_csrf()
        reset_rules_to_default(app.config["DB_PATH"])
        flash("Tariff slabs and billing rules reset to academic defaults.", "info")
        return redirect(url_for("tariff_rules_page"))

    # ------------------------------------------------------------------
    # K. Reports & Analytics + CSV Export
    # ------------------------------------------------------------------
    @app.route("/reports")
    def reports_page():
        db = app.config["DB_PATH"]
        households = get_all_households(db_path=db)
        bills = get_all_bills(sort_by="month_desc", db_path=db)
        rules = get_rules(db)
        slabs = get_slabs(db)

        analysis = analyze_monthly_consumption(bills)
        warnings = detect_unusual_consumption(bills, rules)

        total_consumption = round(sum(b["units_consumed"] for b in bills), 2)
        total_revenue = round(sum(b["final_payable"] for b in bills), 2)
        total_surcharges = round(sum(b["surcharge_amount"] for b in bills), 2)
        total_rebates = round(sum(b["rebate_amount"] for b in bills), 2)
        paid_revenue = round(
            sum(b["final_payable"] for b in bills if b["payment_status"] == "Paid"), 2
        )

        highest_household = (
            max(households, key=lambda h: h["total_units"]) if households else None
        )
        highest_bill = max(bills, key=lambda b: b["final_payable"]) if bills else None

        pattern_preview = generate_text_pattern_summary(
            analysis["monthly_rows"], rules["company_name"]
        )

        summary = {
            "total_households": len(households),
            "total_bills": len(bills),
            "total_consumption": total_consumption,
            "total_revenue": total_revenue,
            "paid_revenue": paid_revenue,
            "total_surcharges": total_surcharges,
            "total_rebates": total_rebates,
            "highest_household": highest_household,
            "highest_bill": highest_bill,
            "unusual_count": len(warnings),
        }

        return render_template(
            "reports.html",
            active_page="reports",
            summary=summary,
            monthly_rows=analysis["monthly_rows"],
            households=sorted(
                households, key=lambda h: h["total_units"], reverse=True
            ),
            warnings=warnings,
            pattern_preview=pattern_preview,
            slabs=slabs,
            rules=rules,
        )

    @app.route("/reports/export-csv")
    def export_reports_csv():
        db = app.config["DB_PATH"]
        export_type = request.args.get("type", "all_bills")
        rules = get_rules(db)
        bills = get_all_bills(sort_by="month_desc", db_path=db)

        output = io.StringIO()
        writer = csv.writer(output)

        if export_type == "monthly":
            analysis = analyze_monthly_consumption(bills)
            writer.writerow(
                [
                    "Billing Month",
                    "Month Label",
                    "Bills Generated",
                    "Total Units (kWh)",
                    "Energy Charge (INR)",
                    "Total Bill Amount (INR)",
                    "Consumption Change (%)",
                    "Bill Change (%)",
                ]
            )
            for row in analysis["monthly_rows"]:
                writer.writerow(
                    [
                        row["month"],
                        row["month_label"],
                        row["bill_count"],
                        f"{row['units_consumed']:.2f}",
                        f"{row['energy_charge']:.2f}",
                        f"{row['total_bill']:.2f}",
                        row["pct_change_units"]
                        if row["pct_change_units"] is not None
                        else "N/A",
                        row["pct_change_bill"]
                        if row["pct_change_bill"] is not None
                        else "N/A",
                    ]
                )
            filename = "monthly_consumption_report.csv"

        elif export_type == "unusual":
            warnings = detect_unusual_consumption(bills, rules)
            writer.writerow(
                [
                    "Bill Number",
                    "Household ID",
                    "Consumer Name",
                    "Meter Number",
                    "Billing Month",
                    "Previous Units",
                    "3-Month Avg Units",
                    "Current Units",
                    "Difference (Units)",
                    "Increase (%)",
                    "Final Payable (INR)",
                    "Reasons",
                ]
            )
            for w in warnings:
                writer.writerow(
                    [
                        w["bill_number"],
                        w["household_id"],
                        w["consumer_name"],
                        w["meter_number"],
                        w["billing_month"],
                        w["previous_consumption"]
                        if w["previous_consumption"] is not None
                        else "N/A",
                        w["three_month_avg"]
                        if w["three_month_avg"] is not None
                        else "N/A",
                        f"{w['current_consumption']:.2f}",
                        w["difference_units"]
                        if w["difference_units"] is not None
                        else "N/A",
                        w["percentage_increase"]
                        if w["percentage_increase"] is not None
                        else "N/A",
                        f"{w['final_payable']:.2f}",
                        w["reason_text"],
                    ]
                )
            filename = "unusual_consumption_report.csv"

        else:
            writer.writerow(
                [
                    "Bill Number",
                    "Billing Month",
                    "Billing Date",
                    "Household ID",
                    "Consumer Name",
                    "Meter Number",
                    "Area",
                    "Connection Type",
                    "Previous Reading",
                    "Current Reading",
                    "Units Consumed",
                    "Energy Charge (INR)",
                    "Fixed Charge (INR)",
                    "Electricity Duty (INR)",
                    "Surcharge (INR)",
                    "Rebate (INR)",
                    "Late Penalty (INR)",
                    "Final Payable (INR)",
                    "Payment Status",
                ]
            )
            for b in bills:
                writer.writerow(
                    [
                        b["bill_number"],
                        b["billing_month"],
                        b["billing_date"],
                        b["household_id"],
                        b["consumer_name"],
                        b["meter_number"],
                        b["area"],
                        b["connection_type"],
                        f"{b['previous_reading']:.2f}",
                        f"{b['current_reading']:.2f}",
                        f"{b['units_consumed']:.2f}",
                        f"{b['energy_charge']:.2f}",
                        f"{b['fixed_charge']:.2f}",
                        f"{b['electricity_duty']:.2f}",
                        f"{b['surcharge_amount']:.2f}",
                        f"{b['rebate_amount']:.2f}",
                        f"{b['late_penalty_amount']:.2f}",
                        f"{b['final_payable']:.2f}",
                        b["payment_status"],
                    ]
                )
            filename = "electricity_billing_full_report.csv"

        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="127.0.0.1", port=port)
