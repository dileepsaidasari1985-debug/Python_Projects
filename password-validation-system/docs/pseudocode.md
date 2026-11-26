# Pseudocode

```text
FUNCTION EvaluatePassword(pw, username, policy)
    upper <- 0; lower <- 0; digit <- 0; special <- 0; space <- 0
    max_run <- 0; cur_run <- 0; prev <- NULL

    FOR EACH ch IN pw DO
        IF IsUpper(ch) THEN upper <- upper + 1
        ELSE IF IsLower(ch) THEN lower <- lower + 1
        ELSE IF IsDigit(ch) THEN digit <- digit + 1
        ELSE IF IsSpace(ch) THEN space <- space + 1
        ELSE IF ch IN SPECIAL_CHARS THEN special <- special + 1
        END IF

        IF ch == prev THEN cur_run <- cur_run + 1
        ELSE cur_run <- 1; prev <- ch
        END IF
        IF cur_run > max_run THEN max_run <- cur_run
    END FOR

    failed <- EMPTY LIST
    IF LENGTH(pw) < policy.min_length THEN APPEND "Too short" TO failed
    IF upper < policy.min_upper THEN APPEND "Missing uppercase" TO failed
    IF lower < policy.min_lower THEN APPEND "Missing lowercase" TO failed
    IF digit < policy.min_digits THEN APPEND "Missing digits" TO failed
    IF special < policy.min_special THEN APPEND "Missing special chars" TO failed
    IF max_run > policy.max_consecutive_repeat THEN APPEND "Excessive repetition" TO failed

    FOR EACH word IN policy.prohibited + [LOWER(username)] DO
        IF word IN LOWER(pw) THEN APPEND ("Contains prohibited substring: " + word) TO failed
    END FOR

    RETURN (LENGTH(failed) == 0, failed)
END FUNCTION
```
