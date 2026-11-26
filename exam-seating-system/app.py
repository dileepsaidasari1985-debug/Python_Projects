"""Nested Loop Examination Seating Generator (Case Study #26) - Flask Application."""

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
    add_hall,
    get_all_halls,
    get_all_plans,
    get_hall_by_name,
    get_plan_by_id,
    init_db,
    save_plan,
)
from seating_logic import (
    SEATING_MODES,
    generate_seating_plan,
    generate_sequential_rolls,
    parse_reserved_positions,
    parse_roll_numbers,
    validate_hall_inputs,
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
            "nav_halls": len(get_all_halls(db)),
            "nav_plans": len(get_all_plans(db)),
        }

    @app.route("/")
    def dashboard():
        db = app.config["DB_PATH"]
        halls = get_all_halls(db)
        plans = get_all_plans(db)
        default_hall = halls[0] if halls else {"hall_name": "HALL-101", "rows": 5, "cols": 6, "fixed_capacity": 16, "default_reserved": "A1:PROCTOR"}
        _, resv_tuples, _ = parse_reserved_positions(default_hall["default_reserved"], default_hall["rows"], default_hall["cols"])
        preview_plan = generate_seating_plan(
            default_hall["hall_name"],
            default_hall["rows"],
            default_hall["cols"],
            default_hall["fixed_capacity"],
            generate_sequential_rolls("26CS", 1, 12),
            resv_tuples,
            "ALTERNATE_CHECKERBOARD",
        )
        return render_template("dashboard.html", halls=halls, plans=plans, preview_plan=preview_plan)

    @app.route("/generator", methods=["GET", "POST"])
    def generator():
        db = app.config["DB_PATH"]
        halls = get_all_halls(db)
        selected_hall = halls[0] if halls else {"hall_name": "HALL-101", "rows": 5, "cols": 6, "fixed_capacity": 16, "default_reserved": "A1:PROCTOR,A6:ACCESSIBLE"}

        form_data = {
            "exam_title": "CS301 Algorithms Mid-Semester",
            "hall_name": selected_hall["hall_name"],
            "rows": selected_hall["rows"],
            "cols": selected_hall["cols"],
            "fixed_capacity": selected_hall["fixed_capacity"],
            "reserved_spec": selected_hall["default_reserved"],
            "seating_mode": "ALTERNATE_CHECKERBOARD",
            "students_text": ", ".join(generate_sequential_rolls("26CS", 1, 14)),
        }
        errors = []
        plan = None

        if request.method == "POST":
            form_data["exam_title"] = request.form.get("exam_title", "").strip() or "Examination Seating"
            form_data["hall_name"] = request.form.get("hall_name", selected_hall["hall_name"]).strip().upper()
            form_data["rows"] = request.form.get("rows", selected_hall["rows"])
            form_data["cols"] = request.form.get("cols", selected_hall["cols"])
            form_data["fixed_capacity"] = request.form.get("fixed_capacity", selected_hall["fixed_capacity"])
            form_data["reserved_spec"] = request.form.get("reserved_spec", "").strip()
            form_data["seating_mode"] = request.form.get("seating_mode", "ALTERNATE_CHECKERBOARD")
            form_data["students_text"] = request.form.get("students_text", "").strip()

            ok_hall, cleaned, hall_errs = validate_hall_inputs(
                form_data["hall_name"], form_data["rows"], form_data["cols"], form_data["fixed_capacity"]
            )
            errors.extend(hall_errs)

            if ok_hall:
                ok_resv, resv_tuples, resv_errs = parse_reserved_positions(
                    form_data["reserved_spec"], cleaned["rows"], cleaned["cols"]
                )
                errors.extend(resv_errs)
                rolls = parse_roll_numbers(form_data["students_text"])
                if not rolls:
                    errors.append("Enter at least one student roll number.")

                if ok_resv and rolls and not errors:
                    plan = generate_seating_plan(
                        cleaned["hall_name"],
                        cleaned["rows"],
                        cleaned["cols"],
                        cleaned["capacity"],
                        rolls,
                        resv_tuples,
                        form_data["seating_mode"],
                    )
                    if request.form.get("action") == "save":
                        pid = save_plan(
                            form_data["exam_title"],
                            cleaned["hall_name"],
                            form_data["seating_mode"],
                            plan["assigned_count"],
                            len(plan["unassigned_students"]),
                            form_data["reserved_spec"],
                            ",".join(rolls),
                            db,
                        )
                        flash(f"Seating plan {pid} saved successfully.", "success")
        else:
            _, resv_tuples, _ = parse_reserved_positions(form_data["reserved_spec"], int(form_data["rows"]), int(form_data["cols"]))
            rolls = parse_roll_numbers(form_data["students_text"])
            plan = generate_seating_plan(
                form_data["hall_name"],
                int(form_data["rows"]),
                int(form_data["cols"]),
                int(form_data["fixed_capacity"]),
                rolls,
                resv_tuples,
                form_data["seating_mode"],
            )

        return render_template("generator.html", halls=halls, modes=SEATING_MODES, form_data=form_data, errors=errors, plan=plan)

    @app.route("/halls", methods=["GET", "POST"])
    def halls():
        db = app.config["DB_PATH"]
        if request.method == "POST":
            ok, cleaned, errs = validate_hall_inputs(
                request.form.get("hall_name"),
                request.form.get("rows"),
                request.form.get("cols"),
                request.form.get("fixed_capacity"),
            )
            building = request.form.get("building", "").strip() or "Main Campus"
            resv_raw = request.form.get("default_reserved", "").strip()
            if not ok:
                for e in errs:
                    flash(e, "danger")
            else:
                ok_r, _, r_errs = parse_reserved_positions(resv_raw, cleaned["rows"], cleaned["cols"])
                if not ok_r:
                    for e in r_errs:
                        flash(e, "danger")
                else:
                    added, msg = add_hall(cleaned["hall_name"], building, cleaned["rows"], cleaned["cols"], cleaned["capacity"], resv_raw, db)
                    flash(msg, "success" if added else "danger")
            return redirect(url_for("halls"))

        return render_template("halls.html", halls=get_all_halls(db))

    @app.route("/plans")
    def plans():
        return render_template("plans.html", plans=get_all_plans(app.config["DB_PATH"]))

    @app.route("/plans/<plan_id>")
    def plan_detail(plan_id):
        db = app.config["DB_PATH"]
        saved = get_plan_by_id(plan_id, db)
        if not saved:
            abort(404)
        hall = get_hall_by_name(saved["hall_name"], db) or {"rows": 5, "cols": 6, "fixed_capacity": 20}
        _, resv_tuples, _ = parse_reserved_positions(saved["reserved_spec"], hall["rows"], hall["cols"])
        rolls = parse_roll_numbers(saved["students_csv"])
        plan = generate_seating_plan(
            saved["hall_name"], hall["rows"], hall["cols"], hall["fixed_capacity"], rolls, resv_tuples, saved["seating_mode"]
        )
        return render_template("plan_detail.html", saved=saved, plan=plan)

    @app.route("/reports/export-csv")
    def export_csv():
        db = app.config["DB_PATH"]
        plans_list = get_all_plans(db)
        first = plans_list[0] if plans_list else None
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Seat ID", "Coordinate", "Status", "Assigned Roll / Tag"])
        if first:
            hall = get_hall_by_name(first["hall_name"], db) or {"rows": 5, "cols": 6, "fixed_capacity": 20}
            _, resv_tuples, _ = parse_reserved_positions(first["reserved_spec"], hall["rows"], hall["cols"])
            rolls = parse_roll_numbers(first["students_csv"])
            plan = generate_seating_plan(first["hall_name"], hall["rows"], hall["cols"], hall["fixed_capacity"], rolls, resv_tuples, first["seating_mode"])
            for row in plan["matrix"]:
                for cell in row["cells"]:
                    writer.writerow([cell["seat_id"], cell["coord"], cell["status"], cell["student"]])

        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=exam_seating_chart.csv"},
        )

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5026)
