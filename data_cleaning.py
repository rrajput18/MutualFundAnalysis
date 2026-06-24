from pathlib import Path
import pandas as pd

raw_dir = Path("./data/raw")
processed_dir = Path("./data/processed")
processed_dir.mkdir(parents=True, exist_ok=True)

print("Starting data cleaning...")

# 1. Clean Fund Master
print("Cleaning fund master...")
fm = pd.read_csv(raw_dir / "01_fund_master.csv")
fm = fm.drop_duplicates()
string_cols = ['fund_house', 'scheme_name', 'category', 'sub_category', 'plan', 'benchmark', 'fund_manager', 'risk_category']
for col in string_cols:
    if col in fm.columns:
        fm[col] = fm[col].astype(str).str.strip()
fm.to_csv(processed_dir / "clean_fund_master.csv", index=False)

# 2. Clean NAV History (Holidays/Weekends handling + Returns calculation)
print("Cleaning NAV history...")
nav = pd.read_csv(raw_dir / "02_nav_history.csv")
nav['date'] = pd.to_datetime(nav['date'])
nav = nav.drop_duplicates(subset=['amfi_code', 'date'])

# Forward fill NAV for holidays/weekends by reindexing to a full calendar date range
all_dates = pd.date_range(start=nav['date'].min(), end=nav['date'].max(), freq='D')

cleaned_nav_list = []
for code, group in nav.groupby('amfi_code'):
    group = group.set_index('date').reindex(all_dates)
    group['amfi_code'] = code
    group['nav'] = group['nav'].ffill()
    group = group.dropna(subset=['nav'])  # Remove leading NaNs before the launch date
    group = group.reset_index().rename(columns={'index': 'date'})
    
    # Calculate daily return percentage
    group = group.sort_values('date')
    group['daily_return_pct'] = group['nav'].pct_change() * 100
    group['daily_return_pct'] = group['daily_return_pct'].fillna(0.0)
    
    cleaned_nav_list.append(group)

clean_nav = pd.concat(cleaned_nav_list).sort_values(by=['amfi_code', 'date'])
clean_nav.to_csv(processed_dir / "clean_nav.csv", index=False)

# 3. Clean AUM
print("Cleaning AUM by fund house...")
aum = pd.read_csv(raw_dir / "03_aum_by_fund_house.csv")
aum['date'] = pd.to_datetime(aum['date'])
aum['fund_house'] = aum['fund_house'].str.strip()
aum = aum.drop_duplicates()
aum.to_csv(processed_dir / "clean_aum_by_fund_house.csv", index=False)

# 4. Clean Monthly SIP Inflows
print("Cleaning monthly SIP inflows...")
sip = pd.read_csv(raw_dir / "04_monthly_sip_inflows.csv")
sip['month'] = sip['month'].str.strip()
sip = sip.drop_duplicates()
sip.to_csv(processed_dir / "clean_monthly_sip_inflows.csv", index=False)

# 5. Clean Category Inflows
print("Cleaning category inflows...")
cat = pd.read_csv(raw_dir / "05_category_inflows.csv")
cat['month'] = cat['month'].str.strip()
cat['category'] = cat['category'].str.strip()
cat = cat.drop_duplicates()
cat.to_csv(processed_dir / "clean_category_inflows.csv", index=False)

# 6. Clean Industry Folio Count
print("Cleaning industry folio count...")
folios = pd.read_csv(raw_dir / "06_industry_folio_count.csv")
folios['month'] = folios['month'].str.strip()
folios = folios.drop_duplicates()
folios.to_csv(processed_dir / "clean_industry_folio_count.csv", index=False)

# 7. Clean Scheme Performance
print("Cleaning scheme performance...")
perf = pd.read_csv(raw_dir / "07_scheme_performance.csv")
for col in ['scheme_name', 'fund_house', 'category', 'plan', 'risk_grade']:
    perf[col] = perf[col].astype(str).str.strip()

perf['negative_sharpe'] = perf['sharpe_ratio'] < 0
perf = perf.drop_duplicates()
perf.to_csv(processed_dir / "clean_performance.csv", index=False)

# 8. Clean Investor Transactions
print("Cleaning investor transactions...")
tx = pd.read_csv(raw_dir / "08_investor_transactions.csv")
tx['transaction_date'] = pd.to_datetime(tx['transaction_date'])
tx['transaction_type'] = tx['transaction_type'].str.strip()
tx['kyc_status'] = tx['kyc_status'].str.strip()
tx['state'] = tx['state'].str.strip()
tx['city'] = tx['city'].str.strip()
tx['city_tier'] = tx['city_tier'].str.strip()
tx['age_group'] = tx['age_group'].str.strip()
tx['gender'] = tx['gender'].str.strip()
tx['payment_mode'] = tx['payment_mode'].str.strip()

tx = tx[tx['amount_inr'] > 0]
tx = tx.drop_duplicates()
tx.to_csv(processed_dir / "clean_transactions.csv", index=False)

# 9. Clean Portfolio Holdings
print("Cleaning portfolio holdings...")
holdings = pd.read_csv(raw_dir / "09_portfolio_holdings.csv")
holdings['portfolio_date'] = pd.to_datetime(holdings['portfolio_date'])
holdings['stock_symbol'] = holdings['stock_symbol'].str.strip()
holdings['stock_name'] = holdings['stock_name'].str.strip()
holdings['sector'] = holdings['sector'].str.strip()
holdings = holdings.drop_duplicates()
holdings.to_csv(processed_dir / "clean_portfolio_holdings.csv", index=False)

# 10. Clean Benchmark Indices
print("Cleaning benchmark indices...")
bench = pd.read_csv(raw_dir / "10_benchmark_indices.csv")
bench['date'] = pd.to_datetime(bench['date'])
bench['index_name'] = bench['index_name'].str.strip()
bench = bench.drop_duplicates()
bench.to_csv(processed_dir / "clean_benchmark_indices.csv", index=False)

print("Data cleaning complete! All files saved in ./data/processed/")