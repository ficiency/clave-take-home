"""
Extracts DoorDash data and loads into raw_data table.
Uses batch upsert for O(n) processing with single DB round-trip.
"""

import json
from pathlib import Path
from etl.db.connection import db


def _batch_upsert(client, entities: list, id_key: str, entity_type: str) -> int:
    """Batch upserts entities into raw_data. Single round-trip vs n round-trips."""
    records = [
        {
            "source_name": "doordash",
            "entity_type": entity_type,
            "source_entity_id": entity[id_key],
            "data": entity
        }
        for entity in entities if entity.get(id_key)
    ]
    
    if not records:
        return 0
    
    try:
        client.table("raw_data").upsert(records).execute()
        return len(records)
    except Exception as e:
        print(f"[WARNING] Batch upsert failed for {entity_type}: {e}")
        return 0


def extract_doordash(file_path: Path) -> dict[str, int]:
    """Extracts DoorDash stores and orders from JSON into raw_data table."""
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)
    
    client = db.client
    return {
        "locations": _batch_upsert(client, data.get("stores", []), "store_id", "location"),
        "orders": _batch_upsert(client, data.get("orders", []), "external_delivery_id", "order"),
    }


if __name__ == "__main__":
    path = Path(__file__).parent.parent.parent / "etl" / "data" / "sources" / "doordash_orders.json"
    print("Extracting DoorDash data...\n" + "-" * 50)
    counts = extract_doordash(path)
    print(f"[OK] Locations: {counts['locations']} | Orders: {counts['orders']}\n" + "-" * 50)
