"""Comprehensive Smart Campus Management Simulation (Case Study #100) - Flask App."""

import csv
import io
import os
import secrets

from flask import Flask, Response, abort, flash, redirect, render_template, request, session, url_for

from campus_logic import (
    ACADEMIC_YEARS,
    DEPARTMENTS,
    build_campus_summary,
    check_resource_allocation,
    evaluate_attendance_record,
    process_event_registration,
    validate_student_record,
)
from database import (
    DEFAULT_DB_PATH,
    add_student,
    allocate_resource,
    get_allocations,
    get_events,
    get_registrations,
    get_resources,
    get_students,
    init_db,
    register_student_event,
    update_attendance,
    update_marks,
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
        return {
            "current_endpoint": request.endpoint or "dashboard",
            "nav_students": len(get_students(db)),
            "nav_events": len(get_events(db)),
            "departments": DEPARTMENTS,
            "years": ACADEMIC_YEARS,
        }

    def _full_summary():
        db = app.config["DB_PATH"]
        students = get_students(db)
        events = get_events(db)
        regs = get_registrations(db)
        resources = get_resources(db)
        allocs = get_allocations(db)
        summary = build_campus_summary(students, events, regs, resources, allocs)
        return students, events, regs, resources, allocs, summary

    @app.route("/")
    def dashboard():
        students, events, regs, resources, allocs, summary = _full_summary()
        return render_template("dashboard.html", students=students, summary=summary)

    @app.route("/students", methods=["GET", "POST"])
    def students_page():
        db = app.config["DB_PATH"]
        if request.method == "POST":
            ok, cleaned, errs = validate_student_record(
                request.form.get("student_id"),
                request.form.get("name"),
                request.form.get("department"),
                request.form.get("year"),
            )
            if not ok:
                for e in errs:
                    flash(e, "danger")
            else:
                sid, sname, dept, yr = cleaned
                added, msg = add_student(sid, sname, dept, yr, db)
                flash(msg, "success" if added else "danger")
            return redirect(url_for("students_page"))
        students, _, _, _, _, _ = _full_summary()
        return render_template("students.html", students=students)

    @app.route("/academics", methods=["GET", "POST"])
    def academics():
        db = app.config["DB_PATH"]
        if request.method == "POST":
            action = request.form.get("action")
            sid = request.form.get("student_id", "").strip().upper()
            if action == "attendance":
                ok, att, tot, pct, err = evaluate_attendance_record(request.form.get("attended"), request.form.get("total"))
                if ok:
                    update_attendance(sid, att, tot, db)
                    flash(f"Updated attendance for {sid} to {pct}%.", "success")
                else:
                    flash(err, "danger")
            elif action == "marks":
                try:
                    m1 = float(request.form.get("math_mark", 0))
                    m2 = float(request.form.get("cs_mark", 0))
                    m3 = float(request.form.get("eng_mark", 0))
                    if 0 <= m1 <= 100 and 0 <= m2 <= 100 and 0 <= m3 <= 100:
                        update_marks(sid, m1, m2, m3, db)
                        flash(f"Updated marks for {sid}.", "success")
                    else:
                        flash("Marks must be between 0 and 100.", "danger")
                except ValueError:
                    flash("Marks must be numeric.", "danger")
            return redirect(url_for("academics"))
        students, _, _, _, _, _ = _full_summary()
        return render_template("academics.html", students=students)

    @app.route("/events", methods=["GET", "POST"])
    def events_page():
        db = app.config["DB_PATH"]
        if request.method == "POST":
            sid = request.form.get("student_id", "").strip().upper()
            ecode = request.form.get("event_code", "").strip().upper()
            ok, msg = process_event_registration(sid, ecode, get_events(db), get_registrations(db))
            if ok:
                register_student_event(sid, ecode, db)
                flash(msg, "success")
            else:
                flash(msg, "danger")
            return redirect(url_for("events_page"))
        students, _, regs, _, _, summary = _full_summary()
        return render_template("events.html", students=students, event_summary=summary["event_summary"], registrations=regs)

    @app.route("/resources", methods=["GET", "POST"])
    def resources_page():
        db = app.config["DB_PATH"]
        if request.method == "POST":
            rcode = request.form.get("resource_code", "").strip().upper()
            req = request.form.get("requester_id", "").strip().upper()
            slot = request.form.get("slot_label", "").strip()
            purpose = request.form.get("purpose", "").strip() or "Academic Activity"
            ok, msg = check_resource_allocation(rcode, req, slot, get_resources(db), get_allocations(db))
            if ok:
                allocate_resource(rcode, req, slot, purpose, db)
                flash(msg, "success")
            else:
                flash(msg, "danger")
            return redirect(url_for("resources_page"))
        students, _, _, resources, allocs, _ = _full_summary()
        return render_template("resources.html", students=students, resources=resources, allocations=allocs)

    @app.route("/reports")
    def reports():
        students, _, _, _, _, summary = _full_summary()
        return render_template("reports.html", students=students, summary=summary)

    @app.route("/reports/export-csv")
    def export_csv():
        students, _, _, _, _, _ = _full_summary()
        out = io.StringIO()
        writer = csv.writer(out)
        writer.writerow(["Student ID", "Name", "Department", "Year", "Attendance %", "Math", "CS", "English", "Average %", "Grade"])
        for s in students:
            writer.writerow([s["student_id"], s["name"], s["department"], s["year"], s["attendance_pct"], s["math_mark"], s["cs_mark"], s["eng_mark"], s["avg_marks"], s["grade"]])
        return Response(out.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=smart_campus_report.csv"})

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5100)
