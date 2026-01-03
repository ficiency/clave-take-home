"""
Extracts Square data and loads into raw_data table.
Uses batch upsert for O(n) processing with single DB round-trip per file.
"""

import json
from pathlib import Path
from etl.db.connection import db


def _load_and_batch_upsert(client, file_path: Path, data_key: str, entity_type: str) -> int:
    """Loads JSON and batch upserts entities. Single round-trip vs n round-trips."""
    if not file_path.exists():
        return 0
    
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)
    
    records = [
        {
            "source_name": "square",
            "entity_type": entity_type,
            "source_entity_id": entity["id"],
            "data": entity
        }
        for entity in data.get(data_key, []) if entity.get("id")
    ]
    
    if not records:
        return 0
    
    try:
        client.table("raw_data").upsert(records).execute()
        return len(records)
    except Exception as e:
        print(f"[WARNING] Batch upsert failed for {entity_type}: {e}")
        return 0


def extract_square(sources_dir: Path) -> dict[str, int]:
    """Extracts Square locations, orders, and payments from JSON files into raw_data table."""
    client = db.client
    return {
        "locations": _load_and_batch_upsert(client, sources_dir / "locations.json", "locations", "location"),
        "orders": _load_and_batch_upsert(client, sources_dir / "orders.json", "orders", "order"),
        "payments": _load_and_batch_upsert(client, sources_dir / "payments.json", "payments", "payment"),
    }


if __name__ == "__main__":
    path = Path(__file__).parent.parent.parent / "etl" / "data" / "sources" / "square"
    print("Extracting Square data...\n" + "-" * 50)
    counts = extract_square(path)
    print(f"[OK] Locations: {counts['locations']} | Orders: {counts['orders']} | Payments: {counts['payments']}\n" + "-" * 50)
