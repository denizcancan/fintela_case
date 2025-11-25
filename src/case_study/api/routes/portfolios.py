"""Portfolio CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, text
from typing import List

from case_study.api.database import get_db
from case_study.api.models import (
    PortfolioCreate,
    PortfolioUpdate,
    PortfolioResponse,
    PortfolioListResponse,
    PositionResponse,
    RiskResponse,
)
from case_study.db.models import Portfolio, PortfolioPosition

router = APIRouter(prefix="/portfolios", tags=["portfolios"])


@router.post("", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
def create_portfolio(portfolio: PortfolioCreate, db: Session = Depends(get_db)):
    """Create a new portfolio."""
    # Check if portfolio already exists
    existing = db.query(Portfolio).filter(Portfolio.id == portfolio.id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Portfolio with id {portfolio.id} already exists"
        )
    
    # Create portfolio
    db_portfolio = Portfolio(
        id=portfolio.id,
        name=portfolio.name,
    )
    db.add(db_portfolio)
    
    # Create positions
    for position in portfolio.positions:
        db_position = PortfolioPosition(
            portfolio_id=portfolio.id,
            fund_code=position.fund_code,
            weight=position.weight,
        )
        db.add(db_position)
    
    db.commit()
    db.refresh(db_portfolio)
    
    return db_portfolio


@router.get("", response_model=PortfolioListResponse)
def list_portfolios(db: Session = Depends(get_db)):
    """List all portfolios."""
    portfolios = db.query(Portfolio).all()
    return PortfolioListResponse(portfolios=portfolios)


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
def get_portfolio(portfolio_id: int, db: Session = Depends(get_db)):
    """Get a single portfolio by ID."""
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio with id {portfolio_id} not found"
        )
    return portfolio


@router.put("/{portfolio_id}", response_model=PortfolioResponse)
def update_portfolio(
    portfolio_id: int,
    portfolio_update: PortfolioUpdate,
    db: Session = Depends(get_db)
):
    """Update a portfolio."""
    db_portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not db_portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio with id {portfolio_id} not found"
        )
    
    # Update name if provided
    if portfolio_update.name is not None:
        db_portfolio.name = portfolio_update.name
    
    # Update positions if provided
    if portfolio_update.positions is not None:
        # Delete existing positions
        db.query(PortfolioPosition).filter(
            PortfolioPosition.portfolio_id == portfolio_id
        ).delete()
        
        # Create new positions
        for position in portfolio_update.positions:
            db_position = PortfolioPosition(
                portfolio_id=portfolio_id,
                fund_code=position.fund_code,
                weight=position.weight,
            )
            db.add(db_position)
    
    db.commit()
    db.refresh(db_portfolio)
    
    return db_portfolio


@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio(portfolio_id: int, db: Session = Depends(get_db)):
    """Delete a portfolio."""
    db_portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not db_portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio with id {portfolio_id} not found"
        )
    
    db.delete(db_portfolio)
    db.commit()
    
    return None


@router.get("/{portfolio_id}/risk", response_model=RiskResponse)
def get_portfolio_risk(portfolio_id: int, db: Session = Depends(get_db)):
    """Get risk for a specific portfolio."""
    # Check if portfolio exists
    db_portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not db_portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio with id {portfolio_id} not found"
        )
    
    # Query from portfolio_risk_scores table for the latest risk score
    query = text("""
        SELECT 
            portfolio_id,
            risk_score,
            risk
        FROM portfolio_risk_scores
        WHERE portfolio_id = :portfolio_id
        ORDER BY date DESC
        LIMIT 1
    """)
    
    result = db.execute(query, {"portfolio_id": portfolio_id})
    row = result.fetchone()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Risk score not found for portfolio {portfolio_id}"
        )
    
    return RiskResponse(
        portfolio_id=row.portfolio_id,
        risk_score=float(row.risk_score),
        risk=row.risk
    )

