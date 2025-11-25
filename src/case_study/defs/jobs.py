"""Dagster jobs for the case study project.

Jobs group assets together and define execution order.
They can be run manually or scheduled.
"""

import dagster as dg
from case_study.defs import assets


# ============================================================================
# PART A: DATA INGESTION JOB
# ============================================================================

ingest_fund_data_job = dg.define_asset_job(
    name="ingest_fund_data_job",
    description="Ingests fund data from TEFAS website and stores in PostgreSQL",
    selection=dg.AssetSelection.assets(
        assets.raw_fund_data,
        assets.fund_prices,
        assets.instrument_distributions
    ),
)


# ============================================================================
# PART C: ANALYTICS JOBS (TODO: Add later)
# ============================================================================
# We'll add portfolio_risk_job and fund_performance_job here later
portfolio_risk_job = dg.define_asset_job(
    name="portfolio_risk_job",
    description="Calculates risk scores for all portfolios",
    selection=dg.AssetSelection.assets(assets.portfolio_risk_scores),
    # This will run: portfolio_risk_scores (which depends on fund_prices)
)

fund_performance_job = dg.define_asset_job(
    name="fund_performance_job",
    description="Evaluates fund performance compared to peers",
    selection=dg.AssetSelection.assets(assets.fund_performance_metrics),
    # This will run: fund_performance_metrics (which depends on fund_prices)
)


daily_pipeline_job = dg.define_asset_job(
    name="daily_pipeline_job",
    description="Daily pipeline: ingestion + analytics (fund_prices, instrument_distributions, portfolio_risk_scores, fund_performance_metrics)",
    selection=dg.AssetSelection.assets(
        assets.raw_fund_data, 
        assets.fund_prices,
        assets.instrument_distributions,
        assets.portfolio_risk_scores,
        assets.fund_performance_metrics
    ),
)
