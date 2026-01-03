"""Tests for transform_enriched_orders - Uses REAL data from data/sources/*.json"""

import pytest
from etl.transformers.transform_enriched_orders import extract_doordash_metadata, extract_square_metadata, extract_toast_metadata
from etl.transformers.utils import map_payment_type, normalize_card_brand


class TestPaymentTypeMapping:
    """Test payment type normalization."""
    
    def test_toast_credit_maps_to_card(self):
        assert map_payment_type("toast", "CREDIT") == "CARD"
    
    def test_unknown_type_returns_as_is(self):
        assert map_payment_type("square", "CARD") == "CARD"
        assert map_payment_type("square", "CASH") == "CASH"


class TestCardBrandNormalization:
    """Test card brand normalization."""
    
    def test_normalizes_to_uppercase(self):
        assert normalize_card_brand("visa") == "VISA"
        assert normalize_card_brand("Mastercard") == "MASTERCARD"
    
    def test_handles_none_or_empty(self):
        assert normalize_card_brand("") is None
        assert normalize_card_brand(None) is None


class TestDoorDashMetadataExtraction:
    """Test DoorDash metadata extraction with REAL data."""
    
    def test_extracts_metadata(self, doordash_order):
        meta = extract_doordash_metadata(doordash_order)
        assert isinstance(meta, dict)
    
    def test_extracts_fee_fields_if_present(self, doordash_order):
        meta = extract_doordash_metadata(doordash_order)
        
        # Check fees are extracted if present in source
        if doordash_order.get("delivery_fee") is not None:
            assert "delivery_fee" in meta
        if doordash_order.get("service_fee") is not None:
            assert "service_fee" in meta
    
    def test_extracts_time_fields_if_present(self, doordash_order):
        meta = extract_doordash_metadata(doordash_order)
        
        if doordash_order.get("pickup_time"):
            assert "pickup_time" in meta
        if doordash_order.get("delivery_time"):
            assert "delivery_time" in meta


class TestSquareMetadataExtraction:
    """Test Square metadata extraction with REAL data."""
    
    def test_extracts_payment_info(self, square_order, square_payment):
        meta = extract_square_metadata(square_order, square_payment)
        
        # Should have payment_type if payment has source_type
        if square_payment.get("source_type"):
            assert "payment_type" in meta
    
    def test_extracts_card_brand_if_card_payment(self, square_order, square_payment):
        meta = extract_square_metadata(square_order, square_payment)
        
        if square_payment.get("source_type") == "CARD":
            card_details = square_payment.get("card_details", {})
            if card_details.get("card", {}).get("card_brand"):
                assert "card_brand" in meta
    
    def test_returns_empty_without_payment(self, square_order):
        meta = extract_square_metadata(square_order, None)
        assert meta == {}


class TestToastMetadataExtraction:
    """Test Toast metadata extraction with REAL data."""
    
    def test_extracts_dates_if_present(self, toast_order):
        meta = extract_toast_metadata(toast_order)
        
        if toast_order.get("paidDate"):
            assert "paid_date" in meta
        if toast_order.get("businessDate"):
            assert "business_date" in meta
    
    def test_extracts_payment_from_checks(self, toast_order):
        meta = extract_toast_metadata(toast_order)
        
        checks = toast_order.get("checks", [])
        if checks and checks[0].get("payments"):
            payment = checks[0]["payments"][0]
            if payment.get("type"):
                assert "payment_type" in meta
    
    def test_handles_order_without_checks(self):
        order_no_checks = {"paidDate": "2025-01-01T12:00:00Z"}
        meta = extract_toast_metadata(order_no_checks)
        assert meta == {"paid_date": "2025-01-01T12:00:00Z"}
