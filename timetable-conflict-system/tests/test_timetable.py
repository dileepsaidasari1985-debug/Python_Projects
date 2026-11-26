"""Automated unit and integration tests for Timetable Conflict Detection (Case Study #23)."""

import os
import re
import tempfile
import unittest

from app import create_app
from timetable_logic import (
    detect_overlapping_periods,
    detect_unavailable_rooms,
    intervals_overlap,
    parse_schedule_string,
    validate_course_fields,
    validate_proposed_timetable,
)


class TestTimetableLogic(unittest.TestCase):
    def test_01_parse_valid_schedule_string(self):
        ok, tup, err = parse_schedule_string("cs101 | Data Structures | Mon 09:00-10:30 | r-204")
        self.assertTrue(ok, err)
        self.assertEqual(tup[0], "CS101")
        self.assertEqual(tup[2], "Mon")
        self.assertEqual(tup[5], 540)
        self.assertEqual(tup[6], 630)
        self.assertEqual(tup[7], "R-204")

    def test_02_parse_invalid_schedule_strings(self):
        for bad in ["", "CS101 | Mon", "CS101 | Fun 09:00-10:00 | R1", "CS101 | Mon 11:00-10:00 | R1"]:
            ok, _, err = parse_schedule_string(bad)
            self.assertFalse(ok)
            self.assertTrue(len(err) > 0)

    def test_03_adjacent_intervals_do_not_overlap(self):
        self.assertFalse(intervals_overlap(540, 630, 630, 720))
        self.assertTrue(intervals_overlap(540, 630, 570, 660))

    def test_04_detect_overlapping_periods_and_same_room_clash(self):
        c1 = parse_schedule_string("CS101 | DSA | Mon 09:00-10:30 | R-204")[1]
        c2 = parse_schedule_string("CS109 | Web | Mon 09:30-11:00 | R-204")[1]
        c3 = parse_schedule_string("MA102 | Math | Mon 10:30-12:00 | R-201")[1]
        conflicts = detect_overlapping_periods([c1, c2, c3])
        self.assertEqual(len(conflicts), 2)
        self.assertEqual(conflicts[0]["kind"], "TIME_AND_ROOM_CLASH")
        self.assertEqual(conflicts[0]["overlap_window"], "09:30-10:30")
        self.assertEqual(conflicts[1]["kind"], "STUDENT_TIME_OVERLAP")

    def test_05_detect_unavailable_and_unknown_rooms(self):
        rooms = [
            ("R-201", "Block A", 60, "Available", "ALL", 0, 0, "OK"),
            ("LAB-102", "CS Wing", 40, "Maintenance", "Wed", 600, 780, "Switch upgrade"),
        ]
        c_ok = parse_schedule_string("CS101 | DSA | Mon 09:00-10:30 | R-201")[1]
        c_maint = parse_schedule_string("CS106 | OS Lab | Wed 10:30-12:30 | LAB-102")[1]
        c_unknown = parse_schedule_string("CS999 | Ghost | Thu 10:00-11:00 | Z-999")[1]
        issues = detect_unavailable_rooms([c_ok, c_maint, c_unknown], rooms)
        self.assertEqual(len(issues), 2)
        self.assertEqual(issues[0]["status"], "Maintenance")
        self.assertEqual(issues[1]["status"], "Unknown")

    def test_06_validate_proposed_timetable_and_suggestions(self):
        rooms = [
            ("R-201", "Block A", 60, "Available", "ALL", 0, 0, "OK"),
            ("R-204", "Block A", 60, "Available", "ALL", 0, 0, "OK"),
        ]
        c1 = parse_schedule_string("CS101 | DSA | Mon 09:00-10:30 | R-204")[1]
        c2 = parse_schedule_string("CS102 | Algo | Mon 10:30-12:00 | R-201")[1]
        valid_rep = validate_proposed_timetable([c1, c2], rooms)
        self.assertTrue(valid_rep["is_valid"])
        self.assertIn("VALID TIMETABLE", valid_rep["ascii_pattern"])

        c3 = parse_schedule_string("CS109 | Web | Mon 09:30-11:00 | R-204")[1]
        bad_rep = validate_proposed_timetable([c1, c3], rooms)
        self.assertFalse(bad_rep["is_valid"])
        self.assertEqual(bad_rep["total_conflicts"], 1)
        self.assertTrue(len(bad_rep["suggestions"]) >= 1)

    def test_07_validate_course_fields(self):
        ok, cleaned, errs = validate_course_fields("cs205", "AI", "Dr. Rao", "Tue", "14:00", "15:30", "r-201", "4")
        self.assertTrue(ok, errs)
        self.assertEqual(cleaned["course_code"], "CS205")
        bad_ok, _, bad_errs = validate_course_fields("", "", "", "Funday", "15:00", "14:00", "", "9")
        self.assertFalse(bad_ok)
        self.assertGreaterEqual(len(bad_errs), 4)


class TestTimetableFlaskApp(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.app = create_app(db_path=self.db_path)
        self.client = self.app.test_client()

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _get_csrf(self, url):
        resp = self.client.get(url)
        m = re.search(r'name="csrf_token" value="([^"]+)"', resp.get_data(as_text=True))
        return m.group(1) if m else ""

    def test_08_all_pages_return_200(self):
        for route in ["/", "/validator", "/courses", "/rooms", "/proposals", "/proposals/TT-2026-001", "/reports"]:
            resp = self.client.get(route)
            self.assertEqual(resp.status_code, 200, f"Route {route} failed")

    def test_09_string_validator_and_save_proposal(self):
        token = self._get_csrf("/validator")
        resp = self.client.post("/validator", data={
            "csrf_token": token,
            "input_mode": "strings",
            "action": "save",
            "student_id": "STU2401",
            "student_name": "Kiran Rao",
            "raw_schedules": "CS101 | DSA | Mon 09:00-10:00 | R-201\nCS102 | Algo | Tue 09:00-10:00 | R-201",
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("VALID TIMETABLE", resp.get_data(as_text=True))

    def test_10_add_course_and_csv_export(self):
        token = self._get_csrf("/courses")
        resp = self.client.post("/courses", data={
            "csrf_token": token,
            "course_code": "CS299",
            "course_title": "Cloud Systems",
            "instructor": "Dr. Bose",
            "day": "Thu",
            "start_time": "14:00",
            "end_time": "15:30",
            "room_code": "R-201",
            "credits": "3",
        }, follow_redirects=True)
        self.assertIn("CS299", resp.get_data(as_text=True))

        csv_resp = self.client.get("/reports/export-csv")
        self.assertEqual(csv_resp.status_code, 200)
        self.assertIn("text/csv", csv_resp.content_type)
        self.assertIn("CS299", csv_resp.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
