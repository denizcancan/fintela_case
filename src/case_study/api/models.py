"""Pydantic models for request/response validation."""

from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime


# ============================================================================
# Request Models
# ============================================================================

class PositionCreate(BaseModel):
    """Position in a portfolio."""
    fund_code: str = Field(..., description="Fund code")
    weight: float = Field(..., ge=0, le=1, description="Weight (0.0 to 1.0)")
    
    @validator('weight')
    def validate_weight(cls, v):
        if v < 0 or v > 1:
            raise ValueError('Weight must be between 0 and 1')
        return v


class PortfolioCreate(BaseModel):
    """Create portfolio request."""
    id: int = Field(..., description="Portfolio ID")
    name: Optional[str] = Field(None, description="Portfolio name")
    positions: List[PositionCreate] = Field(..., description="List of positions")
    
    @validator('positions')
    def validate_weights_sum(cls, v):
        """Validate that weights sum to approximately 1.0."""
        total_weight = sum(pos.weight for pos in v)
        if abs(total_weight - 1.0) > 0.001:  # Allow small floating point errors
            raise ValueError(f'Sum of weights must equal 1.0, got {total_weight}')
        return v


class PortfolioUpdate(BaseModel):
    """Update portfolio request."""
    name: Optional[str] = Field(None, description="Portfolio name")
    positions: Optional[List[PositionCreate]] = Field(None, description="List of positions")
    
    @validator('positions')
    def validate_weights_sum(cls, v):
        """Validate that weights sum to approximately 1.0 if positions provided."""
        if v is None:
            return v
        total_weight = sum(pos.weight for pos in v)
        if abs(total_weight - 1.0) > 0.001:
            raise ValueError(f'Sum of weights must equal 1.0, got {total_weight}')
        return v


# ============================================================================
# Response Models
# ============================================================================

class PositionResponse(BaseModel):
    """Position response."""
    fund_code: str
    weight: float
    
    class Config:
        from_attributes = True


class PortfolioResponse(BaseModel):
    """Portfolio response."""
    id: int
    name: Optional[str]
    positions: List[PositionResponse]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PortfolioListResponse(BaseModel):
    """List of portfolios response."""
    portfolios: List[PortfolioResponse]


class RiskResponse(BaseModel):
    """Portfolio risk response."""
    portfolio_id: int
    risk_score: float
    risk: str  # LOW, MEDIUM, or HIGH


class PortfolioRiskListResponse(BaseModel):
    """List of portfolio risks response."""
    portfolios: List[RiskResponse]


class FundAlertResponse(BaseModel):
    """Fund alert response."""
    fund_code: str
    confidence: Optional[float] = None


class FundAlertListResponse(BaseModel):
    """List of fund alerts response."""
    funds: List[FundAlertResponse]

