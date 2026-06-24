import os
import sqlite3
import pandas as pd
from sqlalchemy import create_engine

db_file = "bluestock_mf.db"
if os.path.exists(db_file):
    os.remove(db_file)

engine = create_engine(f"sqlite:///{db_file}")

# Initialize schema
with sqlite3.connect(db_file) as conn:
    with open("sql/schema.sql", "r") as f:
        conn.executescript(f.read())

processed = "data/processed"

dfs = {
    "dim_fund": pd.read_csv(f"{processed}/clean_fund_master.csv"),
    "fact_nav": pd.read_csv(f"{processed}/clean_nav.csv"),
    "fact_transactions": pd.read_csv(f"{processed}/clean_transactions.csv"),
    "fact_performance": pd.read_csv(f"{processed}/clean_performance.csv"),
    "fact_aum": pd.read_csv(f"{processed}/clean_aum_by_fund_house.csv"),
    "fact_portfolio": pd.read_csv(f"{processed}/clean_portfolio_holdings.csv"),
    "fact_benchmarks": pd.read_csv(f"{processed}/clean_benchmark_indices.csv"),
    "fact_sip_industry": pd.read_csv(f"{processed}/clean_monthly_sip_inflows.csv"),
    "fact_category_inflows": pd.read_csv(f"{processed}/clean_category_inflows.csv"),
    "fact_folio_count": pd.read_csv(f"{processed}/clean_industry_folio_count.csv")
}

# Generate dim_date dynamically
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

print("Database loaded successfully.")