# Problem Statement

## Case Study #29: Password Policy Validation Engine

Users frequently select weak, predictable passwords containing repeated characters or common dictionary words, while poorly designed validators display generic `"Invalid password"` messages that fail to explain what rule was violated.

**Problem Statement:**
Design and implement a **Password Policy Validation Engine** in Python that inspects sample password strings against configurable minimum length, character-category counts (uppercase, lowercase, numeric digits, special characters), whitespace restrictions, consecutive character repetition limits, and prohibited dictionary/username substrings, returning clear per-rule explanations for every failed condition alongside masked SQLite audit logs and CSV exports.
