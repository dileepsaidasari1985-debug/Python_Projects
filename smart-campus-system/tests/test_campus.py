"""Automated tests for Comprehensive Smart Campus Management Simulation (Case Study #100)."""

import os
import re
import tempfile
import unittest

from app import create_app
from campus_logic import (
    check_resource_allocation,
    evaluate_attendance_record,
    evaluate_marks_tuple,
    process_event_registration,
    validate_student_record,
)


class TestCampusLogic(unittest.TestCase):
    def test_01_student_record_validation(self):
        ok, tup, errs = validate_student_record("camp201", "  ananya   rao ", "Computer Science", "2nd Year")
        self.assertTrue(ok, errs)
        self.assertEqual(tup, ("CAMP201", "Ananya Rao", "Computer Science", "2nd Year"))

        bad_ok, _, bad_errs = validate_student_record("A", "", "Unknown", "9th Year")
        self.assertFalse(bad_ok)
        self.assertEqual(len(bad_errs), 4)

    def test_02_attendance_and_marks(self):
        ok, _, _, pct, _ = evaluate_attendance_record("36", "48")
        self.assertTrue(ok)
        self.assertEqual(pct, 75.0)
        bad_ok, _, _, _, _ = evaluate_attendance_record("50", "48")
        self.assertFalse(bad_ok)

        total, avg, grade, passed = evaluate_marks_tuple((90.0, 95.0, 85.0))
        self.assertEqual(total, 270.0)
        self.assertEqual(avg, 90.0)
        self.assertEqual(grade, "A+")
        self.assertTrue(passed)

    def test_03_event_registration_capacity_and_duplicates(self):
        events = [{"event_code": "EVT103", "event_name": "Coding Cup", "capacity": 2}]
        regs = [{"student_id": "CAMP101", "event_code": "EVT103"}]
        ok_dup, _ = process_event_registration("CAMP101", "EVT103", events, regs)
        self.assertFalse(ok_dup)

        ok_new, _ = process_event_registration("CAMP102", "EVT103", events, regs)
        self.assertTrue(ok_new)

        regs.append({"student_id": "CAMP102", "event_code": "EVT103"})
        ok_full, msg_full = process_event_registration("CAMP103", "EVT103", events, regs)
        self.assertFalse(ok_full)
        self.assertIn("full", msg_full)

    def test_04_resource_allocation_conflicts(self):
        resources = [
            {"resource_code": "RES-LAB1", "resource_name": "Lab 1", "status": "Available"},
            {"resource_code": "RES-CONF", "resource_name": "Conf", "status": "Maintenance"},
        ]
        allocs = [{"resource_code": "RES-LAB1", "requester_id": "CAMP101", "slot_label": "Mon 14:00-16:00"}]
        ok_maint, _ = check_resource_allocation("RES-CONF", "CAMP102", "Tue 10:00", resources, allocs)
        self.assertFalse(ok_maint)
        ok_clash, _ = check_resource_allocation("RES-LAB1", "CAMP102", "Mon 14:00-16:00", resources, allocs)
        self.assertFalse(ok_clash)
        ok_free, _ = check_resource_allocation("RES-LAB1", "CAMP102", "Tue 14:00-16:00", resources, allocs)
        self.assertTrue(ok_free)


class TestCampusFlaskApp(unittest.TestCase):
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
        for r in ["/", "/students", "/academics", "/events", "/resources", "/reports"]:
            self.assertEqual(self.client.get(r).status_code, 200)
        csv_resp = self.client.get("/reports/export-csv")
        self.assertEqual(csv_resp.status_code, 200)
        self.assertIn("Attendance %", csv_resp.get_data(as_text=True))

    def test_06_add_student_and_register_event(self):
        token = self._csrf("/students")
        resp = self.client.post("/students", data={
            "csrf_token": token,
            "student_id": "CAMP901",
            "name": "Devika Menon",
            "department": "Computer Science",
            "year": "2nd Year",
        }, follow_redirects=True)
        self.assertIn("CAMP901", resp.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
