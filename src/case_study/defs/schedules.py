"""Dagster schedules for the case study project.

Schedules define when jobs should run automatically.
They enable automation of your data pipelines.
"""

import dagster as dg
from case_study.defs.jobs import (
    ingest_fund_data_job,
    portfolio_risk_job,
    fund_performance_job,
    daily_pipeline_job,
)


# ============================================================================
# AUTOMATION SCHEDULES
# ============================================================================

daily_ingestion_schedule = dg.ScheduleDefinition(
    name="daily_ingestion_schedule",
    job=ingest_fund_data_job,
    cron_schedule="0 2 * * *",  # Run daily at 2 AM
    default_status=dg.DefaultScheduleStatus.RUNNING,  # Enabled by default
    description="Runs daily to ingest latest fund data from TEFAS",
)

# TODO: Add analytics schedules later
# daily_risk_calculation_schedule = ...
# daily_performance_evaluation_schedule = ...
daily_risk_calculation_schedule = dg.ScheduleDefinition(
    name="daily_risk_calculation_schedule",
    job=portfolio_risk_job,
    cron_schedule="0 3 * * *",  # Run daily at 3 AM (after ingestion)
    default_status=dg.DefaultScheduleStatus.RUNNING,
    description="Runs daily to calculate portfolio risk scores",
)

daily_performance_evaluation_schedule = dg.ScheduleDefinition(
    name="daily_performance_evaluation_schedule",
    job=fund_performance_job,
    cron_schedule="0 4 * * *",  # Run daily at 4 AM (after ingestion)
    default_status=dg.DefaultScheduleStatus.RUNNING,
    description="Runs daily to evaluate fund performance",
)

# Combined daily schedule at 06:00 Istanbul time (03:00 UTC)
# Istanbul is UTC+3, so 06:00 Istanbul = 03:00 UTC
daily_pipeline_schedule = dg.ScheduleDefinition(
    name="daily_pipeline_schedule",
    job=daily_pipeline_job,
    cron_schedule="0 3 * * *",  # 06:00 Istanbul time (UTC+3) = 03:00 UTC
    default_status=dg.DefaultScheduleStatus.RUNNING,
    description="Runs daily at 06:00 Istanbul time to execute ingestion + analytics pipeline",
)
