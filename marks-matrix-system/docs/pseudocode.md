# Pseudocode

```text
FUNCTION AnalyzeMarksMatrix(rows, subjects, low_threshold, pass_mark)
    row_stats <- EMPTY LIST
    FOR EACH (sid, name, marks) IN rows DO
        total <- 0; min_m <- marks[0]; max_m <- marks[0]
        FOR EACH m IN marks DO
            total <- total + m
            IF m < min_m THEN min_m <- m
            IF m > max_m THEN max_m <- m
        END FOR
        avg <- total / LENGTH(subjects)
        APPEND (sid, name, total, avg, min_m, max_m, Grade(avg)) TO row_stats
    END FOR

    ranked <- SortDescending(row_stats, BY (avg, total, min_m))
    top_performers <- ranked[0 : 3]

    col_stats <- EMPTY LIST
    low_subjects <- EMPTY LIST
    FOR col FROM 0 TO LENGTH(subjects) - 1 DO
        sum_col <- 0; high <- rows[0][2][col]; low <- rows[0][2][col]; passes <- 0
        FOR EACH row IN rows DO
            val <- row[2][col]
            sum_col <- sum_col + val
            IF val > high THEN high <- val
            IF val < low THEN low <- val
            IF val >= pass_mark THEN passes <- passes + 1
        END FOR
        subj_avg <- sum_col / LENGTH(rows)
        IF subj_avg < low_threshold THEN APPEND subjects[col] TO low_subjects
        APPEND (subjects[col], subj_avg, high, low, passes) TO col_stats
    END FOR

    RETURN (row_stats, col_stats, top_performers, low_subjects)
END FUNCTION
```
