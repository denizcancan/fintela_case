CREATE INDEX IF NOT EXISTS idx_fund_prices_code_date 
ON fund_prices (code, date);

CREATE INDEX IF NOT EXISTS idx_fund_prices_date 
ON fund_prices (date);

CREATE INDEX IF NOT EXISTS idx_inst_dist_code_date 
ON instrument_distributions(code, date);
