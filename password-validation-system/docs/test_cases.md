# Test Cases

Automated in [`tests/test_password.py`](../tests/test_password.py).

| Test ID | Scenario | Input / Condition | Expected Result |
|---|---|---|---|
| **TC-01** | Strong Compliant Password | `"Vortex#749!K"`, user `"ananya"` | `PASS`, 0 failed conditions. |
| **TC-02** | Short & Missing Categories | `"abc"`, user `"user1"` | `FAIL`, explains length, uppercase, digit, and special failures. |
| **TC-03** | Consecutive Repetition | `"Securrrre@99"` | `FAIL`, reports `max_consecutive_repeat = 4`. |
| **TC-04** | Prohibited Substring & Username | `"MyAdmin#2026"` and `"Meera@2026!"` (user `meera`) | `FAIL`, flags `admin` and `meera`. |
| **TC-05** | Batch Evaluation & Masking | `SAMPLE_PASSWORD_TUPLES` | Masks middle chars and evaluates all 6 samples. |
| **TC-06** | Policy Configuration Bounds | Sum of minimums `> min_length` | Validation rejects inconsistent policy. |
| **TC-07** | Web Routes & CSV Export | GET `/`, `/validator`, `/batch`, `/policy`, `/logs`, `/reports/export-csv` | HTTP `200` and valid CSV log export. |
| **TC-08** | Interactive Validator POST | POST `"aaapassword"` | Displays `FAIL` and `"Excessive repetition"`. |
