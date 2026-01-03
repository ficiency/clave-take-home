# Field Mappings & Transformations

This directory documents the mappings and transformations required to convert raw data from each source (DoorDash, Square, Toast) into the Core layer tables.

## Overview

The Core layer consists of three main tables:
1. `core_locations` - Unified location data
2. `core_orders` - Unified order data
3. `core_order_items` - Unified order item data

## Documentation Files

- [`core_locations.md`](./core_locations.md) - Location field mappings
- [`core_orders.md`](./core_orders.md) - Order field mappings and transformations
- [`core_order_items.md`](./core_order_items.md) - Order item field mappings and transformations

## Key Concepts

### Direct Mapping
Fields that exist in the source and map directly to the core table without transformation.

### Lookup Operations
Fields that require querying another table or data structure:
- Location lookups: Convert `source_location_id` to `location_id` UUID from `core_locations`
- Order lookups: Convert `source_order_id` to `order_id` UUID from `core_orders`
- Item catalog lookups: Get normalized `item_name` and `category` from `item_catalog.json`

### Calculations
Fields that require computation:
- Square `subtotal`: Sum of line item gross sales
- Toast financials: Sum across all checks
- Toast `unit_price`: Divide total price by quantity

### Value Mapping
Fields that require converting values to a common schema:
- Status values: "DELIVERED" → "completed", "COMPLETED" → "completed", etc.
- Fulfillment methods: "TO_GO" → "PICKUP", "SHIPMENT" → "DELIVERY", etc.

### Fallback Logic
Fields that may not exist in all sources:
- DoorDash `closed_at`: Use `delivery_time`, fallback to `pickup_time`, then `created_at`
- Toast `closed_at`: Use `closedDate`, fallback to `paidDate`

## Item Catalog Usage

All order items use the internal `item_catalog.json` for:
- **Normalized item names**: Consistent naming without typos, emojis, or variations
- **Normalized categories**: Unified category names across all sources

This eliminates the need to clean item names during transformation and ensures consistency across all sources.

