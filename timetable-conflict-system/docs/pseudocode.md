# Pseudocode

```text
FUNCTION ParseScheduleString(raw_string)
    parts <- SPLIT(TRIM(raw_string), "|")
    IF LENGTH(parts) == 4 THEN
        (code, title, slot, room) <- parts
    ELSE IF LENGTH(parts) == 3 THEN
        (code, slot, room) <- parts
        title <- code
    ELSE
        RETURN (FALSE, NULL, "Invalid format")
    END IF

    (day_str, time_range) <- SPLIT_WHITESPACE(slot)
    day <- NormalizeDay(day_str)
    (start_str, end_str) <- SPLIT(time_range, "-")
    start_min <- ToMinutes(start_str)
    end_min <- ToMinutes(end_str)

    IF day == "" OR end_min <= start_min THEN
        RETURN (FALSE, NULL, "Invalid day or time range")
    END IF
    RETURN (TRUE, (UPPER(code), title, day, start_str, end_str, start_min, end_min, UPPER(room)), "")
END FUNCTION

FUNCTION ValidateProposedTimetable(course_tuples, room_tuples)
    time_conflicts <- EMPTY LIST
    room_issues <- EMPTY LIST

    FOR i FROM 0 TO LENGTH(course_tuples) - 1 DO
        (c1, t1, d1, ss1, es1, s1, e1, r1) <- UNPACK course_tuples[i]
        FOR j FROM i + 1 TO LENGTH(course_tuples) - 1 DO
            (c2, t2, d2, ss2, es2, s2, e2, r2) <- UNPACK course_tuples[j]
            IF d1 == d2 AND s1 < e2 AND s2 < e1 THEN
                ov_start <- MAX(s1, s2)
                ov_end <- MIN(e1, e2)
                APPEND (c1, c2, d1, ov_start, ov_end, r1 == r2) TO time_conflicts
            END IF
        END FOR
    END FOR

    FOR EACH course IN course_tuples DO
        room <- LookupRoom(course.room_code, room_tuples)
        IF room IS NULL OR (room.status != "Available" AND OverlapsBlockedWindow(course, room)) THEN
            APPEND (course.code, course.room_code, "Unavailable") TO room_issues
        END IF
    END FOR

    is_valid <- (LENGTH(time_conflicts) == 0 AND LENGTH(room_issues) == 0)
    RETURN (is_valid, time_conflicts, room_issues)
END FUNCTION
```
