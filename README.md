# Clave Engineering Take-Home Assessment

> **Solution Submission** - This repository contains my implementation of the Clave Engineering Take-Home Assessment.  
> **Live Demo:** [Deployed on Vercel](https://clave-take-home.vercel.app)  
> **Original Challenge:** [clave-take-home](https://github.com/vale-clave/clave-take-home)

A natural language analytics dashboard for restaurant data, consolidating information from multiple POS systems (DoorDash, Square, Toast) and enabling AI-powered insights through conversational queries.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Data Pipeline](#data-pipeline)
- [Web Application](#web-application)
- [Database Schema](#database-schema)
- [Features](#features)
- [Future Improvements](#future-improvements)

## Overview

This project implements a complete data engineering and AI integration solution for restaurant analytics. It processes messy, multi-source JSON data into a clean, normalized database, then provides an intelligent chat interface where users can query their data using natural language.

**Key Capabilities:**
- Multi-source data ingestion (DoorDash, Square, Toast POS)
- Data normalization and cleaning
- Medallion architecture for scalable data processing
- AI-powered natural language query interface
- Dynamic visualization generation (charts, tables, metrics)
- Real-time streaming responses

## Architecture

The solution follows a **Medallion Architecture** (Bronze → Silver → Gold) pattern, optimizing for both data quality and AI query efficiency.

### Bronze Layer (Raw)
Stores original JSON from all sources in the `raw_data` table. Preserves complete audit trail and enables reprocessing without data loss. No transformation—pure preservation.

### Silver Layer (Core)
Normalized, production-ready tables (`locations`, `orders`, `order_items`) containing fields shared across all sources. Source-specific metadata stored in JSONB `metadata` columns to avoid nullable columns and wasted space. Optimized for standard analytics queries.

### Gold Layer (Curated)
AI-optimized VIEWs (`ai_orders`, `ai_order_items`) that flatten JSONB metadata into columns and pre-resolve JOINs. Simplifies AI queries, reduces token usage, and improves response times.

**Benefits:**
- Evolution-ready: frequently accessed metadata fields can be promoted from JSONB to core columns
- Token-efficient: AI queries simplified views instead of complex JSONB extraction
- Maintainable: clear separation between raw, processed, and curated data

## Tech Stack

### Backend / ETL
- **Python 3.12+** - Data processing and transformation
- **Pydantic** - Data validation and schema enforcement
- **Supabase (PostgreSQL)** - Primary database
- **PostgreSQL** - Direct connection for AI agent queries

### Frontend / Web Application
- **Next.js 16** (App Router) - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **shadcn/ui** - UI components
- **Recharts** - Chart visualization library

### AI / ML
- **LangChain** - Agent orchestration
- **OpenAI GPT-4** - Language model
- **LangChain Tools** - SQL execution and chart generation

### Infrastructure
- **Supabase** - Database, authentication, API

## Project Structure

```
clave-take-home/
├── etl/                          # Data pipeline
│   ├── extractors/               # Raw data extraction
│   ├── transformers/             # Data transformation
│   ├── catalog/                  # Item catalog (normalization)
│   ├── schemas/                  # Pydantic models
│   └── data/sources/             # Raw JSON source files
│
├── my-dashboard/                 # Next.js web application
│   ├── app/
│   │   ├── (dashboard)/          # Dashboard routes
│   │   ├── api/                  # API routes (chat, auth, conversations)
│   │   ├── _components/          # React components
│   │   ├── _lib/                 # Utilities (agent, db, auth)
│   │   └── _types/               # TypeScript types
│   └── components/ui/            # shadcn/ui components
│
└── docs/                         # Documentation
    ├── EXAMPLE_QUERIES.md        # Query examples
    └── SCHEMA_HINTS.md           # Schema documentation
```

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 18+
- Supabase account
- OpenAI API key

### Environment Setup

1. **Clone the repository:**
```bash
git clone [repository-url]
cd clave-take-home
```

2. **Set up Python environment:**
```bash
cd etl
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Set up Next.js application:**
```bash
cd my-dashboard
npm install
```

4. **Configure environment variables:**

Create `.env.local` in `my-dashboard/`:
```env
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
OPENAI_API_KEY=your_openai_api_key
DATABASE_URL=postgresql://user:password@host:port/database
```

Create `.env` in `etl/`:
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_service_role_key
```

5. **Set up Supabase database:**
   - Create tables using SQL from `etl/schemas/`
   - Create views using SQL from `etl/schemas/views.py`

### Running the ETL Pipeline

```bash
cd etl

# Extract raw data
python extractors/extract_all.py

# Transform and load
python transformers/run.py
```

### Running the Web Application

**Local Development:**
```bash
cd my-dashboard
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

**Production Deployment:**
The application is deployed on Vercel and available at: [https://clave-take-home.vercel.app](https://clave-take-home.vercel.app)

## Data Pipeline

### Extract
Reads JSON files from `etl/data/sources/` and inserts raw data into the `raw_data` table. Each entity (location, order, payment) gets its own row with source metadata. No transformation—pure preservation.

**Source Files:**
- `doordash_orders.json` - DoorDash orders
- `square/catalog.json`, `square/orders.json`, `square/payments.json`, `square/locations.json` - Square POS data
- `toast_pos_export.json` - Toast POS data

### Transform
Multi-stage transformation pipeline with dependency management:

1. **Locations** - Extract and normalize location data
2. **Orders** - Transform orders with FK lookups to locations
3. **Order Items** - Process items with catalog lookups for normalized names/categories
4. **Metadata Enrichment** - Populate JSONB `metadata` columns with source-specific fields

**Key Transformations:**
- Status normalization ("DELIVERED" → "completed")
- Fulfillment method mapping ("MERCHANT_DELIVERY" → "DELIVERY")
- Money value handling (already in cents)
- Catalog-based item name/category normalization
- Source-specific field extraction to JSONB

**Item Catalog:**
A pre-built catalog (`etl/catalog/item_catalog.json`) maps source-specific item IDs to normalized names and categories. Built during onboarding, updated when menus change. Enables clean data insertion without per-run parsing or regex.

### Load
Validates data using Pydantic schemas before insertion. Reports counts and errors per stage for transparency.

### Reprocessability
The entire pipeline is rerunnable. Truncate downstream tables, re-execute transforms—Bronze layer preserves everything.

## Web Application

### Features

**Natural Language Query Interface**
- Chat-based interface for asking questions in plain English
- Real-time streaming responses
- Conversation history persistence

**AI Agent**
- LangChain-powered agent with tools for SQL execution and chart generation
- Context-aware responses using conversation history
- Automatic query generation based on user intent

**Dynamic Visualizations**
- Automatically generates appropriate chart types (bar, line, pie, table, card)
- Supports multiple data series and complex comparisons
- Responsive, interactive charts using Recharts

**Conversation Management**
- Persistent conversations with message history
- Sidebar navigation for conversation switching
- Automatic conversation creation on first message

### Architecture

**Frontend (Next.js App Router)**
- Server-side rendering for performance
- Client components for interactivity
- API routes for backend logic

**API Routes**
- `/api/chat` - Streaming chat endpoint with SSE
- `/api/auth/login` - Authentication
- `/api/conversations` - Conversation management
- `/api/conversations/[id]/messages` - Message history

**AI Agent Tools**
- `execute_sql` - Validated SQL execution against PostgreSQL
- `create_chart` - Chart configuration generation

### Query Flow

1. User sends natural language query
2. AI agent interprets intent and generates SQL (if needed)
3. SQL executed against Gold layer views (`ai_orders`, `ai_order_items`)
4. Results processed and formatted
5. Chart generated if visualization requested
6. Response streamed back to user via SSE

## Database Schema

### Silver Layer Tables

**`locations`**
- `location_id` (UUID, PK)
- `source_name`, `source_location_id`
- `name`, `address_line_1`, `city`, `state`, `postal_code`, `country`, `timezone`

**`orders`**
- `order_id` (UUID, PK)
- `location_id` (FK → locations)
- `source_name`, `source_order_id`
- `created_at`, `closed_at`, `status`, `fulfillment_method`
- `subtotal`, `tax_amount`, `tip_amount`, `total_amount` (all in cents)
- `metadata` (JSONB) - Source-specific fields

**`order_items`**
- `order_item_id` (UUID, PK)
- `order_id` (FK → orders)
- `source_name`, `source_order_item_id`
- `item_name`, `category` (normalized via catalog)
- `quantity`, `unit_price`, `total_price` (in cents)

### Gold Layer Views

**`ai_orders`**
Flattened view of orders with:
- All core order fields
- Pre-joined location information
- Extracted metadata fields as columns (payment_type, delivery_fee, etc.)

**`ai_order_items`**
Flattened view of order items with:
- All core item fields
- Pre-joined order and location context
- Ready for analytics queries

### Raw Layer

**`raw_data`**
- `raw_id` (UUID, PK)
- `source_name`, `entity_type`, `source_entity_id`
- `data` (JSONB) - Complete original JSON

## Features

✅ Multi-source data ingestion (DoorDash, Square, Toast)
✅ Data normalization and cleaning pipeline
✅ Medallion architecture for scalable processing
✅ Item catalog for consistent product naming
✅ Natural language query interface
✅ AI-powered SQL generation and execution
✅ Dynamic chart generation (bar, line, pie, table, card)
✅ Real-time streaming responses
✅ Conversation history persistence
✅ Secure authentication
✅ Production-ready error handling
✅ **Deployed on Vercel** - Live demo available

## Deployment

The application is deployed on **Vercel** and accessible at:
- **Production URL:** [https://clave-take-home.vercel.app](https://clave-take-home.vercel.app)

The deployment includes:
- Next.js application (frontend + API routes)
- Environment variables configured for production
- Automatic deployments on push to main branch

## Future Improvements

- **Schema Evolution:** Promote frequently accessed metadata fields from JSONB to core columns based on usage patterns
- **Query Optimization:** Add indexes based on actual query patterns
- **Error Recovery:** Implement retry logic and partial failure handling
- **Monitoring:** Add observability for ETL pipeline and AI agent performance
- **Caching:** Cache common query results to reduce database load
- **Export:** Add data export functionality (CSV, PDF reports)
- **Advanced Visualizations:** Support for more chart types (heatmaps, scatter plots)
- **Multi-tenant:** Support for multiple restaurant accounts with data isolation
