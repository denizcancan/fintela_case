"""SQLAlchemy database models for the FastAPI service."""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, TIMESTAMP, CheckConstraint, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class Portfolio(Base):
    """Portfolio model."""
    
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationship to positions
    positions = relationship("PortfolioPosition", back_populates="portfolio", cascade="all, delete-orphan")


class PortfolioPosition(Base):
    """Portfolio position model - represents a fund in a portfolio."""
    
    __tablename__ = "portfolio_positions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True)
    fund_code = Column(String(10), nullable=False, index=True)
    weight = Column(Float, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    
    # Constraints
    __table_args__ = (
        CheckConstraint("weight >= 0 AND weight <= 1", name="weight_check"),
        UniqueConstraint("portfolio_id", "fund_code", name="unique_portfolio_fund"),
    )
    
    # Relationship to portfolio
    portfolio = relationship("Portfolio", back_populates="positions")

