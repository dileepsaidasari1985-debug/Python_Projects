"""Automated unittest suite for Smart ATM Transaction & Banking Simulation (Case Study #13)."""

import csv
import io
import os
import re
import tempfile
import unittest

import app as atm_app_module
import database
import transaction_logic as logic


class TestATMTransactionLogic(unittest.TestCase):
    """Unit tests for pure Python transaction, validation, sequence, and summary logic."""

    def setUp(self):
        self.settings = {
            "max_per_transaction": 10000.0,
            "max_daily_withdrawal": 25000.0,
            "min_withdrawal": 100.0,
            "withdrawal_denomination": 100,
            "initial_demo_balance": 10000.0,
        }

    def test_valid_deposit_and_balance_update(self):
        outcome = logic.execute_single_transaction(
            txn_type="DEPOSIT",
            raw_amount="2000",
            current_balance=5000.0,
            daily_withdrawn=0.0,
            settings=self.settings,
            description="Test Deposit",
        )
        self.assertEqual(outcome["status"], "SUCCESS")
        self.assertEqual(outcome["balance_before"], 5000.0)
        self.assertEqual(outcome["amount"], 2000.0)
        self.assertEqual(outcome["balance_after"], 7000.0)
        self.assertTrue(outcome["transaction_id"].startswith("TXN-"))

    def test_invalid_zero_and_negative_deposits_rejected(self):
        for bad_value in ("abc", "", "0", "-500"):
            outcome = logic.execute_single_transaction(
                txn_type="DEPOSIT",
                raw_amount=bad_value,
                current_balance=5000.0,
                daily_withdrawn=0.0,
                settings=self.settings,
            )
            self.assertEqual(outcome["status"], "REJECTED")
            self.assertEqual(outcome["balance_after"], 5000.0)
            self.assertTrue(len(outcome["rejection_reason"]) > 0)

    def test_valid_withdrawal_and_daily_tracking(self):
        outcome = logic.execute_single_transaction(
            txn_type="WITHDRAWAL",
            raw_amount="1500",
            current_balance=10000.0,
            daily_withdrawn=2000.0,
            settings=self.settings,
        )
        self.assertEqual(outcome["status"], "SUCCESS")
        self.assertEqual(outcome["balance_after"], 8500.0)
        self.assertEqual(outcome["daily_withdrawn_after"], 3500.0)

    def test_withdrawal_rules_and_limits(self):
        # Negative and zero
        for bad in ("-100", "0", "xyz"):
            res = logic.execute_single_transaction(
                "WITHDRAWAL", bad, 10000.0, 0.0, self.settings
            )
            self.assertEqual(res["status"], "REJECTED")
            self.assertEqual(res["balance_after"], 10000.0)

        # Below minimum (< 100)
        res_min = logic.execute_single_transaction(
            "WITHDRAWAL", "50", 10000.0, 0.0, self.settings
        )
        self.assertEqual(res_min["status"], "REJECTED")
        self.assertIn("Minimum withdrawal", res_min["rejection_reason"])

        # Invalid denomination (not multiple of 100)
        res_denom = logic.execute_single_transaction(
            "WITHDRAWAL", "250", 10000.0, 0.0, self.settings
        )
        self.assertEqual(res_denom["status"], "REJECTED")
        self.assertIn("multiple of", res_denom["rejection_reason"])

        # Above per-transaction limit (> 10000)
        res_max_txn = logic.execute_single_transaction(
            "WITHDRAWAL", "15000", 30000.0, 0.0, self.settings
        )
        self.assertEqual(res_max_txn["status"], "REJECTED")
        self.assertIn("per-transaction", res_max_txn["rejection_reason"])

        # Exceeds available balance (never negative)
        res_bal = logic.execute_single_transaction(
            "WITHDRAWAL", "5000", 3000.0, 0.0, self.settings
        )
        self.assertEqual(res_bal["status"], "REJECTED")
        self.assertIn("Insufficient balance", res_bal["rejection_reason"])
        self.assertEqual(res_bal["balance_after"], 3000.0)

        # Exceeds daily limit
        res_daily = logic.execute_single_transaction(
            "WITHDRAWAL", "6000", 30000.0, 20000.0, self.settings
        )
        self.assertEqual(res_daily["status"], "REJECTED")
        self.assertIn("daily withdrawal limit", res_daily["rejection_reason"])

    def test_transaction_sequence_processing(self):
        # Case Study #13 prompt example: +2000, -500, +1000, -3000, -15000
        sim = logic.process_transaction_sequence(
            sequence_items=logic.EXAMPLE_SEQUENCE_TUPLES,
            starting_balance=10000.0,
            starting_daily_withdrawn=0.0,
            settings=self.settings,
        )
        summary = sim["summary"]
        self.assertEqual(summary["opening_balance"], 10000.0)
        self.assertEqual(summary["total_attempted"], 5)
        self.assertEqual(summary["success_count"], 4)
        self.assertEqual(summary["rejected_count"], 1)
        self.assertEqual(summary["total_deposited"], 3000.0)
        self.assertEqual(summary["total_withdrawn"], 3500.0)
        # 10000 + 2000 - 500 + 1000 - 3000 = 9500 (15000 rejected)
        self.assertEqual(summary["closing_balance"], 9500.0)
        self.assertEqual(summary["net_change"], -500.0)
        self.assertEqual(len(sim["nested_rows"]), 5)
        self.assertEqual(sim["results"][4]["status"], "REJECTED")
        self.assertEqual(sim["results"][4]["balance_after"], 9500.0)

    def test_unique_transaction_ids_and_patterns(self):
        ids = {logic.generate_transaction_id() for _ in range(15)}
        self.assertEqual(len(ids), 15)

        sample_txn = {
            "transaction_id": "TXN-20261126-0001",
            "created_at": "2026-11-26 09:00:00",
            "transaction_type": "DEPOSIT",
            "status": "SUCCESS",
            "amount": 2000.0,
            "balance_before": 10000.0,
            "balance_after": 12000.0,
            "description": "Unit Test",
            "rejection_reason": "",
        }
        acct = {"account_number": "DEMO1001", "holder_name": "Demo Student"}
        slip = logic.generate_atm_receipt_pattern(acct, sample_txn)
        self.assertIn("SMART ATM SIMULATION - RECEIPT", slip)
        self.assertIn("TXN-20261126-0001", slip)

    def test_summary_calculation(self):
        txns = [
            {
                "transaction_id": "T1",
                "transaction_type": "DEPOSIT",
                "amount": 2000.0,
                "balance_after": 12000.0,
                "status": "SUCCESS",
                "rejection_reason": "",
            },
            {
                "transaction_id": "T2",
                "transaction_type": "WITHDRAWAL",
                "amount": 500.0,
                "balance_after": 11500.0,
                "status": "SUCCESS",
                "rejection_reason": "",
            },
            {
                "transaction_id": "T3",
                "transaction_type": "WITHDRAWAL",
                "amount": 15000.0,
                "balance_after": 11500.0,
                "status": "REJECTED",
                "rejection_reason": "Exceeds limit",
            },
        ]
        summary = logic.calculate_transaction_summary(txns, 10000.0, 11500.0)
        self.assertEqual(summary["total_successful"], 2)
        self.assertEqual(summary["total_rejected"], 1)
        self.assertEqual(summary["largest_deposit"], 2000.0)
        self.assertEqual(summary["largest_withdrawal"], 500.0)
        self.assertEqual(summary["average_transaction_amount"], 1250.0)
        self.assertEqual(summary["net_balance_change"], 1500.0)


class TestATMDatabaseAndFlaskApp(unittest.TestCase):
    """Integration tests for SQLite persistence, Flask endpoints, limits, and CSV export."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_atm.db")
        self.app = atm_app_module.create_app(db_path=self.db_path)
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def _get_csrf(self, path="/"):
        resp = self.client.get(path)
        html = resp.get_data(as_text=True)
        match = re.search(r'name="csrf_token"\s+value="([^"]+)"', html)
        self.assertIsNotNone(match, f"CSRF token not found on {path}")
        return match.group(1)

    def test_database_initialization_and_persistence(self):
        acct = database.get_demo_account("DEMO1001", db_path=self.db_path)
        self.assertIsNotNone(acct)
        self.assertEqual(acct["holder_name"], "Demo Student")
        self.assertEqual(acct["current_balance"], 10000.0)

        ok, out, _ = database.record_single_transaction(
            "DEMO1001", "DEPOSIT", "2500", "Scholarship", db_path=self.db_path
        )
        self.assertTrue(ok)
        self.assertEqual(out["balance_after"], 12500.0)

        reloaded = database.get_demo_account("DEMO1001", db_path=self.db_path)
        self.assertEqual(reloaded["current_balance"], 12500.0)

    def test_deposit_withdrawal_sequence_and_csv_routes(self):
        # Deposit via POST
        token = self._get_csrf("/deposit")
        dep_resp = self.client.post(
            "/deposit",
            data={
                "csrf_token": token,
                "account_number": "DEMO1001",
                "amount": "2000",
                "description": "Flask Deposit",
            },
        )
        self.assertEqual(dep_resp.status_code, 200)
        self.assertIn("12,000.00", dep_resp.get_data(as_text=True))

        # Withdrawal via POST (valid + invalid)
        token = self._get_csrf("/withdrawal")
        wd_ok = self.client.post(
            "/withdrawal",
            data={
                "csrf_token": token,
                "account_number": "DEMO1001",
                "amount": "500",
                "description": "Flask Withdrawal",
            },
        )
        self.assertEqual(wd_ok.status_code, 200)
        self.assertIn("11,500.00", wd_ok.get_data(as_text=True))

        wd_bad = self.client.post(
            "/withdrawal",
            data={
                "csrf_token": token,
                "account_number": "DEMO1001",
                "amount": "15000",
                "description": "Too High",
            },
        )
        self.assertEqual(wd_bad.status_code, 200)
        self.assertIn("REJECTED", wd_bad.get_data(as_text=True))

        # Balance inquiry, history, reports
        self.assertEqual(self.client.get("/balance").status_code, 200)
        hist_resp = self.client.get("/history?status=REJECTED")
        self.assertEqual(hist_resp.status_code, 200)
        self.assertIn("Too High", hist_resp.get_data(as_text=True))
        self.assertEqual(self.client.get("/reports").status_code, 200)

        # CSV export verification
        csv_resp = self.client.get("/reports/export-csv")
        self.assertEqual(csv_resp.status_code, 200)
        self.assertIn("text/csv", csv_resp.content_type)
        reader = list(csv.reader(io.StringIO(csv_resp.get_data(as_text=True))))
        self.assertEqual(reader[0][0], "Transaction ID")
        self.assertEqual(len(reader), 4)  # header + 3 logged transactions

    def test_settings_update_and_account_reset(self):
        token = self._get_csrf("/settings")
        set_resp = self.client.post(
            "/settings",
            data={
                "csrf_token": token,
                "max_per_transaction": "5000",
                "max_daily_withdrawal": "10000",
                "min_withdrawal": "500",
                "withdrawal_denomination": "500",
                "initial_demo_balance": "15000",
            },
        )
        self.assertEqual(set_resp.status_code, 200)
        self.assertIn("ATM rules updated successfully", set_resp.get_data(as_text=True))

        # Withdrawal of 6000 should now fail against updated 5000 limit
        ok, out, _ = database.record_single_transaction(
            "DEMO1001", "WITHDRAWAL", "6000", db_path=self.db_path
        )
        self.assertFalse(ok)
        self.assertEqual(out["status"], "REJECTED")

        # Reset demo account
        reset_resp = self.client.post(
            "/settings/reset",
            data={"csrf_token": token},
            follow_redirects=True,
        )
        self.assertEqual(reset_resp.status_code, 200)
        acct = database.get_demo_account("DEMO1001", db_path=self.db_path)
        self.assertEqual(acct["current_balance"], 15000.0)
        self.assertEqual(
            len(database.get_transactions("DEMO1001", db_path=self.db_path)), 0
        )


if __name__ == "__main__":
    unittest.main()
