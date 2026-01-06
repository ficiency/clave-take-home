# Clave Take-Home Challenge Solution 🚀

Hello Clave team!

Below, I walk through the technical reasoning behind key architectural decisions, why these choices were made, and how the system was designed.

You can directly test the app here:
**Deployment:** [https://clave-take-home.vercel.app](https://clave-take-home.vercel.app)  
**Credentials:** `challenge@tryclave.ai` / `123`

---

## TL;DR

- The db architecture (supabase) is divided into three layers: **Raw**, **Silver**, and **Gold**. Raw stores the original data so it can be reprocessed if schemas evolve. Silver contains tables with clean, normalized fields that are relevant for analytics and likely to be queried by AI. Gold consists of views optimized for AI SQL queries to **reduce token usage**.

- **ETL pipeline** first ingests data as-is into the raw layer. Then, it is cleaned, transformed and loaded into the Silver layer. Rather than parsing and cleaning emojis or variations in product names and categories, each original product's ID was used to build a **catalog mapping** ID → clean, standardized name and category. **Pydantic validation** ensures only correct records are loaded, and fundamental **DSA concepts** like hash maps, dependency ordering, and set operations were applied to guarantee efficiency and correctness.

- The web app was built with **Next.js** and **TypeScript**, prioritizing **type safety**. It includes the essentials: login, chat interface, and chart components. The **AI agent** (LangChain) interprets user intent, generates validated SQL queries, and creates charts using pre-defined components.

**Table of Contents**

1. [Understanding the Real Problem](#1-understanding-the-real-problem)
2. [DB & Schema Thinking](#2-db--schema-thinking)
3. [Designing the Data Pipeline](#3-designing-the-data-pipeline)
4. [Web Application](#4-web-application)
5. [AI Agent, Queries and Charts](#5-ai-agent-querys-and-charts)
6. [Live App & Credentials](#6-live-app--credentials)
7. [What I'd Do If I Had More Time](#7-what-id-do-if-i-had-more-time)
8. [Explore and run the codebase!](#8-explore-and-run-the-codebase)
9. [Final Message](#9-final-message)


## 1. Understanding the Real Problem

Three different data sources: DoorDash, Square, and Toast. Each comes with its own schema, hundreds of fields, different naming conventions, formats, and inconsistencies.

The goal was to build a system that ensures consistent data integrity, reliable business analytics, and efficient AI usage.

Questions I asked myself before writing a single line of code:

- How can one ensure that the data the AI queries is **100% correct** based on the raw data? (Most important in my opinion)

- Which fields are truly useful for **analytics and AI**, and which are less critical?

- How do I handle **source-specific fields** without complicating AI SQL queries?

- How could the **schema and DB architecture** be designed to keep AI SQL queries **efficient in cost and performance**?

- How can the schema **scale and evolve over time**?


## 2. DB & Schema Thinking

The system is built on **Supabase**, and the database follows a **Medallion Architecture** to balance data integrity, analytics needs, and AI efficiency. 

### Architecture Layers

- **Raw layer**: stores all raw source data in a parsed, organized way (entities → locations, orders, payments, items), preserving data for reprocessing if schemas evolve.

- **Silver layer**: contains cleaned and normalized tables with fields strictly shared across all sources.

    Existing tables include `accounts`, `locations`, `orders`, `order_items`, `conversations`, `messages`, and `raw_data`. `accounts` is the parent table. `conversations`, `raw_data`, and `locations` are at the second level. `orders` are children of `locations`, and `order_items` are children of `orders`. Source-specific or unusual fields are stored in a **JSONB metadata** column inside `orders`.

- **Gold layer**: consists of AI-optimized **views** that flatten JSONB metadata and pre-resolve joins, making data easily queryable without complex SQL. The main views are:

    - **`ai_orders`**: combines core order fields, pre-joined location info, and flattened source-specific metadata (`payment_type`, `card_brand`, `delivery_fee`, etc.).

    - **`ai_order_items`**: includes core item fields, order context (status, timestamps, fulfillment method), and location context, all pre-joined.

These views simplify AI SQL queries and reduce execution complexity by pre-flattening JSONB and pre-joining relations, enabling efficient queries without runtime joins or complex JSON path expressions.

This design also allows the schema to evolve based on **real AI usage patterns**. Fields and joins frequently queried by the agent can be **promoted** into Gold views, while rarely used ones are **moved** to JSONB or removed from optimized paths.

### Key Schema Decisions

- **UUIDs** for all primary keys to prevent collisions across sources.

- **Monetary values** stored as integers (cents) to avoid floating-point errors.

- **Status normalization** to unify values across sources ("completed", "cancelled", etc.).

- **Relationships and indexes** designed to support fast, safe, and cost-effective queries for both analytics and AI.


## 3. Designing the Data Pipeline

### Extract – Keep it Simple

I read JSONs as-is and inserted them into `raw_data`.

**Decision:** No transformation here, preserving the ability to reprocess if schemas evolve or upstream sources change (they will).

### Transform – Maintaining Consistency

A **product catalog** (`item_catalog.json`) was built to map raw product IDs to clean, normalized names and categories, avoiding parsing emojis, typo errors or variations for every run.

Shared fields across all sources were normalized, source-specific or unusual fields were stored in **JSONB metadata**.

**Transformation steps:**

- Normalize locations
- Transform orders with FK lookups to locations
- Transform order items using the catalog
- Enrich JSONB metadata with source-specific fields

**Key transformations:** status normalization, fulfillment method mapping, monetary values stored as cents, catalog-based item normalization.

**Efficiency note:** Fundamental **DSA concepts** were applied: dictionaries for **O(1) lookups**, dependency graphs for ordering, and sets for deduplication and validation.

### Load – Validation at the Gate

Before inserting this into the Silver layer, every record is validated with **Pydantic**.

**Why:** DB constraints catch errors too late. Early validation gives clear messages and prevents partial states.

**Pipeline is re-runnable:** truncate downstream tables, re-run transforms; Bronze layer preserves everything.

**Testing:** Each transformer has unit tests (`pytest`) that validate field extraction and transformation logic using real source data. Tests ensure that all three sources (DoorDash, Square, Toast) are correctly parsed and mapped to the normalized schema, catching regressions early before data reaches the database.


## 4. Web Application

The web app was built with **Next.js**, **TypeScript**, and **shadCN UI**, prioritizing **type-safe design** and rapid development. It includes login, chat interface, and conversation management.

> "Design is how it works." — Steve Jobs

UI/UX was built first to define user interactions, letting backend and AI logic follow. The app is **responsive and mobile-friendly**, designed for frequent access from various devices.

The app was deployed on **Vercel**, connected directly to GitHub, with environment variables configured via Vercel's app settings.


## 5. AI Agent, Queries and Charts

**LangChain** was chosen for its simplicity in building agents and potential future uses. The agent uses **GPT-5-2** for code generation and features **automatic retries**, **streaming output**, and two tools: **SQL-query** and **create chart**.


### System Prompt & Schema Documentation

The agent operates with a comprehensive **system prompt** that includes the complete database schema (Silver and Gold layers), normalization rules, SQL guidelines (prefer Gold views), and time awareness patterns. This ensures correct queries from the start.

### SQL Safety Validation

Every SQL query passes through **strict validation**: only `SELECT` statements (including CTEs), whitelisted tables, and blocked destructive keywords. Validation happens before database connection, preventing destructive operations.

### Chart Generation

Chart generation uses pre-defined, **type-safe React components** (**Recharts**) with deterministic configurations. The agent receives a tool that accepts structured chart configs (validated via **Zod**) for types: **bar**, **line**, **pie**, **card**, and **table**. The agent selects the appropriate type, formats monetary values, and populates the configuration. The frontend renders using these validated configs.

## 6. Live App & Credentials

**Deployment URL:** [clave-take-home.vercel.app](https://clave-take-home.vercel.app)

**Credentials:**
- Email: `challenge@tryclave.ai`
- Password: `123`

You can interact directly with the AI chat or open existing conversations from the side panel with example queries from `/docs`.


## 7. What I'd Do If I Had More Time

### LangSmith for AI Observability

**LangSmith** provides crucial visibility: user queries, **response latency**, **token costs**, and **agentic SQL queries**. This enables continuous optimization of schemas, views, and query cost based on real usage patterns.

Additionally, the **evaluation suite** enables systematic testing of agent behavior across different query types, ensuring reliability as the system scales.

### ETL Pipeline as a Web Service

Transform the ETL pipeline into a scalable web service using **FastAPI** and **Redis** for job queuing: on-demand data ingestion from new sources (using **Fivetran** as a connector), scheduled transformations and catalog updates, API endpoints for triggering pipeline runs, and better error handling and retry mechanisms.

### Real-time Alerts

Send **real-time alerts** when business rules are triggered from source data. The agent can reason about the situation, create actionable insights ("call to action"), and send notifications via email to the business owner's mobile device.

### Additional Features

- **More chart types** and customization options
- **Export functionality** for generated charts and data (PDF or XLSX)


## 8. Explore and run the codebase!

### Project Structure

The codebase is organized into two main parts: the ETL pipeline (`etl/`) and the web application (`my-dashboard/`).

```
clave-take-home/
├── etl/                    # ETL pipeline (Python)
│   ├── catalog/           # Item catalog mapping
│   ├── data/sources/      # Raw JSON data files
│   ├── extractors/        # Extract raw data to Bronze layer
│   ├── transformers/      # Transform to Silver layer
│   ├── schemas/           # Pydantic schemas
│   ├── db/                # Database connection
│   └── requirements.txt   # Python dependencies
├── my-dashboard/          # Web application (Next.js)
│   ├── app/              # Next.js App Router
│   │   ├── api/          # API routes (chat, auth, conversations)
│   │   ├── _lib/         # Core libraries (agent, supabase, auth)
│   │   └── _components/  # React components
│   └── package.json      # Node.js dependencies
└── docs/                  # Documentation
```

### Environment Variables

The ETL pipeline requires a `.env` file in the project root with:

```
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_service_role_key
```

The web application requires environment variables in `my-dashboard/.env.local`:

```
# Supabase (server-side)
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_service_role_key

# Supabase (client-side)
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key

# Database connection (for direct SQL queries)
DATABASE_URL=postgresql://user:password@host:port/database
# OR
SUPABASE_DB_URL=postgresql://user:password@host:port/database

# OpenAI (for LangChain agent)
OPENAI_API_KEY=your_openai_api_key
```

### Setup Instructions

To run the ETL pipeline, first set up a Python virtual environment and install dependencies:

```bash
# Create virtual environment (Python 3.12+)
python -m venv etl/venv

# Activate virtual environment
# On Windows:
etl\venv\Scripts\activate
# On macOS/Linux:
source etl/venv/bin/activate

# Install dependencies
cd etl
pip install -r requirements.txt

# Run ETL pipeline
python transformers/run.py
```

To run the web application, install Node.js dependencies and start the development server:

```bash
cd my-dashboard

# Install dependencies
npm install

# Run development server
npm run dev
```

The application will be available at `http://localhost:3000`. Make sure your Supabase database is set up with the required tables (see schema section above) and that all environment variables are configured before running either component.


## 9. Final Message

This solution was challenging (in the best way). Many steps I took to make the right product and technical decisions taught me something new and pushed me to grow. Still, **feedback is always welcome**—there's always a better way to do things.

Special shoutout to **Carlos and Vale**, who designed a great take-home challenge—thanks for the time invested.

— Luis Chapa 🚀