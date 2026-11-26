# Project Objectives

The primary objectives of the **Smart ATM Transaction and Banking Simulation System (Case Study #13)** are:

1. **Simulate an ATM Banking Environment**: Provide an intuitive, responsive web interface modeled after digital banking dashboards and ATM terminals using an educational demo account (`DEMO1001`).
2. **Maintain Simulated Account Balance**: Track opening, running, and closing balances accurately in SQLite without ever allowing the balance to become negative.
3. **Process Cash Deposits**: Validate positive numeric deposit inputs, credit the simulated balance, generate unique transaction IDs, and store records persistently.
4. **Process Cash Withdrawals**: Validate and dispense simulated withdrawals while tracking daily withdrawal totals.
5. **Enforce Configurable Withdrawal Limits**: Apply minimum withdrawal, denomination multiple, maximum per-transaction limit, and maximum daily withdrawal limit dynamically from database settings.
6. **Reject Invalid Transactions Safely**: Catch non-numeric, zero, negative, non-multiple, limit-exceeding, and insufficient-balance attempts, record them as `REJECTED` with explicit reasons, and leave the account balance unchanged.
7. **Simulate Transaction Sequences**: Process ordered sequences of deposits and withdrawals using Python loops and tuple unpacking, displaying step-by-step balance before/after and status.
8. **Maintain Searchable Transaction History**: Persist all transactions in SQLite and allow searching by Transaction ID, filtering by type/status/date, and sorting by amount or timestamp.
9. **Generate Transaction Summaries & CSV Reports**: Compute opening/closing balances, totals, largest deposit/withdrawal, averages, net balance change, ASCII receipt slips, and CSV downloads via Python's built-in `csv` module.
10. **Demonstrate Core Python Syllabus Concepts**: Naturally apply variables, data types, operators, conditionals, loops, strings, ASCII pattern generation, lists, nested lists, tuples, tuple operations, and tuple unpacking.
