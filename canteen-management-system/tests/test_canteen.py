"""Automated tests for Smart Canteen Order and Stock Management (Case Study #57)."""

import os
import re
import tempfile
import unittest

from app import create_app
from canteen_logic import process_single_order, process_successive_orders, summarize_daily_sales


class TestCanteenLogic(unittest.TestCase):
    def setUp(self):
        self.inv = [
            {"item_code": "ITM101", "item_name": "Dosa", "category": "Breakfast", "unit_price": 50.0, "stock": 5, "reorder_level": 2, "sold_today": 0},
            {"item_code": "ITM102", "item_name": "Coffee", "category": "Beverages", "unit_price": 20.0, "stock": 3, "reorder_level": 2, "sold_today": 0},
        ]

    def test_01_valid_order_deducts_stock_and_calculates_gst(self):
        res, updated = process_single_order("Aarav", [("ITM101", 2), ("ITM102", 1)], self.inv)
        self.assertEqual(res["status"], "COMPLETED")
        self.assertEqual(res["subtotal"], 120.0)
        self.assertEqual(res["gst_amount"], 6.0)
        self.assertEqual(res["grand_total"], 126.0)
        self.assertEqual(updated[0]["stock"], 3)
        self.assertEqual(updated[1]["stock"], 2)

    def test_02_rejects_unavailable_quantity(self):
        res, updated = process_single_order("Rohan", [("ITM101", 10), ("ITM102", 2)], self.inv)
        self.assertEqual(res["status"], "PARTIAL")
        self.assertEqual(len(res["rejected_lines"]), 1)
        self.assertIn("only 5 available", res["rejected_lines"][0][2])
        self.assertEqual(updated[0]["stock"], 5)
        self.assertEqual(updated[1]["stock"], 1)

    def test_03_successive_orders_share_running_inventory(self):
        queue = [
            ("Customer 1", [("ITM102", 2)]),
            ("Customer 2", [("ITM102", 2)]),
        ]
        batch = process_successive_orders(queue, self.inv)
        self.assertEqual(batch["orders"][0]["status"], "COMPLETED")
        self.assertEqual(batch["orders"][1]["status"], "REJECTED")
        self.assertEqual(batch["updated_inventory"][1]["stock"], 1)

    def test_04_daily_summary_and_low_stock(self):
        orders = [{"status": "COMPLETED", "grand_total": 126.0, "items_count": 3}]
        summary = summarize_daily_sales(orders, self.inv)
        self.assertEqual(summary["total_revenue"], 126.0)
        self.assertIn("SMART CANTEEN", summary["ascii_summary"])


class TestCanteenFlaskApp(unittest.TestCase):
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
        for r in ["/", "/order", "/queue", "/inventory", "/reports"]:
            self.assertEqual(self.client.get(r).status_code, 200)
        csv_resp = self.client.get("/reports/export-csv")
        self.assertEqual(csv_resp.status_code, 200)
        self.assertIn("Remaining Stock", csv_resp.get_data(as_text=True))

    def test_06_place_order_route(self):
        token = self._csrf("/order")
        resp = self.client.post("/order", data={
            "csrf_token": token,
            "customer_name": "Meera",
            "qty_ITM101": "2",
        }, follow_redirects=True)
        self.assertIn("completed", resp.get_data(as_text=True).lower())


if __name__ == "__main__":
    unittest.main()
