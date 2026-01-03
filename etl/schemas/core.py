"""
Core schema definitions for unified restaurant data.

These schemas represent fields shared across all sources (DoorDash, Square, Toast),
are stable (no NULLs), and optimized for AI queries and analytics.

Tables are created manually via Supabase dashboard SQL editor.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4


# ============================================================================
# ACCOUNTS (FRANCHISE/USER)
# ============================================================================

class Account(BaseModel):
    """Account schema - franchise/restaurant owner account."""
    
    account_id: UUID = Field(default_factory=uuid4, description="Primary key")
    email: str = Field(..., description="Account email")
    password_hash: str = Field(..., description="Hashed password")
    franchise_name: str = Field(..., description="Franchise or restaurant name")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# LOCATIONS
# ============================================================================

class Location(BaseModel):
    """Location schema - fields shared across all sources."""
    
    location_id: UUID = Field(default_factory=uuid4, description="Primary key")
    account_id: UUID = Field(..., description="Foreign key to accounts")
    source_name: str = Field(..., description="Source: doordash, square, or toast")
    source_location_id: str = Field(..., description="Original location ID from source")
    name: str = Field(..., description="Location name")
    address_line_1: str = Field(..., description="Street address")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State/province")
    postal_code: str = Field(..., description="ZIP/postal code")
    country: str = Field(..., description="Country code")
    timezone: str = Field(..., description="Timezone identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# ORDERS
# ============================================================================

class Order(BaseModel):
    """Order schema - fields shared across all sources."""
    
    order_id: UUID = Field(default_factory=uuid4, description="Primary key")
    location_id: UUID = Field(..., description="Foreign key to locations")
    source_name: str = Field(..., description="Source: doordash, square, or toast")
    source_order_id: str = Field(..., description="Original order ID from source")
    created_at: datetime = Field(..., description="Order creation time")
    closed_at: datetime = Field(..., description="Order completion time")
    status: str = Field(..., description="Order status (completed, delivered, voided, etc.)")
    fulfillment_method: str = Field(..., description="Delivery method (DELIVERY, PICKUP, DINE_IN, etc.)")
    subtotal: int = Field(..., description="Subtotal in cents")
    tax_amount: int = Field(..., description="Tax amount in cents")
    tip_amount: int = Field(..., description="Tip amount in cents")
    total_amount: int = Field(..., description="Total amount in cents")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Source-specific metadata as JSONB (payment info, fees, dates, etc.)")
    record_created_at: datetime = Field(default_factory=datetime.utcnow)
    record_updated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# ORDER ITEMS
# ============================================================================

class OrderItem(BaseModel):
    """Order item schema - fields shared across all sources."""
    
    order_item_id: UUID = Field(default_factory=uuid4, description="Primary key")
    order_id: UUID = Field(..., description="Foreign key to orders")
    source_name: str = Field(..., description="Source: doordash, square, or toast")
    source_order_item_id: str = Field(..., description="Original item ID from source")
    item_name: str = Field(..., description="Normalized item name from internal catalog")
    quantity: int = Field(..., description="Quantity ordered")
    unit_price: int = Field(..., description="Unit price in cents")
    total_price: int = Field(..., description="Total price in cents")
    category: str = Field(..., description="Item category")
    record_created_at: datetime = Field(default_factory=datetime.utcnow)
    record_updated_at: datetime = Field(default_factory=datetime.utcnow)
