# Item Catalog

Normalized item catalog mapping source-specific item IDs to standardized names and categories.

## Structure

```
catalog/
  ├── item_catalog.json          # Output: normalized catalog
  ├── build_catalog.py           # Main script: orchestrates extract → normalize → build
  ├── extract/                   # 1️⃣ EXTRACT: raw data extraction from sources
  │   ├── __init__.py            # Public exports
  │   ├── doordash.py
  │   ├── square.py
  │   └── toast.py
  ├── normalize/                 # 2️⃣ NORMALIZE: cleaning and standardization
  │   ├── __init__.py            # Public exports
  │   ├── config.py              # Constants and pre-compiled regex patterns
  │   └── core.py                # Normalization functions
  └── scripts/                   # Utility scripts
      └── verify_all_items.py    # Verification script
```

## Pipeline Flow

1. **EXTRACT** (`extract/`) - Extracts raw item data from source files
   - `doordash.py`: Extracts from DoorDash orders
   - `square.py`: Extracts from Square catalog and orders
   - `toast.py`: Extracts from Toast orders

2. **NORMALIZE** (`normalize/`) - Cleans and standardizes item names and categories
   - Fixes typos (e.g., "Griled" → "Grilled")
   - Removes emojis from categories
   - Expands abbreviations (e.g., "Lg" → "Large")
   - Standardizes capitalization and formatting

3. **BUILD** (`build_catalog.py`) - Orchestrates the pipeline and generates the catalog
   - Calls extractors to get raw data
   - Applies normalization functions
   - Generates `item_catalog.json`

## Usage

### Generate Catalog

```powershell
python etl/catalog/build_catalog.py
```

Generates `item_catalog_generated.json` (does not override verified catalog).

### Verify Catalog

```powershell
python etl/catalog/scripts/verify_all_items.py
```

Verifies that the catalog matches source data.

## Output Format

The catalog maps source-specific IDs to normalized names and categories:

```json
{
  "doordash": {
    "itm_001": {
      "name": "Classic Burger",
      "category": "Entrees"
    }
  },
  "square": {
    "VAR_BURGER_REG": {
      "name": "Classic Burger",
      "category": "Burgers"
    }
  },
  "toast": {
    "itm_burger_001": {
      "name": "Classic Burger",
      "category": "Burgers"
    }
  }
}
```

## Source ID Formats

- **DoorDash**: `item_id` (e.g., `"itm_001"`)
- **Square**: `catalog_object_id` - variation ID (e.g., `"VAR_BURGER_REG"`)
- **Toast**: `item.guid` (e.g., `"itm_burger_001"`)

