"""Automated tests for Password Policy Validation Engine (Case Study #29)."""

import os
import re
import tempfile
import unittest

from app import create_app
from password_logic import (
    SAMPLE_PASSWORD_TUPLES,
    evaluate_password,
    evaluate_password_batch,
    mask_password,
    validate_policy_inputs,
)


class TestPasswordLogic(unittest.TestCase):
    def test_01_compliant_strong_password(self):
        res = evaluate_password("Vortex#749!K", "ananya")
        self.assertTrue(res["is_compliant"])
        self.assertEqual(res["verdict"], "PASS")
        self.assertEqual(len(res["failed_explanations"]), 0)

    def test_02_minimum_length_and_missing_categories(self):
        res = evaluate_password("abc", "user1")
        self.assertFalse(res["is_compliant"])
        joined = " ".join(res["failed_explanations"]).lower()
        self.assertIn("too short", joined)
        self.assertIn("uppercase", joined)
        self.assertIn("numeric digits", joined)
        self.assertIn("special characters", joined)

    def test_03_consecutive_repetition_rule(self):
        res = evaluate_password("Securrrre@99", "rohan")
        self.assertFalse(res["is_compliant"])
        self.assertEqual(res["max_consecutive_repeat"], 4)
        self.assertTrue(any("Excessive repetition" in m for m in res["failed_explanations"]))

    def test_04_prohibited_substring_and_username(self):
        res1 = evaluate_password("MyAdmin#2026", "kiran")
        self.assertFalse(res1["is_compliant"])
        self.assertIn("admin", res1["matched_prohibited"])

        res2 = evaluate_password("Meera@2026!", "meera")
        self.assertFalse(res2["is_compliant"])
        self.assertIn("meera", res2["matched_prohibited"])

    def test_05_batch_evaluation_and_masking(self):
        self.assertEqual(mask_password("Vortex#749!K"), "Vo********!K")
        batch = evaluate_password_batch(SAMPLE_PASSWORD_TUPLES)
        self.assertEqual(len(batch), len(SAMPLE_PASSWORD_TUPLES))
        self.assertTrue(batch[-1]["evaluation"]["is_compliant"])

    def test_06_policy_validation(self):
        ok, cleaned, _ = validate_policy_inputs({
            "min_length": "12", "min_upper": "2", "min_lower": "2",
            "min_digits": "2", "min_special": "1", "max_consecutive_repeat": "2",
            "prohibited_csv": "admin, test",
        })
        self.assertTrue(ok)
        self.assertEqual(cleaned["min_length"], 12)

        bad_ok, _, errs = validate_policy_inputs({
            "min_length": "6", "min_upper": "3", "min_lower": "3",
            "min_digits": "2", "min_special": "1", "max_consecutive_repeat": "2",
        })
        self.assertFalse(bad_ok)
        self.assertTrue(len(errs) >= 1)


class TestPasswordFlaskApp(unittest.TestCase):
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

    def test_07_pages_and_csv(self):
        for r in ["/", "/validator", "/batch", "/policy", "/logs"]:
            self.assertEqual(self.client.get(r).status_code, 200)
        csv_resp = self.client.get("/reports/export-csv")
        self.assertEqual(csv_resp.status_code, 200)
        self.assertIn("Masked Preview", csv_resp.get_data(as_text=True))

    def test_08_validator_post(self):
        token = self._csrf("/validator")
        resp = self.client.post("/validator", data={
            "csrf_token": token,
            "sample_label": "Weak Test",
            "username": "rohan",
            "password": "aaapassword",
            "log_result": "1",
        }, follow_redirects=True)
        txt = resp.get_data(as_text=True)
        self.assertIn("FAIL", txt)
        self.assertIn("Excessive repetition", txt)


if __name__ == "__main__":
    unittest.main()
