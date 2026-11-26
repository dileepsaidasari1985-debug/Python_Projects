"""Student Marks Matrix Analysis (Case Study #42) - Flask Application."""

import csv
import io
import os
import secrets

from flask import Flask, Response, abort, flash, redirect, render_template, request, session, url_for

from database import (
    DEFAULT_DB_PATH,
    add_student_row,
    delete_student_by_id,
    get_settings,
    get_student_matrix_rows,
    init_db,
    update_settings,
)
from matrix_logic import (
    DEFAULT_SUBJECTS,
    analyze_marks_matrix,
    parse_matrix_text,
    validate_student_marks_row,
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
        rows = get_student_matrix_rows(db)
        settings = get_settings(db)
        return {
            "current_endpoint": request.endpoint or "dashboard",
            "nav_students": len(rows),
            "settings": settings,
            "subjects": DEFAULT_SUBJECTS,
        }

    @app.route("/")
    def dashboard():
        db = app.config["DB_PATH"]
        settings = get_settings(db)
        rows = get_student_matrix_rows(db)
        analysis = analyze_marks_matrix(rows, DEFAULT_SUBJECTS, settings["low_avg_threshold"], settings["pass_mark"])
        return render_template("dashboard.html", analysis=analysis)

    @app.route("/matrix", methods=["GET", "POST"])
    def matrix_view():
        db = app.config["DB_PATH"]
        settings = get_settings(db)
        if request.method == "POST":
            action = request.form.get("action", "add")
            if action == "settings":
                try:
                    low_t = float(request.form.get("low_avg_threshold", 60))
                    pass_m = float(request.form.get("pass_mark", 40))
                    if 0 <= low_t <= 100 and 0 <= pass_m <= 100:
                        update_settings(low_t, pass_m, db)
                        flash("Analysis thresholds updated.", "success")
                    else:
                        flash("Thresholds must be between 0 and 100.", "danger")
                except ValueError:
                    flash("Invalid threshold numbers.", "danger")
                return redirect(url_for("matrix_view"))
            else:
                raw_marks = [
                    request.form.get("math_mark"),
                    request.form.get("physics_mark"),
                    request.form.get("chemistry_mark"),
                    request.form.get("english_mark"),
                    request.form.get("cs_mark"),
                ]
                ok, cleaned, errs = validate_student_marks_row(
                    request.form.get("student_id"), request.form.get("student_name"), raw_marks, DEFAULT_SUBJECTS
                )
                if not ok:
                    for e in errs:
                        flash(e, "danger")
                else:
                    sid, sname, marks = cleaned
                    added, msg = add_student_row(sid, sname, marks, db)
                    flash(msg, "success" if added else "danger")
                    if added:
                        return redirect(url_for("matrix_view"))

        rows = get_student_matrix_rows(db)
        analysis = analyze_marks_matrix(rows, DEFAULT_SUBJECTS, settings["low_avg_threshold"], settings["pass_mark"])
        return render_template("matrix.html", analysis=analysis)

    @app.route("/matrix/delete/<student_id>", methods=["POST"])
    def delete_student(student_id):
        delete_student_by_id(student_id, app.config["DB_PATH"])
        flash(f"Removed {student_id} from marks matrix.", "success")
        return redirect(url_for("matrix_view"))

    @app.route("/sandbox", methods=["GET", "POST"])
    def sandbox():
        default_text = "\n".join([
            "S101, Kavya Nair, 95, 78, 72, 90, 96",
            "S102, Dev Patel, 82, 45, 51, 79, 85",
            "S103, Riya Sen, 74, 42, 48, 81, 76",
            "S104, Aman Verma, 88, 52, 59, 86, 91",
        ])
        raw_text = default_text
        errors = []
        settings = get_settings(app.config["DB_PATH"])

        if request.method == "POST":
            raw_text = request.form.get("matrix_text", "").strip()
            ok, parsed_rows, errors = parse_matrix_text(raw_text, DEFAULT_SUBJECTS)
            analysis = analyze_marks_matrix(parsed_rows, DEFAULT_SUBJECTS, settings["low_avg_threshold"], settings["pass_mark"]) if ok else None
        else:
            _, parsed_rows, _ = parse_matrix_text(raw_text, DEFAULT_SUBJECTS)
            analysis = analyze_marks_matrix(parsed_rows, DEFAULT_SUBJECTS, settings["low_avg_threshold"], settings["pass_mark"])

        return render_template("sandbox.html", raw_text=raw_text, errors=errors, analysis=analysis)

    @app.route("/reports/export-csv")
    def export_csv():
        db = app.config["DB_PATH"]
        settings = get_settings(db)
        rows = get_student_matrix_rows(db)
        analysis = analyze_marks_matrix(rows, DEFAULT_SUBJECTS, settings["low_avg_threshold"], settings["pass_mark"])
        out = io.StringIO()
        writer = csv.writer(out)
        writer.writerow(["Rank", "Student ID", "Student Name"] + list(DEFAULT_SUBJECTS) + ["Total", "Average", "Min", "Max", "Grade"])
        for r in analysis["ranked_rows"]:
            writer.writerow([r["rank"], r["student_id"], r["student_name"]] + r["marks"] + [r["total"], r["average"], r["min_mark"], r["max_mark"], r["grade"]])
        writer.writerow([])
        writer.writerow(["Subject", "Average", "Highest", "Lowest", "Pass Rate %", "Low Avg Alert"])
        for c in analysis["col_stats"]:
            writer.writerow([c["subject"], c["average"], c["highest"], c["lowest"], c["pass_rate"], "LOW" if c["is_low_avg"] else "OK"])
        return Response(out.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=marks_matrix_analysis.csv"})

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5042)
