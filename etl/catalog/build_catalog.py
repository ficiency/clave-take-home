"""
Builds item_catalog_generated.json from all POS sources.
Uses hash maps for O(1) lookups during catalog assembly.
"""

import json
import sys
from pathlib import Path

# Allow running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))

from extract import extract_doordash, extract_square, extract_toast
from normalize import normalize_item_name, normalize_category_name, square_variation_suffix

DATA_DIR = Path(__file__).parent.parent / "data" / "sources"
OUTPUT_PATH = Path(__file__).parent / "item_catalog_generated.json"


def build_catalog():
    """Runs the catalog build pipeline."""
    
    # Extract from sources
    dd_names, dd_cats = extract_doordash(DATA_DIR / "doordash_orders.json")
    sq_names, sq_cats, sq_vars, sq_used = extract_square(DATA_DIR / "square" / "catalog.json", DATA_DIR / "square" / "orders.json")
    toast_names, toast_cats = extract_toast(DATA_DIR / "toast_pos_export.json")
    
    # Build catalog
    catalog = {
        "doordash": {"_comment": "Maps DoorDash item IDs to normalized names."},
        "square": {"_comment": "Maps Square item IDs to normalized names."},
        "toast": {"_comment": "Maps Toast item IDs to normalized names."},
    }
    
    # DoorDash
    for item_id, name in dd_names.items():
        catalog["doordash"][item_id] = {
            "name": normalize_item_name(name),
            "category": normalize_category_name(dd_cats.get(item_id, ""))
        }
    
    # Square (only items used in orders)
    for var_id in sq_used:
        if var_id in sq_names:
            base = normalize_item_name(sq_names[var_id])
            suffix = square_variation_suffix(sq_vars.get(var_id, ""), base)
            catalog["square"][var_id] = {
                "name": base + suffix,
                "category": normalize_category_name(sq_cats.get(var_id, ""))
            }
    
    # Toast
    for item_id, name in toast_names.items():
        catalog["toast"][item_id] = {
            "name": normalize_item_name(name),
            "category": normalize_category_name(toast_cats.get(item_id, ""))
        }
    
    # Save
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
    
    # Summary
    counts = {k: len(v) - 1 for k, v in catalog.items()}
    print(f"Catalog saved: {OUTPUT_PATH.name}")
    print(f"  DoorDash: {counts['doordash']} | Square: {counts['square']} | Toast: {counts['toast']}")
    print(f"  Total: {sum(counts.values())} items")


if __name__ == "__main__":
    build_catalog()
