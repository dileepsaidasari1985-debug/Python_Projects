# Smart Canteen Order and Stock Management

**Case Study #57:** *Process successive customer orders, calculate bills, update available inventory, reject unavailable quantities, and summarize daily sales and remaining stock.*

## Key Features
- **Order Counter & Successive Queue**: Processes individual or sequential customer orders via loops and `(item_code, qty)` tuple unpacking.
- **Inventory Guardrails**: Rejects unknown codes, zero/negative quantities, out-of-stock items, and over-requested quantities while completing valid line items.
- **Bill & GST Engine**: Computes line totals, order subtotal, 5% campus GST, and grand payable total.
- **Daily Sales & Stock Summary**: Tracks cumulative revenue, units sold, low-stock reorder alerts, ASCII stock gauges, and CSV exports.
