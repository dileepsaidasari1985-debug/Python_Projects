# Step-by-Step Algorithm

1. **Start** and load active policy parameters from SQLite (`policy_settings`).
2. **Input**: Read sample password string `pw` and optional `username`.
3. **Character Scan Loop**:
   - Initialize `upper = lower = digit = special = space = max_run = current_run = 0`, `prev_char = None`.
   - For each `ch` in `pw`: increment the matching category counter; update `current_run` if `ch == prev_char` else reset to `1`; update `max_run`.
4. **Evaluate All Rules Independently**:
   - Check `len(pw) >= min_length`.
   - Check `upper >= min_upper`, `lower >= min_lower`, `digit >= min_digits`, `special >= min_special`.
   - Check `space == 0` if `disallow_spaces` is enabled.
   - Check `len(pw) > 0` and `max_run <= max_consecutive_repeat`.
   - Convert `pw` to lowercase and loop over `prohibited_list + [username.lower()]`; record any substring present in `pw.lower()`.
5. **Compile Explanations & Strength Score**:
   - Collect every failed rule's descriptive message into `failed_explanations`.
   - Compute score `0..100` and generate the ASCII strength bar pattern.
6. **Persist Masked Log & End**.
