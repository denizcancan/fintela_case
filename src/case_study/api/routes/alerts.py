"""Risk and alert endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from case_study.api.database import get_db
from case_study.api.models import (
    PortfolioRiskListResponse,
    RiskResponse,
    FundAlertResponse,
    FundAlertListResponse,
)

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/portfolios", response_model=PortfolioRiskListResponse)
def get_high_risk_portfolios(db: Session = Depends(get_db)):
    """Get all portfolios with HIGH risk."""
    # Query portfolio_risk_scores table for HIGH risk portfolios
    # Get the latest risk score for each portfolio (most recent date)
    query = text("""
        SELECT 
            prs.portfolio_id,
            prs.risk_score,
            prs.risk
        FROM portfolio_risk_scores prs
        INNER JOIN (
            SELECT portfolio_id, MAX(date) as max_date
            FROM portfolio_risk_scores
            WHERE risk = 'HIGH'
            GROUP BY portfolio_id
        ) latest ON prs.portfolio_id = latest.portfolio_id 
                AND prs.date = latest.max_date
        WHERE prs.risk = 'HIGH'
        ORDER BY prs.portfolio_id
    """)
    
    result = db.execute(query)
    rows = result.fetchall()
    
    # Map results to response models
    portfolios = [
        RiskResponse(
            portfolio_id=row.portfolio_id,
            risk_score=float(row.risk_score),
            risk=row.risk
        )
        for row in rows
    ]
    
    return PortfolioRiskListResponse(portfolios=portfolios)


@router.get("/funds", response_model=FundAlertListResponse)
def get_underperforming_funds(db: Session = Depends(get_db)):
    """Get funds that perform significantly bad compared to peers."""
    # Query fund_performance_metrics table for poor performers
    # Get the latest performance metrics for each fund (most recent date)
    query = text("""
        SELECT 
            fpm.fund_code,
            fpm.confidence
        FROM fund_performance_metrics fpm
        INNER JOIN (
            SELECT fund_code, MAX(date) as max_date
            FROM fund_performance_metrics
            WHERE is_poor_performer = TRUE
            GROUP BY fund_code
        ) latest ON fpm.fund_code = latest.fund_code 
                AND fpm.date = latest.max_date
        WHERE fpm.is_poor_performer = TRUE
        ORDER BY fpm.fund_code
    """)
    
    result = db.execute(query)
    rows = result.fetchall()
    
    # Map results to response models
    funds = [
        FundAlertResponse(
            fund_code=row.fund_code,
            confidence=float(row.confidence) if row.confidence is not None else None
        )
        for row in rows
    ]
    
    return FundAlertListResponse(funds=funds)

