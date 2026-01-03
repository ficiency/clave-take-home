"""Tests for transform_orders - Uses REAL data from data/sources/*.json"""

import pytest
from etl.transformers.transform_orders import extract_doordash, extract_square, extract_toast
from etl.transformers.utils import map_status, map_fulfillment


class TestStatusMapping:
    """Test status normalization across sources."""
    
    def test_doordash_delivered_maps_to_completed(self):
        assert map_status("doordash", "DELIVERED") == "completed"
    
    def test_doordash_cancelled_maps_to_cancelled(self):
        assert map_status("doordash", "CANCELLED") == "cancelled"
    
    def test_square_completed_maps_to_completed(self):
        assert map_status("square", "COMPLETED") == "completed"
    
    def test_square_canceled_maps_to_cancelled(self):
        assert map_status("square", "CANCELED") == "cancelled"
    
    def test_toast_voided_flag_maps_to_voided(self):
        assert map_status("toast", {"voided": True, "deleted": False}) == "voided"
    
    def test_toast_deleted_flag_maps_to_deleted(self):
        assert map_status("toast", {"voided": False, "deleted": True}) == "deleted"
    
    def test_toast_normal_maps_to_completed(self):
        assert map_status("toast", {"voided": False, "deleted": False}) == "completed"


class TestFulfillmentMapping:
    """Test fulfillment method normalization."""
    
    def test_doordash_merchant_delivery_maps_to_delivery(self):
        assert map_fulfillment("doordash", "MERCHANT_DELIVERY") == "DELIVERY"
    
    def test_doordash_pickup_stays_pickup(self):
        assert map_fulfillment("doordash", "PICKUP") == "PICKUP"
    
    def test_square_shipment_maps_to_delivery(self):
        assert map_fulfillment("square", "SHIPMENT") == "DELIVERY"
    
    def test_toast_to_go_maps_to_pickup(self):
        assert map_fulfillment("toast", "TO_GO") == "PICKUP"
    
    def test_toast_take_out_maps_to_pickup(self):
        assert map_fulfillment("toast", "TAKE_OUT") == "PICKUP"


class TestDoorDashOrderExtraction:
    """Test DoorDash order extraction with REAL data."""
    
    def test_extracts_required_fields(self, doordash_order, mock_location_lookup):
        result = extract_doordash(doordash_order, mock_location_lookup)
        
        # Verify all required fields are present
        required = ["location_id", "source_name", "source_order_id", "created_at", 
                    "closed_at", "status", "fulfillment_method", "subtotal", 
                    "tax_amount", "tip_amount", "total_amount"]
        for field in required:
            assert field in result, f"Missing field: {field}"
    
    def test_source_name_is_doordash(self, doordash_order, mock_location_lookup):
        result = extract_doordash(doordash_order, mock_location_lookup)
        assert result["source_name"] == "doordash"
    
    def test_financial_fields_are_numeric(self, doordash_order, mock_location_lookup):
        result = extract_doordash(doordash_order, mock_location_lookup)
        assert isinstance(result["subtotal"], (int, float))
        assert isinstance(result["tax_amount"], (int, float))
        assert isinstance(result["total_amount"], (int, float))
    
    def test_status_is_normalized(self, doordash_order, mock_location_lookup):
        result = extract_doordash(doordash_order, mock_location_lookup)
        # Status should be lowercase normalized
        assert result["status"] in ["completed", "cancelled", "pending"]


class TestSquareOrderExtraction:
    """Test Square order extraction with REAL data."""
    
    def test_extracts_required_fields(self, square_order, mock_location_lookup):
        result = extract_square(square_order, mock_location_lookup)
        
        required = ["location_id", "source_name", "source_order_id", "created_at",
                    "closed_at", "status", "fulfillment_method", "subtotal",
                    "tax_amount", "tip_amount", "total_amount"]
        for field in required:
            assert field in result, f"Missing field: {field}"
    
    def test_source_name_is_square(self, square_order, mock_location_lookup):
        result = extract_square(square_order, mock_location_lookup)
        assert result["source_name"] == "square"
    
    def test_subtotal_sums_line_items(self, square_order, mock_location_lookup):
        result = extract_square(square_order, mock_location_lookup)
        # Calculate expected subtotal from line items
        expected = sum(
            item.get("gross_sales_money", {}).get("amount", 0) 
            for item in square_order.get("line_items", [])
        )
        assert result["subtotal"] == expected


class TestToastOrderExtraction:
    """Test Toast order extraction with REAL data."""
    
    def test_extracts_required_fields(self, toast_order, mock_location_lookup):
        result = extract_toast(toast_order, mock_location_lookup)
        
        required = ["location_id", "source_name", "source_order_id", "created_at",
                    "closed_at", "status", "fulfillment_method", "subtotal",
                    "tax_amount", "tip_amount", "total_amount"]
        for field in required:
            assert field in result, f"Missing field: {field}"
    
    def test_source_name_is_toast(self, toast_order, mock_location_lookup):
        result = extract_toast(toast_order, mock_location_lookup)
        assert result["source_name"] == "toast"
    
    def test_sums_amounts_across_checks(self, toast_order, mock_location_lookup):
        result = extract_toast(toast_order, mock_location_lookup)
        # Calculate expected from checks
        checks = toast_order.get("checks", [])
        expected_subtotal = sum(c.get("amount", 0) for c in checks)
        expected_tax = sum(c.get("taxAmount", 0) for c in checks)
        expected_tip = sum(c.get("tipAmount", 0) for c in checks)
        
        assert result["subtotal"] == expected_subtotal
        assert result["tax_amount"] == expected_tax
        assert result["tip_amount"] == expected_tip
