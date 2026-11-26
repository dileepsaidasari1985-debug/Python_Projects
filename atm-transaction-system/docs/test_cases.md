# Test Cases Document (20+ Cases)

All test cases below verify the **Smart ATM Transaction and Banking Simulation System** against Case Study #13 requirements (default starting balance: `₹10,000.00`, min withdrawal: `₹100.00`, max per transaction: `₹10,000.00`, max daily: `₹25,000.00`, denomination: `₹100`).

| Test ID | Scenario | Input / Action | Expected Output |
| :--- | :--- | :--- | :--- |
| **TC-01** | Valid deposit | Deposit `₹2,000` into `DEMO1001` (`₹10,000`) | `SUCCESS`; balance updates to `₹12,000.00`; saved to SQLite |
| **TC-02** | Invalid non-numeric deposit | Deposit `"abc"` | `REJECTED` ("Invalid numeric amount"); balance stays `₹10,000.00` |
| **TC-03** | Zero deposit | Deposit `0` | `REJECTED` ("Deposit amount must be greater than ₹0.00"); balance unchanged |
| **TC-04** | Negative deposit | Deposit `-500` | `REJECTED` ("Deposit amount cannot be negative"); balance unchanged |
| **TC-05** | Valid withdrawal | Withdraw `₹1,500` from `₹10,000` | `SUCCESS`; balance updates to `₹8,500.00`; daily total increases by `₹1,500` |
| **TC-06** | Invalid non-numeric withdrawal | Withdraw `"ten"` | `REJECTED` ("Invalid numeric amount"); balance unchanged |
| **TC-07** | Insufficient balance | Balance `₹1,000`; withdraw `₹2,000` | `REJECTED` ("Insufficient balance"); balance remains `₹1,000.00` (never negative) |
| **TC-08** | Exceeds per-transaction limit | Balance `₹20,000`; withdraw `₹15,000` (limit `₹10,000`) | `REJECTED` ("Exceeds per-transaction withdrawal limit"); balance unchanged |
| **TC-09** | Exceeds daily withdrawal limit | Balance `₹30,000`; withdraw `₹10,000`, `₹10,000`, then `₹6,000` | First two `SUCCESS` (`₹20,000` used); third `REJECTED` ("Exceeds daily withdrawal limit") |
| **TC-10** | Below minimum withdrawal | Withdraw `₹50` (min `₹100`) | `REJECTED` ("Minimum withdrawal amount is ₹100.00"); balance unchanged |
| **TC-11** | Invalid denomination | Withdraw `₹250` (multiple of `₹100` required) | `REJECTED` ("Withdrawal amount must be a multiple of ₹100"); balance unchanged |
| **TC-12** | Balance inquiry | Open `/balance` after deposit `₹2,000` and withdraw `₹500` | Displays `₹11,500.00`, total deposits `₹2,000`, total withdrawals `₹500`, last txn date |
| **TC-13** | Transaction sequence simulation | Run `[+2000, -500, +1000, -3000, -15000]` starting at `₹10,000` | Steps 1–4 `SUCCESS`, Step 5 `REJECTED`; closing balance `₹9,500.00` |
| **TC-14** | Rejected transaction isolation | Submit rejected withdrawal `₹15,000` | Logged in `transactions` with `status='REJECTED'`, `balance_before == balance_after` |
| **TC-15** | Sequential balance update | Deposit `₹5,000` then withdraw `₹2,000` | Step 1: `10,000 -> 15,000`; Step 2: `15,000 -> 13,000` |
| **TC-16** | Unique Transaction ID generation | Execute 10 consecutive transactions in a loop | All 10 receive distinct `TXN-YYYYMMDD-...` string IDs |
| **TC-17** | Transaction history search & filter | Filter `/history` by `type=WITHDRAWAL`, `status=REJECTED`, or `q=TXN-` | Returns only matching SQLite rows sorted as requested |
| **TC-18** | SQLite database persistence | Commit transactions, close connection, reopen DB | Account balance and all transaction records persist identically |
| **TC-19** | CSV report export | Request `GET /reports/export-csv` | Returns HTTP 200 `text/csv` with header row and all matching ledger records |
| **TC-20** | Transaction summary calculation | Compute summary on mixed successful & rejected transactions | Accurately reports opening, closing, net change, largest deposit/withdrawal, average |
| **TC-21** | Configurable ATM settings | Update max per-transaction to `₹5,000` and test `₹6,000` withdrawal | Withdrawal `₹6,000` is rejected using the updated rule |
| **TC-22** | Safe demo account reset | Confirm reset via modal `POST /settings/reset` | Clears `DEMO1001` transactions and restores `initial_demo_balance` |
