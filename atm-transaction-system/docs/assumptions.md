# System Assumptions & Validation Rules

This document records the default assumptions and business rules used in the **Smart ATM Transaction and Banking Simulation System**.

## 1. Simulated Account Assumptions
- **Educational Scope**: The system simulates banking behavior locally using SQLite (`database/atm.db`). It never connects to real banking networks, UPI/card rails, or payment gateways.
- **Default Demo Account**:
  - Account Holder: `Demo Student`
  - Account Number: `DEMO1001`
  - Initial Simulated Balance: `₹10,000.00`
- **Currency**: All monetary values are represented in Indian Rupees (`₹` / INR) rounded to 2 decimal places.

## 2. Default ATM Withdrawal Rules (Configurable via Settings)
| Rule | Default Value | Description |
| :--- | :--- | :--- |
| **Minimum Withdrawal** | `₹100.00` | Smallest cash amount dispensed per withdrawal. |
| **Maximum Withdrawal per Transaction** | `₹10,000.00` | Upper cap for any single withdrawal attempt. |
| **Maximum Daily Withdrawal** | `₹25,000.00` | Cumulative cap for successful withdrawals on the same calendar date. |
| **Withdrawal Denomination** | `₹100` | Withdrawal amounts must be exact integer multiples of `₹100` (e.g., `500`, `1200`). |
| **Initial Demo Balance** | `₹10,000.00` | Starting balance restored when the demo account is reset. |

## 3. Transaction Validation Rules
- **Deposits**:
  - Must parse as a finite numeric value.
  - Must be strictly greater than zero (`amount > 0`).
  - Zero, negative, empty, or alphabetic inputs are marked `REJECTED`.
- **Withdrawals**:
  - Must parse as a finite numeric value and be greater than zero.
  - Must be `>= min_withdrawal` and `<= max_per_transaction`.
  - Must satisfy `amount == int(amount)` and `int(amount) % withdrawal_denomination == 0`.
  - Must not exceed `current_balance` (negative balances are strictly prohibited).
  - Must satisfy `daily_withdrawn + amount <= max_daily_withdrawal`.
- **Rejected Transaction Handling**:
  - Rejected transactions are assigned a unique `TXN-...` ID and stored in SQLite with `status = 'REJECTED'` and a descriptive `rejection_reason`.
  - `balance_after` always equals `balance_before` for rejected transactions.
