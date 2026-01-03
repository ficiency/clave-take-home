"""
Transform location data from raw_data to locations table.
Uses batch upsert for O(n) processing with single DB round-trip.
"""

from etl.db.connection import db
from .utils import ACCOUNT_ID, batch_upsert

# Extractors: source -> (id_field, address_field_map)
EXTRACTORS = {
    "doordash": lambda d: (d["store_id"], d["address"]["street"], d["address"]["city"], d["address"]["state"], d["address"]["zip_code"], d["address"]["country"]),
    "square": lambda d: (d["id"], d["address"]["address_line_1"], d["address"]["locality"], d["address"]["administrative_district_level_1"], d["address"]["postal_code"], d["address"]["country"]),
    "toast": lambda d: (d["guid"], d["address"]["line1"], d["address"]["city"], d["address"]["state"], d["address"]["zip"], d["address"]["country"]),
}


def transform_locations() -> dict:
    """Transform all locations from raw_data to locations table."""
    client = db.client
    counts = {"doordash": 0, "square": 0, "toast": 0, "errors": 0}
    
    response = client.table("raw_data").select("source_name, data").eq("entity_type", "location").execute()
    
    records = []
    for row in response.data:
        source, data = row["source_name"], row["data"]
        try:
            loc_id, addr1, city, state, postal, country = EXTRACTORS[source](data)
            records.append({
                "account_id": ACCOUNT_ID,
                "source_name": source,
                "source_location_id": loc_id,
                "name": data["name"],
                "address_line_1": addr1,
                "city": city,
                "state": state,
                "postal_code": postal,
                "country": country,
                "timezone": data.get("timezone", ""),
            })
            counts[source] += 1
        except Exception as e:
            print(f"[ERROR] {source} location: {e}")
            counts["errors"] += 1
    
    batch_upsert(client, "locations", records)
    return counts


if __name__ == "__main__":
    print("Transforming locations...")
    counts = transform_locations()
    total = sum(v for k, v in counts.items() if k != "errors")
    print(f"Done: {total} locations ({counts})")
