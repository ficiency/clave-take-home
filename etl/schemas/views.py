"""
AI Views (Gold Layer) - Flattened views optimized for AI queries.

These PostgreSQL VIEWs flatten JSONB metadata and pre-resolve JOINs,
making data easily queryable by AI without complex syntax.

VIEWs are created via Supabase dashboard SQL editor.
"""

# SQL to create AI views in Supabase:

AI_ORDERS_VIEW = """
CREATE OR REPLACE VIEW ai_orders AS
SELECT
    -- Core fields
    o.order_id,
    o.source_name,
    o.source_order_id,
    o.created_at,
    o.closed_at,
    o.status,
    o.fulfillment_method,
    o.subtotal,
    o.tax_amount,
    o.tip_amount,
    o.total_amount,
    
    -- Location fields (pre-joined)
    l.name AS location_name,
    l.city AS location_city,
    l.state AS location_state,
    
    -- Flattened metadata (source-specific fields)
    o.metadata->>'payment_type' AS payment_type,
    o.metadata->>'card_brand' AS card_brand,
    o.metadata->>'delivery_fee' AS delivery_fee,
    o.metadata->>'service_fee' AS service_fee,
    o.metadata->>'commission' AS commission,
    o.metadata->>'business_date' AS business_date,
    o.metadata->>'server_name' AS server_name,
    o.metadata->>'revenue_center' AS revenue_center
    
FROM orders o
JOIN locations l ON o.location_id = l.location_id;
"""

AI_ORDER_ITEMS_VIEW = """
CREATE OR REPLACE VIEW ai_order_items AS
SELECT
    -- Core fields
    oi.order_item_id,
    oi.order_id,
    oi.source_name,
    oi.item_name,
    oi.quantity,
    oi.unit_price,
    oi.total_price,
    oi.category,
    
    -- Order context (pre-joined)
    o.created_at AS order_created_at,
    o.status AS order_status,
    o.fulfillment_method,
    
    -- Location context (pre-joined)
    l.name AS location_name,
    l.city AS location_city
    
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
JOIN locations l ON o.location_id = l.location_id;
"""

# Combined SQL for easy copy-paste
ALL_VIEWS_SQL = f"""
-- AI Views (Gold Layer)
-- Run this in Supabase SQL Editor

{AI_ORDERS_VIEW}

{AI_ORDER_ITEMS_VIEW}
"""

