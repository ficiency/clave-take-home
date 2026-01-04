# Clave Engineering Take-Home Assessment

> **Solution Submission** - This repository contains my implementation of the Clave Engineering Take-Home Assessment.  
> **Live Demo:** [Deployed on Vercel](https://clave-take-home.vercel.app)  
> **Credentials:** `challenge@tryclave.ai` / `123`

---

## The Problem: Three Sources, One Truth

DoorDash, Square, and Toast each expose their own data models. Hundreds of fields. Some shared, many unique. Different formats, different semantics, different quirks.

The challenge isn't just storing the data—it's designing a system that:
- Preserves fidelity (never lose data)
- Enables efficient analytics (query what matters)
- Simplifies AI interactions (reduce token overhead)
- Adapts over time (schema evolution without breaking)

This document explains the decisions that shaped the architecture.

---

## Core Decision: Medallion Architecture

**Why Medallion?** Because the problem requires three different levels of abstraction.

### Bronze: The Immutable Record

Every JSON file from every source is stored exactly as received. No cleaning, no normalization, no assumptions.

**Decision rationale:** When upstream schemas change (they will) or transformation logic has bugs (it will), Bronze becomes the recovery mechanism. Storage cost is trivial compared to the cost of lost data.

**Trade-off:** We pay storage for insurance. Acceptable.

### Silver: The Normalized Foundation

Three tables. Only fields shared across multiple sources. Everything else goes into JSONB `metadata`.

**Decision rationale:** Adding nullable columns for source-specific fields creates two problems: (1) most rows have NULLs, wasting space and complicating queries, (2) schema changes require migrations for fields that may rarely be queried.

JSONB `metadata` avoids both. The schema stays stable. Source-specific fields remain queryable, just not as convenient.

**Trade-off:** JSONB extraction adds complexity to queries. But most analytics queries use shared fields anyway. The inconvenience is isolated to edge cases.

### Gold: The AI Optimization Layer

Two VIEWs that flatten JSONB and pre-resolve JOINs.

**Decision rationale:** When an AI agent needs to query data, every token counts. Complex JSONB paths like `metadata->>'payment_type'` consume tokens in prompts. Pre-joining tables means the agent writes simpler queries.

But here's the key insight: VIEWs don't store data. If a field becomes frequently queried, we promote it from JSONB to a core column. The view adapts. No data migration needed.

**Trade-off:** VIEWs add a query planning step. But PostgreSQL optimizes this transparently. The AI simplicity wins.

---

## Data Pipeline: Extract, Transform, Load (with Intent)

### Extract: Dumb Ingestion

Read JSON. Insert into `raw_data`. That's it.

**Decision rationale:** Ingestion should be fast and reliable. Complexity lives downstream. If extraction logic is complex, every schema change breaks it. Keep it simple.

**Source Files:**
- `doordash_orders.json` - DoorDash orders
- `square/catalog.json`, `square/orders.json`, `square/payments.json`, `square/locations.json` - Square POS data
- `toast_pos_export.json` - Toast POS data

### Transform: The Catalog Pattern

A pre-built `item_catalog.json` maps source IDs to normalized names and categories. Built once during onboarding, updated when menus change.

**Decision rationale:** The alternative—parsing and normalizing item names on every pipeline run—is expensive and error-prone. Typos, emojis, variations all require regex and heuristics. The catalog eliminates guesswork.

The catalog is static by design. New products require manual updates. For franchises with standardized menus, this is acceptable. The trade-off: occasional manual work for guaranteed data quality on every order.

**Transformation Steps:**
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

**Implementation Note:** The pipeline leverages fundamental DSA concepts for efficiency—dictionaries (hash maps) for O(1) catalog lookups, dependency graphs for transformation ordering, and set operations for deduplication and validation.

### Load: Validation at the Gate

Pydantic schemas validate every record before insertion.

**Decision rationale:** Database constraints catch errors too late. Validation at the transform layer catches errors early, with clear messages. Failed records don't create partial data states.

### Reprocessability

The entire pipeline is rerunnable. Truncate downstream tables, re-execute transforms—Bronze layer preserves everything.

---

## The AI Agent: Intelligence with Guardrails

### Architecture Choice: LangChain Agent with Tools

**Decision rationale:** The agent needs to (1) understand natural language, (2) generate SQL, (3) execute queries, (4) format results, (5) generate visualizations. This is a multi-step process with branching logic.

LangChain's agent pattern handles this elegantly. The agent iterates until it solves the user's request. It can call tools, see results, and try again if needed.

### Tool 1: SQL Execution with Validation

The agent generates SQL. But it never executes directly.

**Decision rationale:** LLMs are unpredictable. They might generate valid SQL that's dangerous (`DROP TABLE orders`), or invalid SQL that crashes queries. Defense-in-depth requires validation.

**Validation layer:**
- Only `SELECT` statements (or `WITH ... SELECT` CTEs)
- Blacklist of dangerous keywords (`DELETE`, `DROP`, `INSERT`, `UPDATE`, etc.)
- Whitelist of allowed tables
- Direct PostgreSQL connection (bypasses Supabase API rate limits)

**Trade-off:** Validation adds latency. But the security and reliability wins are non-negotiable.

### Tool 2: Chart Configuration (Not Generation)

The agent generates chart configurations. React components render them.

**Decision rationale:** LLMs can't reliably generate SVG or React components. They might hallucinate props, create invalid layouts, or produce inconsistent styling. 

Instead, the agent populates pre-defined chart types with data. The chart components are deterministic—same input, same output. No surprises.

**Supported Chart Types:** bar, bar-horizontal, bar-grouped, line, line-multi, pie, card, table

**Trade-off:** Limited chart flexibility. But reliability and consistency win.

Also, temperature set to 0.3 for consistency, not creativity.

### Context Management

The last 5 messages are loaded as context. This is a deliberate limit—too much history dilutes relevance, too little loses nuance. The agent receives conversation history as LangChain messages, enabling multi-turn interactions without losing thread.

---

## Web Application: Maximum Determinism

**Philosophy:** Trust the types. Validate the inputs. Render predictably.

### Type Safety First

TypeScript everywhere. Every API response, database row, component prop is typed.

**Decision rationale:** Runtime errors are expensive. Type errors surface at build time. This catches bugs early and makes refactoring safe.

### Deterministic Rendering

Chart components accept a `ChartConfig` type. Zod validates it. Invalid configurations are rejected before rendering.

**Decision rationale:** When data is invalid, fail early with clear errors. Don't render partial charts or broken layouts.

### State Management: Database as Source of Truth

Conversation history lives in the database, not component state.

**Decision rationale:** Component state is ephemeral. Database state persists. When a user refreshes, they see their history. When they switch conversations, context is preserved.

### Architecture: Next.js App Router

- Server-side rendering for performance
- Client components for interactivity
- API routes for backend logic
- `/api/chat` - Streaming chat endpoint with SSE
- `/api/auth/login` - Authentication
- `/api/conversations` - Conversation management

---

## Database Schema Decisions

### UUIDs Over Integers

All primary keys are UUIDs.

**Decision rationale:** Multi-source data requires collision-free IDs. UUIDs eliminate the risk of ID conflicts when merging data from different sources.

### Money in Cents

All monetary values stored as integers (cents).

**Decision rationale:** Floating-point arithmetic introduces rounding errors. Integers eliminate this. Conversion to dollars happens at display time.

### Status Normalization

All status values normalized to lowercase: `"completed"`, `"cancelled"`, `"voided"`, `"deleted"`.

**Decision rationale:** Sources use different formats (`"DELIVERED"`, `"COMPLETED"`, `"Delivered"`). Normalization simplifies queries and reduces token usage in AI prompts.

### Schema Structure

**Silver Layer Tables:**
- `locations` - location_id (UUID), source_name, name, address fields, timezone
- `orders` - order_id (UUID), location_id (FK), source_order_id, timestamps, status, fulfillment_method, monetary amounts, metadata (JSONB)
- `order_items` - order_item_id (UUID), order_id (FK), item_name, category, quantities, prices

**Gold Layer Views:**
- `ai_orders` - Flattened view with pre-joined locations and extracted metadata columns
- `ai_order_items` - Flattened view with pre-joined order and location context

**Raw Layer:**
- `raw_data` - raw_id (UUID), source_name, entity_type, source_entity_id, data (JSONB)

---

## Technical Stack: Deliberate Choices

**Python 3.12+** for ETL: Rich ecosystem for data processing, strong typing with Pydantic.

**Next.js 16 (App Router)** for web app: Server-side rendering for performance, API routes for backend logic, TypeScript for type safety.

**LangChain** for agent orchestration: Battle-tested patterns for multi-step AI workflows.

**Recharts** for visualizations: React-native, deterministic rendering, accessible.

**Zod** for validation: Runtime type validation that matches TypeScript types.

---

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

---

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

---

## Features

✅ Multi-source data ingestion (DoorDash, Square, Toast)  
✅ Data normalization and cleaning pipeline  
✅ Medallion architecture for scalable processing  
✅ Item catalog for consistent product naming  
✅ Natural language query interface  
✅ AI-powered SQL generation with security validation  
✅ Deterministic chart rendering (bar, line, pie, table, card)  
✅ Real-time streaming responses via SSE  
✅ Conversation history persistence  
✅ Secure authentication  
✅ Production-ready error handling  
✅ **Deployed on Vercel** - Live demo available

---

## Deployment

The application is deployed on **Vercel** and accessible at:
- **Production URL:** [https://clave-take-home.vercel.app](https://clave-take-home.vercel.app)

### Access Credentials

For evaluators and reviewers:
- **Email:** `challenge@tryclave.ai`
- **Password:** `123`

The deployment includes:
- Next.js application (frontend + API routes)
- Environment variables configured for production
- Automatic deployments on push to main branch

---

## Future Improvements

- **AI Observability with LangSmith:** Integrate LangSmith for comprehensive AI agent observability—tracking tool usage, query patterns, token consumption, and response quality. Use this data to drive schema evolution: promote frequently accessed metadata fields from JSONB to core columns, and demote rarely queried fields back to JSONB.

- **ETL as a Service:** Evolve the ETL pipeline into a production-grade web service using FastAPI. Redis would serve as both queue system and message broker, enabling efficient and scalable handling of incoming data streams. This architecture supports distributed processing, retry mechanisms, and graceful handling of backpressure.

- **Query Optimization:** Add indexes based on actual query patterns observed through production usage

- **Error Recovery:** Implement retry logic and partial failure handling for the ETL pipeline

- **Caching:** Cache common query results to reduce database load

- **Export:** Add data export functionality (CSV, PDF reports)

- **Advanced Visualizations:** Support for more chart types (heatmaps, scatter plots)
