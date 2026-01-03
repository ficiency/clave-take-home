"""
Extracts item data from Toast orders.

DSA: Uses hash map (dict) for O(1) deduplication - first occurrence wins.
Single pass through nested structure (orders -> checks -> selections): O(n).
"""

import json
from pathlib import Path


def extract_items(path: Path) -> tuple[dict, dict]:
    """Returns (item_names, item_categories) from Toast orders."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    
    names, categories = {}, {}
    for order in data.get("orders", []):
        for check in order.get("checks", []):
            for sel in check.get("selections", []):
                if "item" in sel and "guid" in sel["item"]:
                    guid = sel["item"]["guid"]
                    if guid not in names:  # O(1) lookup
                        names[guid] = sel.get("displayName") or sel["item"].get("name", "")
                        categories[guid] = sel.get("itemGroup", {}).get("name", "")
    
    return names, categories
