# Mutual Fund Analytics - Data Dictionary

This document outlines the SQLite schema, column data types, key constraints, business definitions, and sources for the database tables loaded on Day 2.

---

## 1. Dimension Tables

### Table: `dim_fund`
Stores metadata and details about the mutual fund schemes.
* **Source Raw File**: `01_fund_master.csv`

| Column Name | Data Type | Constraint | Description |
| :--- | :--- | :--- | :--- |
| `amfi_code` | INTEGER | PRIMARY KEY | Unique 6-digit identifier code issued by AMFI. |
| `fund_house` | TEXT | NOT NULL | Asset Management Company (AMC) name. |
| `scheme_name` | TEXT | NOT NULL | Full name of the mutual fund scheme. |
| `category` | TEXT | NOT NULL | Broader category classification (e.g., Equity, Debt). |
| `sub_category` | TEXT | - | Specific fund type (e.g., Large Cap, Small Cap, Gilt). |
| `plan` | TEXT | - | Growth plan option (Direct or Regular). |
| `launch_date` | TEXT | - | Date when the fund scheme was launched. |
| `benchmark` | TEXT | - | Benchmark index name against which performance is compared. |
| `expense_ratio_pct` | REAL | - | Annual fund management fee expressed as a percentage. |
| `exit_load_pct` | REAL | - | Fee charged when redeeming units early. |
| `min_sip_amount` | REAL | - | Minimum amount required for a monthly SIP. |
| `min_lumpsum_amount`| REAL | - | Minimum amount required for a one-time purchase. |
| `fund_manager` | TEXT | - | Primary manager handling the fund portfolio. |
| `risk_category` | TEXT | - | Standard risk rating level (e.g., Moderate, Very High). |
| `sebi_category_code`| TEXT | - | SEBI internal category code (e.g., EC01, EC03). |

---

### Table: `dim_date`
Dynamically generated calendar dates table for temporal analytical grouping.
* **Source**: Generated dynamically from dates in NAV, Transaction, and Benchmark datasets.

| Column Name | Data Type | Constraint | Description |
| :--- | :--- | :--- | :--- |
| `date_id` | TEXT | PRIMARY KEY | Calendar date in YYYY-MM-DD string format. |
| `date` | TEXT | NOT NULL | Duplicate representation of date_id. |
| `year` | INTEGER | NOT NULL | Calendar year (e.g., 2024). |
| `month` | INTEGER | NOT NULL | Calendar month index (1 to 12). |
| `quarter` | INTEGER | NOT NULL | Calendar quarter index (1 to 4). |
| `is_weekday` | INTEGER | NOT NULL | Flag (1 for Monday-Friday, 0 for Saturday-Sunday). |

---

## 2. Fact Tables

### Table: `fact_nav`
Daily Net Asset Value (NAV) price tracking records.
* **Source Raw File**: `02_nav_history.csv`

| Column Name | Data Type | Constraint | Description |
| :--- | :--- | :--- | :--- |
| `amfi_code` | INTEGER | FK (dim_fund) | Scheme ID. Combined with date to form composite PK. |
| `date` | TEXT | FK (dim_date) | Valuation date. Combined with amfi_code to form PK. |
| `nav` | REAL | NOT NULL | Net Asset Value (unit price in INR). |
| `daily_return_pct` | REAL | - | Computed daily percentage return of the NAV. |

---

### Table: `fact_transactions`
Individual investor transactions (SIPs, Lumpsum, and Redemptions).
* **Source Raw File**: `08_investor_transactions.csv`

| Column Name | Data Type | Constraint | Description |
| :--- | :--- | :--- | :--- |
| `tx_id` | INTEGER | PRIMARY KEY | Autoincrementing transaction ID. |
| `investor_id` | TEXT | NOT NULL | Unique identifier for each investor (e.g., INV000001). |
| `amfi_code` | INTEGER | FK (dim_fund) | Scheme code where transaction occurred. |
| `transaction_date` | TEXT | FK (dim_date) | Date of transaction. |
| `transaction_type` | TEXT | NOT NULL | Action type (SIP, Lumpsum, Redemption). |
| `amount_inr` | REAL | NOT NULL | Transaction amount in Indian Rupees. |
| `state` | TEXT | - | State of residence of the investor. |
| `city` | TEXT | - | City of residence of the investor. |
| `city_tier` | TEXT | - | Classification of city tier (T30 or B30). |
| `age_group` | TEXT | - | Age bracket of the investor. |
| `gender` | TEXT | - | Gender of the investor. |
| `annual_income_lakh`| REAL | - | Annual income of the investor in lakhs. |
| `payment_mode` | TEXT | - | Mode of payment (UPI, Net Banking, Mandate, Cheque). |
| `kyc_status` | TEXT | - | KYC compliance status (Verified or Pending). |

---

### Table: `fact_performance`
Calculated fund performance statistics and ratings.
* **Source Raw File**: `07_scheme_performance.csv`

| Column Name | Data Type | Constraint | Description |
| :--- | :--- | :--- | :--- |
| `amfi_code` | INTEGER | PRIMARY KEY | Scheme code. Maps to dim_fund. |
| `scheme_name` | TEXT | NOT NULL | Name of the fund scheme. |
| `fund_house` | TEXT | NOT NULL | Asset management house name. |
| `category` | TEXT | - | Fund category. |
| `plan` | TEXT | - | Scheme plan type (Regular/Direct). |
| `return_1yr_pct` | REAL | - | 1-year absolute performance return percentage. |
| `return_3yr_pct` | REAL | - | 3-year compound annual growth rate (CAGR). |
| `return_5yr_pct` | REAL | - | 5-year compound annual growth rate (CAGR). |
| `benchmark_3yr_pct` | REAL | - | 3-year CAGR of the fund's benchmark index. |
| `alpha` | REAL | - | Return outperformance relative to benchmark. |
| `beta` | REAL | - | Volatility sensitivity relative to benchmark. |
| `sharpe_ratio` | REAL | - | Risk-adjusted return measure (Sharpe). |
| `sortino_ratio` | REAL | - | Downside risk-adjusted return measure (Sortino). |
| `std_dev_ann_pct` | REAL | - | Annualized standard deviation of returns. |
| `max_drawdown_pct` | REAL | - | Worst peak-to-trough drop percentage. |
| `aum_crore` | REAL | - | Assets Under Management in crores INR. |
| `expense_ratio_pct` | REAL | - | Total expense ratio percentage. |
| `morningstar_rating`| INTEGER | - | Morningstar star rating rating (1 to 5). |
| `risk_grade` | TEXT | - | Assigned risk profile grade. |
| `negative_sharpe` | INTEGER | - | Flag indicating negative Sharpe ratio (1=True, 0=False). |

---

### Table: `fact_aum`
Historical Assets Under Management (AUM) trends per fund house.
* **Source Raw File**: `03_aum_by_fund_house.csv`

| Column Name | Data Type | Constraint | Description |
| :--- | :--- | :--- | :--- |
| `date` | TEXT | FK (dim_date) | Report date. Combined with fund_house to form PK. |
| `fund_house` | TEXT | NOT NULL | Fund house name. Combined with date to form PK. |
| `aum_lakh_crore` | REAL | - | AUM represented in lakh crores. |
| `aum_crore` | REAL | - | AUM represented in crores. |
| `num_schemes` | INTEGER | - | Total active schemes managed by the AMC. |

---

### Table: `fact_portfolio`
Portfolio equity holdings and sector weightings.
* **Source Raw File**: `09_portfolio_holdings.csv`

| Column Name | Data Type | Constraint | Description |
| :--- | :--- | :--- | :--- |
| `amfi_code` | INTEGER | FK (dim_fund) | Scheme code. Part of composite PK. |
| `stock_symbol` | TEXT | NOT NULL | Exchange ticker symbol of holding. Part of PK. |
| `stock_name` | TEXT | NOT NULL | Name of the company. |
| `sector` | TEXT | - | Industry sector (e.g., Banking, Utilities). |
| `weight_pct` | REAL | - | Holding portfolio weight percentage. |
| `market_value_cr` | REAL | - | Market value of holding in crores. |
| `current_price_inr` | REAL | - | Trading price of stock in INR. |
| `portfolio_date` | TEXT | FK (dim_date) | Date of portfolio snapshot. Part of PK. |

---

### Table: `fact_benchmarks`
Daily benchmark index pricing.
* **Source Raw File**: `10_benchmark_indices.csv`

| Column Name | Data Type | Constraint | Description |
| :--- | :--- | :--- | :--- |
| `date` | TEXT | FK (dim_date) | Price date. Combined with index_name to form PK. |
| `index_name` | TEXT | NOT NULL | Name of index (e.g., NIFTY50, NIFTY100). Part of PK. |
| `close_value` | REAL | - | Daily closing index price. |

---

### Table: `fact_sip_industry`
Monthly aggregated industry-wide SIP flow stats.
* **Source Raw File**: `04_monthly_sip_inflows.csv`

| Column Name | Data Type | Constraint | Description |
| :--- | :--- | :--- | :--- |
| `month` | TEXT | PRIMARY KEY | Month of record (YYYY-MM). |
| `sip_inflow_crore` | REAL | - | Monthly SIP inflow in crores. |
| `active_sip_accounts_crore` | REAL | - | Active contributing accounts in crores. |
| `new_sip_accounts_lakh` | REAL | - | New SIP accounts registered in lakhs. |
| `sip_aum_lakh_crore` | REAL | - | Overall SIP AUM in lakh crores. |
| `yoy_growth_pct` | REAL | - | YoY growth of monthly inflows. |

---

### Table: `fact_category_inflows`
Industry inflows aggregated by mutual fund categories.
* **Source Raw File**: `05_category_inflows.csv`

| Column Name | Data Type | Constraint | Description |
| :--- | :--- | :--- | :--- |
| `month` | TEXT | - | Month of inflows (YYYY-MM). Part of PK. |
| `category` | TEXT | NOT NULL | Mutual fund sub-category. Part of PK. |
| `net_inflow_crore` | REAL | - | Net inflows for the category in crores. |

---

### Table: `fact_folio_count`
Mutual fund industry folios count by broad class.
* **Source Raw File**: `06_industry_folio_count.csv`

| Column Name | Data Type | Constraint | Description |
| :--- | :--- | :--- | :--- |
| `month` | TEXT | PRIMARY KEY | Month of record (YYYY-MM). |
| `total_folios_crore` | REAL | - | Total mutual fund accounts in crores. |
| `equity_folios_crore` | REAL | - | Equity accounts in crores. |
| `debt_folios_crore` | REAL | - | Debt accounts in crores. |
| `hybrid_folios_crore` | REAL | - | Hybrid accounts in crores. |
| `others_folios_crore` | REAL | - | Other accounts (liquid, cash) in crores. |