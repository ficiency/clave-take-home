"""
Transform order item data from raw_data to order_items table.
Uses hash maps for O(1) lookups and batch upsert.
"""

from etl.db.connection import db
from .utils import build_order_lookup, load_item_catalog, load_square_prices, get_item_info, batch_upsert


def extract_doordash_items(data: dict, order_id: str, catalog: dict) -> list:
    """Extract DoorDash order items."""
    source_order_id = data["external_delivery_id"]
    items = []
    for item in data.get("order_items", []):
        item_id = item["item_id"]
        name, category = get_item_info(catalog, "doordash", item_id)
        items.append({
            "order_id": order_id,
            "source_name": "doordash",
            "source_order_item_id": f"{source_order_id}_{item_id}",
            "item_name": name,
            "quantity": item["quantity"],
            "unit_price": item["unit_price"],
            "total_price": item["quantity"] * item["unit_price"],
            "category": category,
        })
    return items


def extract_square_items(data: dict, order_id: str, catalog: dict, prices: dict) -> list:
    """Extract Square order items."""
    items = []
    for item in data.get("line_items", []):
        cat_id = item["catalog_object_id"]
        name, category = get_item_info(catalog, "square", cat_id)
        qty = int(item["quantity"])
        total = item.get("gross_sales_money", {}).get("amount", 0)
        unit = prices.get(cat_id) or (total // qty if qty > 0 else 0)
        items.append({
            "order_id": order_id,
            "source_name": "square",
            "source_order_item_id": item["uid"],
            "item_name": name,
            "quantity": qty,
            "unit_price": unit,
            "total_price": total,
            "category": category,
        })
    return items


def extract_toast_items(data: dict, order_id: str, catalog: dict) -> list:
    """Extract Toast order items from nested checks/selections."""
    items = []
    for check in data.get("checks", []):
        for sel in check.get("selections", []):
            if not sel.get("item") or not sel["item"].get("guid"):
                continue
            item_guid = sel["item"]["guid"]
            name, category = get_item_info(catalog, "toast", item_guid)
            qty = sel.get("quantity", 0)
            price = sel.get("price", 0)
            items.append({
                "order_id": order_id,
                "source_name": "toast",
                "source_order_item_id": sel["guid"],
                "item_name": name,
                "quantity": qty,
                "unit_price": price // qty if qty > 0 else 0,
                "total_price": price,
                "category": category,
            })
    return items


def transform_order_items() -> dict:
    """Transform all order items from raw_data to order_items table."""
    client = db.client
    counts = {"doordash": 0, "square": 0, "toast": 0, "errors": 0}
    
    # Build lookups once - O(1) per item instead of O(n) DB queries
    order_lookup = build_order_lookup(client)
    catalog = load_item_catalog()
    square_prices = load_square_prices()
    
    response = client.table("raw_data").select("source_name, data").eq("entity_type", "order").execute()
    
    all_items = []
    for row in response.data:
        source, data = row["source_name"], row["data"]
        try:
            source_order_id = data.get("external_delivery_id") or data.get("id") or data.get("guid")
            order_id = order_lookup[(source, source_order_id)]
            
            if source == "doordash":
                items = extract_doordash_items(data, order_id, catalog)
            elif source == "square":
                items = extract_square_items(data, order_id, catalog, square_prices)
            elif source == "toast":
                items = extract_toast_items(data, order_id, catalog)
            else:
                continue
            
            all_items.extend(items)
            counts[source] += len(items)
        except Exception as e:
            print(f"[ERROR] {source} order items: {e}")
            counts["errors"] += 1
    
    batch_upsert(client, "order_items", all_items)
    return counts


if __name__ == "__main__":
    print("Transforming order items...")
    counts = transform_order_items()
    total = sum(v for k, v in counts.items() if k != "errors")
    print(f"Done: {total} items ({counts})")
