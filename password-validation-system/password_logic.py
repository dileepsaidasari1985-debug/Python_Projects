"""Core Password Policy Validation Engine (Case Study #29).

Demonstrates Python syllabus concepts:
- Variables, data types, arithmetic & relational/logical operators
- Conditional statements (if / elif / else) and loops (for, while)
- Strings and string operations (.lower, .isupper, .islower, .isdigit, slicing, 'in')
- Pattern generation (ASCII strength meter bar and audit badge)
- Lists and nested lists (per-rule result rows & batch evaluation matrix)
- Tuples, tuple operations, and tuple unpacking
"""

SPECIAL_CHARS_TUPLE = (
    "!", "@", "#", "$", "%", "^", "&", "*", "(", ")",
    "-", "_", "+", "=", "[", "]", "{", "}", ";", ":",
    ",", ".", "?", "/", "~",
)

DEFAULT_PROHIBITED_SUBSTRINGS = (
    "password",
    "pass123",
    "admin",
    "qwerty",
    "1234",
    "abcd",
    "welcome",
    "letmein",
    "campus",
    "student",
)

DEFAULT_POLICY = {
    "min_length": 10,
    "min_upper": 1,
    "min_lower": 1,
    "min_digits": 1,
    "min_special": 1,
    "max_consecutive_repeat": 2,
    "disallow_spaces": 1,
    "prohibited_csv": ",".join(DEFAULT_PROHIBITED_SUBSTRINGS),
}

# Tuple of sample test passwords: (label, sample_password, username)
SAMPLE_PASSWORD_TUPLES = (
    ("Too Short", "Ab1!", "arjun"),
    ("Missing Upper & Special", "campus2026", "priya"),
    ("Excessive Repetition", "Securrrre@99", "rohan"),
    ("Prohibited Substring (admin)", "MyAdmin#2026", "kiran"),
    ("Contains Username", "Meera@2026!", "meera"),
    ("Compliant Strong Password", "Vortex#749!K", "ananya"),
)


def mask_password(password):
    """Mask middle characters of a password string using slicing for safe display."""
    pw = str(password or "")
    if len(pw) <= 2:
        return "*" * len(pw)
    if len(pw) <= 4:
        return pw[0] + ("*" * (len(pw) - 2)) + pw[-1]
    return pw[:2] + ("*" * (len(pw) - 4)) + pw[-2:]


def parse_prohibited_list(prohibited_csv):
    """Parse comma-separated prohibited substrings into a clean tuple."""
    items = []
    for part in str(prohibited_csv or "").split(","):
        cleaned = part.strip().lower()
        if cleaned and cleaned not in items:
            items.append(cleaned)
    return tuple(items)


def validate_policy_inputs(form_dict):
    """Validate configurable password policy parameters."""
    errors = []
    cleaned = {}
    int_fields = (
        ("min_length", "Minimum Length", 4, 64),
        ("min_upper", "Minimum Uppercase", 0, 10),
        ("min_lower", "Minimum Lowercase", 0, 10),
        ("min_digits", "Minimum Digits", 0, 10),
        ("min_special", "Minimum Special Chars", 0, 10),
        ("max_consecutive_repeat", "Max Consecutive Repeats", 1, 10),
    )

    for key, label, lo, hi in int_fields:
        try:
            val = int(str(form_dict.get(key, "")).strip())
            if val < lo or val > hi:
                errors.append(f"{label} must be between {lo} and {hi}.")
            else:
                cleaned[key] = val
        except (ValueError, TypeError):
            errors.append(f"{label} must be a valid integer.")

    if not errors:
        category_sum = cleaned["min_upper"] + cleaned["min_lower"] + cleaned["min_digits"] + cleaned["min_special"]
        if category_sum > cleaned["min_length"]:
            errors.append("Sum of minimum character categories cannot exceed Minimum Length.")

    cleaned["disallow_spaces"] = 1 if str(form_dict.get("disallow_spaces", "1")) in ("1", "on", "true", "True") else 0
    prohibited_tuple = parse_prohibited_list(form_dict.get("prohibited_csv", ""))
    cleaned["prohibited_csv"] = ",".join(prohibited_tuple)
    return (len(errors) == 0, cleaned, errors)


def generate_strength_bar(score):
    """Generate an ASCII progress bar pattern using a loop."""
    filled = int(round(score / 10.0))
    if filled < 0:
        filled = 0
    elif filled > 10:
        filled = 10

    bar = ""
    idx = 0
    while idx < 10:
        if idx < filled:
            bar = bar + "█"
        else:
            bar = bar + "░"
        idx += 1
    return f"[{bar}] {score}/100"


def evaluate_password(raw_password, username="", policy=None):
    """Evaluate a password string against length, category, repetition, and prohibited-substring rules.

    Explains EVERY failed (and passed) condition explicitly.
    """
    active = dict(DEFAULT_POLICY)
    if policy:
        active.update(policy)

    pw = str(raw_password or "")
    pw_len = len(pw)
    upper_count = 0
    lower_count = 0
    digit_count = 0
    special_count = 0
    space_count = 0

    max_run = 0
    max_run_char = ""
    current_run = 0
    prev_char = None

    # Character-by-character scan using a for loop
    for ch in pw:
        if ch.isupper():
            upper_count += 1
        elif ch.islower():
            lower_count += 1
        elif ch.isdigit():
            digit_count += 1
        elif ch.isspace():
            space_count += 1
        elif ch in SPECIAL_CHARS_TUPLE:
            special_count += 1

        if ch == prev_char:
            current_run += 1
        else:
            current_run = 1
            prev_char = ch

        if current_run > max_run:
            max_run = current_run
            max_run_char = ch

    rule_results = []
    failed_explanations = []

    # 1. Minimum length check
    min_len = int(active["min_length"])
    len_ok = pw_len >= min_len
    len_msg = (
        f"Length is {pw_len} characters (meets minimum {min_len})."
        if len_ok
        else f"Too short: length is {pw_len}, but at least {min_len} characters are required."
    )
    rule_results.append(("MIN_LENGTH", "Minimum Length", len_ok, len_msg))
    if not len_ok:
        failed_explanations.append(len_msg)

    # 2. Character category checks
    categories = (
        ("UPPERCASE", "Uppercase Letters (A-Z)", upper_count, int(active["min_upper"])),
        ("LOWERCASE", "Lowercase Letters (a-z)", lower_count, int(active["min_lower"])),
        ("DIGITS", "Numeric Digits (0-9)", digit_count, int(active["min_digits"])),
        ("SPECIAL", "Special Characters (!@#$...)", special_count, int(active["min_special"])),
    )
    for r_id, r_name, actual, required in categories:
        ok = actual >= required
        if ok:
            msg = f"Contains {actual} {r_name.lower()} (minimum {required} required)."
        else:
            msg = f"Missing {r_name.lower()}: found {actual}, requires at least {required}."
        rule_results.append((r_id, r_name, ok, msg))
        if not ok:
            failed_explanations.append(msg)

    # 3. Whitespace rule
    if int(active["disallow_spaces"]) == 1:
        space_ok = space_count == 0
        space_msg = (
            "No whitespace characters found."
            if space_ok
            else f"Contains {space_count} whitespace character(s); spaces are not permitted."
        )
        rule_results.append(("NO_SPACES", "No Whitespace", space_ok, space_msg))
        if not space_ok:
            failed_explanations.append(space_msg)

    # 4. Consecutive repetition rule
    max_allowed_rep = int(active["max_consecutive_repeat"])
    rep_ok = (pw_len > 0) and (max_run <= max_allowed_rep)
    if pw_len == 0:
        rep_msg = "Password is empty; cannot evaluate character repetition."
    elif rep_ok:
        rep_msg = f"Max consecutive identical characters is {max_run} (limit: {max_allowed_rep})."
    else:
        rep_msg = f"Excessive repetition: '{max_run_char}' repeats {max_run} times consecutively (max allowed: {max_allowed_rep})."
    rule_results.append(("REPETITION", "Consecutive Repetition Limit", rep_ok, rep_msg))
    if not rep_ok:
        failed_explanations.append(rep_msg)

    # 5. Prohibited substring rule (dictionary words + username)
    lower_pw = pw.lower()
    prohibited_items = list(parse_prohibited_list(active.get("prohibited_csv", "")))
    clean_user = str(username or "").strip().lower()
    if len(clean_user) >= 3 and clean_user not in prohibited_items:
        prohibited_items.append(clean_user)

    matched_prohibited = []
    for sub in prohibited_items:
        if sub in lower_pw:
            matched_prohibited.append(sub)

    sub_ok = len(matched_prohibited) == 0 and pw_len > 0
    if pw_len == 0:
        sub_msg = "Password is empty; prohibited-substring check failed."
    elif sub_ok:
        sub_msg = "No prohibited words or username substrings detected."
    else:
        sub_msg = f"Contains prohibited substring(s): {', '.join(matched_prohibited)}."
    rule_results.append(("PROHIBITED", "No Prohibited Substrings", sub_ok, sub_msg))
    if not sub_ok:
        failed_explanations.append(sub_msg)

    passed_count = sum(1 for _, _, ok, _ in rule_results if ok)
    total_rules = len(rule_results)
    is_compliant = passed_count == total_rules

    # Strength score out of 100
    base_score = int(round((passed_count / total_rules) * 75)) if total_rules else 0
    bonus = min(25, max(0, (pw_len - 6) * 3)) if pw_len > 0 else 0
    if not sub_ok:
        bonus = 0
    score = min(100, base_score + bonus)

    if is_compliant and score >= 85:
        strength_label = "Very Strong"
    elif is_compliant:
        strength_label = "Strong"
    elif score >= 50:
        strength_label = "Fair"
    else:
        strength_label = "Weak"

    return {
        "masked_password": mask_password(pw),
        "length": pw_len,
        "upper_count": upper_count,
        "lower_count": lower_count,
        "digit_count": digit_count,
        "special_count": special_count,
        "max_consecutive_repeat": max_run,
        "matched_prohibited": matched_prohibited,
        "rule_results": rule_results,
        "failed_explanations": failed_explanations,
        "passed_rules": passed_count,
        "total_rules": total_rules,
        "is_compliant": is_compliant,
        "verdict": "PASS" if is_compliant else "FAIL",
        "score": score,
        "strength_label": strength_label,
        "strength_bar": generate_strength_bar(score),
    }


def evaluate_password_batch(password_tuples, policy=None):
    """Evaluate a sequence of (label, password, username) tuples using tuple unpacking."""
    results = []
    for label, pw, user in password_tuples:
        res = evaluate_password(pw, user, policy)
        results.append({
            "label": label,
            "username": user,
            "evaluation": res,
        })
    return results
