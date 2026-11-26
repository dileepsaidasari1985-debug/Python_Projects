# Assumptions

1. **Equal Subject Weightage:** Each of the 5 core subjects (Mathematics, Physics, Chemistry, English, Computer Science) is scored out of 100 marks (total = 500), and the aggregate percentage is the arithmetic mean of the 5 scores.
2. **Strict All-Conditions Eligibility:** A student is eligible only when **all** active conditions pass simultaneously (minimum aggregate, every subject >= minimum subject marks, minimum attendance, income <= cap, and income certificate status = `Available` when required).
3. **Single Unique Application per Student:** Each applicant is uniquely identified by `student_id` (case-insensitive, normalized to uppercase), preventing duplicate applications.
4. **Configurable Score Weights:** By default, Scholarship Score weights are `0.70` (Aggregate), `0.20` (Attendance), and `0.10` (Income Merit Score). When customized by an administrator, the three weights must sum to `1.00`.
5. **Income Merit Slabs:** Annual family income is mapped to discrete points (default: `<= ₹1,00,000 -> 100`, `<= ₹1,50,000 -> 80`, `<= ₹2,00,000 -> 60`, `<= ₹2,50,000 -> 40`, `> ₹2,50,000 -> 0`).
6. **Quota & Waitlisting:** Only the top `K` ranked eligible students (default `K = 10`) are marked **Eligible & Selected**; eligible students ranked beyond `K` are marked **Eligible (Waitlisted)** due to quota limits.
7. **Local Demonstration Scope:** The system runs locally using Flask and SQLite without external APIs or complex authentication overhead.
