# Core Orders - Field Mappings & Transformations

Maps order data from all sources to `core_orders` table.

## Source Fields → Core Fields

### DoorDash
- `external_delivery_id` → `source_order_id`
- `store_id` → Lookup to `core_locations` by `source_location_id` → `location_id`
- `created_at` → `created_at` (parse ISO 8601)
- `delivery_time` OR `pickup_time` (priority: delivery_time) → `closed_at`
  - Fallback: `created_at` if neither exists
- `order_status` → `status` (map: "DELIVERED" → "completed", etc.)
- `order_fulfillment_method` → `fulfillment_method` (map: "MERCHANT_DELIVERY" → "DELIVERY", "PICKUP" → "PICKUP")
- `order_subtotal` → `subtotal` (already in cents)
- `tax_amount` → `tax_amount` (already in cents)
- `dasher_tip` → `tip_amount` (already in cents)
- `total_charged_to_consumer` → `total_amount` (already in cents)

### Square
- `id` → `source_order_id`
- `location_id` → Lookup to `core_locations` by `source_location_id` → `location_id`
- `created_at` → `created_at` (parse ISO 8601)
- `closed_at` → `closed_at` (parse ISO 8601)
- `state` → `status` (map: "COMPLETED" → "completed", etc.)
- `fulfillments[0].type` → `fulfillment_method` (map: "DINE_IN" → "DINE_IN", "PICKUP" → "PICKUP", "SHIPMENT" → "DELIVERY")
- Calculate `subtotal`: Sum of `line_items[].gross_sales_money.amount`
- `total_tax_money.amount` → `tax_amount` (already in cents)
- `total_tip_money.amount` → `tip_amount` (already in cents)
- `total_money.amount` → `total_amount` (already in cents)

### Toast
- `guid` → `source_order_id`
- `restaurantGuid` → Lookup to `core_locations` by `source_location_id` → `location_id`
- `openedDate` → `created_at` (parse ISO 8601)
- `closedDate` → `closed_at` (parse ISO 8601)
  - Fallback: `paidDate` if `closedDate` is null
- Map `voided`/`deleted` → `status`:
  - `voided=true` → "voided"
  - `deleted=true` → "deleted"
  - Both false → "completed"
- `diningOption.behavior` → `fulfillment_method` (map: "TO_GO" → "PICKUP", "DINE_IN" → "DINE_IN", "DELIVERY" → "DELIVERY")
- Calculate `subtotal`: Sum of `checks[].amount` (in cents, already)
- Calculate `tax_amount`: Sum of `checks[].taxAmount` (in cents, already)
- Calculate `tip_amount`: Sum of `checks[].tipAmount` (in cents, already)
- Calculate `total_amount`: Sum of `checks[].totalAmount` (in cents, already)

## Transformations

### Status Mapping
- DoorDash: "DELIVERED" → "completed", "CANCELLED" → "cancelled"
- Square: "COMPLETED" → "completed", "CANCELED" → "cancelled"
- Toast: Boolean flags → "voided", "deleted", or "completed"

### Fulfillment Method Mapping
- DoorDash: "MERCHANT_DELIVERY" → "DELIVERY", "PICKUP" → "PICKUP"
- Square: "DINE_IN" → "DINE_IN", "PICKUP" → "PICKUP", "SHIPMENT" → "DELIVERY"
- Toast: "TO_GO" → "PICKUP", "DINE_IN" → "DINE_IN", "DELIVERY" → "DELIVERY"

### Calculations
- Square `subtotal`: Requires summing `line_items[].gross_sales_money.amount`
- Toast financials: Requires summing across all `checks[]` arrays
- All amounts are already in cents (no conversion needed)

### Lookups
- All sources require lookup to `core_locations` table using `source_location_id` to get `location_id` UUID

