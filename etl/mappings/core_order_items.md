# Core Order Items - Field Mappings & Transformations

Maps order item data from all sources to `core_order_items` table.

## Source Fields → Core Fields

### DoorDash
- `{external_delivery_id}_{item_id}` → `source_order_item_id` (combined to ensure uniqueness - same item_id can appear in multiple orders)
- `external_delivery_id` → Lookup to `core_orders` by `source_order_id` → `order_id`
- Lookup `item_id` in `item_catalog.json` → `item_name`
- `quantity` → `quantity` (already integer)
- `unit_price` → `unit_price` (already in cents)
- Calculate `total_price`: `quantity * unit_price`
- Lookup `item_id` in `item_catalog.json` → `category`
- `category` (original from source) → discard (use normalized from catalog)

### Square
- `line_items[].uid` → `source_order_item_id`
- `id` (order id) → Lookup to `core_orders` by `source_order_id` → `order_id`
- Lookup `catalog_object_id` in `item_catalog.json` → `item_name`
- `quantity` → `quantity` (convert string to integer)
- Lookup `catalog_object_id` in `square/catalog.json` → Find variation → `item_variation_data.price_money.amount` → `unit_price`
  - Alternative: Calculate from `gross_sales_money.amount / quantity` (if catalog lookup fails)
- `gross_sales_money.amount` → `total_price` (already in cents)
- Lookup `catalog_object_id` in `item_catalog.json` → `category`

### Toast
- `selections[].guid` → `source_order_item_id`
- `guid` (order guid) → Lookup to `core_orders` by `source_order_id` → `order_id`
- Lookup `item.guid` in `item_catalog.json` → `item_name`
- `quantity` → `quantity` (already integer)
- Calculate `unit_price`: `price / quantity` (price is total, need to divide)
- `price` → `total_price` (already in cents, but represents total for the item)
- Lookup `item.guid` in `item_catalog.json` → `category`

## Transformations

### Item Name & Category Lookup
**All sources use `item_catalog.json` for normalized names and categories:**

- DoorDash: Lookup by `item_id` → get `name` and `category`
- Square: Lookup by `catalog_object_id` (variation ID) → get `name` and `category`
- Toast: Lookup by `item.guid` → get `name` and `category`

This ensures:
- Consistent naming (no typos, emojis, or variations)
- Categories preserved from original source (only emojis removed and typos corrected, NOT normalized between sources)
- Single source of truth for item metadata

### Quantity Transformations
- DoorDash: Already integer → use directly
- Square: String → convert to integer
- Toast: Already integer → use directly

### Price Calculations
- DoorDash: `unit_price` is direct, `total_price = quantity * unit_price`
- Square: `unit_price` from catalog lookup or calculation, `total_price` from `gross_sales_money.amount`
- Toast: `unit_price = price / quantity`, `total_price = price`

### Lookups
- All sources require lookup to `core_orders` table using `source_order_id` to get `order_id` UUID
- All sources require lookup to `item_catalog.json` to get normalized `item_name` and `category`
- Square additionally requires lookup to `square/catalog.json` for `unit_price` (if not using calculated method)

