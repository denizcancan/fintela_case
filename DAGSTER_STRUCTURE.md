# Dagster Project Structure

## Overview

This document explains the Dagster architecture for the Fintela case study project.

## Core Concepts

### 1. **Assets** - The Data Products
Assets represent the data/products we're creating and storing. Each asset is a logical unit of data.

**For Part A (Data Ingestion):**
- `raw_fund_data` - Raw data fetched from TEFAS website (temporary, in-memory)
- `fund_prices` - Processed fund price data stored in PostgreSQL
- `instrument_distributions` - Processed instrument distribution data stored in PostgreSQL

**For Part C (Analytics):**
- `portfolio_risk_scores` - Calculated risk scores for all portfolios (stored in DB)
- `fund_performance_metrics` - Calculated performance metrics for all funds (stored in DB)

### 2. **Resources** - External Dependencies
Resources are external systems or services that assets need to interact with.

- `postgres_resource` - PostgreSQL database connection
- `tefas_crawler_resource` - TEFAS website crawler instance

### 3. **Jobs** - Orchestration Units
Jobs group assets together and define execution order.

- `ingest_fund_data_job` - Runs data ingestion (Part A)
  - Fetches from TEFAS → Parses → Upserts to PostgreSQL
- `portfolio_risk_job` - Calculates portfolio risks (Part C)
  - Reads prices → Calculates risk → Stores results
- `fund_performance_job` - Evaluates fund performance (Part C)
  - Reads prices & categories → Compares to peers → Stores results

### 4. **Schedules** - Automation
Schedules define when jobs should run automatically.

- `daily_ingestion_schedule` - Runs `ingest_fund_data_job` daily
- `daily_risk_calculation_schedule` - Runs `portfolio_risk_job` daily
- `daily_performance_evaluation_schedule` - Runs `fund_performance_job` daily

### 5. **Asset Dependencies** - Data Lineage
Assets can depend on other assets, creating a dependency graph.

```
raw_fund_data → fund_prices
raw_fund_data → instrument_distributions

fund_prices → portfolio_risk_scores
fund_prices → fund_performance_metrics
```

### 6. **Asset Checks** (Optional but Recommended)
Checks validate data quality after materialization.

- Check that fund_prices has data for expected date range
- Check that portfolio_risk_scores has all portfolios
- Check that fund_performance_metrics has reasonable values

## File Structure

```
src/case_study/
├── defs/
│   ├── __init__.py          # Exports all definitions
│   ├── assets.py            # Asset definitions
│   ├── resources.py         # Resource definitions (PostgreSQL, TEFAS)
│   ├── jobs.py              # Job definitions
│   └── schedules.py         # Schedule definitions
├── tefas_parser.py          # Existing TEFAS crawler
└── definitions.py           # Main definitions file (exports everything)
```

## Implementation Strategy

1. **Start with Resources** - Set up PostgreSQL and TEFAS crawler resources
2. **Create Ingestion Assets** - Build assets for Part A
3. **Create Ingestion Job** - Orchestrate the ingestion pipeline
4. **Create Analytics Assets** - Build assets for Part C
5. **Create Analytics Jobs** - Orchestrate the analytics pipelines
6. **Add Schedules** - Automate daily runs
7. **Add Asset Checks** - Validate data quality

