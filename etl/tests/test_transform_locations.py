"""Tests for transform_locations - Uses REAL data from data/sources/*.json"""

import pytest
from etl.transformers.transform_locations import EXTRACTORS
from etl.transformers.utils import ACCOUNT_ID


class TestLocationExtractors:
    """Test location field extraction with REAL data."""
    
    def test_doordash_extracts_all_fields(self, doordash_location):
        loc_id, addr1, city, state, postal, country = EXTRACTORS["doordash"](doordash_location)
        
        # Verify fields are strings
        assert isinstance(loc_id, str) and len(loc_id) > 0
        assert isinstance(addr1, str) and len(addr1) > 0
        assert isinstance(city, str) and len(city) > 0
        assert isinstance(state, str) and len(state) > 0
        assert isinstance(postal, str) and len(postal) > 0
        assert isinstance(country, str) and len(country) > 0
    
    def test_square_extracts_all_fields(self, square_location):
        loc_id, addr1, city, state, postal, country = EXTRACTORS["square"](square_location)
        
        assert isinstance(loc_id, str) and len(loc_id) > 0
        assert isinstance(addr1, str) and len(addr1) > 0
        assert isinstance(city, str) and len(city) > 0
        assert isinstance(state, str) and len(state) > 0
        assert isinstance(postal, str) and len(postal) > 0
        assert isinstance(country, str) and len(country) > 0
    
    def test_toast_extracts_all_fields(self, toast_location):
        loc_id, addr1, city, state, postal, country = EXTRACTORS["toast"](toast_location)
        
        assert isinstance(loc_id, str) and len(loc_id) > 0
        assert isinstance(addr1, str) and len(addr1) > 0
        assert isinstance(city, str) and len(city) > 0
        assert isinstance(state, str) and len(state) > 0
        assert isinstance(postal, str) and len(postal) > 0
        assert isinstance(country, str) and len(country) > 0
    
    def test_all_sources_same_location_match(self, doordash_location, square_location, toast_location):
        """All sources have Downtown location - address should match."""
        dd = EXTRACTORS["doordash"](doordash_location)
        sq = EXTRACTORS["square"](square_location)
        toast = EXTRACTORS["toast"](toast_location)
        
        # All Downtown locations should have same address
        # (city, state, country at minimum)
        assert dd[2] == sq[2] == toast[2]  # city
        assert dd[3] == sq[3] == toast[3]  # state
        assert dd[5] == sq[5] == toast[5]  # country


class TestAccountId:
    """Test account ID configuration."""
    
    def test_account_id_is_valid_uuid_format(self):
        import re
        uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
        assert uuid_pattern.match(ACCOUNT_ID), "ACCOUNT_ID should be valid UUID format"
