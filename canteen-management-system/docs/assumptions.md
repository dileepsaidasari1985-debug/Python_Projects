# Project Assumptions & Business Rules

1. **Tax Rate**: All fulfilled canteen items carry a uniform `5%` campus GST (`DEFAULT_GST_RATE = 0.05`).
2. **Partial Order Handling**: If a multi-item order has one available item and one out-of-stock/over-requested item, the available item is billed and deducted (`PARTIAL` status) while the unavailable quantity is rejected with an explicit reason.
3. **Sequential Stock Consistency**: In a queue of successive orders, stock deducted by Order #1 immediately constrains Order #2.
4. **Reorder Alert**: Any item with `stock <= reorder_level` triggers a `LOW` stock badge.
