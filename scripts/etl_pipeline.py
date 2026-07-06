from pathlib import Path
import pandas as pd
import os
import sqlite3
from sqlalchemy import create_engine

raw_dir = Path("./data/raw")
processed_dir = Path("./data/processed")
processed_dir.mkdir(parents=True, exist_ok=True)

db_dir = Path("./data/db")
db_dir.mkdir(parents=True, exist_ok=True)
db_file = db_dir / "bluestock_mf.db"

print("1. Cleaning fund master...")
fm = pd.read_csv(raw_dir / "01_fund_master.csv")
fm = fm.drop_duplicates()
string_cols = ['fund_house', 'scheme_name', 'category', 'sub_category', 'plan', 'benchmark', 'fund_manager', 'risk_category']
for col in string_cols:
    if col in fm.columns:
        fm[col] = fm[col].astype(str).str.strip()
fm.to_csv(processed_dir / "clean_fund_master.csv", index=False)

print("2. Cleaning NAV history...")
nav = pd.read_csv(raw_dir / "02_nav_history.csv")
nav['date'] = pd.to_datetime(nav['date'])
nav = nav.drop_duplicates(subset=['amfi_code', 'date'])
all_dates = pd.date_range(start=nav['date'].min(), end=nav['date'].max(), freq='D')
cleaned_nav_list = []
for code, group in nav.groupby('amfi_code'):
    group = group.set_index('date').reindex(all_dates)
    group['amfi_code'] = code
    group['nav'] = group['nav'].ffill()
    group = group.dropna(subset=['nav'])
    group = group.reset_index().rename(columns={'index': 'date'})
    group = group.sort_values('date')
    group['daily_return_pct'] = group['nav'].pct_change() * 100
    group['daily_return_pct'] = group['daily_return_pct'].fillna(0.0)
    cleaned_nav_list.append(group)
clean_nav = pd.concat(cleaned_nav_list).sort_values(by=['amfi_code', 'date'])
clean_nav.to_csv(processed_dir / "clean_nav.csv", index=False)

print("3. Cleaning remaining dimension/fact tables...")
for filename, name in [
    ("03_aum_by_fund_house.csv", "clean_aum_by_fund_house.csv"),
    ("04_monthly_sip_inflows.csv", "clean_monthly_sip_inflows.csv"),
    ("05_category_inflows.csv", "clean_category_inflows.csv"),
    ("06_industry_folio_count.csv", "clean_industry_folio_count.csv"),
    ("09_portfolio_holdings.csv", "clean_portfolio_holdings.csv"),
    ("10_benchmark_indices.csv", "clean_benchmark_indices.csv"),
]:
    df = pd.read_csv(raw_dir / filename)
    date_col = 'date' if 'date' in df.columns else 'month' if 'month' in df.columns else 'portfolio_date'
    df[date_col] = df[date_col].astype(str).str.strip()
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].astype(str).str.strip()
    df = df.drop_duplicates()
    df.to_csv(processed_dir / name, index=False)

print("4. Cleaning performance...")
perf = pd.read_csv(raw_dir / "07_scheme_performance.csv")
for col in ['scheme_name', 'fund_house', 'category', 'plan', 'risk_grade']:
    perf[col] = perf[col].astype(str).str.strip()
perf['negative_sharpe'] = perf['sharpe_ratio'] < 0
perf = perf.drop_duplicates()
perf.to_csv(processed_dir / "clean_performance.csv", index=False)

print("5. Cleaning transactions...")
tx = pd.read_csv(raw_dir / "08_investor_transactions.csv")
tx['transaction_date'] = pd.to_datetime(tx['transaction_date'])
for col in ['transaction_type', 'kyc_status', 'state', 'city', 'city_tier', 'age_group', 'gender', 'payment_mode']:
    tx[col] = tx[col].astype(str).str.strip()
tx = tx[tx['amount_inr'] > 0]
tx = tx.drop_duplicates()
tx.to_csv(processed_dir / "clean_transactions.csv", index=False)

print("6. Initializing SQLite Schema and Loading Database...")
if db_file.exists():
    os.remove(db_file)

engine = create_engine(f"sqlite:///{db_file}")

with sqlite3.connect(db_file) as conn:
    with open("sql/schema.sql", "r") as f:
        conn.executescript(f.read())

dfs = {
    "dim_fund": pd.read_csv(processed_dir / "clean_fund_master.csv"),
    "fact_nav": pd.read_csv(processed_dir / "clean_nav.csv"),
    "fact_transactions": pd.read_csv(processed_dir / "clean_transactions.csv"),
    "fact_performance": pd.read_csv(processed_dir / "clean_performance.csv"),
    "fact_aum": pd.read_csv(processed_dir / "clean_aum_by_fund_house.csv"),
    "fact_portfolio": pd.read_csv(processed_dir / "clean_portfolio_holdings.csv"),
    "fact_benchmarks": pd.read_csv(processed_dir / "clean_benchmark_indices.csv"),
    "fact_sip_industry": pd.read_csv(processed_dir / "clean_monthly_sip_inflows.csv"),
    "fact_category_inflows": pd.read_csv(processed_dir / "clean_category_inflows.csv"),
    "fact_folio_count": pd.read_csv(processed_dir / "clean_industry_folio_count.csv")
}

nav_dates = pd.to_datetime(dfs["fact_nav"]["date"])
tx_dates = pd.to_datetime(dfs["fact_transactions"]["transaction_date"])
bench_dates = pd.to_datetime(dfs["fact_benchmarks"]["date"])

unique_dates = pd.concat([nav_dates, tx_dates, bench_dates]).dropna().unique()
date_df = pd.DataFrame({"date": unique_dates})
date_df["date_id"] = date_df["date"].dt.strftime("%Y-%m-%d")
date_df["year"] = date_df["date"].dt.year
date_df["month"] = date_df["date"].dt.month
date_df["quarter"] = date_df["date"].dt.quarter
date_df["is_weekday"] = date_df["date"].dt.dayofweek.isin(range(5)).astype(int)

dim_date = date_df[["date_id", "year", "month", "quarter", "is_weekday"]].copy()
dim_date["date"] = dim_date["date_id"]
dim_date = dim_date[["date_id", "date", "year", "month", "quarter", "is_weekday"]].drop_duplicates().sort_values("date_id")

with engine.connect() as conn:
    dim_date.to_sql("dim_date", conn, if_exists="append", index=False)
    dfs["dim_fund"].to_sql("dim_fund", conn, if_exists="append", index=False)
    for table_name, df in dfs.items():
        if table_name != "dim_fund":
            df.to_sql(table_name, conn, if_exists="append", index=False)

print("ETL complete. SQLite database generated.")
