# Step-by-Step Transaction Algorithm

## Algorithm: ATM Transaction & Sequence Simulation

1. **Start** and initialize the SQLite database (`demo_accounts`, `transactions`, `atm_settings`).
2. **Load State**: Retrieve the simulated account (`DEMO1001`) current balance, active ATM rules tuple `(max_per_txn, max_daily, min_wd, denom, init_bal)`, and today's cumulative successful withdrawal total (`daily_withdrawn`).
3. **Display ATM Menu / Interface**: Present options for Balance Inquiry, Cash Deposit, Cash Withdrawal, Transaction History, Transaction Sequence Simulator, Reports, Settings, and Exit.
4. **Accept Input**:
   - For a single transaction: read `transaction_type` (`DEPOSIT` or `WITHDRAWAL`), `raw_amount`, and optional `description`.
   - For a transaction sequence: read an ordered list of `(transaction_type, raw_amount, description)` tuples.
5. **Loop Over Transaction(s)**:
   - For each transaction item:
     1. Record `balance_before = current_balance`.
     2. Generate a unique `transaction_id` string (`TXN-YYYYMMDD-HHMMSSXXXX`).
     3. Validate `raw_amount` by parsing into a finite float rounded to 2 decimal places.
     4. **If `transaction_type == "DEPOSIT"`**:
        - Check `parsed_amount > 0`.
        - If valid: `balance_after = balance_before + parsed_amount`, `status = "SUCCESS"`.
        - Else: `balance_after = balance_before`, `status = "REJECTED"`, set rejection reason.
     5. **Else if `transaction_type == "WITHDRAWAL"`**:
        - Check `parsed_amount > 0`, `parsed_amount >= min_wd`, `parsed_amount <= max_per_txn`, integer multiple of `denom`, `parsed_amount <= balance_before`, and `daily_withdrawn + parsed_amount <= max_daily`.
        - If all checks pass: `balance_after = balance_before - parsed_amount`, `daily_withdrawn += parsed_amount`, `status = "SUCCESS"`.
        - Else: `balance_after = balance_before`, `status = "REJECTED"`, set specific rejection reason.
     6. Update `current_balance = balance_after`.
     7. Append the result row `[step, txn_id, type, amount, before, after, status, reason]` to the nested results list.
6. **Persist to SQLite**: Insert every processed transaction record (both `SUCCESS` and `REJECTED`) using parameterized SQL queries and update `demo_accounts.current_balance`.
7. **Display Result & Receipt**: Show the updated balance, step-by-step sequence table, or ASCII receipt slip.
8. **Generate Summary**: Loop through stored transactions to compute total deposits, total withdrawals, successful count, rejected count, largest deposit/withdrawal, average amount, net balance change, and optional CSV export.
9. **End**.
