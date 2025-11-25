-- 1. Portfolio Risk Scores table
CREATE TABLE IF NOT EXISTS portfolio_risk_scores (
    portfolio_id INTEGER NOT NULL,
    date DATE NOT NULL,
    risk_score FLOAT NOT NULL,
    risk VARCHAR(10) NOT NULL CHECK (risk IN ('LOW', 'MEDIUM', 'HIGH')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (portfolio_id, date),
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_portfolio_risk_scores_portfolio_id 
ON portfolio_risk_scores(portfolio_id);

CREATE INDEX IF NOT EXISTS idx_portfolio_risk_scores_date 
ON portfolio_risk_scores(date);

CREATE INDEX IF NOT EXISTS idx_portfolio_risk_scores_risk 
ON portfolio_risk_scores(risk);


-- 2. Fund Performance Metrics table
CREATE TABLE IF NOT EXISTS fund_performance_metrics (
    fund_code VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    performance_score FLOAT,
    peer_category VARCHAR(255),
    is_poor_performer BOOLEAN DEFAULT FALSE,
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (fund_code, date)
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_fund_performance_metrics_fund_code 
ON fund_performance_metrics(fund_code);

CREATE INDEX IF NOT EXISTS idx_fund_performance_metrics_date 
ON fund_performance_metrics(date);

CREATE INDEX IF NOT EXISTS idx_fund_performance_metrics_poor_performer 
ON fund_performance_metrics(is_poor_performer) WHERE is_poor_performer = TRUE;