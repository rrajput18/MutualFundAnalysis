-- Enable foreign key support
PRAGMA foreign_keys = ON;

-- 1. DIMENSION TABLES

-- Fund Dimension Table
CREATE TABLE IF NOT EXISTS dim_fund (
    amfi_code INTEGER PRIMARY KEY,
    fund_house TEXT NOT NULL,
    scheme_name TEXT NOT NULL,
    category TEXT NOT NULL,
    sub_category TEXT,
    plan TEXT,
    launch_date TEXT,
    benchmark TEXT,
    expense_ratio_pct REAL,
    exit_load_pct REAL,
    min_sip_amount REAL,
    min_lumpsum_amount REAL,
    fund_manager TEXT,
    risk_category TEXT,
    sebi_category_code TEXT
);

-- Date Dimension Table
CREATE TABLE IF NOT EXISTS dim_date (
    date_id TEXT PRIMARY KEY, -- YYYY-MM-DD
    date TEXT NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    is_weekday INTEGER NOT NULL
);


-- 2. FACT TABLES

-- NAV Price History
CREATE TABLE IF NOT EXISTS fact_nav (
    amfi_code INTEGER NOT NULL,
    date TEXT NOT NULL,
    nav REAL NOT NULL,
    daily_return_pct REAL,
    PRIMARY KEY (amfi_code, date),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (date) REFERENCES dim_date(date_id)
);

-- Investor Transactions
CREATE TABLE IF NOT EXISTS fact_transactions (
    tx_id INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id TEXT NOT NULL,
    amfi_code INTEGER NOT NULL,
    transaction_date TEXT NOT NULL,
    transaction_type TEXT NOT NULL, -- SIP, Lumpsum, Redemption
    amount_inr REAL NOT NULL,
    state TEXT,
    city TEXT,
    city_tier TEXT,
    age_group TEXT,
    gender TEXT,
    annual_income_lakh REAL,
    payment_mode TEXT,
    kyc_status TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (transaction_date) REFERENCES dim_date(date_id)
);

-- Scheme Performance Metrics
CREATE TABLE IF NOT EXISTS fact_performance (
    amfi_code INTEGER PRIMARY KEY,
    scheme_name TEXT NOT NULL,
    fund_house TEXT NOT NULL,
    category TEXT,
    plan TEXT,
    return_1yr_pct REAL,
    return_3yr_pct REAL,
    return_5yr_pct REAL,
    benchmark_3yr_pct REAL,
    alpha REAL,
    beta REAL,
    sharpe_ratio REAL,
    sortino_ratio REAL,
    std_dev_ann_pct REAL,
    max_drawdown_pct REAL,
    aum_crore REAL,
    expense_ratio_pct REAL,
    morningstar_rating INTEGER,
    risk_grade TEXT,
    negative_sharpe INTEGER,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

-- AUM by Fund House
CREATE TABLE IF NOT EXISTS fact_aum (
    date TEXT NOT NULL,
    fund_house TEXT NOT NULL,
    aum_lakh_crore REAL,
    aum_crore REAL,
    num_schemes INTEGER,
    PRIMARY KEY (date, fund_house),
    FOREIGN KEY (date) REFERENCES dim_date(date_id)
);

-- Portfolio Holdings
CREATE TABLE IF NOT EXISTS fact_portfolio (
    amfi_code INTEGER NOT NULL,
    stock_symbol TEXT NOT NULL,
    stock_name TEXT NOT NULL,
    sector TEXT,
    weight_pct REAL,
    market_value_cr REAL,
    current_price_inr REAL,
    portfolio_date TEXT NOT NULL,
    PRIMARY KEY (amfi_code, stock_symbol, portfolio_date),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (portfolio_date) REFERENCES dim_date(date_id)
);

-- Benchmark Indices Daily Closing Value
CREATE TABLE IF NOT EXISTS fact_benchmarks (
    date TEXT NOT NULL,
    index_name TEXT NOT NULL,
    close_value REAL,
    PRIMARY KEY (date, index_name),
    FOREIGN KEY (date) REFERENCES dim_date(date_id)
);

-- Monthly SIP Inflows
CREATE TABLE IF NOT EXISTS fact_sip_industry (
    month TEXT PRIMARY KEY, -- YYYY-MM
    sip_inflow_crore REAL,
    active_sip_accounts_crore REAL,
    new_sip_accounts_lakh REAL,
    sip_aum_lakh_crore REAL,
    yoy_growth_pct REAL
);

-- Category Inflows
CREATE TABLE IF NOT EXISTS fact_category_inflows (
    month TEXT NOT NULL,
    category TEXT NOT NULL,
    net_inflow_crore REAL,
    PRIMARY KEY (month, category)
);

-- Industry Folio Count
CREATE TABLE IF NOT EXISTS fact_folio_count (
    month TEXT PRIMARY KEY,
    total_folios_crore REAL,
    equity_folios_crore REAL,
    debt_folios_crore REAL,
    hybrid_folios_crore REAL,
    others_folios_crore REAL
);

-- 3. INDEXES FOR PERFORMANCE OPTIMIZATION
CREATE INDEX IF NOT EXISTS idx_nav_amfi_date ON fact_nav(amfi_code, date);
CREATE INDEX IF NOT EXISTS idx_transactions_amfi ON fact_transactions(amfi_code);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON fact_transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_portfolio_amfi ON fact_portfolio(amfi_code);