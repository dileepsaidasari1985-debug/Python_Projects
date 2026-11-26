"""Password Policy Validation Engine (Case Study #29) - Flask Application."""

import csv
import io
import os
import secrets

from flask import Flask, Response, abort, flash, redirect, render_template, request, session, url_for

from database import DEFAULT_DB_PATH, add_log, get_logs, get_policy, init_db, update_policy
from password_logic import (
    DEFAULT_POLICY,
    SAMPLE_PASSWORD_TUPLES,
    evaluate_password,
    evaluate_password_batch,
    validate_policy_inputs,
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
        policy = get_policy(app.config["DB_PATH"])
        logs = get_logs(app.config["DB_PATH"])
        return {
            "current_endpoint": request.endpoint or "dashboard",
            "policy": policy,
            "nav_logs": len(logs),
        }

    @app.route("/")
    def dashboard():
        db = app.config["DB_PATH"]
        policy = get_policy(db)
        logs = get_logs(db)
        passed = sum(1 for l in logs if l["verdict"] == "PASS")
        failed = len(logs) - passed
        batch_preview = evaluate_password_batch(SAMPLE_PASSWORD_TUPLES, policy)
        return render_template("dashboard.html", logs=logs[:6], passed=passed, failed=failed, batch_preview=batch_preview)

    @app.route("/validator", methods=["GET", "POST"])
    def validator():
        db = app.config["DB_PATH"]
        policy = get_policy(db)
        sample_pw = "Campus@2026"
        sample_user = "arjun"
        sample_label = "Interactive Check"
        result = evaluate_password(sample_pw, sample_user, policy)

        if request.method == "POST":
            sample_pw = request.form.get("password", "")
            sample_user = request.form.get("username", "").strip()
            sample_label = request.form.get("sample_label", "").strip() or "Custom Sample"
            result = evaluate_password(sample_pw, sample_user, policy)
            if request.form.get("log_result") == "1":
                add_log(sample_label, sample_user or "anonymous", result, db)
                flash(f"Evaluated '{sample_label}': {result['verdict']} ({result['score']}/100).", "success" if result["is_compliant"] else "danger")

        return render_template(
            "validator.html",
            sample_pw=sample_pw,
            sample_user=sample_user,
            sample_label=sample_label,
            result=result,
        )

    @app.route("/batch", methods=["GET", "POST"])
    def batch():
        db = app.config["DB_PATH"]
        policy = get_policy(db)
        raw_lines = "\n".join(f"{lbl} | {pw} | {usr}" for lbl, pw, usr in SAMPLE_PASSWORD_TUPLES)
        batch_tuples = list(SAMPLE_PASSWORD_TUPLES)

        if request.method == "POST":
            raw_lines = request.form.get("batch_lines", "").strip()
            parsed = []
            for idx, ln in enumerate(raw_lines.splitlines(), start=1):
                if not ln.strip():
                    continue
                parts = [p.strip() for p in ln.split("|")]
                if len(parts) == 3:
                    parsed.append((parts[0], parts[1], parts[2]))
                elif len(parts) == 2:
                    parsed.append((parts[0], parts[1], ""))
                else:
                    parsed.append((f"Sample #{idx}", parts[0], ""))
            if parsed:
                batch_tuples = parsed

        results = evaluate_password_batch(batch_tuples, policy)
        return render_template("batch.html", raw_lines=raw_lines, results=results)

    @app.route("/policy", methods=["GET", "POST"])
    def policy_rules():
        db = app.config["DB_PATH"]
        if request.method == "POST":
            if request.form.get("action") == "reset":
                update_policy(DEFAULT_POLICY, db)
                flash("Password policy reset to defaults.", "success")
                return redirect(url_for("policy_rules"))
            ok, cleaned, errs = validate_policy_inputs(request.form)
            if not ok:
                for e in errs:
                    flash(e, "danger")
            else:
                update_policy(cleaned, db)
                flash("Password policy rules updated.", "success")
                return redirect(url_for("policy_rules"))
        return render_template("policy.html")

    @app.route("/logs")
    def logs():
        return render_template("logs.html", logs=get_logs(app.config["DB_PATH"]))

    @app.route("/reports/export-csv")
    def export_csv():
        logs_list = get_logs(app.config["DB_PATH"])
        out = io.StringIO()
        writer = csv.writer(out)
        writer.writerow(["ID", "Sample Label", "Username", "Masked Preview", "Length", "Verdict", "Score", "Strength", "Failed Reasons", "Timestamp"])
        for row in logs_list:
            writer.writerow([
                row["id"], row["sample_label"], row["username"], row["masked_preview"],
                row["pw_length"], row["verdict"], row["score"], row["strength_label"],
                row["failed_reasons"], row["evaluated_at"],
            ])
        return Response(out.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=password_policy_audit.csv"})

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5029)
