"""Main Dagster definitions file.

This file exports all assets, resources, jobs, and schedules
so Dagster can discover and use them.
"""

import dagster as dg
from case_study.defs import assets, resources, jobs, schedules
from dotenv import load_dotenv
from urllib.parse import urlparse

# Load .env file
load_dotenv()
# Create resource instances
import os

# Get database connection details
# Support DATABASE_URL or individual env vars with local defaults
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    # Parse DATABASE_URL to extract components
    parsed = urlparse(DATABASE_URL)
    postgres_resource = resources.PostgresResource(
        host=parsed.hostname or "localhost",
        port=parsed.port or 5432,
        database=parsed.path.lstrip("/") if parsed.path else "fintela",
        user=parsed.username or "fintela",
        password=parsed.password or "fintela_password",
    )
else:
    # Use individual env vars with local defaults
    postgres_resource = resources.PostgresResource(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB", "fintela"),
        user=os.getenv("POSTGRES_USER", "fintela"),
        password=os.getenv("POSTGRES_PASSWORD", "fintela_password"),
    )
tefas_crawler_resource = resources.TefasCrawlerResource()

# Export everything to Dagster
# For now, we only have Part A (data ingestion) implemented
defs = dg.Definitions(
    assets=[
        assets.raw_fund_data,
        assets.fund_prices,
        assets.instrument_distributions,
        # TODO: Add analytics assets later
        assets.portfolio_risk_scores,
        assets.fund_performance_metrics,
    ],
    resources={
        "postgres": postgres_resource,
        "tefas_crawler": tefas_crawler_resource,
    },
    jobs=[
        jobs.ingest_fund_data_job,
        jobs.portfolio_risk_job,
        jobs.fund_performance_job,
        jobs.daily_pipeline_job,
    ],
    schedules=[
        schedules.daily_ingestion_schedule,
        schedules.daily_risk_calculation_schedule,
        schedules.daily_performance_evaluation_schedule,
        schedules.daily_pipeline_schedule,
    ],
    executor=dg.in_process_executor, 
)

