# Problem Statement

## Case Study #13: ATM Transaction Sequence Simulation

Modern banking relies on Automated Teller Machines (ATMs) to process continuous sequences of customer deposits and cash withdrawals reliably while enforcing strict business and safety rules. In an educational programming context, simulating an ATM system requires tracking mutable account state across sequential operations, validating every input before modifying balances, enforcing withdrawal thresholds and denomination multiples, rejecting invalid attempts without corrupting account balances, and producing accurate audit trails.

### Problem Description

Design and implement the **Smart ATM Transaction and Banking Simulation System**, a beginner-friendly Python and Flask web application backed by SQLite that simulates an ATM environment for a demo student account (`DEMO1001`, initial balance `₹10,000.00`).

The system must:
1. Accept individual cash deposits and withdrawals as well as multi-step **transaction sequences** (e.g., Deposit `₹2,000` → Withdraw `₹500` → Deposit `₹1,000` → Withdraw `₹3,000` → Withdraw `₹15,000`).
2. Process each transaction in strict chronological order, preserving the running balance after every valid transaction.
3. Enforce configurable ATM rules: minimum withdrawal (`₹100`), denomination multiple (`₹100`), maximum per-transaction limit (`₹10,000`), maximum daily withdrawal limit (`₹25,000`), and sufficient balance (never allowing a negative balance).
4. Reject invalid, zero, negative, non-numeric, or limit-violating transactions while logging both successful and rejected attempts in SQLite with clear rejection reasons.
5. Generate comprehensive transaction summaries, printable ASCII receipt slips, and downloadable CSV reports using core Python syllabus constructs.
