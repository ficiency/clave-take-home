"""Tests for transform_order_items - Uses REAL data from data/sources/*.json"""

import pytest
from etl.transformers.transform_order_items import extract_doordash_items, extract_square_items, extract_toast_items
from etl.transformers.utils import get_item_info


class TestItemInfoLookup:
    """Test item catalog lookups with REAL catalog."""
    
    def test_returns_tuple_for_known_item(self, mock_item_catalog):
        # Get a real item ID from doordash catalog (skip _comment)
        if "doordash" in mock_item_catalog:
            item_id = next((k for k in mock_item_catalog["doordash"].keys() if not k.startswith("_")), None)
            if item_id:
                name, category = get_item_info(mock_item_catalog, "doordash", item_id)
                assert isinstance(name, str) and len(name) > 0
                assert isinstance(category, str)
    
    def test_returns_empty_for_missing_item(self, mock_item_catalog):
        name, category = get_item_info(mock_item_catalog, "doordash", "nonexistent_item_xyz")
        assert name == ""
        assert category == "Unknown"
    
    def test_returns_empty_for_missing_source(self, mock_item_catalog):
        name, category = get_item_info(mock_item_catalog, "invalid_source", "any_id")
        assert name == ""
        assert category == "Unknown"


class TestDoorDashItemExtraction:
    """Test DoorDash order item extraction with REAL data."""
    
    def test_extracts_items_from_order(self, doordash_order, mock_item_catalog):
        items = extract_doordash_items(doordash_order, "test-order-uuid", mock_item_catalog)
        
        # Should have same number of items as in order
        expected_count = len(doordash_order.get("order_items", []))
        assert len(items) == expected_count
    
    def test_items_have_required_fields(self, doordash_order, mock_item_catalog):
        items = extract_doordash_items(doordash_order, "test-order-uuid", mock_item_catalog)
        
        if items:
            required = ["order_id", "source_name", "source_order_item_id", 
                       "item_name", "quantity", "unit_price", "total_price", "category"]
            for field in required:
                assert field in items[0], f"Missing field: {field}"
    
    def test_source_name_is_doordash(self, doordash_order, mock_item_catalog):
        items = extract_doordash_items(doordash_order, "test-order-uuid", mock_item_catalog)
        for item in items:
            assert item["source_name"] == "doordash"
    
    def test_total_price_equals_qty_times_unit(self, doordash_order, mock_item_catalog):
        items = extract_doordash_items(doordash_order, "test-order-uuid", mock_item_catalog)
        for item in items:
            assert item["total_price"] == item["quantity"] * item["unit_price"]


class TestSquareItemExtraction:
    """Test Square order item extraction with REAL data."""
    
    def test_extracts_items_from_order(self, square_order, mock_item_catalog, mock_square_prices):
        items = extract_square_items(square_order, "test-order-uuid", mock_item_catalog, mock_square_prices)
        
        expected_count = len(square_order.get("line_items", []))
        assert len(items) == expected_count
    
    def test_quantity_is_integer(self, square_order, mock_item_catalog, mock_square_prices):
        items = extract_square_items(square_order, "test-order-uuid", mock_item_catalog, mock_square_prices)
        for item in items:
            assert isinstance(item["quantity"], int)
    
    def test_source_name_is_square(self, square_order, mock_item_catalog, mock_square_prices):
        items = extract_square_items(square_order, "test-order-uuid", mock_item_catalog, mock_square_prices)
        for item in items:
            assert item["source_name"] == "square"


class TestToastItemExtraction:
    """Test Toast order item extraction with REAL data."""
    
    def test_extracts_items_from_nested_checks(self, toast_order, mock_item_catalog):
        items = extract_toast_items(toast_order, "test-order-uuid", mock_item_catalog)
        
        # Count expected items across all checks
        expected_count = sum(
            len([s for s in check.get("selections", []) 
                 if s.get("item") and s["item"].get("guid")])
            for check in toast_order.get("checks", [])
        )
        assert len(items) == expected_count
    
    def test_source_name_is_toast(self, toast_order, mock_item_catalog):
        items = extract_toast_items(toast_order, "test-order-uuid", mock_item_catalog)
        for item in items:
            assert item["source_name"] == "toast"
    
    def test_items_have_required_fields(self, toast_order, mock_item_catalog):
        items = extract_toast_items(toast_order, "test-order-uuid", mock_item_catalog)
        
        if items:
            required = ["order_id", "source_name", "source_order_item_id",
                       "item_name", "quantity", "unit_price", "total_price", "category"]
            for field in required:
                assert field in items[0], f"Missing field: {field}"
