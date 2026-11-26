# Pseudocode

```text
FUNCTION GenerateSeatingPlan(hall, rows, cols, fixed_cap, rolls, reserved, mode)
    matrix <- EMPTY LIST
    usable <- 0
    idx <- 0

    FOR r FROM 0 TO rows - 1 DO
        row_cells <- EMPTY LIST
        FOR c FROM 0 TO cols - 1 DO
            (row_lbl, col_num, seat_id) <- BuildSeatId(r, c)
            IF seat_id IN reserved THEN
                APPEND (seat_id, "RESERVED", reserved[seat_id]) TO row_cells
            ELSE IF (mode == "ALTERNATE_CHECKERBOARD" AND (r + c) MOD 2 == 1) OR
                    (mode == "ALTERNATE_COLUMN" AND c MOD 2 == 1) THEN
                APPEND (seat_id, "GAP", "ALT-GAP") TO row_cells
            ELSE IF usable >= fixed_cap THEN
                APPEND (seat_id, "CAP_LIMIT", "CAP-FULL") TO row_cells
            ELSE
                usable <- usable + 1
                IF idx < LENGTH(rolls) THEN
                    APPEND (seat_id, "OCCUPIED", rolls[idx]) TO row_cells
                    idx <- idx + 1
                ELSE
                    APPEND (seat_id, "VACANT", "OPEN") TO row_cells
                END IF
            END IF
        END FOR
        APPEND row_cells TO matrix
    END FOR

    overflow <- rolls[idx : LENGTH(rolls)]
    RETURN (matrix, overflow)
END FUNCTION
```
