# Core Locations - Field Mappings & Transformations

Maps location data from all sources to `core_locations` table.

## Source Fields → Core Fields

### DoorDash
- `store_id` → `source_location_id`
- `name` → `name`
- `address.street` → `address_line_1`
- `address.city` → `city`
- `address.state` → `state`
- `address.zip_code` → `postal_code`
- `address.country` → `country`
- `timezone` → `timezone`

### Square
- `id` → `source_location_id`
- `name` → `name`
- `address.address_line_1` → `address_line_1`
- `address.locality` → `city`
- `address.administrative_district_level_1` → `state`
- `address.postal_code` → `postal_code`
- `address.country` → `country`
- `timezone` → `timezone`

### Toast
- `guid` → `source_location_id` (each location object from `locations[]` array)
- `name` → `name`
- `address.line1` → `address_line_1`
- `address.city` → `city`
- `address.state` → `state`
- `address.zip` → `postal_code`
- `address.country` → `country`
- `timezone` → `timezone`

## Transformations
- All fields map directly (no calculations needed)
- `source_name` is set to: "doordash", "square", or "toast"
- `location_id` is a generated UUID
- `created_at` and `updated_at` are set to current timestamp

