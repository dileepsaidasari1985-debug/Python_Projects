# Project Objectives

1. **Validate Minimum Length & Character Categories**: Count uppercase, lowercase, digit, special, and whitespace characters using a single `for` loop.
2. **Detect Consecutive Repetition**: Track consecutive identical character runs and reject runs exceeding `max_consecutive_repeat`.
3. **Block Prohibited Substrings**: Check case-insensitive membership of blocked dictionary words and user identifiers (`len >= 3`).
4. **Explain Every Failed Condition**: Return granular diagnostic messages for every rule that fails (rather than stopping at the first error).
5. **Support Batch Evaluation & Policy Configuration**: Allow live customization of policy thresholds and batch testing via tuple unpacking.
