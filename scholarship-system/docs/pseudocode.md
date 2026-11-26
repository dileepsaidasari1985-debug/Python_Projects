# Pseudocode

```text
ALGORITHM ScholarshipAllocationSystem

BEGIN
    INITIALIZE SQLite database tables (students, scholarship_rules)
    LOAD active rules FROM scholarship_rules

    FUNCTION ValidateStudent(data)
        errors <- empty list
        IF data.student_id is empty OR already exists THEN
            APPEND "Invalid or duplicate Student ID" TO errors
        ENDIF
        FOR EACH mark IN [math, physics, chemistry, english, cs]
            IF mark < 0 OR mark > 100 THEN
                APPEND "Marks must be between 0 and 100" TO errors
            ENDIF
        ENDFOR
        IF data.attendance < 0 OR data.attendance > 100 THEN
            APPEND "Attendance must be between 0 and 100" TO errors
        ENDIF
        IF data.annual_income < 0 THEN
            APPEND "Income cannot be negative" TO errors
        ENDIF
        RETURN (errors is empty), errors
    END FUNCTION

    FUNCTION GetIncomeMeritScore(income, slabs)
        FOR EACH (upper_limit, points) IN slabs
            IF income <= upper_limit THEN
                RETURN points
            ENDIF
        ENDFOR
        RETURN slab_above_points
    END FUNCTION

    FUNCTION EvaluateAndRank(students, rules)
        eligible_list <- empty list
        rejected_list <- empty list

        FOR EACH student IN students
            total <- student.math + student.physics + student.chemistry + student.english + student.cs
            aggregate <- total / 5.0
            reasons <- empty list

            IF aggregate < rules.min_aggregate THEN
                APPEND "Aggregate percentage below minimum" TO reasons
            ENDIF
            FOR EACH (subject_name, subject_mark) IN student.subjects
                IF subject_mark < rules.min_subject_marks THEN
                    APPEND "Subject marks below minimum" TO reasons
                ENDIF
            ENDFOR
            IF student.attendance < rules.min_attendance THEN
                APPEND "Attendance below minimum" TO reasons
            ENDIF
            IF student.annual_income > rules.max_family_income THEN
                APPEND "Family income exceeds limit" TO reasons
            ENDIF
            IF rules.income_certificate_required AND student.certificate != "Available" THEN
                APPEND "Income certificate missing" TO reasons
            ENDIF

            IF reasons is empty THEN
                income_merit <- GetIncomeMeritScore(student.annual_income, rules.slabs)
                score <- ROUND((aggregate * rules.w_agg) + (student.attendance * rules.w_att) + (income_merit * rules.w_inc), 2)
                student.scholarship_score <- score
                APPEND student TO eligible_list
            ELSE
                student.scholarship_score <- 0.00
                student.status <- "Not Eligible"
                APPEND student TO rejected_list
            ENDIF
        ENDFOR

        SORT eligible_list BY TUPLE (
            -scholarship_score,
            -aggregate,
            -attendance,
            annual_income,
            -total_marks,
            student_id
        )

        FOR rank FROM 1 TO LENGTH(eligible_list)
            student <- eligible_list[rank - 1]
            student.rank <- rank
            IF rank <= rules.scholarship_quota THEN
                student.selection_status <- "Eligible & Selected"
            ELSE
                student.selection_status <- "Eligible (Waitlisted)"
            ENDIF
        ENDFOR

        RETURN eligible_list, rejected_list
    END FUNCTION
END
```
