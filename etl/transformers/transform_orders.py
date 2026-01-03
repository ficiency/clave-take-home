"""
Transform order data from raw_data to orders table.
Uses hash maps for O(1) location lookups and batch upsert.
"""

from etl.db.connection import db
from .utils import build_location_lookup, map_status, map_fulfillment, batch_upsert


def extract_doordash(data: dict, loc_lookup: dict) -> dict:
    """Extract DoorDash order fields."""
    return {
        "location_id": loc_lookup[("doordash", data["store_id"])],
        "source_name": "doordash",
        "source_order_id": data["external_delivery_id"],
        "created_at": data["created_at"],
        "closed_at": data.get("delivery_time") or data.get("pickup_time") or data["created_at"],
        "status": map_status("doordash", data["order_status"]),
        "fulfillment_method": map_fulfillment("doordash", data.get("order_fulfillment_method", "")),
        "subtotal": data["order_subtotal"],
        "tax_amount": data["tax_amount"],
        "tip_amount": data.get("dasher_tip", 0),
        "total_amount": data["total_charged_to_consumer"],
    }


def extract_square(data: dict, loc_lookup: dict) -> dict:
    """Extract Square order fields."""
    fulfillments = data.get("fulfillments", [])
    return {
        "location_id": loc_lookup[("square", data["location_id"])],
        "source_name": "square",
        "source_order_id": data["id"],
        "created_at": data["created_at"],
        "closed_at": data["closed_at"],
        "status": map_status("square", data["state"]),
        "fulfillment_method": map_fulfillment("square", fulfillments[0].get("type", "") if fulfillments else ""),
        "subtotal": sum(i.get("gross_sales_money", {}).get("amount", 0) for i in data.get("line_items", [])),
        "tax_amount": data.get("total_tax_money", {}).get("amount", 0),
        "tip_amount": data.get("total_tip_money", {}).get("amount", 0),
        "total_amount": data.get("total_money", {}).get("amount", 0),
    }


def extract_toast(data: dict, loc_lookup: dict) -> dict:
    """Extract Toast order fields."""
    checks = data.get("checks", [])
    return {
        "location_id": loc_lookup[("toast", data["restaurantGuid"])],
        "source_name": "toast",
        "source_order_id": data["guid"],
        "created_at": data["openedDate"],
        "closed_at": data.get("closedDate") or data.get("paidDate"),
        "status": map_status("toast", {"voided": data.get("voided", False), "deleted": data.get("deleted", False)}),
        "fulfillment_method": map_fulfillment("toast", data.get("diningOption", {}).get("behavior", "")),
        "subtotal": sum(c.get("amount", 0) for c in checks),
        "tax_amount": sum(c.get("taxAmount", 0) for c in checks),
        "tip_amount": sum(c.get("tipAmount", 0) for c in checks),
        "total_amount": sum(c.get("totalAmount", 0) for c in checks),
    }


EXTRACTORS = {"doordash": extract_doordash, "square": extract_square, "toast": extract_toast}


def transform_orders() -> dict:
    """Transform all orders from raw_data to orders table."""
    client = db.client
    counts = {"doordash": 0, "square": 0, "toast": 0, "errors": 0}
    
    # Build location lookup once - O(1) per order instead of O(n) DB queries
    loc_lookup = build_location_lookup(client)
    
    response = client.table("raw_data").select("source_name, data").eq("entity_type", "order").execute()
    
    records = []
    for row in response.data:
        source, data = row["source_name"], row["data"]
        try:
            records.append(EXTRACTORS[source](data, loc_lookup))
            counts[source] += 1
        except Exception as e:
            order_id = data.get("external_delivery_id") or data.get("id") or data.get("guid", "?")
            print(f"[ERROR] {source} order {order_id}: {e}")
            counts["errors"] += 1
    
    batch_upsert(client, "orders", records)
    return counts


if __name__ == "__main__":
    print("Transforming orders...")
    counts = transform_orders()
    total = sum(v for k, v in counts.items() if k != "errors")
    print(f"Done: {total} orders ({counts})")
