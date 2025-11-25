# Architecture & Design Decisions

This document explains the design approaches, methodologies, and technical decisions behind the Fintela case study implementation.

---

## System Architecture

### Overview
The system consists of three main components:
1. **Dagster Data Pipeline** - Ingests fund data from TEFAS and computes analytics
2. **FastAPI Service** - Provides REST API for portfolio management and risk/alerts
3. **React Dashboard** - Visualizes portfolio risks and alerts

All services are containerized with Docker Compose for easy deployment and isolation.

---

## Data Ingestion (Part A)

### Incremental Data Fetching
The `raw_fund_data` asset implements an intelligent incremental fetching strategy:

- **First Run**: Automatically fetches last 200 days of historical data for initial setup
- **Subsequent Runs**: Only fetches missing dates since the last successful run
- **Weekend/Holiday Handling**: Gracefully handles empty results when TEFAS has no new data

**Rationale**: 
- Avoids redundant data fetching on each run
- Maintains a rolling 200-day window via deletion logic
- Optimizes performance for daily scheduled runs

### Rolling Window Management
Both `fund_prices` and `instrument_distributions` maintain a 200-day rolling window:
- Old data (>200 days) is automatically deleted
- New data is upserted using `ON CONFLICT` to handle duplicates
- Ensures database size remains manageable while providing sufficient history

**Data Sources**:
- **TEFAS Crawler**: Fetches raw fund data (prices, market cap, investors, instrument distributions)
- **CSV Import**: Fund metadata (categories, labels) loaded once via `init_db.py`

---

## Portfolio Risk Calculation (Part C)

### Risk Model Overview
The portfolio risk calculation uses a multi-component approach that combines:

1. **Markowitz-lite Volatility** (60% weight)
2. **Concentration Penalty** (20% weight)
3. **Max Drawdown** (10% weight)
4. **Liquidity Penalty** (10% weight)

### Component Details

#### 1. Markowitz-lite Volatility (60%)
Calculates portfolio volatility using covariance matrix:
- Computes daily returns for each fund in the portfolio
- Builds covariance matrix of fund returns
- Portfolio variance: `σ²_p = w^T Σ w` where `w` is weight vector, `Σ` is covariance matrix
- Volatility = `√(max(0, portfolio_variance))`

**Why**: Captures diversification benefits - portfolios with negatively correlated assets have lower risk.

#### 2. Concentration Penalty - Herfindahl Index (20%)
Measures portfolio concentration:
- `H = Σ w_i²` where `w_i` is weight of fund `i`
- Higher values indicate more concentrated (risky) portfolios

**Why**: Concentrated portfolios are more vulnerable to single-fund failures.

#### 3. Max Drawdown (10%)
Measures worst peak-to-trough decline:
- Builds cumulative return curve: `C_t = ∏(1 + r_p,t)`
- Drawdown = `1 - (C_t / running_max)`
- Max drawdown = maximum drawdown over the period

**Why**: Captures crash risk and worst-case scenario impact.

#### 4. Liquidity Penalty (10%)
Penalizes portfolios with less liquid funds:
- For each fund: `L_i = log(1 + avg_market_cap) + log(1 + avg_investors)` (last 30 days)
- Normalized to 0-1 scale across all funds
- Portfolio penalty: `Σ w_i (1 - L_i~)`

**Why**: Less liquid funds are harder to exit during market stress.

### Normalization Strategy
All components are **percentile-normalized** before combining:
- First pass: Calculate raw components for all portfolios
- Second pass: Convert each component to percentile rank (0-1 scale)
- Final score: Weighted combination of normalized components

**Rationale**: 
- Prevents scale differences from dominating (e.g., drawdown 0.05-0.30 vs volatility 0.005-0.02)
- Ensures fair ranking across all portfolios
- Maintains stable relative rankings day-to-day

### Risk Classification
Fixed thresholds after percentile normalization:
- **LOW**: risk_score < 0.33 (bottom third)
- **MEDIUM**: 0.33 ≤ risk_score < 0.67 (middle third)
- **HIGH**: risk_score ≥ 0.67 (top third)

**Why Fixed Thresholds**: More stable than quantile-based classification, which can change daily.

---

## Fund Performance Evaluation (Part C)

### Risk-Adjusted Performance Metric
Funds are evaluated using a **Sharpe-like ratio** that accounts for both returns and volatility:

- **Total Return**: 90-day cumulative return via compounding: `∏(1 + r_t) - 1`
- **Volatility**: Standard deviation of daily returns over 90-day window
- **Sharpe-like Score**: `total_return / volatility` (risk-adjusted performance)

**Why**: Raw returns don't tell the full story. A fund with high returns but high volatility is riskier than one with moderate returns and low volatility.

### Hierarchical Peer Grouping
Funds are compared to peers using a fallback strategy:

1. **Primary**: Same `category` (if ≥5 peers)
2. **Fallback**: Same `main_category` (if ≥5 peers)
3. **Final**: All funds (if category groups too small)

**Why**: Ensures meaningful peer comparisons even when category has few funds. Minimum 5 peers prevents statistical noise.

### Performance Scoring
Each fund receives a `performance_score` (0-1) based on percentile rank within its peer group:
- Calculated using `rank(pct=True)` on Sharpe-like scores
- Higher score = better risk-adjusted performance relative to peers

### Poor Performer Detection
Uses a **conservative two-condition rule** to reduce false positives:

- **Condition 1**: `performance_score ≤ 0.10` (bottom 10th percentile)
- **Condition 2**: `z-score ≤ -1.5` (statistically significant underperformance)

Both conditions must be true for a fund to be flagged as a poor performer.

**Robust Z-Score Calculation**:
- Uses **median** and **MAD** (Median Absolute Deviation) instead of mean/std
- `z = (sharpe_like - median) / (1.4826 * MAD)`
- More resistant to outliers than traditional z-score

### Confidence Score
Confidence measures statistical significance of underperformance:
- `confidence = min(1.0, abs(z) / 3.0)` for poor performers
- Higher confidence = further below peer median (more significant)
- Only calculated for funds flagged as poor performers

**Rationale**: 
- Dual-condition approach (percentile + z-score) reduces false positives
- Robust statistics (median/MAD) handle outliers better
- Confidence based on z-score magnitude is more statistically meaningful

---

## Technical Design Decisions

### Data Pipeline (Dagster)

**Why Dagster?**
- Declarative asset dependencies make data lineage clear
- Built-in scheduling and monitoring
- Handles retries and failure recovery
- Good separation between data ingestion and analytics

**Asset Design**:
- `raw_fund_data`: Fetches from external source (source of truth)
- `fund_prices` / `instrument_distributions`: Transform and store (derived assets)
- `portfolio_risk_scores` / `fund_performance_metrics`: Analytics (computed assets)

### API Design (FastAPI)

**RESTful Principles**:
- Clear resource hierarchy: `/portfolios/{id}/risk`
- Semantic HTTP methods (GET, POST, PUT, DELETE)
- Consistent JSON response format

**Database Access**:
- SQLAlchemy ORM for type safety
- Session management via dependency injection
- Direct SQL for complex queries (risk scores, alerts)

### Database Schema

**Tables**:
- `portfolios` / `portfolio_positions`: Portfolio definitions (CRUD data)
- `fund_labels`: Fund metadata (reference data)
- `fund_prices` / `instrument_distributions`: Time-series data (ingestion)
- `portfolio_risk_scores` / `fund_performance_metrics`: Analytics results

**Indexes**: Strategically placed on foreign keys and frequently queried columns (portfolio_id, date, risk, is_poor_performer)

**Primary Keys**: Composite keys `(portfolio_id, date)` and `(fund_code, date)` ensure one record per entity per day.

### Docker Architecture

**Service Isolation**:
- Each service runs in its own container
- Shared network for inter-service communication
- PostgreSQL in separate container with persistent volume
- Services connect using service names (`postgres`, not `localhost`)

**Data Persistence**:
- PostgreSQL data: Docker volume (`postgres_data`)
- Dagster metadata: Docker volume (`dagster_home`)

**Why**: Ensures data survives container restarts and allows easy backups.

---

## Data Flow

```
TEFAS Website
    ↓
raw_fund_data (asset)
    ↓
┌─────────────────┬──────────────────┐
↓                 ↓                  ↓
fund_prices   instrument_distributions
    ↓
portfolio_risk_scores (depends on fund_prices)
    ↓
FastAPI → Dashboard
```

---

## Performance Considerations

1. **Batch Processing**: Large inserts use temporary tables and `ON CONFLICT` for atomicity
2. **Rolling Windows**: Automatic deletion prevents unbounded data growth
3. **Indexed Queries**: Foreign keys and date columns are indexed for fast lookups
4. **Incremental Updates**: Only new/missing data is fetched, reducing TEFAS API load
5. **Vectorized Operations**: NumPy and Pandas operations used for computational efficiency

---

## Future Improvements

- **Caching**: Cache frequently accessed portfolio risk scores
- **Parallel Processing**: Process multiple portfolios concurrently
- **Real-time Updates**: WebSocket support for live dashboard updates
- **Advanced Analytics**: Additional risk metrics (VaR, Sharpe ratio, etc.)
- **Alert Notifications**: Email/Slack integration for poor performers

