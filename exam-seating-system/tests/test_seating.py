"""Automated tests for Nested Loop Examination Seating Generator (Case Study #26)."""

import os
import re
import tempfile
import unittest

from app import create_app
from seating_logic import (
    build_seat_id,
    generate_seating_plan,
    generate_sequential_rolls,
    parse_reserved_positions,
    validate_hall_inputs,
)


class TestSeatingLogic(unittest.TestCase):
    def test_01_seat_identifier(self):
        self.assertEqual(build_seat_id(0, 0), ("A", 1, "A1"))
        self.assertEqual(build_seat_id(2, 4), ("C", 5, "C5"))

    def test_02_reserved_positions_bounds(self):
        ok, resv, errs = parse_reserved_positions("a1:proctor, b3", 4, 4)
        self.assertTrue(ok, errs)
        self.assertEqual(resv, [("A1", "PROCTOR"), ("B3", "RESERVED")])

        bad_ok, _, bad_errs = parse_reserved_positions("Z9:PROCTOR", 4, 4)
        self.assertFalse(bad_ok)
        self.assertEqual(len(bad_errs), 1)

    def test_03_checkerboard_and_reserved_positions(self):
        rolls = generate_sequential_rolls("26CS", 1, 6)
        plan = generate_seating_plan("HALL-A", 3, 4, 10, rolls, [("A1", "PROCTOR")], "ALTERNATE_CHECKERBOARD")
        self.assertEqual(plan["matrix"][0]["cells"][0]["status"], "RESERVED")
        self.assertEqual(plan["matrix"][0]["cells"][1]["status"], "GAP")
        self.assertEqual(plan["matrix"][0]["cells"][2]["status"], "OCCUPIED")
        self.assertEqual(plan["assigned_count"], 5)
        self.assertEqual(len(plan["unassigned_students"]), 1)

    def test_04_fixed_capacity_enforcement(self):
        rolls = generate_sequential_rolls("26IT", 1, 10)
        plan = generate_seating_plan("HALL-B", 3, 4, 5, rolls, [], "FULL_CAPACITY")
        self.assertEqual(plan["assigned_count"], 5)
        self.assertEqual(plan["cap_blocked_count"], 7)
        self.assertEqual(len(plan["unassigned_students"]), 5)

    def test_05_validate_hall_inputs(self):
        ok, cleaned, _ = validate_hall_inputs("Hall 1", "5", "6", "20")
        self.assertTrue(ok)
        self.assertEqual(cleaned["capacity"], 20)
        bad_ok, _, errs = validate_hall_inputs("", "0", "20", "999")
        self.assertFalse(bad_ok)
        self.assertGreaterEqual(len(errs), 3)


class TestSeatingFlaskApp(unittest.TestCase):
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

    def test_06_routes_and_csv(self):
        for r in ["/", "/generator", "/halls", "/plans", "/plans/PLAN-2026-001"]:
            self.assertEqual(self.client.get(r).status_code, 200)
        csv_resp = self.client.get("/reports/export-csv")
        self.assertEqual(csv_resp.status_code, 200)
        self.assertIn("Seat ID", csv_resp.get_data(as_text=True))

    def test_07_generate_and_save_plan(self):
        token = self._csrf("/generator")
        resp = self.client.post("/generator", data={
            "csrf_token": token,
            "exam_title": "OS Quiz",
            "hall_name": "HALL-101",
            "rows": "4",
            "cols": "5",
            "fixed_capacity": "8",
            "seating_mode": "ALTERNATE_COLUMN",
            "reserved_spec": "A1:PROCTOR",
            "students_text": "26CS001, 26CS002, 26CS003, 26CS004",
            "action": "save",
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("PLAN-2026-003", resp.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
