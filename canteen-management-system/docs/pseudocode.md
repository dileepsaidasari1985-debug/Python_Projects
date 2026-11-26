# Pseudocode

```text
FUNCTION ProcessSingleOrder(customer, items, inventory, gst_rate)
    subtotal <- 0.0
    accepted <- EMPTY LIST
    rejected <- EMPTY LIST

    FOR EACH (code, raw_qty) IN items DO
        qty <- ParsePositiveInt(raw_qty)
        IF qty <= 0 THEN
            APPEND (code, raw_qty, "Invalid quantity") TO rejected
            CONTINUE
        END IF

        item <- FindItem(inventory, code)
        IF item IS NULL OR qty > item.stock THEN
            APPEND (code, qty, "Unavailable quantity") TO rejected
            CONTINUE
        END IF

        item.stock <- item.stock - qty
        line_total <- item.unit_price * qty
        subtotal <- subtotal + line_total
        APPEND (code, qty, line_total) TO accepted
    END FOR

    gst <- ROUND(subtotal * gst_rate, 2)
    total <- subtotal + gst
    RETURN (accepted, rejected, subtotal, gst, total, inventory)
END FUNCTION
```
