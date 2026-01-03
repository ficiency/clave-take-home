"""
Pytest fixtures - Loads REAL data from data/sources/*.json
"""

import json
import pytest
from pathlib import Path

# Path to source data (etl/data/sources)
SOURCES_DIR = Path(__file__).parent.parent / "data" / "sources"


def _load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# Lazy-loaded data cache (load once per test session)
_data_cache = {}

def _get_data(key: str):
    if key not in _data_cache:
        loaders = {
            "doordash": lambda: _load_json(SOURCES_DIR / "doordash_orders.json"),
            "square_locations": lambda: _load_json(SOURCES_DIR / "square" / "locations.json"),
            "square_orders": lambda: _load_json(SOURCES_DIR / "square" / "orders.json"),
            "square_payments": lambda: _load_json(SOURCES_DIR / "square" / "payments.json"),
            "toast": lambda: _load_json(SOURCES_DIR / "toast_pos_export.json"),
        }
        _data_cache[key] = loaders[key]()
    return _data_cache[key]


# Location fixtures (first location from each source)
@pytest.fixture
def doordash_location():
    return _get_data("doordash")["stores"][0]

@pytest.fixture
def square_location():
    return _get_data("square_locations")["locations"][0]

@pytest.fixture
def toast_location():
    return _get_data("toast")["locations"][0]


# Order fixtures (first order from each source)
@pytest.fixture
def doordash_order():
    return _get_data("doordash")["orders"][0]

@pytest.fixture
def square_order():
    return _get_data("square_orders")["orders"][0]

@pytest.fixture
def toast_order():
    return _get_data("toast")["orders"][0]


# Payment fixtures
@pytest.fixture
def square_payment():
    return _get_data("square_payments")["payments"][0]


# Mock lookups (simulate what would come from DB)
# These map source IDs to UUIDs as the real transformers would use
@pytest.fixture
def mock_location_lookup():
    """Maps (source_name, source_location_id) -> location_id (simulated UUID)."""
    dd = _get_data("doordash")
    sq = _get_data("square_locations")
    toast = _get_data("toast")
    
    lookup = {}
    for store in dd.get("stores", []):
        lookup[("doordash", store["store_id"])] = f"uuid-dd-{store['store_id']}"
    for loc in sq.get("locations", []):
        lookup[("square", loc["id"])] = f"uuid-sq-{loc['id']}"
    for loc in toast.get("locations", []):
        lookup[("toast", loc["guid"])] = f"uuid-toast-{loc['guid']}"
    
    return lookup


@pytest.fixture
def mock_order_lookup():
    """Maps (source_name, source_order_id) -> order_id (simulated UUID)."""
    dd = _get_data("doordash")
    sq = _get_data("square_orders")
    toast = _get_data("toast")
    
    lookup = {}
    for order in dd.get("orders", []):
        lookup[("doordash", order["external_delivery_id"])] = f"uuid-dd-{order['external_delivery_id']}"
    for order in sq.get("orders", []):
        lookup[("square", order["id"])] = f"uuid-sq-{order['id']}"
    for order in toast.get("orders", []):
        lookup[("toast", order["guid"])] = f"uuid-toast-{order['guid']}"
    
    return lookup


@pytest.fixture
def mock_item_catalog():
    """Loads the real item catalog."""
    catalog_path = SOURCES_DIR.parent.parent / "catalog" / "item_catalog.json"
    return _load_json(catalog_path)


@pytest.fixture
def mock_square_prices():
    """Builds price lookup from real Square catalog."""
    catalog = _load_json(SOURCES_DIR / "square" / "catalog.json")
    return {
        var["id"]: var.get("item_variation_data", {}).get("price_money", {}).get("amount", 0)
        for obj in catalog.get("objects", []) if obj["type"] == "ITEM"
        for var in obj.get("item_data", {}).get("variations", [])
    }


@pytest.fixture
def mock_payment_lookup():
    """Maps order_id -> payment data for Square."""
    payments = _get_data("square_payments")
    return {p["order_id"]: p for p in payments.get("payments", [])}
