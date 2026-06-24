-- 1. Top 5 funds by AUM
SELECT amfi_code, scheme_name, fund_house, aum_crore
FROM fact_performance
ORDER BY aum_crore DESC
LIMIT 5;

-- 2. Average NAV per month for SBI Bluechip Regular (amfi_code: 119551)
SELECT d.year, d.month, AVG(n.nav) AS avg_nav
FROM fact_nav n
JOIN dim_date d ON n.date = d.date_id
WHERE n.amfi_code = 119551
GROUP BY d.year, d.month
ORDER BY d.year, d.month;

-- 3. SIP Inflow YoY Growth (Yearly comparison)
WITH yearly_inflows AS (
    SELECT SUBSTR(month, 1, 4) AS year, SUM(sip_inflow_crore) AS total_inflow
    FROM fact_sip_industry
    GROUP BY year
)
SELECT 
    curr.year, 
    curr.total_inflow,
    prev.total_inflow AS prev_year_inflow,
    ROUND(((curr.total_inflow - prev.total_inflow) * 100.0 / prev.total_inflow), 2) AS yoy_growth_pct
FROM yearly_inflows curr
LEFT JOIN yearly_inflows prev ON CAST(curr.year AS INTEGER) = CAST(prev.year AS INTEGER) + 1
ORDER BY curr.year;

-- 4. Total transactions and total amount invested by state
SELECT state, COUNT(*) AS total_transactions, SUM(amount_inr) AS total_amount_invested
FROM fact_transactions
GROUP BY state
ORDER BY total_amount_invested DESC;

-- 5. Active funds with an expense ratio less than 1%
SELECT amfi_code, scheme_name, fund_house, expense_ratio_pct
FROM dim_fund
WHERE expense_ratio_pct < 1.0
ORDER BY expense_ratio_pct ASC;

-- 6. Average transaction amount by age group and gender (Cohort Analysis)
SELECT age_group, gender, COUNT(*) AS tx_count, AVG(amount_inr) AS avg_tx_amount
FROM fact_transactions
GROUP BY age_group, gender
ORDER BY age_group, gender;

-- 7. Top 5 stocks by average weight % across all portfolios
SELECT stock_symbol, stock_name, AVG(weight_pct) AS avg_weight_pct
FROM fact_portfolio
GROUP BY stock_symbol, stock_name
ORDER BY avg_weight_pct DESC
LIMIT 5;

-- 8. Risk-return profile (average daily returns and variance)
SELECT f.scheme_name, AVG(n.daily_return_pct) AS avg_daily_return,
       (AVG(n.daily_return_pct * n.daily_return_pct) - AVG(n.daily_return_pct) * AVG(n.daily_return_pct)) AS variance
FROM fact_nav n
JOIN dim_fund f ON n.amfi_code = f.amfi_code
GROUP BY f.scheme_name;

-- 9. Monthly Nifty 50 close value vs Monthly SIP Inflows
WITH monthly_nifty AS (
    SELECT SUBSTR(date, 1, 7) AS month, AVG(close_value) AS avg_nifty_close
    FROM fact_benchmarks
    WHERE index_name = 'NIFTY50'
    GROUP BY month
)
SELECT s.month, s.sip_inflow_crore, ROUND(n.avg_nifty_close, 2) AS avg_nifty_close
FROM fact_sip_industry s
JOIN monthly_nifty n ON s.month = n.month
ORDER BY s.month;

-- 10. Funds with negative Sharpe ratio ranked by Max Drawdown (High risk)
SELECT amfi_code, scheme_name, fund_house, sharpe_ratio, max_drawdown_pct, risk_grade
FROM fact_performance
WHERE negative_sharpe = 1
ORDER BY max_drawdown_pct ASC;