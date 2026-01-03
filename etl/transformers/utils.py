"""
Shared utilities for transformers.
Uses hash maps for O(1) lookups instead of O(n) DB queries per item.
"""

import json
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
CATALOG_PATH = PROJECT_ROOT / "etl" / "catalog" / "item_catalog.json"
SQUARE_CATALOG_PATH = PROJECT_ROOT / "etl" / "data" / "sources" / "square" / "catalog.json"

# Account ID for all locations
ACCOUNT_ID = "33ccddbb-fe9f-489f-83b0-69e2a1e4eff8"


# Value mappings (hash maps for O(1) lookups)
STATUS_MAP = {
    "doordash": {"DELIVERED": "completed", "PICKED_UP": "completed", "CANCELLED": "cancelled"},
    "square": {"COMPLETED": "completed", "CANCELED": "cancelled"},
}

FULFILLMENT_MAP = {
    "doordash": {"MERCHANT_DELIVERY": "DELIVERY"},
    "square": {"SHIPMENT": "DELIVERY"},
    "toast": {"TO_GO": "PICKUP", "TAKE_OUT": "PICKUP"},
}

PAYMENT_TYPE_MAP = {
    "toast": {"CREDIT": "CARD"},
}


def map_status(source: str, value) -> str:
    """Map status to normalized value. O(1) lookup."""
    if source == "toast" and isinstance(value, dict):
        if value.get("voided"): return "voided"
        if value.get("deleted"): return "deleted"
        return "completed"
    return STATUS_MAP.get(source, {}).get(value, value.lower() if value else "completed")


def map_fulfillment(source: str, value: str) -> str:
    """Map fulfillment method to normalized value. O(1) lookup."""
    return FULFILLMENT_MAP.get(source, {}).get(value, value or "")


def map_payment_type(source: str, value: str) -> str:
    """Map payment type to normalized value. O(1) lookup."""
    return PAYMENT_TYPE_MAP.get(source, {}).get(value, value)


def normalize_card_brand(value: str) -> str:
    """Normalize card brand to uppercase."""
    return value.upper() if value else None


# Lookup builders (build once, query O(1))
def build_location_lookup(client) -> dict:
    """Build hash map: (source_name, source_location_id) -> location_id"""
    response = client.table("locations").select("location_id, source_name, source_location_id").execute()
    return {(r["source_name"], r["source_location_id"]): r["location_id"] for r in response.data}


def build_order_lookup(client) -> dict:
    """Build hash map: (source_name, source_order_id) -> order_id"""
    response = client.table("orders").select("order_id, source_name, source_order_id").execute()
    return {(r["source_name"], r["source_order_id"]): r["order_id"] for r in response.data}


def build_payment_lookup(client) -> dict:
    """Build hash map: square_order_id -> payment_data"""
    response = client.table("raw_data").select("data").eq("source_name", "square").eq("entity_type", "payment").execute()
    return {r["data"]["order_id"]: r["data"] for r in response.data if r["data"].get("order_id")}


def load_item_catalog() -> dict:
    """Load item catalog (normalized names/categories)."""
    with open(CATALOG_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_square_prices() -> dict:
    """Build hash map: variation_id -> unit_price from Square catalog."""
    if not SQUARE_CATALOG_PATH.exists():
        return {}
    with open(SQUARE_CATALOG_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return {
        var["id"]: var.get("item_variation_data", {}).get("price_money", {}).get("amount", 0)
        for obj in data.get("objects", []) if obj["type"] == "ITEM"
        for var in obj.get("item_data", {}).get("variations", [])
    }


def get_item_info(catalog: dict, source: str, item_id: str) -> tuple:
    """Get (name, category) from catalog. O(1) lookup."""
    info = catalog.get(source, {}).get(item_id, {})
    return info.get("name", ""), info.get("category", "Unknown")


def batch_upsert(client, table: str, records: list) -> int:
    """Batch upsert records. Single round-trip."""
    if not records:
        return 0
    client.table(table).upsert(records).execute()
    return len(records)


def batch_update_metadata(client, updates: list) -> int:
    """Batch update metadata field. One query per update (Supabase limitation)."""
    count = 0
    for order_id, metadata in updates:
        if metadata:
            client.table("orders").update({"metadata": metadata}).eq("order_id", order_id).execute()
            count += 1
    return count

