"""
Raw (Staging) schema definitions for storing original JSON data.

This layer stores original JSON as-is from all sources using JSONB,
preserving auditability and allowing schema evolution.

Tables are created manually via Supabase dashboard SQL editor.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any
from datetime import datetime
from uuid import UUID, uuid4


# ============================================================================
# RAW DATA
# ============================================================================

class RawData(BaseModel):
    """Raw data schema - stores original JSON as-is from all sources."""
    
    raw_id: UUID = Field(default_factory=uuid4, description="Primary key")
    source_name: str = Field(..., description="Source: doordash, square, or toast")
    entity_type: str = Field(..., description="Entity type: location, order, payment, catalog_item, etc.")
    source_entity_id: str = Field(..., description="Original entity ID from source")
    data: Dict[str, Any] = Field(..., description="Complete original JSON data")
    created_at: datetime = Field(default_factory=datetime.utcnow)

