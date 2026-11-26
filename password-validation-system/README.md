# Password Policy Validation Engine

**Case Study #29:** *Evaluate sample password strings against minimum length, character-category, repetition, and prohibited-substring rules; explain each failed condition.*

## Key Features
- **Character-by-Character Policy Scanner**: Uses Python loops and string checks to count uppercase, lowercase, digits, special characters, whitespace, and consecutive repetition runs.
- **Prohibited Substring & Username Detection**: Checks case-insensitive substring membership against configurable blocked words and the active username.
- **Explicit Failure Explanations**: Lists every passed and failed rule individually with concrete counts and thresholds.
- **Batch Sample Evaluator & Masked SQLite Audit Log**: Evaluates multiple sample strings via tuple unpacking and logs masked previews (`Vo********!K`) with CSV export.
