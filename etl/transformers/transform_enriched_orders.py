"""
Transform enriched order data to orders.metadata JSONB field.
Uses hash maps for O(1) lookups.
"""

from etl.db.connection import db
from .utils import build_order_lookup, build_payment_lookup, map_payment_type, normalize_card_brand, batch_update_metadata


def extract_doordash_metadata(data: dict) -> dict:
    """Extract DoorDash metadata fields (fees, times, flags)."""
    meta = {}
    for key in ("delivery_fee", "service_fee", "commission", "merchant_payout"):
        if data.get(key) is not None:
            meta[key] = data[key]
    for key in ("pickup_time", "delivery_time"):
        if data.get(key):
            meta[key] = data[key]
    for key in ("contains_alcohol", "is_catering"):
        if data.get(key) is not None:
            meta[key] = data[key]
    return meta


def extract_square_metadata(data: dict, payment: dict) -> dict:
    """Extract Square metadata fields (payment info)."""
    if not payment:
        return {}
    
    meta = {}
    source_type = payment.get("source_type")
    if source_type:
        meta["payment_type"] = map_payment_type("square", source_type)
    
    if source_type == "CARD" and payment.get("card_details"):
        card = payment["card_details"]
        if card.get("card", {}).get("card_brand"):
            meta["card_brand"] = normalize_card_brand(card["card"]["card_brand"])
        if card.get("entry_method"):
            meta["entry_method"] = card["entry_method"]
    
    return meta


def extract_toast_metadata(data: dict) -> dict:
    """Extract Toast metadata fields (dates, payment info)."""
    meta = {}
    
    if data.get("paidDate"):
        meta["paid_date"] = data["paidDate"]
    if data.get("businessDate"):
        meta["business_date"] = data["businessDate"]
    
    # Payment from first check's first payment
    checks = data.get("checks", [])
    if checks:
        payments = checks[0].get("payments", [])
        if payments:
            p = payments[0]
            if p.get("type"):
                meta["payment_type"] = map_payment_type("toast", p["type"])
            if p.get("cardType"):
                meta["card_brand"] = normalize_card_brand(p["cardType"])
    
    return meta


def transform_enriched_orders() -> dict:
    """Transform enriched data to orders.metadata JSONB field."""
    client = db.client
    counts = {"doordash": 0, "square": 0, "toast": 0, "errors": 0}
    
    # Build lookups once - O(1) per order
    order_lookup = build_order_lookup(client)
    payment_lookup = build_payment_lookup(client)
    
    response = client.table("raw_data").select("source_name, data").eq("entity_type", "order").execute()
    
    updates = []
    for row in response.data:
        source, data = row["source_name"], row["data"]
        try:
            source_order_id = data.get("external_delivery_id") or data.get("id") or data.get("guid")
            order_id = order_lookup[(source, source_order_id)]
            
            if source == "doordash":
                meta = extract_doordash_metadata(data)
            elif source == "square":
                meta = extract_square_metadata(data, payment_lookup.get(source_order_id))
            elif source == "toast":
                meta = extract_toast_metadata(data)
            else:
                continue
            
            if meta:
                updates.append((order_id, meta))
            counts[source] += 1
        except Exception as e:
            print(f"[ERROR] {source} metadata: {e}")
            counts["errors"] += 1
    
    batch_update_metadata(client, updates)
    return counts


if __name__ == "__main__":
    print("Transforming enriched metadata...")
    counts = transform_enriched_orders()
    total = sum(v for k, v in counts.items() if k != "errors")
    print(f"Done: {total} orders ({counts})")
