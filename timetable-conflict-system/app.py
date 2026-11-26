"""Student Timetable Conflict Detection System (Case Study #23) - Flask Application."""

import csv
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
    add_course,
    courses_to_tuples,
    delete_course,
    get_all_courses,
    get_all_proposals,
    get_all_rooms,
    get_courses_by_codes,
    get_proposal_by_id,
    get_room_tuples,
    init_db,
    load_sample_data,
    save_proposal,
    toggle_room_status,
)
from timetable_logic import (
    ROOM_STATUSES,
    VALID_DAYS,
    minutes_to_time_str,
    parse_schedule_string,
    parse_time_to_minutes,
    validate_course_fields,
    validate_proposed_timetable,
)

DEFAULT_RAW_TIMETABLE = "\n".join([
    "CS101 | Data Structures & Algorithms | Mon 09:00-10:30 | R-204",
    "CS109 | Web Engineering Elective | Mon 09:30-11:00 | R-204",
    "MA102 | Discrete Mathematics | Mon 10:30-12:00 | R-201",
    "CS106 | Operating Systems Lab | Wed 10:30-12:30 | LAB-102",
    "CS108 | Python Programming Studio | Fri 14:00-16:00 | LAB-101",
])


def create_app(db_path=None, seed_if_empty=True):
    """Application factory with configurable SQLite path for testing."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)
    app.config["DB_PATH"] = db_path or DEFAULT_DB_PATH
    app.config["SEED_IF_EMPTY"] = seed_if_empty

    init_db(app.config["DB_PATH"], seed_if_empty=seed_if_empty)

    def get_csrf_token():
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_hex(24)
        return session["csrf_token"]

    app.jinja_env.globals["csrf_token"] = get_csrf_token

    @app.template_filter("mins_to_hhmm")
    def mins_to_hhmm_filter(val):
        return minutes_to_time_str(val)

    @app.before_request
    def verify_csrf():
        if request.method == "POST":
            expected = session.get("csrf_token", "")
            submitted = request.form.get("csrf_token", "")
            if not expected or not secrets.compare_digest(expected, submitted):
                abort(400, description="Invalid or missing CSRF token.")

    @app.context_processor
    def inject_nav_context():
        db = app.config["DB_PATH"]
        courses = get_all_courses(db)
        rooms = get_all_rooms(db)
        unavail_count = sum(1 for r in rooms if r["status"] != "Available")
        return {
            "current_endpoint": request.endpoint or "dashboard",
            "nav_course_count": len(courses),
            "nav_room_count": len(rooms),
            "nav_unavail_count": unavail_count,
            "valid_days": VALID_DAYS,
        }

    @app.route("/")
    def dashboard():
        db = app.config["DB_PATH"]
        courses = get_all_courses(db)
        rooms = get_all_rooms(db)
        proposals = get_all_proposals(db)
        room_tuples = get_room_tuples(db)
        catalog_report = validate_proposed_timetable(courses_to_tuples(courses), room_tuples)

        valid_proposals = sum(1 for p in proposals if p["is_valid"] == 1)
        conflicted_proposals = len(proposals) - valid_proposals
        avail_rooms = sum(1 for r in rooms if r["status"] == "Available")

        return render_template(
            "dashboard.html",
            courses=courses,
            rooms=rooms,
            proposals=proposals[:5],
            catalog_report=catalog_report,
            valid_proposals=valid_proposals,
            conflicted_proposals=conflicted_proposals,
            avail_rooms=avail_rooms,
        )

    @app.route("/validator", methods=["GET", "POST"])
    def validator():
        db = app.config["DB_PATH"]
        all_courses = get_all_courses(db)
        room_tuples = get_room_tuples(db)

        mode = "catalog"
        selected_codes = ["CS101", "CS109", "MA102", "CS106", "CS108"]
        raw_text = DEFAULT_RAW_TIMETABLE
        parse_errors = []
        saved_id = None

        if request.method == "POST":
            mode = request.form.get("input_mode", "catalog")
            action = request.form.get("action", "validate")
            student_id = request.form.get("student_id", "STU2399").strip().upper() or "STU2399"
            student_name = request.form.get("student_name", "Demo Student").strip() or "Demo Student"
            semester = request.form.get("semester", "Fall 2026").strip() or "Fall 2026"

            course_tuples = []
            if mode == "strings":
                raw_text = request.form.get("raw_schedules", "").strip()
                lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip()]
                if not lines:
                    parse_errors.append("Please enter at least one schedule string line.")
                for idx, line in enumerate(lines, start=1):
                    ok, parsed, err = parse_schedule_string(line)
                    if ok:
                        course_tuples.append(parsed)
                    else:
                        parse_errors.append(f"Line {idx}: {err}")
            else:
                selected_codes = request.form.getlist("course_codes")
                if not selected_codes:
                    parse_errors.append("Select at least one course to validate.")
                else:
                    picked = get_courses_by_codes(selected_codes, db)
                    course_tuples = courses_to_tuples(picked)

            report = validate_proposed_timetable(course_tuples, room_tuples) if not parse_errors else None

            if report and action == "save":
                codes_csv = ",".join(c[0] for c in course_tuples)
                if report["is_valid"]:
                    summary = f"Valid timetable ({len(course_tuples)} courses, 0 conflicts)."
                else:
                    msgs = [tc["message"] for tc in report["time_conflicts"]] + [ri["reason"] for ri in report["room_issues"]]
                    summary = " | ".join(msgs[:3])
                saved_id = save_proposal(
                    student_id,
                    student_name,
                    semester,
                    codes_csv,
                    report["is_valid"],
                    report["total_conflicts"],
                    summary,
                    db,
                )
                flash(f"Timetable proposal {saved_id} saved ({report['status_label']}).", "success" if report["is_valid"] else "warning")
        else:
            picked = get_courses_by_codes(selected_codes, db)
            course_tuples = courses_to_tuples(picked)
            report = validate_proposed_timetable(course_tuples, room_tuples)

        return render_template(
            "validator.html",
            all_courses=all_courses,
            mode=mode,
            selected_codes=selected_codes,
            raw_text=raw_text,
            parse_errors=parse_errors,
            report=report,
            saved_id=saved_id,
        )

    @app.route("/courses", methods=["GET", "POST"])
    def courses():
        db = app.config["DB_PATH"]
        rooms = get_all_rooms(db)

        if request.method == "POST":
            ok, cleaned, errors = validate_course_fields(
                request.form.get("course_code"),
                request.form.get("course_title"),
                request.form.get("instructor"),
                request.form.get("day"),
                request.form.get("start_time"),
                request.form.get("end_time"),
                request.form.get("room_code"),
                request.form.get("credits", "3"),
            )
            if not ok:
                for err in errors:
                    flash(err, "danger")
            else:
                added, msg = add_course(cleaned, db)
                flash(msg, "success" if added else "danger")
                if added:
                    return redirect(url_for("courses"))

        day_filter = request.args.get("day", "").strip()
        search = request.args.get("q", "").strip()
        course_list = get_all_courses(db, day_filter=day_filter, search=search)
        return render_template(
            "courses.html",
            courses=course_list,
            rooms=rooms,
            day_filter=day_filter,
            search=search,
        )

    @app.route("/courses/<int:course_id>/delete", methods=["POST"])
    def remove_course(course_id):
        delete_course(course_id, app.config["DB_PATH"])
        flash("Course removed from schedule catalog.", "success")
        return redirect(url_for("courses"))

    @app.route("/rooms", methods=["GET", "POST"])
    def rooms():
        db = app.config["DB_PATH"]
        if request.method == "POST":
            room_id = request.form.get("room_id", type=int)
            status = request.form.get("status", "Available")
            un_day = request.form.get("unavailable_day", "ALL").strip() or "ALL"
            reason = request.form.get("reason", "").strip() or ("Operational" if status == "Available" else "Scheduled block")
            ok_s, s_min, _, _ = parse_time_to_minutes(request.form.get("start_time", "08:00"))
            ok_e, e_min, _, _ = parse_time_to_minutes(request.form.get("end_time", "18:00"))
            if not (ok_s and ok_e and e_min > s_min):
                s_min, e_min = 420, 1260
            if status not in ROOM_STATUSES:
                flash("Invalid room status.", "danger")
            elif room_id:
                toggle_room_status(room_id, status, un_day, s_min, e_min, reason, db)
                flash("Room availability updated.", "success")
            return redirect(url_for("rooms"))

        room_list = get_all_rooms(db)
        return render_template("rooms.html", rooms=room_list, room_statuses=ROOM_STATUSES)

    @app.route("/proposals")
    def proposals():
        db = app.config["DB_PATH"]
        proposal_list = get_all_proposals(db)
        return render_template("proposals.html", proposals=proposal_list)

    @app.route("/proposals/<proposal_id>")
    def proposal_detail(proposal_id):
        db = app.config["DB_PATH"]
        prop = get_proposal_by_id(proposal_id, db)
        if not prop:
            abort(404)
        codes = [c.strip() for c in prop["course_codes_csv"].split(",") if c.strip()]
        picked = get_courses_by_codes(codes, db)
        report = validate_proposed_timetable(courses_to_tuples(picked), get_room_tuples(db))
        return render_template("proposal_detail.html", proposal=prop, courses=picked, report=report)

    @app.route("/reports")
    def reports():
        db = app.config["DB_PATH"]
        courses_list = get_all_courses(db)
        rooms_list = get_all_rooms(db)
        proposals_list = get_all_proposals(db)
        report = validate_proposed_timetable(courses_to_tuples(courses_list), get_room_tuples(db))
        return render_template(
            "reports.html",
            courses=courses_list,
            rooms=rooms_list,
            proposals=proposals_list,
            report=report,
        )

    @app.route("/reports/export-csv")
    def export_csv():
        db = app.config["DB_PATH"]
        courses_list = get_all_courses(db)
        report = validate_proposed_timetable(courses_to_tuples(courses_list), get_room_tuples(db))

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Course Code", "Course Title", "Day", "Start Time", "End Time", "Room", "Credits", "Schedule String"])
        for c in courses_list:
            writer.writerow([
                c["course_code"],
                c["course_title"],
                c["day"],
                c["start_time"],
                c["end_time"],
                c["room_code"],
                c["credits"],
                c["schedule_string"],
            ])
        writer.writerow([])
        writer.writerow(["Conflict Type", "Course A", "Course B", "Day", "Window", "Details"])
        for tc in report["time_conflicts"]:
            writer.writerow([tc["kind"], tc["course_a"], tc["course_b"], tc["day"], tc["overlap_window"], tc["message"]])
        for ri in report["room_issues"]:
            writer.writerow(["ROOM_UNAVAILABLE", ri["course_code"], ri["room_code"], ri["day"], ri["slot"], ri["reason"]])

        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=timetable_conflict_report.csv"},
        )

    @app.route("/reload-samples", methods=["POST"])
    def reload_samples():
        load_sample_data(app.config["DB_PATH"])
        flash("Sample rooms, courses, and timetable proposals ensured.", "success")
        return redirect(url_for("dashboard"))

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5023)
