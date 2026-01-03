"""
Extracts Toast data and loads into raw_data table.
Uses batch upsert for O(n) processing with single DB round-trip.
"""

import json
from pathlib import Path
from etl.db.connection import db


def _batch_upsert(client, entities: list, entity_type: str) -> int:
    """Batch upserts entities into raw_data using 'guid' as ID. Single round-trip."""
    records = [
        {
            "source_name": "toast",
            "entity_type": entity_type,
            "source_entity_id": entity["guid"],
            "data": entity
        }
        for entity in entities if entity.get("guid")
    ]
    
    if not records:
        return 0
    
    try:
        client.table("raw_data").upsert(records).execute()
        return len(records)
    except Exception as e:
        print(f"[WARNING] Batch upsert failed for {entity_type}: {e}")
        return 0


def extract_toast(file_path: Path) -> dict[str, int]:
    """Extracts Toast locations and orders from JSON into raw_data table."""
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)
    
    client = db.client
    return {
        "locations": _batch_upsert(client, data.get("locations", []), "location"),
        "orders": _batch_upsert(client, data.get("orders", []), "order"),
    }


if __name__ == "__main__":
    path = Path(__file__).parent.parent.parent / "etl" / "data" / "sources" / "toast_pos_export.json"
    print("Extracting Toast data...\n" + "-" * 50)
    counts = extract_toast(path)
    print(f"[OK] Locations: {counts['locations']} | Orders: {counts['orders']}\n" + "-" * 50)
