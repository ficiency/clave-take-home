"""
Extracts item data from Square catalog and orders.

DSA: Uses hash maps (dict) for O(1) category lookups.
      Uses set for O(1) membership checks on used variation IDs.
Single pass through catalog objects and orders: O(n + m).
"""

import json
from pathlib import Path


def extract_items(catalog_path: Path, orders_path: Path) -> tuple[dict, dict, dict, set]:
    """Returns (item_names, item_categories, variation_names, used_ids) from Square."""
    with open(catalog_path, encoding="utf-8") as f:
        catalog = json.load(f)
    with open(orders_path, encoding="utf-8") as f:
        orders = json.load(f)
    
    # Category lookup - O(1) access
    cat_lookup = {
        obj["id"]: obj["category_data"]["name"]
        for obj in catalog.get("objects", [])
        if obj["type"] == "CATEGORY"
    }
    
    # Build item/variation maps in single pass
    names, categories, var_names = {}, {}, {}
    for obj in catalog.get("objects", []):
        if obj["type"] != "ITEM":
            continue
        base = obj["item_data"]["name"]
        cat = cat_lookup.get(obj["item_data"].get("category_id"), "")  # O(1)
        
        for var in obj["item_data"].get("variations", []):
            var_id = var["id"]
            names[var_id] = base
            categories[var_id] = cat
            var_names[var_id] = var["item_variation_data"].get("name", "")
    
    # Set for O(1) membership checks
    used_ids = {
        item["catalog_object_id"]
        for order in orders.get("orders", [])
        for item in order.get("line_items", [])
    }
    
    return names, categories, var_names, used_ids
