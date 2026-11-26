"""
Automated Test Suite for University Scholarship Allocation System
-----------------------------------------------------------------
Covers all 15+ assignment test cases using Python's built-in unittest module.
"""

import csv
import io
import os
import re
import tempfile
import unittest

from app import create_app
from database import (
    count_students,
    get_rules,
    get_student_by_id,
    init_db,
    load_sample_students,
    update_rules,
)
from scholarship_logic import (
    DEFAULT_RULES,
    calculate_academic_totals,
    calculate_scholarship_score,
    evaluate_and_rank_all,
    evaluate_eligibility,
    generate_award_banner,
    generate_merit_pattern,
    get_income_merit_score,
    validate_rules_data,
    validate_student_data,
)


def make_student_payload(**overrides):
    """Helper to build a valid student application dictionary with optional overrides."""
    base = {
        "student_id": "STU901",
        "full_name": "Kiran Rao",
        "age": "20",
        "gender": "Female",
        "department": "Computer Science",
        "academic_year": "3rd Year",
        "phone": "9876543210",
        "email": "kiran@university.edu",
        "math_marks": "90",
        "physics_marks": "85",
        "chemistry_marks": "88",
        "english_marks": "92",
        "cs_marks": "95",
        "attendance_percentage": "92",
        "annual_income": "120000",
        "income_certificate_status": "Available",
        "scholarship_category": "Merit-cum-Means",
        "application_date": "2026-10-15",
    }
    base.update(overrides)
    return base


class TestScholarshipLogic(unittest.TestCase):
    """Unit tests for validation, eligibility, scoring, ranking, and tie-breaking."""

    def test_01_valid_application_and_totals(self):
        payload = make_student_payload()
        is_valid, cleaned, errors = validate_student_data(payload)
        self.assertTrue(is_valid, f"Expected valid, got errors: {errors}")
        self.assertEqual(cleaned["total_marks"], 450.0)
        self.assertEqual(cleaned["aggregate_percentage"], 90.0)
        self.assertEqual(cleaned["student_id"], "STU901")

    def test_02_invalid_marks_out_of_range(self):
        for bad_mark in ("-5", "105", "abc"):
            payload = make_student_payload(math_marks=bad_mark)
            is_valid, _, errors = validate_student_data(payload)
            self.assertFalse(is_valid)
            self.assertTrue(any("Mathematics" in e for e in errors))

    def test_03_invalid_attendance_out_of_range(self):
        for bad_att in ("-1", "101.5"):
            payload = make_student_payload(attendance_percentage=bad_att)
            is_valid, _, errors = validate_student_data(payload)
            self.assertFalse(is_valid)
            self.assertTrue(any("Attendance" in e for e in errors))

    def test_04_negative_income_rejected(self):
        payload = make_student_payload(annual_income="-5000")
        is_valid, _, errors = validate_student_data(payload)
        self.assertFalse(is_valid)
        self.assertTrue(any("negative" in e.lower() for e in errors))

    def test_06_minimum_aggregate_boundary(self):
        # Exactly 75.00% -> Eligible
        s_pass = {
            "math_marks": 75, "physics_marks": 75, "chemistry_marks": 75,
            "english_marks": 75, "cs_marks": 75, "aggregate_percentage": 75.0,
            "attendance_percentage": 80.0, "annual_income": 100000.0,
            "income_certificate_status": "Available",
        }
        elig, reasons = evaluate_eligibility(s_pass, DEFAULT_RULES)
        self.assertTrue(elig)
        self.assertEqual(reasons, [])

        # 74.80% -> Rejected
        s_fail = dict(s_pass, math_marks=74, aggregate_percentage=74.8)
        elig_f, reasons_f = evaluate_eligibility(s_fail, DEFAULT_RULES)
        self.assertFalse(elig_f)
        self.assertTrue(any("Aggregate percentage below minimum" in r for r in reasons_f))

    def test_07_minimum_subject_boundary(self):
        # Aggregate is 85.80% (>= 75), but CS = 49 (< 50) -> Rejected
        s_fail = {
            "math_marks": 95, "physics_marks": 95, "chemistry_marks": 95,
            "english_marks": 95, "cs_marks": 49, "aggregate_percentage": 85.8,
            "attendance_percentage": 90.0, "annual_income": 100000.0,
            "income_certificate_status": "Available",
        }
        elig, reasons = evaluate_eligibility(s_fail, DEFAULT_RULES)
        self.assertFalse(elig)
        self.assertTrue(any("Computer Science (49)" in r for r in reasons))

        # CS = 50 -> Eligible
        s_pass = dict(s_fail, cs_marks=50, aggregate_percentage=86.0)
        elig_p, _ = evaluate_eligibility(s_pass, DEFAULT_RULES)
        self.assertTrue(elig_p)

    def test_08_minimum_attendance_boundary(self):
        s_pass = {
            "math_marks": 80, "physics_marks": 80, "chemistry_marks": 80,
            "english_marks": 80, "cs_marks": 80, "aggregate_percentage": 80.0,
            "attendance_percentage": 75.0, "annual_income": 100000.0,
            "income_certificate_status": "Available",
        }
        self.assertTrue(evaluate_eligibility(s_pass, DEFAULT_RULES)[0])

        s_fail = dict(s_pass, attendance_percentage=74.99)
        elig, reasons = evaluate_eligibility(s_fail, DEFAULT_RULES)
        self.assertFalse(elig)
        self.assertTrue(any("Attendance below minimum" in r for r in reasons))

    def test_09_maximum_income_boundary(self):
        s_pass = {
            "math_marks": 80, "physics_marks": 80, "chemistry_marks": 80,
            "english_marks": 80, "cs_marks": 80, "aggregate_percentage": 80.0,
            "attendance_percentage": 85.0, "annual_income": 250000.0,
            "income_certificate_status": "Available",
        }
        self.assertTrue(evaluate_eligibility(s_pass, DEFAULT_RULES)[0])
        self.assertEqual(get_income_merit_score(250000.0, DEFAULT_RULES), 40.0)

        s_fail = dict(s_pass, annual_income=250001.0)
        elig, reasons = evaluate_eligibility(s_fail, DEFAULT_RULES)
        self.assertFalse(elig)
        self.assertTrue(any("Family income exceeds limit" in r for r in reasons))

    def test_10_missing_income_certificate(self):
        s_missing = {
            "math_marks": 85, "physics_marks": 85, "chemistry_marks": 85,
            "english_marks": 85, "cs_marks": 85, "aggregate_percentage": 85.0,
            "attendance_percentage": 90.0, "annual_income": 100000.0,
            "income_certificate_status": "Missing",
        }
        elig, reasons = evaluate_eligibility(s_missing, DEFAULT_RULES)
        self.assertFalse(elig)
        self.assertIn("Income certificate missing", reasons)

        relaxed_rules = dict(DEFAULT_RULES, income_certificate_required=0)
        elig_relaxed, _ = evaluate_eligibility(s_missing, relaxed_rules)
        self.assertTrue(elig_relaxed)

    def test_11_score_calculation_and_income_slabs(self):
        self.assertEqual(get_income_merit_score(90000, DEFAULT_RULES), 100.0)
        self.assertEqual(get_income_merit_score(150000, DEFAULT_RULES), 80.0)
        self.assertEqual(get_income_merit_score(200000, DEFAULT_RULES), 60.0)
        self.assertEqual(get_income_merit_score(250000, DEFAULT_RULES), 40.0)
        self.assertEqual(get_income_merit_score(300000, DEFAULT_RULES), 0.0)

        student = {
            "aggregate_percentage": 90.0,
            "attendance_percentage": 80.0,
            "annual_income": 100000.0,
        }
        score, inc_merit = calculate_scholarship_score(student, DEFAULT_RULES)
        self.assertEqual(inc_merit, 100.0)
        # (90 * 0.70) + (80 * 0.20) + (100 * 0.10) = 63 + 16 + 10 = 89.00
        self.assertEqual(score, 89.00)

    def test_12_and_13_ranking_and_all_tie_breakers(self):
        # Construct students that test descending score AND tie-breaking order
        def mk(sid, agg, att, inc):
            return {
                "id": 1,
                "student_id": sid,
                "full_name": f"Student {sid}",
                "age": 20,
                "gender": "",
                "department": "Computer Science",
                "academic_year": "3rd Year",
                "phone": "",
                "email": "",
                "math_marks": agg,
                "physics_marks": agg,
                "chemistry_marks": agg,
                "english_marks": agg,
                "cs_marks": agg,
                "attendance_percentage": att,
                "annual_income": inc,
                "income_certificate_status": "Available",
                "scholarship_category": "Merit-cum-Means",
                "application_date": "2026-10-15",
            }

        # Both S_AGG_WIN and S_AGG_LOSE get score 81.80:
        # S_AGG_WIN: 86*0.7 + 78*0.2 + 60*0.1 = 81.80 (agg 86)
        # S_AGG_LOSE: 84*0.7 + 85*0.2 + 60*0.1 = 81.80 (agg 84)
        # Next tie on 89.00 with same agg=90, att=90, different income:
        # S_INC_WIN: inc 110k (80 pts) -> 89.00
        # S_INC_LOSE: inc 140k (80 pts) -> 89.00
        # Next tie on identical marks/att/income -> alphabetical ID:
        # STU_A vs STU_B -> STU_A wins
        students = [
            mk("STU_B", 80, 80, 100000),      # 82.00
            mk("STU_A", 80, 80, 100000),      # 82.00 (wins by ID over STU_B)
            mk("S_AGG_LOSE", 84, 85, 180000), # 81.80
            mk("S_AGG_WIN", 86, 78, 175000),  # 81.80 (wins by higher agg)
            mk("S_INC_LOSE", 90, 90, 140000), # 89.00
            mk("S_INC_WIN", 90, 90, 110000),  # 89.00 (wins by lower income)
            mk("S_REJ", 60, 90, 100000),      # Rejected (agg < 75)
        ]

        result = evaluate_and_rank_all(students, DEFAULT_RULES)
        ranked_ids = [s["student_id"] for s in result["eligible_ranked"]]
        self.assertEqual(
            ranked_ids,
            ["S_INC_WIN", "S_INC_LOSE", "STU_A", "STU_B", "S_AGG_WIN", "S_AGG_LOSE"],
        )
        self.assertEqual(len(result["rejected_students"]), 1)
        self.assertEqual(result["rejected_students"][0]["student_id"], "S_REJ")

    def test_14_scholarship_quota_and_waitlist(self):
        rules = dict(DEFAULT_RULES, scholarship_quota=2)
        students = []
        for idx, marks in enumerate((95, 90, 85, 80), start=1):
            students.append(
                {
                    "id": idx,
                    "student_id": f"STU00{idx}",
                    "full_name": f"Scholar {idx}",
                    "age": 20,
                    "gender": "",
                    "department": "Mathematics",
                    "academic_year": "2nd Year",
                    "phone": "",
                    "email": "",
                    "math_marks": marks,
                    "physics_marks": marks,
                    "chemistry_marks": marks,
                    "english_marks": marks,
                    "cs_marks": marks,
                    "attendance_percentage": 90.0,
                    "annual_income": 100000.0,
                    "income_certificate_status": "Available",
                    "scholarship_category": "Merit-cum-Means",
                    "application_date": "2026-10-15",
                }
            )
        result = evaluate_and_rank_all(students, rules)
        self.assertEqual(len(result["selected_students"]), 2)
        self.assertEqual(len(result["waitlisted_students"]), 2)
        self.assertEqual(result["selected_students"][0]["selection_status"], "Eligible & Selected")
        self.assertEqual(result["waitlisted_students"][0]["selection_status"], "Eligible (Waitlisted)")

    def test_pattern_generation_helpers(self):
        self.assertIn("★★★★★", generate_merit_pattern(92.5, True))
        self.assertIn("☆☆☆☆☆", generate_merit_pattern(0.0, False))
        banner = generate_award_banner("Aarav Sharma", "STU2026001", 1, 95.8)
        self.assertIn("RANK #1", banner)
        self.assertIn("Aarav Sharma", banner)

    def test_rules_weight_validation(self):
        bad_rules = dict(DEFAULT_RULES, weight_aggregate=0.5, weight_attendance=0.2, weight_income=0.1)
        valid, _, errors = validate_rules_data(bad_rules)
        self.assertFalse(valid)
        self.assertTrue(any("sum to 1.00" in e for e in errors))


class TestFlaskAppAndDatabase(unittest.TestCase):
    """Integration tests for Flask routes, SQLite CRUD, duplicate checks, and CSV export."""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "test_scholarship.db")
        self.app = create_app(db_path=self.db_path, seed_if_empty=True)
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_DISABLED"] = True
        self.client = self.app.test_client()

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_dashboard_and_sample_data_seeded_once(self):
        self.assertEqual(count_students(self.db_path), 18)
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Scholarship Overview", resp.data)
        self.assertIn(b"Aarav Sharma", resp.data)

        # Idempotent load should insert 0 new records and skip all 18
        inserted, skipped = load_sample_students(self.db_path)
        self.assertEqual(inserted, 0)
        self.assertEqual(skipped, 18)
        self.assertEqual(count_students(self.db_path), 18)

    def test_05_add_and_duplicate_student_id_via_route(self):
        payload = make_student_payload(student_id="STU999", full_name="Riya Sen")
        resp = self.client.post("/add", data=payload, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Riya Sen", resp.data)
        self.assertIsNotNone(get_student_by_id("STU999", self.db_path))

        # Attempt duplicate with lowercase ID
        dup_payload = make_student_payload(student_id="stu999", full_name="Duplicate Person")
        resp_dup = self.client.post("/add", data=dup_payload)
        self.assertEqual(resp_dup.status_code, 200)
        self.assertIn(b"already exists", resp_dup.data)

    def test_edit_and_delete_student(self):
        edit_payload = make_student_payload(
            student_id="STU2026001",
            full_name="Aarav Sharma Updated",
            math_marks="99",
        )
        resp = self.client.post("/student/STU2026001/edit", data=edit_payload, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Aarav Sharma Updated", resp.data)

        del_resp = self.client.post("/student/STU2026001/delete", follow_redirects=True)
        self.assertEqual(del_resp.status_code, 200)
        self.assertIsNone(get_student_by_id("STU2026001", self.db_path))

    def test_rules_update_recalculates_rankings(self):
        rules = dict(DEFAULT_RULES)
        rules["scholarship_quota"] = "3"
        rules["income_certificate_required"] = "1"
        resp = self.client.post("/rules", data=rules, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(get_rules(self.db_path)["scholarship_quota"], 3)

        rank_resp = self.client.get("/rankings")
        self.assertEqual(rank_resp.status_code, 200)
        self.assertIn(b"Quota: Top 3", rank_resp.data)

    def test_15_csv_report_export(self):
        resp = self.client.get("/reports/export-csv")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/csv", resp.content_type)

        text = resp.data.decode("utf-8-sig")
        reader = list(csv.reader(io.StringIO(text)))
        self.assertEqual(reader[0][0], "Rank")
        self.assertEqual(reader[0][1], "Student ID")
        # Header + 18 sample students = 19 rows
        self.assertEqual(len(reader), 19)
        self.assertEqual(reader[1][0], "1")

    def test_16_invalid_student_id_characters_blocked(self):
        for bad_id in ("STU/01", "STU 01", "AB", "STU?99"):
            is_valid, _, errors = validate_student_data(make_student_payload(student_id=bad_id))
            self.assertFalse(is_valid)
            self.assertTrue(any("Student ID" in e for e in errors))

    def test_17_applicants_search_filter_sort_and_sample_reload(self):
        # Search by name
        resp = self.client.get("/applicants?q=Aarav")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Aarav Sharma", resp.data)
        self.assertNotIn(b"Priya Nair", resp.data)

        # Filter rejected only
        rej_resp = self.client.get("/applicants?eligibility=rejected&sort=marks_desc")
        self.assertEqual(rej_resp.status_code, 200)
        self.assertIn(b"Arjun Malhotra", rej_resp.data)
        self.assertNotIn(b"Aarav Sharma", rej_resp.data)

        # Delete one sample student, verify Load Sample Data restores only the missing one
        self.client.post("/student/STU2026001/delete", follow_redirects=True)
        self.assertEqual(count_students(self.db_path), 17)
        reload_resp = self.client.post(
            "/load-sample-data",
            data={"next": "applicants"},
            follow_redirects=True,
        )
        self.assertEqual(reload_resp.status_code, 200)
        self.assertEqual(count_students(self.db_path), 18)
        self.assertIn(b"Loaded 1 sample student", reload_resp.data)

    def test_18_rules_reset_and_empty_db_handling(self):
        # Change rules then reset back to defaults
        custom = dict(DEFAULT_RULES, scholarship_quota="2")
        self.client.post("/rules", data=custom, follow_redirects=True)
        self.assertEqual(get_rules(self.db_path)["scholarship_quota"], 2)

        reset_resp = self.client.post("/rules", data={"action": "reset"}, follow_redirects=True)
        self.assertEqual(reset_resp.status_code, 200)
        self.assertEqual(get_rules(self.db_path)["scholarship_quota"], 10)

        # Check all pages & favicon work cleanly even when DB has 0 students
        empty_dir = tempfile.TemporaryDirectory()
        try:
            empty_db = os.path.join(empty_dir.name, "empty.db")
            empty_app = create_app(db_path=empty_db, seed_if_empty=False)
            empty_app.config["TESTING"] = True
            ec = empty_app.test_client()
            for path in ("/", "/applicants", "/rankings", "/rules", "/reports", "/reports/export-csv"):
                r = ec.get(path)
                self.assertEqual(r.status_code, 200)
            self.assertEqual(ec.get("/favicon.ico").status_code, 302)
        finally:
            empty_dir.cleanup()

    def test_19_csrf_enforcement_and_responsive_assets(self):
        # Test with CSRF enabled (real browser behavior)
        csrf_dir = tempfile.TemporaryDirectory()
        try:
            csrf_db = os.path.join(csrf_dir.name, "csrf.db")
            csrf_app = create_app(db_path=csrf_db, seed_if_empty=True)
            csrf_app.config["TESTING"] = True
            cc = csrf_app.test_client()

            # POST without CSRF token should be blocked (student not added)
            blocked = cc.post(
                "/add",
                data=make_student_payload(student_id="STU888"),
                follow_redirects=True,
            )
            self.assertIn(b"Security verification failed", blocked.data)
            self.assertIsNone(get_student_by_id("STU888", csrf_db))

            # Extract real CSRF token from /add page and submit successfully
            page = cc.get("/add")
            match = re.search(rb'name="csrf_token"\s+value="([^"]+)"', page.data)
            self.assertIsNotNone(match)
            token = match.group(1).decode("utf-8")

            ok_resp = cc.post(
                "/add",
                data=make_student_payload(student_id="STU888", full_name="Meenakshi Iyer", csrf_token=token),
                follow_redirects=True,
            )
            self.assertEqual(ok_resp.status_code, 200)
            self.assertIn(b"Meenakshi Iyer", ok_resp.data)
            self.assertIsNotNone(get_student_by_id("STU888", csrf_db))

            # Verify responsive drawer, modal dialog, and CSS container queries exist
            self.assertIn(b'id="mobile-drawer"', ok_resp.data)
            self.assertIn(b'id="confirm-delete-dialog"', ok_resp.data)
            with cc.get("/static/css/style.css") as css_resp:
                self.assertEqual(css_resp.status_code, 200)
                css_bytes = css_resp.data
            self.assertIn(b"container-type: inline-size", css_bytes)
            self.assertIn(b"@container (width < 600px)", css_bytes)
            self.assertIn(b"@media (min-width: 960px)", css_bytes)
        finally:
            csrf_dir.cleanup()

    def test_20_vercel_entrypoint_serves_pages(self):
        from api.index import app as vercel_app

        vercel_app.config["TESTING"] = True
        vc = vercel_app.test_client()
        resp = vc.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Scholarship Overview", resp.data)
        with vc.get("/static/css/style.css") as css_resp:
            self.assertEqual(css_resp.status_code, 200)

    def test_21_double_submit_csrf_survives_secret_key_rotation(self):
        # Simulate Vercel cold-start where POST hits a worker with a new random secret_key
        rot_dir = tempfile.TemporaryDirectory()
        try:
            rot_db = os.path.join(rot_dir.name, "rot.db")
            app_a = create_app(db_path=rot_db, seed_if_empty=True)
            app_a.config["TESTING"] = True
            client_a = app_a.test_client()
            page = client_a.get("/add")
            token = re.search(rb'name="csrf_token"\s+value="([^"]+)"', page.data).group(1).decode("utf-8")

            # Extract csrf_cookie set by worker A and send it to worker B (different secret_key)
            app_b = create_app(db_path=rot_db, seed_if_empty=True)
            app_b.config["TESTING"] = True
            client_b = app_b.test_client()
            client_b.set_cookie("csrf_cookie", token)
            ok_resp = client_b.post(
                "/add",
                data=make_student_payload(student_id="VERCEL1", full_name="Serverless Test", csrf_token=token),
                follow_redirects=True,
            )
            self.assertEqual(ok_resp.status_code, 200)
            self.assertIn(b"Serverless Test", ok_resp.data)
            self.assertIsNotNone(get_student_by_id("VERCEL1", rot_db))
        finally:
            rot_dir.cleanup()

    def test_22_vercel_json_routes_and_static_bundle(self):
        import json

        vercel_cfg_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "vercel.json",
        )
        with open(vercel_cfg_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)

        self.assertEqual(cfg["builds"][0]["src"], "app.py")
        self.assertEqual(cfg["builds"][0]["use"], "@vercel/python")
        include_files = cfg["builds"][0]["config"]["includeFiles"]
        self.assertIn("templates/**", include_files)
        self.assertIn("static/**", include_files)
        self.assertIn("database/**", include_files)
        self.assertEqual(cfg["routes"][0]["dest"], "app.py")

    def test_23_404_page_and_all_pages_static_urls(self):
        not_found = self.client.get("/student/NONEXISTENT999")
        self.assertEqual(not_found.status_code, 404)
        self.assertIn(b"404", not_found.data)
        self.assertIn(b"Return to Dashboard", not_found.data)

        for route in ("/", "/add", "/applicants", "/rankings", "/rules", "/reports"):
            resp = self.client.get(route)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"/static/css/style.css", resp.data)
            self.assertIn(b"/static/js/script.js", resp.data)
            self.assertIn(b"/static/images/university_crest.svg", resp.data)


if __name__ == "__main__":
    unittest.main()
