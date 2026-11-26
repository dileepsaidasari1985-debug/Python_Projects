# Test Cases

Automated in [`tests/test_canteen.py`](../tests/test_canteen.py).

| Test ID | Scenario | Input / Condition | Expected Result |
|---|---|---|---|
| **TC-01** | Valid Order & Stock Deduction | `2x ITM101 (50)`, `1x ITM102 (20)` | `COMPLETED`, subtotal `₹120`, GST `₹6`, total `₹126`, stock updated. |
| **TC-02** | Unavailable Quantity Rejection | Request `10` when stock is `5` | `PARTIAL`, rejects unavailable line with `"only 5 available"`. |
| **TC-03** | Successive Order Queue | Two back-to-back orders requesting `2` each out of `3` stock | Order 1 `COMPLETED`, Order 2 `REJECTED` (only `1` left). |
| **TC-04** | Daily Sales & ASCII Summary | Sample orders + inventory | Computes revenue and ASCII stock gauge. |
| **TC-05** | Web Routes & CSV Export | GET `/`, `/order`, `/queue`, `/inventory`, `/reports`, `/reports/export-csv` | HTTP `200` and valid CSV export. |
| **TC-06** | Order Counter POST | POST `/order` with `2x ITM101` | Order saved and inventory updated. |
