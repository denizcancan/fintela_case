-- 1. Portfolios table
CREATE TABLE IF NOT EXISTS portfolios (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Portfolio positions table
CREATE TABLE IF NOT EXISTS portfolio_positions (
    id SERIAL PRIMARY KEY,
    portfolio_id INTEGER NOT NULL,
    fund_code VARCHAR(10) NOT NULL,
    weight FLOAT NOT NULL CHECK (weight >= 0 AND weight <= 1),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE,
    UNIQUE(portfolio_id, fund_code)  -- Prevent duplicate funds in same portfolio
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_portfolio_positions_portfolio_id 
ON portfolio_positions(portfolio_id);

CREATE INDEX IF NOT EXISTS idx_portfolio_positions_fund_code 
ON portfolio_positions(fund_code);

-- 3. Fund labels table (for the CSV data)
CREATE TABLE IF NOT EXISTS fund_labels (
    code VARCHAR(10) PRIMARY KEY,
    title VARCHAR(500),
    umbrella_code VARCHAR(255),
    founder VARCHAR(255),
    main_category VARCHAR(255),
    category VARCHAR(255),
    has_interest BOOLEAN,
    is_hedge BOOLEAN,
    currency_type VARCHAR(50)
);