"""
Verifies catalog items against source data for all POS systems.
Uses hash maps for O(1) lookups during verification.
"""

import json
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Setup paths for imports
SCRIPT_DIR = Path(__file__).parent
CATALOG_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = CATALOG_DIR.parent.parent
sys.path.insert(0, str(CATALOG_DIR))

from extract import extract_doordash, extract_square, extract_toast
from normalize import normalize_category_name

# Data paths
DATA_DIR = PROJECT_ROOT / "etl" / "data" / "sources"
CATALOG_PATH = CATALOG_DIR / "item_catalog.json"


def verify_source(name: str, catalog_items: dict, source_items: dict, source_cats: dict, valid_ids: set = None):
    """
    Verifies catalog entries against source data.
    Uses set intersection for O(n) verification instead of nested loops O(n²).
    Returns tuple of (errors, category_errors, missing).
    """
    errors, cat_errors, missing = [], [], []
    
    # Use valid_ids filter if provided (for Square orders filter)
    check_ids = valid_ids if valid_ids else set(source_items.keys())
    
    for item_id, catalog_entry in catalog_items.items():
        cat_name = catalog_entry.get("name", "")
        cat_category = catalog_entry.get("category", "")
        
        # Check if item exists in source
        if valid_ids and item_id not in valid_ids:
            errors.append((item_id, "NOT FOUND in orders"))
            continue
        if item_id not in source_items:
            errors.append((item_id, "NOT FOUND in source"))
            continue
        
        original = source_items[item_id]
        status = f"[OK] {item_id}: '{original}' -> '{cat_name}'"
        
        # Verify category
        if cat_category:
            orig_cat = source_cats.get(item_id, "")
            norm_cat = normalize_category_name(orig_cat)
            if norm_cat != cat_category:
                cat_errors.append((item_id, orig_cat, cat_category))
                print(f"{status} | [CAT ERROR] '{orig_cat}' -> '{cat_category}'")
            else:
                print(f"{status} | [CAT OK] '{orig_cat}' -> '{cat_category}'")
        else:
            print(status)
    
    # Find items in source but not in catalog
    for item_id in check_ids:
        if item_id not in catalog_items:
            missing.append((item_id, source_items.get(item_id, "UNKNOWN")))
    
    return errors, cat_errors, missing


def print_results(errors: list, cat_errors: list, missing: list):
    """Prints verification results."""
if errors:
    print("\nERRORS:")
        for item_id, msg in errors:
            print(f"  [ERROR] {item_id}: {msg}")
    if cat_errors:
    print("\nCATEGORY ERRORS:")
        for item_id, orig, cat in cat_errors:
            print(f"  [CAT ERROR] {item_id}: '{orig}' != catalog '{cat}'")
if missing:
    print("\nMISSING IN CATALOG:")
        for item_id, name in missing:
            print(f"  [MISSING] {item_id}: '{name}'")


def main():
    # Load catalog (hash map for O(1) lookups)
    with open(CATALOG_PATH, encoding="utf-8") as f:
        catalog = json.load(f)
    
    results = {}  # Accumulate results for summary
    
    # DoorDash
    print("=" * 80 + "\nVERIFYING DOORDASH\n" + "=" * 80)
    dd_items, dd_cats = extract_doordash(DATA_DIR / "doordash_orders.json")
    dd_catalog = {k: v for k, v in catalog["doordash"].items() if k != "_comment"}
    results["doordash"] = verify_source("doordash", dd_catalog, dd_items, dd_cats)
    print_results(*results["doordash"])
    
    # Square (filter by items in orders)
    print("\n" + "=" * 80 + "\nVERIFYING SQUARE\n" + "=" * 80)
    sq_names, _, sq_cats, sq_in_orders = extract_square(
        DATA_DIR / "square" / "catalog.json",
        DATA_DIR / "square" / "orders.json"
    )
    sq_catalog = {k: v for k, v in catalog["square"].items() if k != "_comment"}
    results["square"] = verify_source("square", sq_catalog, sq_names, sq_cats, sq_in_orders)
    print_results(*results["square"])
    
    # Toast
    print("\n" + "=" * 80 + "\nVERIFYING TOAST\n" + "=" * 80)
    toast_items, toast_cats = extract_toast(DATA_DIR / "toast_pos_export.json")
    toast_catalog = {k: v for k, v in catalog["toast"].items() if k != "_comment"}
    results["toast"] = verify_source("toast", toast_catalog, toast_items, toast_cats)
    print_results(*results["toast"])
    
    # Summary
    print("\n" + "=" * 80 + "\nSUMMARY\n" + "=" * 80)
    total_items = sum(len(catalog[s]) - 1 for s in ["doordash", "square", "toast"])
    total_errors = sum(len(r[0]) for r in results.values())
    total_cat_errors = sum(len(r[1]) for r in results.values())
    total_missing = sum(len(r[2]) for r in results.values())
    
    print(f"Total items in catalog: {total_items}")
print(f"Total errors (IDs not found): {total_errors}")
    print(f"Total category errors: {total_cat_errors}")
print(f"Total missing (IDs in data but not in catalog): {total_missing}")

    if total_errors == 0 and total_missing == 0 and total_cat_errors == 0:
    print("\n[SUCCESS] ALL IDs AND CATEGORIES ARE CORRECT AND COMPLETE!")
elif total_errors == 0 and total_missing == 0:
    print("\n[WARNING] IDs CORRECT, BUT THERE ARE CATEGORY ERRORS")
else:
    print("\n[WARNING] THERE ARE ISSUES TO FIX")


if __name__ == "__main__":
    main()
