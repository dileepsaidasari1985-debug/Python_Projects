# Project Assumptions & Business Rules

1. **Default Policy Thresholds**: Minimum length `10`, uppercase `>= 1`, lowercase `>= 1`, digits `>= 1`, special characters `>= 1`, max consecutive repetition `<= 2`, whitespace disallowed.
2. **Educational Sample Inputs**: All test passwords are non-production academic strings; audit logs store only masked previews (`pw[:2] + *** + pw[-2:]`).
3. **Case-Insensitive Substring Blocking**: Prohibited words (e.g., `admin`, `password`, `qwerty`, `1234`) and usernames of length `>= 3` are blocked anywhere inside the password regardless of casing.
4. **Sum Consistency**: Configurable minimum category counts must not exceed the configured minimum password length.
