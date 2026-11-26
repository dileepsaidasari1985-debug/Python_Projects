# Pseudocode

```text
PROCEDURE SmartCampusMenu()
    InitDatabase()
    WHILE TRUE DO
        DISPLAY MENU_OPTIONS
        choice <- READ_INPUT()
        IF choice == "0" THEN
            BREAK
        ELSE IF choice == "1" THEN
            DisplayOrAddStudents()
        ELSE IF choice == "2" THEN
            FOR EACH s IN GetStudents() DO
                pct <- (s.attended / s.total) * 100
                DISPLAY s.id, pct, IF pct < 75 THEN "SHORTAGE" ELSE "OK"
            END FOR
        ELSE IF choice == "3" THEN
            FOR EACH s IN GetStudents() DO
                (total, avg, grade, passed) <- EvaluateMarks((s.math, s.cs, s.eng))
                DISPLAY s.id, avg, grade
            END FOR
        ELSE IF choice == "4" THEN
            RegisterStudentForEventWithCapacityCheck()
        ELSE IF choice == "5" THEN
            AllocateResourceWithSlotConflictCheck()
        ELSE IF choice == "6" THEN
            BuildCampusSummaryReport()
        END IF
    END WHILE
END PROCEDURE
```
