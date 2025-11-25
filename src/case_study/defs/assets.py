
import dagster as dg
from datetime import datetime, date
import pandas as pd
from typing import Optional
from sqlalchemy import text
from case_study.defs import resources
import numpy as np
# Resources are accessed via context.resources, no need to import here


# ============================================================================
# PART A: DATA INGESTION ASSETS
# ============================================================================

@dg.asset
def raw_fund_data(
    context: dg.AssetExecutionContext,
    tefas_crawler: resources.TefasCrawlerResource,
    postgres: resources.PostgresResource,
) -> pd.DataFrame:
    """
    Fetches raw fund data from TEFAS website.
    
    This asset:
    1. Checks the database for existing data
    2. If no data exists, fetches last 200 days (initial setup)
    3. If data exists, fetches only missing dates (incremental daily updates)
    4. Handles weekends/holidays when TEFAS has no data
    """
    # Get the TEFAS crawler resource from context
    crawler = tefas_crawler.get_crawler()
    engine = postgres.get_engine()
    
    # Check what dates we already have in the database
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT MAX(date) as max_date FROM fund_prices"))
            max_date_row = result.fetchone()
            latest_date = max_date_row[0] if max_date_row and max_date_row[0] else None
    except Exception as e:
        # Table doesn't exist yet or error - treat as no data
        context.log.info(f"Could not check existing dates: {e}. Treating as no existing data.")
        latest_date = None
    
    # Determine date range to fetch
    end_date = date.today() #- pd.Timedelta(days=2)  # TEFAS data is delayed by ~2 days
    
    if latest_date:
        # We have existing data - fetch only missing dates (incremental)
        # Convert latest_date to date if it's datetime
        if isinstance(latest_date, pd.Timestamp):
            latest_date = latest_date.date()
        elif not isinstance(latest_date, date):
            latest_date = pd.to_datetime(latest_date).date()
        
        start_date = latest_date + pd.Timedelta(days=1)
        
        # Only fetch if there are missing dates
        if start_date > end_date:
            context.log.info(f"Database is up to date (latest: {latest_date}, today-2: {end_date}). No new data to fetch.")
            return pd.DataFrame()  # Return empty DataFrame
        
        context.log.info(f"Found existing data up to {latest_date}. Fetching missing dates from {start_date} to {end_date}")
    else:
        # No existing data - fetch last 200 days for initial setup
        start_date = end_date - pd.Timedelta(days=200)
        context.log.info(f"No existing data found. Fetching initial 200-day window from {start_date} to {end_date}")
    
    data = crawler.fetch_historical_data(
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d")
    )
    
    context.log.info(f"Fetched {len(data)} records from TEFAS")
    if data.empty:
        context.log.warning("No data fetched from TEFAS - this may be normal if data is delayed or weekend/holiday")
        return data
    return data


@dg.asset(
    deps=[raw_fund_data]  # This asset depends on raw_fund_data
)
def fund_prices(
    context: dg.AssetExecutionContext,
    raw_fund_data: pd.DataFrame,
    postgres: resources.PostgresResource, 
) -> None:
    """
    Processes and stores fund price data in PostgreSQL.
    
    This asset:
    1. Takes raw_fund_data as input
    2. Extracts/processes price information
    3. Upserts into PostgreSQL (idempotent)
    
    Note: The actual implementation will depend on the structure of data
    returned by the TEFAS crawler. You'll need to parse the DataFrame
    and extract price-related columns.
    """
    # Get the PostgreSQL resource from context
    engine = postgres.get_engine()
    # Handle empty DataFrame (no new data - e.g., weekends when TEFAS has no data)
    if raw_fund_data.empty:
        context.log.info("No new fund data to process (likely weekend/holiday or no new data available).")
        return
    # Extract price-related columns
    price_columns = ['date', 'code', 'price', 'market_cap', 'number_of_shares', 'number_of_investors']
    prices_df = raw_fund_data[price_columns].copy()
    
    # Convert date to datetime if it's a string
    if prices_df['date'].dtype == 'object':
        prices_df['date'] = pd.to_datetime(prices_df['date']).dt.date
    
    # Create table if it doesn't exist
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS fund_prices (
        date DATE NOT NULL,
        code VARCHAR(10) NOT NULL,
        price FLOAT,
        market_cap FLOAT,
        number_of_shares FLOAT,
        number_of_investors FLOAT,
        PRIMARY KEY (date, code)
    );
    """
    with engine.connect() as conn:
        conn.execute(text(create_table_sql))
        conn.commit()
    
    # Upsert data (idempotent - uses ON CONFLICT)
    context.log.info(f"Storing {len(prices_df)} fund price records in PostgreSQL")
    
    # Use pandas to_sql with method='multi' for better performance
    # Then use raw SQL for upsert to handle conflicts
    prices_df.to_sql('fund_prices_temp', engine, if_exists='replace', index=False, method='multi')
    
    # Upsert using ON CONFLICT
    upsert_sql = """
    INSERT INTO fund_prices (date, code, price, market_cap, number_of_shares, number_of_investors)
    SELECT date, code, price, market_cap, number_of_shares, number_of_investors
    FROM fund_prices_temp
    ON CONFLICT (date, code) 
    DO UPDATE SET 
        price = EXCLUDED.price,
        market_cap = EXCLUDED.market_cap,
        number_of_shares = EXCLUDED.number_of_shares,
        number_of_investors = EXCLUDED.number_of_investors;
    
    DROP TABLE fund_prices_temp;
    """
    with engine.connect() as conn:
        conn.execute(text(upsert_sql))
        conn.commit()
    
    # Delete rows older than 200 days to keep rolling window
    cutoff_date = date.today() - pd.Timedelta(days=200)
    delete_old_sql = f"""
        DELETE FROM fund_prices
        WHERE date < '{cutoff_date}'
    """
    with engine.connect() as conn:
        result = conn.execute(text(delete_old_sql))
        deleted_count = result.rowcount
        conn.commit()
    
    if deleted_count > 0:
        context.log.info(f"Deleted {deleted_count} old fund_prices records (older than {cutoff_date})")
    
    context.log.info("Fund prices stored successfully")


@dg.asset(
    deps=[raw_fund_data]
)
def instrument_distributions(
    context: dg.AssetExecutionContext,
    raw_fund_data: pd.DataFrame,
    postgres: resources.PostgresResource,
) -> None:
    """
    Processes and stores instrument distribution data in PostgreSQL.
    
    This asset:
    1. Takes raw_fund_data as input
    2. Extracts/processes instrument distribution information
    3. Upserts into PostgreSQL (idempotent)
    """
    # Get the PostgreSQL resource from context
    engine = postgres.get_engine()
    if raw_fund_data.empty:
        context.log.info("No new instrument distribution data to process (likely weekend/holiday or no new data available).")
        return
    # Get all instrument distribution columns (exclude metadata columns)
    metadata_columns = ['date', 'code', 'title', 'price', 'market_cap', 'number_of_shares', 'number_of_investors']
    instrument_columns = [col for col in raw_fund_data.columns if col not in metadata_columns]
    
    # Melt the DataFrame to convert from wide to long format
    # This creates one row per fund per date per instrument
    id_vars = ['date', 'code']
    distributions_df = raw_fund_data.melt(
        id_vars=id_vars,
        value_vars=instrument_columns,
        var_name='instrument_type',
        value_name='percentage'
    )
    
    # Filter out rows where percentage is 0 or null (optional - saves space)
    distributions_df = distributions_df[distributions_df['percentage'] > 0]
    
    # Convert date to datetime if it's a string
    if distributions_df['date'].dtype == 'object':
        distributions_df['date'] = pd.to_datetime(distributions_df['date']).dt.date
    
    # Create table if it doesn't exist
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS instrument_distributions (
        date DATE NOT NULL,
        code VARCHAR(10) NOT NULL,
        instrument_type VARCHAR(100) NOT NULL,
        percentage FLOAT NOT NULL,
        PRIMARY KEY (date, code, instrument_type)
    );
    """
    with engine.connect() as conn:
        conn.execute(text(create_table_sql))
        conn.commit()
    
    # Upsert data (idempotent)
    context.log.info(f"Storing {len(distributions_df)} instrument distribution records in PostgreSQL")
    
    # Use temporary table for upsert
    distributions_df.to_sql('instrument_distributions_temp', engine, if_exists='replace', index=False, method='multi')
    
    # Upsert using ON CONFLICT
    upsert_sql = """
    INSERT INTO instrument_distributions (date, code, instrument_type, percentage)
    SELECT date, code, instrument_type, percentage
    FROM instrument_distributions_temp
    ON CONFLICT (date, code, instrument_type) 
    DO UPDATE SET percentage = EXCLUDED.percentage;
    
    DROP TABLE instrument_distributions_temp;
    """
    with engine.connect() as conn:
        conn.execute(text(upsert_sql))
        conn.commit()
    
    # Delete rows older than 200 days to keep rolling window
    cutoff_date = date.today() - pd.Timedelta(days=200)
    delete_old_sql = f"""
        DELETE FROM instrument_distributions
        WHERE date < '{cutoff_date}'
    """
    with engine.connect() as conn:
        result = conn.execute(text(delete_old_sql))
        deleted_count = result.rowcount
        conn.commit()
    
    if deleted_count > 0:
        context.log.info(f"Deleted {deleted_count} old instrument_distributions records (older than {cutoff_date})")
    
    context.log.info("Instrument distributions stored successfully")


# ============================================================================
# PART C: ANALYTICS ASSETS
# ============================================================================

@dg.asset(
    deps=[fund_prices]  # Depends on fund_prices being available
)
def portfolio_risk_scores(
    context: dg.AssetExecutionContext,
    postgres: resources.PostgresResource,
) -> None:
    """
    Calculates improved risk scores for all portfolios using:
    - Markowitz-lite volatility (covariance-based) - 60%
    - Concentration penalty (Herfindahl index) - 20%
    - Max Drawdown - 10%
    - Liquidity penalty - 10%
    """
    engine = postgres.get_engine()
    
    context.log.info("Calculating improved portfolio risk scores...")
    
    # Read all portfolios
    portfolios_query = """
        SELECT id, name FROM portfolios
    """
    portfolios_df = pd.read_sql(portfolios_query, engine)
    
    if portfolios_df.empty:
        context.log.warning("No portfolios found in database")
        return
    
    context.log.info(f"Found {len(portfolios_df)} portfolios to calculate risk for")
    
    # Read all portfolio positions
    positions_query = """
        SELECT portfolio_id, fund_code, weight
        FROM portfolio_positions
    """
    positions_df = pd.read_sql(positions_query, engine)
    
    # Read fund prices with liquidity data (last ~200 days)
    min_date = date.today() - pd.Timedelta(days=200)
    prices_query = f"""
        SELECT date, code, price, market_cap, number_of_investors
        FROM fund_prices
        WHERE date >= '{min_date}'
        ORDER BY code, date
    """
    prices_df = pd.read_sql(prices_query, engine)
    
    if prices_df.empty:
        context.log.warning("No fund prices found in database")
        return
    
    # Convert date column
    prices_df['date'] = pd.to_datetime(prices_df['date'])
    prices_df = prices_df.sort_values(['code', 'date'])
    
    # Calculate daily returns for each fund
    prices_df['return'] = prices_df.groupby('code')['price'].pct_change()
    prices_df = prices_df.dropna(subset=['return'])
    
    # Calculate liquidity scores for all funds (last 30 days)
    liquidity_min_date = date.today() - pd.Timedelta(days=30)
    liquidity_df = prices_df[prices_df['date'] >= pd.to_datetime(liquidity_min_date)].copy()
    
    # Compute average market_cap and number_of_investors per fund
    fund_liquidity = liquidity_df.groupby('code').agg({
        'market_cap': 'mean',
        'number_of_investors': 'mean'
    }).reset_index()
    
    # Calculate liquidity score: L_i = log(1 + avg_market_cap) + log(1 + avg_investors)
    fund_liquidity['liquidity_score'] = (
        np.log1p(fund_liquidity['market_cap'].fillna(0)) +
        np.log1p(fund_liquidity['number_of_investors'].fillna(0))
    )
    
    # Min-max normalize liquidity scores to 0-1
    min_liq = fund_liquidity['liquidity_score'].min()
    max_liq = fund_liquidity['liquidity_score'].max()
    if max_liq > min_liq:
        fund_liquidity['liquidity_normalized'] = (
            (fund_liquidity['liquidity_score'] - min_liq) / (max_liq - min_liq)
        )
    else:
        fund_liquidity['liquidity_normalized'] = 0.5  # Default if all same
    
    liquidity_dict = dict(zip(fund_liquidity['code'], fund_liquidity['liquidity_normalized']))
    
    # Prepare results list - store raw components first
    portfolio_components = []
    
    # Calculate all components for all portfolios first
    for _, portfolio in portfolios_df.iterrows():
        portfolio_id = portfolio['id']
        
        # Get positions for this portfolio
        portfolio_positions = positions_df[positions_df['portfolio_id'] == portfolio_id]
        
        if portfolio_positions.empty:
            context.log.warning(f"Portfolio {portfolio_id} has no positions, skipping")
            continue
        
        # Get fund codes and weights
        fund_codes = portfolio_positions['fund_code'].tolist()
        weights_dict = dict(zip(portfolio_positions['fund_code'], portfolio_positions['weight']))
        weights_array = np.array([weights_dict[code] for code in fund_codes])
        
        # Normalize weights to sum to 1.0
        weights_array = weights_array / weights_array.sum()
        
        # Get price data for funds in this portfolio
        portfolio_prices = prices_df[prices_df['code'].isin(fund_codes)].copy()
        
        if portfolio_prices.empty:
            context.log.warning(f"No price data for funds in portfolio {portfolio_id}, skipping")
            continue
        
        # Create pivot table: date as index, fund_code as columns, return as values
        returns_pivot = portfolio_prices.pivot_table(
            index='date',
            columns='code',
            values='return',
            aggfunc='first'
        )
        
        # Align columns with fund_codes order
        returns_pivot = returns_pivot.reindex(columns=fund_codes)
        # Drop rows where any fund has missing data (pairwise complete)
        returns_pivot = returns_pivot.dropna()
        
        if len(returns_pivot) < 30:
            context.log.warning(f"Portfolio {portfolio_id} has insufficient data ({len(returns_pivot)} days), skipping")
            continue
        
        # 1. MARKOWITZ-LITE VOLATILITY
        # Compute covariance matrix (pandas handles NaNs pairwise)
        cov_matrix = returns_pivot.cov().values  # Shape: (n_funds, n_funds)
        
        # Portfolio variance: σ²_p = w^T Σ w
        portfolio_variance = np.dot(weights_array, np.dot(cov_matrix, weights_array))
        markowitz_vol = np.sqrt(max(0, portfolio_variance))  # Ensure non-negative
        
        # 2. CONCENTRATION PENALTY - Herfindahl Index
        herfindahl = np.sum(weights_array ** 2)
        
        # 3. MAX DRAWDOWN
        # Calculate portfolio daily returns
        portfolio_returns = returns_pivot.dot(weights_array)
        
        # Build cumulative curve: C_t = ∏(1 + r_p,t)
        cumulative = (1 + portfolio_returns).cumprod()
        
        # Compute drawdown: 1 - C_t / C_t.cummax()
        running_max = cumulative.cummax()
        drawdown = 1 - (cumulative / running_max)
        max_drawdown = float(drawdown.max())
        
        # 4. LIQUIDITY PENALTY - Vectorized
        # Portfolio liquidity penalty = Σ w_i (1 - L_i~)
        liquidity_scores = np.array([liquidity_dict.get(code, 0.5) for code in fund_codes])
        liquidity_penalty = np.dot(weights_array, 1 - liquidity_scores)
        
        # Store raw components (will normalize later)
        portfolio_components.append({
            'portfolio_id': portfolio_id,
            'markowitz_vol': markowitz_vol,
            'herfindahl': herfindahl,
            'max_drawdown': max_drawdown,
            'liquidity_penalty': liquidity_penalty
        })
    
    if not portfolio_components:
        context.log.warning("No portfolio components calculated")
        return
    
    # Convert to DataFrame for normalization
    components_df = pd.DataFrame(portfolio_components)
    
    # Normalize each component to 0-1 using percentile (rank-based normalization)
    # This ensures fair weighting regardless of scale differences
    components_df['vol_percentile'] = components_df['markowitz_vol'].rank(pct=True)
    components_df['herfindahl_percentile'] = components_df['herfindahl'].rank(pct=True)
    components_df['mdd_percentile'] = components_df['max_drawdown'].rank(pct=True)
    components_df['liq_percentile'] = components_df['liquidity_penalty'].rank(pct=True)
    
    # Combine normalized components with weights
    components_df['risk_score'] = (
        0.6 * components_df['vol_percentile'] +
        0.2 * components_df['herfindahl_percentile'] +
        0.1 * components_df['mdd_percentile'] +
        0.1 * components_df['liq_percentile']
    )
    
    # Prepare results for database
    risk_results = []
    for _, row in components_df.iterrows():
        risk_results.append({
            'portfolio_id': row['portfolio_id'],
            'date': date.today(),
            'risk_score': round(row['risk_score'], 6),
            'risk': None  # Will classify by quantiles after all portfolios calculated
        })
        
        context.log.info(
            f"Portfolio {row['portfolio_id']}: risk_score={row['risk_score']:.6f} "
            f"(vol_p={row['vol_percentile']:.3f}, H_p={row['herfindahl_percentile']:.3f}, "
            f"MDD_p={row['mdd_percentile']:.3f}, liq_p={row['liq_percentile']:.3f})"
        )
    
    if not risk_results:
        context.log.warning("No risk scores calculated")
        return
    
        # Classify by fixed thresholds (since risk_score is already 0-1 from percentile normalization)
    risk_df = pd.DataFrame(risk_results)
    
    # Fixed thresholds for stable labels (risk_score is 0-1 after percentile normalization)
    q33 = 0.33
    q67 = 0.67
    
    # Classify: LOW (bottom 33%), MEDIUM (middle 33%), HIGH (top 33%)
    risk_df['risk'] = risk_df['risk_score'].apply(
        lambda x: 'LOW' if x < q33 else ('MEDIUM' if x < q67 else 'HIGH')
    )
    
    context.log.info(f"Risk classification: LOW threshold < {q33:.3f}, MEDIUM < {q67:.3f}, HIGH >= {q67:.3f}")
    
    # Upsert into database
    risk_df[['portfolio_id', 'date', 'risk_score', 'risk']].to_sql(
        'portfolio_risk_scores_temp', engine, if_exists='replace', index=False, method='multi'
    )
    
    upsert_sql = """
    INSERT INTO portfolio_risk_scores (portfolio_id, date, risk_score, risk)
    SELECT portfolio_id, date, risk_score, risk
    FROM portfolio_risk_scores_temp
    ON CONFLICT (portfolio_id, date) 
    DO UPDATE SET 
        risk_score = EXCLUDED.risk_score,
        risk = EXCLUDED.risk;
    
    DROP TABLE portfolio_risk_scores_temp;
    """
    with engine.connect() as conn:
        conn.execute(text(upsert_sql))
        conn.commit()
    
    context.log.info(f"Successfully stored {len(risk_df)} portfolio risk scores")


@dg.asset(
    deps=[fund_prices]  # Depends on fund_prices being available
)
def fund_performance_metrics(
    context: dg.AssetExecutionContext,
    postgres: resources.PostgresResource,
) -> None:
    """
    Evaluates fund performance compared to peers using a Sharpe-like metric.

    For each fund:
      - compute 90-day cumulative return and volatility
      - compute sharpe_like = total_return / volatility
      - compare to peers (same category -> main_category -> all funds)
      - assign performance_score = peer percentile (0..1)
      - mark poor performers conservatively using percentile + robust z-score
    """
    engine = postgres.get_engine()
    context.log.info("Calculating improved fund performance metrics...")

    # -----------------------------
    # 1. Load labels (categories)
    # -----------------------------
    labels_query = """
        SELECT code, category, main_category
        FROM fund_labels
    """
    labels_df = pd.read_sql(labels_query, engine)

    # -----------------------------
    # 2. Load prices (last ~120 days)
    # -----------------------------
    min_date = date.today() - pd.Timedelta(days=120)
    prices_query = f"""
        SELECT date, code, price
        FROM fund_prices
        WHERE date >= '{min_date}'
        ORDER BY code, date
    """
    prices_df = pd.read_sql(prices_query, engine)

    if prices_df.empty:
        context.log.warning("No fund prices found in database")
        return

    prices_df["date"] = pd.to_datetime(prices_df["date"])
    prices_df = prices_df.sort_values(["code", "date"])

    # Daily returns per fund
    prices_df["return"] = prices_df.groupby("code")["price"].pct_change()
    prices_df = prices_df.dropna(subset=["return"])

    most_recent_date = prices_df["date"].max()
    window_start = most_recent_date - pd.Timedelta(days=90)

    window_returns = prices_df[
        (prices_df["date"] > window_start) & (prices_df["date"] <= most_recent_date)
    ].copy()

    if window_returns.empty:
        context.log.warning("No data in 90-day window for fund performance")
        return

    # -----------------------------------------
    # 3. Compute Sharpe-like metric per fund
    # -----------------------------------------
    fund_rows = []

    for fund_code, grp in window_returns.groupby("code"):
        grp = grp.sort_values("date")
        if len(grp) < 30:  # require some history
            continue

        ret_series = grp["return"].values
        # Total 90-day return via compounding
        total_return = float(np.prod(1.0 + ret_series) - 1.0)
        vol = float(np.std(ret_series, ddof=1))

        if vol <= 0:
            # Flat price, no useful Sharpe-like signal
            continue

        sharpe_like = total_return / (vol + 1e-9)

        # Fetch labels
        label_row = labels_df[labels_df["code"] == fund_code]
        category = None
        main_category = None
        if not label_row.empty:
            category = label_row.iloc[0]["category"]
            main_category = label_row.iloc[0]["main_category"]

        fund_rows.append(
            {
                "fund_code": fund_code,
                "sharpe_like": sharpe_like,
                "total_return_90d": total_return,
                "vol_90d": vol,
                "category": category if pd.notna(category) else None,
                "main_category": main_category if pd.notna(main_category) else None,
            }
        )

    if not fund_rows:
        context.log.warning("No funds had sufficient data for performance metrics")
        return

    perf_df = pd.DataFrame(fund_rows)

    # -----------------------------------------
    # 4. Peer grouping + percentile + z-score
    # -----------------------------------------
    cat_counts = perf_df["category"].value_counts(dropna=True)
    main_cat_counts = perf_df["main_category"].value_counts(dropna=True)

    results = []
    poor_count = 0

    for idx, row in perf_df.iterrows():
        fund_code = row["fund_code"]
        sharpe_like = row["sharpe_like"]
        cat = row["category"]
        main_cat = row["main_category"]

        # Choose peer group
        peers = None
        peer_label = None

        if cat is not None and cat in cat_counts and cat_counts[cat] >= 5:
            peers = perf_df[perf_df["category"] == cat]
            peer_label = cat
        elif main_cat is not None and main_cat in main_cat_counts and main_cat_counts[main_cat] >= 5:
            peers = perf_df[perf_df["main_category"] == main_cat]
            peer_label = main_cat
        else:
            peers = perf_df
            peer_label = "ALL"

        # Percentile rank within peers (0..1)
        ranks = peers["sharpe_like"].rank(pct=True)
        # Align rank with current fund
        peer_rank = float(
            ranks.loc[peers["fund_code"] == fund_code].iloc[0]
        )  # in (0,1]

        performance_score = peer_rank  # already 0..1

        # Robust z-score using median & MAD
        median = float(peers["sharpe_like"].median())
        mad = float(np.median(np.abs(peers["sharpe_like"] - median)))
        robust_sigma = 1.4826 * mad + 1e-9
        z = (sharpe_like - median) / robust_sigma

        # Conservative poor-performer rule
        is_poor = (performance_score <= 0.10) and (z <= -1.5)
        confidence = float(min(1.0, abs(z) / 3.0)) if is_poor else None

        if is_poor:
            poor_count += 1

        results.append(
            {
                "fund_code": fund_code,
                "performance_score": round(performance_score, 6),
                "peer_category": peer_label,
                "is_poor_performer": bool(is_poor),
                "confidence": confidence,
            }
        )

    results_df = pd.DataFrame(results)
    results_df["date"] = most_recent_date.date()

    context.log.info(
        f"Calculated improved performance for {len(results_df)} funds, "
        f"poor performers flagged: {poor_count}"
    )

    # -----------------------------------------
    # 5. Upsert into fund_performance_metrics
    # -----------------------------------------
    results_df.to_sql(
        "fund_performance_metrics_temp",
        engine,
        if_exists="replace",
        index=False,
        method="multi",
    )

    upsert_sql = """
    INSERT INTO fund_performance_metrics
        (fund_code, date, performance_score, peer_category, is_poor_performer, confidence)
    SELECT fund_code, date, performance_score, peer_category, is_poor_performer, confidence
    FROM fund_performance_metrics_temp
    ON CONFLICT (fund_code, date)
    DO UPDATE SET
        performance_score = EXCLUDED.performance_score,
        peer_category = EXCLUDED.peer_category,
        is_poor_performer = EXCLUDED.is_poor_performer,
        confidence = EXCLUDED.confidence;

    DROP TABLE fund_performance_metrics_temp;
    """
    with engine.connect() as conn:
        conn.execute(text(upsert_sql))
        conn.commit()

    context.log.info(
        f"Successfully stored {len(results_df)} improved fund performance metrics "
        f"for date {most_recent_date.date()}"
    )
