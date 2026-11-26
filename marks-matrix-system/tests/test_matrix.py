"""Automated tests for Student Marks Matrix Analysis (Case Study #42)."""

import os
import re
import tempfile
import unittest

from app import create_app
from matrix_logic import (
    DEFAULT_SUBJECTS,
    analyze_marks_matrix,
    compute_grade,
    parse_matrix_text,
    validate_student_marks_row,
)


class TestMarksMatrixLogic(unittest.TestCase):
    def test_01_row_and_column_statistics(self):
        rows = [
            ("S01", "Aarav", [90.0, 50.0, 60.0, 80.0, 90.0]),
            ("S02", "Diya", [80.0, 40.0, 50.0, 70.0, 80.0]),
        ]
        res = analyze_marks_matrix(rows, DEFAULT_SUBJECTS, low_avg_threshold=60.0, pass_mark=40.0)
        self.assertEqual(res["row_stats"][0]["total"], 370.0)
        self.assertEqual(res["row_stats"][0]["average"], 74.0)
        self.assertEqual(res["col_stats"][1]["subject"], "Physics")
        self.assertEqual(res["col_stats"][1]["average"], 45.0)
        self.assertTrue(res["col_stats"][1]["is_low_avg"])

    def test_02_top_performer_tie_breaking(self):
        rows = [
            ("S02", "Beta", [80.0, 80.0, 80.0, 80.0, 80.0]),
            ("S01", "Alpha", [90.0, 70.0, 80.0, 80.0, 80.0]),
        ]
        res = analyze_marks_matrix(rows, DEFAULT_SUBJECTS)
        self.assertEqual(res["top_performers"][0]["student_id"], "S02")

    def test_03_grade_and_validation(self):
        self.assertEqual(compute_grade(92.0), "A+")
        self.assertEqual(compute_grade(35.0), "F")
        ok, _, errs = validate_student_marks_row("S1", "Test", [105, 50, 50, 50, 50])
        self.assertFalse(ok)
        self.assertTrue(len(errs) == 1)

    def test_04_parse_matrix_text(self):
        ok, rows, errs = parse_matrix_text("S1, Alice, 90, 80, 70, 85, 95\nS2, Bob, 60, 50, 40, 70, 65")
        self.assertTrue(ok, errs)
        self.assertEqual(len(rows), 2)


class TestMarksMatrixFlaskApp(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.app = create_app(db_path=self.db_path)
        self.client = self.app.test_client()

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _csrf(self, url):
        m = re.search(r'name="csrf_token" value="([^"]+)"', self.client.get(url).get_data(as_text=True))
        return m.group(1) if m else ""

    def test_05_routes_and_csv(self):
        for r in ["/", "/matrix", "/sandbox"]:
            self.assertEqual(self.client.get(r).status_code, 200)
        csv_resp = self.client.get("/reports/export-csv")
        self.assertEqual(csv_resp.status_code, 200)
        self.assertIn("Low Avg Alert", csv_resp.get_data(as_text=True))

    def test_06_add_student_route(self):
        token = self._csrf("/matrix")
        resp = self.client.post("/matrix", data={
            "csrf_token": token, "action": "add", "student_id": "STU4299", "student_name": "Zoya Khan",
            "math_mark": "90", "physics_mark": "85", "chemistry_mark": "80", "english_mark": "88", "cs_mark": "94",
        }, follow_redirects=True)
        self.assertIn("STU4299", resp.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
