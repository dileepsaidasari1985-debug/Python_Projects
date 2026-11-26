"""
Automated Unit & Integration Tests - Progressive Electricity Billing System
-------------------------------------------------------------------------
Covers progressive slab calculations, fixed charges, duty, surcharges,
rebates, negative-bill prevention, input validation, monthly comparison,
unusual consumption detection, SQLite persistence, and Flask routes/CSV export.
"""

import os
import tempfile
import unittest

from app import create_app
from billing_logic import (
    DEFAULT_RULES,
    DEFAULT_SLABS,
    analyze_monthly_consumption,
    calculate_energy_charge,
    calculate_full_bill,
    calculate_percentage_change,
    detect_unusual_consumption,
    generate_bill_number,
    generate_text_pattern_summary,
    validate_household_data,
    validate_meter_reading_data,
    validate_rules_and_slabs,
)
from database import (
    add_household,
    create_reading_and_bill,
    delete_household,
    get_all_bills,
    get_all_households,
    get_bill_by_id,
    init_db,
    load_sample_data,
    update_household,
    update_rules_and_slabs,
)


class TestBillingLogic(unittest.TestCase):
    """Unit tests for progressive billing calculations and validation."""

    def test_01_zero_consumption_energy_charge(self):
        charge, breakdown = calculate_energy_charge(0, DEFAULT_SLABS)
        self.assertEqual(charge, 0.0)
        self.assertTrue(all(item["units"] == 0 for item in breakdown))

    def test_02_first_slab_consumption(self):
        charge, breakdown = calculate_energy_charge(60, DEFAULT_SLABS)
        self.assertEqual(charge, 120.0)
        self.assertEqual(breakdown[0]["units"], 60.0)
        self.assertEqual(breakdown[1]["units"], 0.0)

    def test_03_slab_boundary_100_and_101(self):
        charge_100, _ = calculate_energy_charge(100, DEFAULT_SLABS)
        charge_101, _ = calculate_energy_charge(101, DEFAULT_SLABS)
        self.assertEqual(charge_100, 200.0)
        self.assertEqual(charge_101, 203.0)

    def test_04_multi_slab_250_units_example(self):
        # 100*2 + 100*3 + 50*5 = 200 + 300 + 250 = 750
        charge, breakdown = calculate_energy_charge(250, DEFAULT_SLABS)
        self.assertEqual(charge, 750.0)
        self.assertEqual(breakdown[0]["units"], 100.0)
        self.assertEqual(breakdown[1]["units"], 100.0)
        self.assertEqual(breakdown[2]["units"], 50.0)
        self.assertEqual(breakdown[3]["units"], 0.0)

    def test_05_above_500_units_consumption(self):
        # 100*2 + 100*3 + 100*5 + 200*7 + 100*8 = 200+300+500+1400+800 = 3200
        charge, breakdown = calculate_energy_charge(600, DEFAULT_SLABS)
        self.assertEqual(charge, 3200.0)
        self.assertEqual(breakdown[4]["units"], 100.0)
        self.assertEqual(breakdown[4]["charge"], 800.0)

    def test_06_negative_consumption_raises(self):
        with self.assertRaises(ValueError):
            calculate_energy_charge(-5, DEFAULT_SLABS)

    def test_07_fixed_charge_and_duty_calculation(self):
        bill = calculate_full_bill(250, DEFAULT_SLABS, DEFAULT_RULES, is_late_payment=False)
        self.assertEqual(bill["energy_charge"], 750.0)
        self.assertEqual(bill["fixed_charge"], 50.0)
        self.assertEqual(bill["electricity_duty"], 37.5)
        self.assertEqual(bill["surcharge_amount"], 0.0)
        self.assertEqual(bill["rebate_amount"], 0.0)
        self.assertEqual(bill["final_payable"], 837.5)

    def test_08_surcharge_above_threshold(self):
        # 350 units: 200+300+500+350 = 1350 energy, 10% surcharge = 135.0
        bill = calculate_full_bill(350, DEFAULT_SLABS, DEFAULT_RULES, is_late_payment=False)
        self.assertEqual(bill["energy_charge"], 1350.0)
        self.assertEqual(bill["surcharge_amount"], 135.0)
        self.assertEqual(bill["electricity_duty"], 67.5)
        self.assertEqual(bill["final_payable"], 1602.5)

    def test_09_rebate_percentage_and_negative_bill_prevention(self):
        bill_low = calculate_full_bill(100, DEFAULT_SLABS, DEFAULT_RULES)
        self.assertEqual(bill_low["energy_charge"], 200.0)
        self.assertEqual(bill_low["rebate_amount"], 10.0)  # 5% of 200
        self.assertEqual(bill_low["final_payable"], 250.0)  # 200 + 50 + 10 - 10

        # Large fixed rebate must be capped so final_payable is never negative
        rules_huge_rebate = dict(DEFAULT_RULES)
        rules_huge_rebate["rebate_mode"] = "fixed"
        rules_huge_rebate["rebate_value"] = 5000.0
        bill_capped = calculate_full_bill(50, DEFAULT_SLABS, rules_huge_rebate)
        self.assertEqual(bill_capped["final_payable"], 0.0)

    def test_10_late_payment_penalty_applied(self):
        bill = calculate_full_bill(250, DEFAULT_SLABS, DEFAULT_RULES, is_late_payment=True)
        self.assertEqual(bill["late_penalty_amount"], 100.0)
        self.assertEqual(bill["final_payable"], 937.5)

    def test_11_meter_reading_validation(self):
        ok, errs, cleaned = validate_meter_reading_data(
            {
                "household_ref_id": "1",
                "billing_month": "2026-11",
                "previous_reading": "500",
                "current_reading": "420",
                "billing_date": "2026-11-25",
            }
        )
        self.assertFalse(ok)
        self.assertTrue(any("less than previous" in e for e in errs))

        ok_neg, errs_neg, _ = validate_meter_reading_data(
            {
                "household_ref_id": "1",
                "billing_month": "2026-13",
                "previous_reading": "-5",
                "current_reading": "10",
                "billing_date": "2026-11-25",
            }
        )
        self.assertFalse(ok_neg)
        self.assertGreaterEqual(len(errs_neg), 2)

    def test_12_household_validation_and_bill_number_format(self):
        ok, errs, cleaned = validate_household_data(
            {
                "household_id": "hh-201",
                "consumer_name": "Neha Joshi",
                "meter_number": "mtr-2001",
                "address": "12 Oak Street",
                "area": "North Zone",
                "connection_type": "Domestic",
                "meter_category": "Single Phase",
            }
        )
        self.assertTrue(ok, errs)
        self.assertEqual(cleaned["household_id"], "HH-201")
        self.assertEqual(
            generate_bill_number("2026-11", cleaned["household_id"], 7),
            "BILL-202611-HH201-007",
        )

    def test_13_percentage_change_zero_safe(self):
        self.assertIsNone(calculate_percentage_change(85, 0))
        self.assertIsNone(calculate_percentage_change(85, None))
        self.assertEqual(calculate_percentage_change(150, 100), 50.0)
        self.assertEqual(calculate_percentage_change(75, 100), -25.0)

    def test_14_monthly_comparison_and_pattern_generation(self):
        sample_bills = [
            {"billing_month": "2026-08", "units_consumed": 100, "energy_charge": 200, "final_payable": 250},
            {"billing_month": "2026-09", "units_consumed": 200, "energy_charge": 500, "final_payable": 575},
            {"billing_month": "2026-10", "units_consumed": 150, "energy_charge": 350, "final_payable": 417.5},
        ]
        analysis = analyze_monthly_consumption(sample_bills)
        self.assertEqual(analysis["total_consumption"], 450.0)
        self.assertEqual(analysis["avg_consumption"], 150.0)
        self.assertEqual(analysis["highest_month"]["month"], "2026-09")
        self.assertEqual(analysis["lowest_month"]["month"], "2026-08")
        self.assertEqual(analysis["monthly_rows"][1]["pct_change_units"], 100.0)

        pattern = generate_text_pattern_summary(analysis["monthly_rows"], "VoltGrid")
        self.assertIn("2026-09", pattern)
        self.assertIn("#", pattern)

    def test_15_unusual_consumption_detection(self):
        bills = [
            {
                "id": 1, "bill_number": "B-1", "household_ref_id": 1,
                "household_id": "HH-101", "consumer_name": "Aarav",
                "meter_number": "MTR-1001", "billing_month": "2026-06",
                "units_consumed": 120, "final_payable": 300,
            },
            {
                "id": 2, "bill_number": "B-2", "household_ref_id": 1,
                "household_id": "HH-101", "consumer_name": "Aarav",
                "meter_number": "MTR-1001", "billing_month": "2026-07",
                "units_consumed": 130, "final_payable": 330,
            },
            {
                "id": 3, "bill_number": "B-3", "household_ref_id": 1,
                "household_id": "HH-101", "consumer_name": "Aarav",
                "meter_number": "MTR-1001", "billing_month": "2026-08",
                "units_consumed": 140, "final_payable": 360,
            },
            {
                "id": 4, "bill_number": "B-4", "household_ref_id": 1,
                "household_id": "HH-101", "consumer_name": "Aarav",
                "meter_number": "MTR-1001", "billing_month": "2026-09",
                "units_consumed": 320, "final_payable": 1300,
            },
        ]
        warnings = detect_unusual_consumption(bills, DEFAULT_RULES)
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]["billing_month"], "2026-09")
        self.assertIn("Unusual consumption increase", warnings[0]["reasons"])
        self.assertIn("Sudden increase in meter usage (vs 3-month avg)", warnings[0]["reasons"])

    def test_16_rules_validation_rejects_invalid_percent(self):
        form = {
            "company_name": "VoltGrid Utility",
            "fixed_charge": "50",
            "duty_percent": "5",
            "surcharge_percent": "-10",
            "surcharge_threshold_units": "300",
            "rebate_mode": "percent",
            "rebate_value": "120",
            "rebate_threshold_units": "150",
            "late_payment_penalty": "100",
            "unusual_increase_percent": "50",
            "high_consumption_threshold": "400",
            "high_bill_threshold": "2500",
            "slab_min_1": "0", "slab_max_1": "100", "slab_rate_1": "2", "slab_label_1": "0-100",
            "slab_min_2": "101", "slab_max_2": "200", "slab_rate_2": "3", "slab_label_2": "101-200",
            "slab_min_3": "201", "slab_max_3": "300", "slab_rate_3": "5", "slab_label_3": "201-300",
            "slab_min_4": "301", "slab_max_4": "500", "slab_rate_4": "7", "slab_label_4": "301-500",
            "slab_min_5": "501", "slab_max_5": "", "slab_rate_5": "8", "slab_label_5": "Above 500",
        }
        ok, errs, _, _ = validate_rules_and_slabs(form)
        self.assertFalse(ok)
        self.assertGreaterEqual(len(errs), 2)


class TestDatabaseAndFlaskApp(unittest.TestCase):
    """Integration tests for SQLite persistence, sample seeding, and Flask routes."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_electricity.db")
        self.app = create_app(db_path=self.db_path, seed_if_empty=True)
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_17_sample_data_seeded_idempotently(self):
        households = get_all_households(db_path=self.db_path)
        bills = get_all_bills(db_path=self.db_path)
        self.assertEqual(len(households), 6)
        self.assertEqual(len(bills), 22)

        # Calling load_sample_data again must not create duplicates
        added_hh, added_bills = load_sample_data(self.db_path)
        self.assertEqual(added_hh, 0)
        self.assertEqual(added_bills, 0)

    def test_18_household_crud_and_duplicate_prevention(self):
        hh_id = add_household(
            {
                "household_id": "HH-999",
                "consumer_name": "Kiran Rao",
                "meter_number": "MTR-9999",
                "address": "99 Test Lane",
                "area": "West End",
                "connection_type": "Domestic",
                "meter_category": "Smart Digital",
            },
            db_path=self.db_path,
        )
        self.assertIsNotNone(hh_id)

        with self.assertRaises(ValueError):
            add_household(
                {
                    "household_id": "HH-999",
                    "consumer_name": "Duplicate",
                    "meter_number": "MTR-8888",
                    "address": "10 Lane",
                    "area": "West End",
                    "connection_type": "Domestic",
                    "meter_category": "Single Phase",
                },
                db_path=self.db_path,
            )

        update_household(
            hh_id,
            {
                "household_id": "HH-999",
                "consumer_name": "Kiran Rao Updated",
                "meter_number": "MTR-9999",
                "address": "99 Test Lane",
                "area": "West End",
                "connection_type": "Commercial",
                "meter_category": "Three Phase",
            },
            db_path=self.db_path,
        )
        bill_id = create_reading_and_bill(
            {
                "household_ref_id": hh_id,
                "billing_month": "2026-11",
                "previous_reading": 100.0,
                "current_reading": 350.0,
                "billing_date": "2026-11-25",
                "is_late_payment": False,
            },
            db_path=self.db_path,
        )
        bill = get_bill_by_id(bill_id, db_path=self.db_path)
        self.assertEqual(bill["units_consumed"], 250.0)
        self.assertEqual(bill["energy_charge"], 750.0)

        # Duplicate billing month prevented
        with self.assertRaises(ValueError):
            create_reading_and_bill(
                {
                    "household_ref_id": hh_id,
                    "billing_month": "2026-11",
                    "previous_reading": 350.0,
                    "current_reading": 400.0,
                    "billing_date": "2026-11-26",
                },
                db_path=self.db_path,
            )

        delete_household(hh_id, db_path=self.db_path)
        self.assertIsNone(get_bill_by_id(bill_id, db_path=self.db_path))

    def test_19_all_main_pages_render_http_200(self):
        routes = (
            "/",
            "/households",
            "/households/add",
            "/meter-reading",
            "/generate-bill",
            "/billing-history",
            "/monthly-analysis",
            "/unusual-consumption",
            "/tariff-rules",
            "/reports",
            "/bill/1",
        )
        for route in routes:
            resp = self.client.get(route)
            self.assertEqual(resp.status_code, 200, f"Route {route} failed")

    def test_20_csv_exports_return_valid_csv(self):
        for export_type in ("all_bills", "monthly", "unusual"):
            resp = self.client.get(f"/reports/export-csv?type={export_type}")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("text/csv", resp.content_type)
            self.assertGreater(len(resp.data), 40)

        single_resp = self.client.get("/bill/1/csv")
        self.assertEqual(single_resp.status_code, 200)
        self.assertIn(b"Final Payable Amount", single_resp.data)


if __name__ == "__main__":
    unittest.main()
