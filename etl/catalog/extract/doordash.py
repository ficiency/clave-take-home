"""
Extracts item data from DoorDash orders.

DSA: Uses hash map (dict) for O(1) deduplication - first occurrence wins.
Single pass through all orders: O(n) time complexity.
"""

import json
from pathlib import Path


def extract_items(path: Path) -> tuple[dict, dict]:
    """Returns (item_names, item_categories) from DoorDash orders."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    
    names, categories = {}, {}
    for order in data.get("orders", []):
        for item in order.get("order_items", []):
            item_id = item["item_id"]
            if item_id not in names:  # O(1) lookup
                names[item_id] = item["name"]
                categories[item_id] = item.get("category", "")
    
    return names, categories
