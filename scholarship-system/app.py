"""
University Scholarship Allocation System - Flask Web Application
----------------------------------------------------------------
Main entry point serving the web dashboard, student application management,
configurable scholarship rules, ranking engine, and CSV/print reports.
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

from database import (
    DEFAULT_DB_PATH,
    add_student,
    count_missing_sample_students,
    delete_student,
    get_all_students,
    get_rules,
    get_student_by_id,
    init_db,
    load_sample_students,
    reset_rules_to_default,
    update_rules,
    update_student,
)
from scholarship_logic import (
    ACADEMIC_YEARS,
    DEPARTMENTS,
    SCHOLARSHIP_CATEGORIES,
    SUBJECT_TUPLE,
    evaluate_and_rank_all,
    format_inr,
    validate_rules_data,
    validate_student_data,
)


def create_app(db_path=None, seed_if_empty=True):
    """Create and configure the Flask application instance."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, "templates"),
        static_folder=os.path.join(base_dir, "static"),
    )

    # Avoid hardcoded secret keys; read from environment or generate runtime key
    app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)
    app.config["DB_PATH"] = db_path or DEFAULT_DB_PATH
    app.config["SEED_IF_EMPTY"] = seed_if_empty

    # Initialize SQLite database and tables automatically on startup
    init_db(app.config["DB_PATH"], seed_if_empty=seed_if_empty)

    @app.before_request
    def ensure_db_exists():
        """Re-initialize SQLite if running on an ephemeral /tmp serverless directory."""
        if not os.path.exists(app.config["DB_PATH"]):
            init_db(app.config["DB_PATH"], seed_if_empty=app.config["SEED_IF_EMPTY"])

    def get_csrf_token():
        """Return a stable CSRF token via double-submit cookie (serverless-safe) and session."""
        cached = getattr(g, "_csrf_token", None)
        if cached:
            return cached
        token = request.cookies.get("csrf_cookie") or session.get("csrf_token")
        if not token:
            token = secrets.token_hex(16)
            g._set_csrf_cookie = True
        elif not request.cookies.get("csrf_cookie"):
            g._set_csrf_cookie = True
        g._csrf_token = token
        session["csrf_token"] = token
        return token

    @app.after_request
    def attach_csrf_cookie(response):
        """Attach the double-submit CSRF cookie so POST forms survive serverless cold starts."""
        token = getattr(g, "_csrf_token", None)
        if token and getattr(g, "_set_csrf_cookie", False):
            response.set_cookie(
                "csrf_cookie",
                token,
                httponly=True,
                samesite="Lax",
                path="/",
            )
        return response

    @app.context_processor
    def inject_globals():
        """Inject CSRF token, helper formatters, and metadata into all templates."""
        return {
            "csrf_token": get_csrf_token(),
            "format_inr": format_inr,
            "departments": DEPARTMENTS,
            "academic_years": ACADEMIC_YEARS,
            "scholarship_categories": SCHOLARSHIP_CATEGORIES,
            "subject_tuple": SUBJECT_TUPLE,
            "missing_sample_count": count_missing_sample_students(app.config["DB_PATH"]),
        }

    def verify_csrf():
        """Validate CSRF token using double-submit cookie or session token."""
        if app.config.get("WTF_CSRF_DISABLED"):
            return True
        submitted = request.form.get("csrf_token", "")
        if not submitted:
            return False
        cookie_token = request.cookies.get("csrf_cookie", "")
        session_token = session.get("csrf_token", "")
        cookie_ok = bool(cookie_token and secrets.compare_digest(cookie_token, submitted))
        session_ok = bool(session_token and secrets.compare_digest(session_token, submitted))
        return cookie_ok or session_ok

    def get_evaluated_state():
        """Load students and rules from SQLite and run the Python ranking engine."""
        db = app.config["DB_PATH"]
        rules = get_rules(db)
        students = get_all_students(db)
        result = evaluate_and_rank_all(students, rules)
        return rules, result

    @app.route("/")
    def dashboard():
        """Render Home / Dashboard with key statistics and recent applicants."""
        rules, state = get_evaluated_state()
        all_students = state["all_evaluated"]
        # Sort recent applicants by application_date descending, then id descending
        recent_applicants = sorted(
            all_students,
            key=lambda s: (str(s["application_date"]), int(s["id"])),
            reverse=True,
        )[:6]
        top_recipients = state["selected_students"][:5]

        return render_template(
            "dashboard.html",
            active_page="dashboard",
            rules=rules,
            summary=state["summary"],
            recent_applicants=recent_applicants,
            top_recipients=top_recipients,
            department_table=state["department_table"],
        )

    @app.route("/add", methods=["GET", "POST"])
    def add_student_view():
        """Render and process the Add Student Application form."""
        db = app.config["DB_PATH"]
        rules = get_rules(db)
        form_values = {
            "application_date": date.today().isoformat(),
            "income_certificate_status": "Available",
            "scholarship_category": "Merit-cum-Means",
        }
        errors = []

        if request.method == "POST":
            if not verify_csrf():
                flash("Security verification failed. Please submit the form again.", "error")
                return redirect(url_for("add_student_view"))

            form_values = request.form.to_dict()
            is_valid, cleaned, errors = validate_student_data(form_values)

            if is_valid:
                existing = get_student_by_id(cleaned["student_id"], db)
                if existing is not None:
                    errors.append(
                        f"Student ID '{cleaned['student_id']}' already exists. Duplicate applications are not allowed."
                    )

            if is_valid and not errors:
                add_student(cleaned, db)
                flash(
                    f"Application for {cleaned['full_name']} ({cleaned['student_id']}) saved and evaluated.",
                    "success",
                )
                return redirect(url_for("student_details", student_id=cleaned["student_id"]))

        return render_template(
            "add_student.html",
            active_page="add_student",
            mode="add",
            rules=rules,
            form_values=form_values,
            errors=errors,
        )

    @app.route("/applicants")
    def applicants():
        """List, search, filter, and sort all student applications."""
        rules, state = get_evaluated_state()
        records = list(state["all_evaluated"])

        query = request.args.get("q", "").strip()
        dept_filter = request.args.get("department", "").strip()
        eligibility_filter = request.args.get("eligibility", "all").strip()
        selection_filter = request.args.get("selection", "all").strip()
        sort_by = request.args.get("sort", "rank").strip()

        filtered = []
        q_lower = query.lower()
        for student in records:
            if q_lower:
                name_match = q_lower in student["full_name"].lower()
                id_match = q_lower in student["student_id"].lower()
                if not (name_match or id_match):
                    continue

            if dept_filter and student["department"] != dept_filter:
                continue

            if eligibility_filter == "eligible" and not student["is_eligible"]:
                continue
            if eligibility_filter == "rejected" and student["is_eligible"]:
                continue

            if selection_filter != "all" and student["selection_code"] != selection_filter:
                continue

            filtered.append(student)

        # Sort records based on selected option
        if sort_by == "marks_desc":
            filtered.sort(key=lambda s: float(s["aggregate_percentage"]), reverse=True)
        elif sort_by == "marks_asc":
            filtered.sort(key=lambda s: float(s["aggregate_percentage"]))
        elif sort_by == "score_desc":
            filtered.sort(
                key=lambda s: (1 if s["is_eligible"] else 0, float(s["scholarship_score"])),
                reverse=True,
            )
        elif sort_by == "score_asc":
            filtered.sort(
                key=lambda s: (0 if s["is_eligible"] else 1, float(s["scholarship_score"]))
            )
        elif sort_by == "name_asc":
            filtered.sort(key=lambda s: s["full_name"].lower())
        elif sort_by == "recent":
            filtered.sort(key=lambda s: (str(s["application_date"]), int(s["id"])), reverse=True)
        else:
            # Default: ranked eligible first (1..N), then rejected by ID
            filtered.sort(
                key=lambda s: (
                    0 if s["rank"] is not None else 1,
                    s["rank"] if s["rank"] is not None else 999999,
                    s["student_id"],
                )
            )

        return render_template(
            "applicants.html",
            active_page="applicants",
            students=filtered,
            total_count=len(records),
            rules=rules,
            filters={
                "q": query,
                "department": dept_filter,
                "eligibility": eligibility_filter,
                "selection": selection_filter,
                "sort": sort_by,
            },
        )

    @app.route("/student/<student_id>")
    def student_details(student_id):
        """Display full details, evaluation breakdown, and award status for one student."""
        rules, state = get_evaluated_state()
        target = None
        for student in state["all_evaluated"]:
            if student["student_id"].upper() == student_id.strip().upper():
                target = student
                break

        if target is None:
            abort(404)

        return render_template(
            "student_details.html",
            active_page="applicants",
            student=target,
            rules=rules,
        )

    @app.route("/student/<student_id>/edit", methods=["GET", "POST"])
    def edit_student_view(student_id):
        """Edit an existing student record and update SQLite."""
        db = app.config["DB_PATH"]
        rules = get_rules(db)
        existing = get_student_by_id(student_id, db)
        if existing is None:
            abort(404)

        form_values = dict(existing)
        errors = []

        if request.method == "POST":
            if not verify_csrf():
                flash("Security verification failed. Please submit the form again.", "error")
                return redirect(url_for("edit_student_view", student_id=student_id))

            form_values = request.form.to_dict()
            is_valid, cleaned, errors = validate_student_data(form_values)

            if is_valid:
                new_id = cleaned["student_id"].upper()
                if new_id != existing["student_id"].upper():
                    conflict = get_student_by_id(new_id, db)
                    if conflict is not None:
                        errors.append(
                            f"Cannot rename Student ID to '{new_id}' because another student already uses it."
                        )

            if is_valid and not errors:
                update_student(existing["student_id"], cleaned, db)
                flash(
                    f"Updated application for {cleaned['full_name']} ({cleaned['student_id']}).",
                    "success",
                )
                return redirect(url_for("student_details", student_id=cleaned["student_id"]))

        return render_template(
            "add_student.html",
            active_page="applicants",
            mode="edit",
            original_student_id=existing["student_id"],
            rules=rules,
            form_values=form_values,
            errors=errors,
        )

    @app.route("/student/<student_id>/delete", methods=["POST"])
    def delete_student_view(student_id):
        """Delete a student record after confirmation."""
        if not verify_csrf():
            flash("Security verification failed. Delete request blocked.", "error")
            return redirect(url_for("applicants"))

        deleted = delete_student(student_id, app.config["DB_PATH"])
        if deleted:
            flash(f"Deleted application for Student ID {student_id.upper()}.", "success")
        else:
            flash(f"Student ID {student_id.upper()} was not found.", "error")
        return redirect(url_for("applicants"))

    @app.route("/rankings")
    def rankings():
        """Display eligible ranked students, quota selection, waitlist, and rejected list."""
        rules, state = get_evaluated_state()
        return render_template(
            "rankings.html",
            active_page="rankings",
            rules=rules,
            summary=state["summary"],
            eligible_ranked=state["eligible_ranked"],
            selected_students=state["selected_students"],
            waitlisted_students=state["waitlisted_students"],
            rejected_students=state["rejected_students"],
        )

    @app.route("/rules", methods=["GET", "POST"])
    def rules_view():
        """Configure scholarship eligibility thresholds, quota, weights, and income slabs."""
        db = app.config["DB_PATH"]
        current_rules = get_rules(db)
        form_values = dict(current_rules)
        errors = []

        if request.method == "POST":
            if not verify_csrf():
                flash("Security verification failed. Please try again.", "error")
                return redirect(url_for("rules_view"))

            action = request.form.get("action", "save")
            if action == "reset":
                reset_rules_to_default(db)
                flash(
                    "Scholarship rules restored to assignment defaults and all rankings recalculated.",
                    "success",
                )
                return redirect(url_for("rules_view"))

            form_values = request.form.to_dict()
            # Unchecked checkbox is omitted from POST body
            if "income_certificate_required" not in form_values:
                form_values["income_certificate_required"] = "0"

            is_valid, cleaned_rules, errors = validate_rules_data(form_values)
            if is_valid:
                update_rules(cleaned_rules, db)
                flash(
                    "Scholarship rules updated! Eligibility and rankings have been recalculated automatically.",
                    "success",
                )
                return redirect(url_for("rules_view"))

        _, state = get_evaluated_state()
        return render_template(
            "rules.html",
            active_page="rules",
            rules=form_values,
            summary=state["summary"],
            errors=errors,
        )

    @app.route("/reports")
    def reports():
        """Render printable analytics and scholarship allocation report."""
        rules, state = get_evaluated_state()
        return render_template(
            "reports.html",
            active_page="reports",
            rules=rules,
            summary=state["summary"],
            selected_students=state["selected_students"],
            waitlisted_students=state["waitlisted_students"],
            rejected_students=state["rejected_students"],
            department_table=state["department_table"],
            generated_date=date.today().isoformat(),
        )

    @app.route("/reports/export-csv")
    def export_csv():
        """Generate and download scholarship ranking report as CSV using built-in csv module."""
        rules, state = get_evaluated_state()

        output = io.StringIO()
        # Add UTF-8 BOM for clean Excel opening on Windows
        output.write("\ufeff")
        writer = csv.writer(output)

        writer.writerow(
            [
                "Rank",
                "Student ID",
                "Full Name",
                "Department",
                "Academic Year",
                "Mathematics",
                "Physics",
                "Chemistry",
                "English",
                "Computer Science",
                "Total Marks",
                "Aggregate (%)",
                "Attendance (%)",
                "Annual Family Income (INR)",
                "Income Certificate",
                "Income Merit Score",
                "Scholarship Score",
                "Eligibility",
                "Selection Status",
                "Tie-Break Note",
                "Rejection Reasons",
                "Scholarship Category",
                "Application Date",
            ]
        )

        for student in state["all_evaluated"]:
            writer.writerow(
                [
                    student["rank"] if student["rank"] is not None else "-",
                    student["student_id"],
                    student["full_name"],
                    student["department"],
                    student["academic_year"],
                    student["math_marks"],
                    student["physics_marks"],
                    student["chemistry_marks"],
                    student["english_marks"],
                    student["cs_marks"],
                    student["total_marks"],
                    f"{student['aggregate_percentage']:.2f}",
                    f"{student['attendance_percentage']:.2f}",
                    f"{student['annual_income']:.2f}",
                    student["income_certificate_status"],
                    f"{student['income_merit_score']:.2f}",
                    f"{student['scholarship_score']:.2f}" if student["is_eligible"] else "0.00",
                    "Eligible" if student["is_eligible"] else "Not Eligible",
                    student["selection_status"],
                    student["tie_note"] or "-",
                    student["rejection_summary"] or "-",
                    student["scholarship_category"],
                    student["application_date"],
                ]
            )

        csv_content = output.getvalue()
        output.close()

        filename = f"scholarship_allocation_report_{date.today().isoformat()}.csv"
        return Response(
            csv_content,
            mimetype="text/csv; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    @app.route("/load-sample-data", methods=["POST"])
    def load_sample_data_view():
        """Load missing sample students safely without creating duplicates."""
        if not verify_csrf():
            flash("Security verification failed.", "error")
            return redirect(url_for("dashboard"))

        inserted, skipped = load_sample_students(app.config["DB_PATH"])
        if inserted > 0:
            flash(
                f"Loaded {inserted} sample student record(s) ({skipped} already present skipped).",
                "success",
            )
        else:
            flash("All 18 sample student records are already loaded in the database.", "info")

        next_url = request.form.get("next", "").strip()
        if next_url in ("dashboard", "applicants", "rankings"):
            return redirect(url_for(next_url))
        return redirect(url_for("dashboard"))

    @app.route("/favicon.ico")
    def favicon():
        """Serve the university crest SVG to avoid browser favicon 404s."""
        return redirect(url_for("static", filename="images/university_crest.svg"))

    @app.errorhandler(404)
    def page_not_found(_error):
        return render_template("404.html", active_page=""), 404

    return app


app = create_app()

if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    port = int(os.environ.get("PORT", "5000"))
    app.run(debug=debug_mode, host="127.0.0.1", port=port)

