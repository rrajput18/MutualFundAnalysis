from pathlib import Path
import pandas as pd

raw_dir = Path("./data/raw")

csv_files = {
    "fund_master": "01_fund_master.csv",
    "nav_history": "02_nav_history.csv",
    "aum_fund_house": "03_aum_by_fund_house.csv",
    "sip_inflows": "04_monthly_sip_inflows.csv",
    "category_inflows": "05_category_inflows.csv",
    "folio_count": "06_industry_folio_count.csv",
    "scheme_performance": "07_scheme_performance.csv",
    "transactions": "08_investor_transactions.csv",
    "holdings": "09_portfolio_holdings.csv",
    "benchmarks": "10_benchmark_indices.csv"
}

dfs = {}

# 1. Load and inspect datasets
for key, filename in csv_files.items():
    path = raw_dir / filename
    if not path.exists():
        print(f"Warning: File not found {path}")
        continue
        
    df = pd.read_csv(path)
    dfs[key] = df
    
    print(f"\n--- {filename} ---")
    print(f"Shape: {df.shape}")
    print("Data types:")
    print(df.dtypes)
    print("Head:")
    print(df.head(2))
    
    # Check for basic anomalies
    null_cols = df.isnull().sum()
    if null_cols.any():
        print("Null values found:")
        print(null_cols[null_cols > 0])
    
    dup_rows = df.duplicated().sum()
    if dup_rows > 0:
        print(f"Duplicates: {dup_rows} rows")

# 2. Explore fund master
fm = dfs.get("fund_master")
if fm is not None:
    print("\n" + "="*40)
    print("FUND MASTER EXPLORATION")
    print("="*40)
    print("Fund Houses:", fm['fund_house'].unique())
    print("\nCategories:", fm['category'].unique())
    print("\nSub-categories:", fm['sub_category'].unique())
    print("\nRisk Categories:", fm['risk_category'].unique())
    print("\nAMFI Code sample:")
    print(fm['amfi_code'].head(5))

# 3. Validate AMFI codes
nav = dfs.get("nav_history")
if fm is not None and nav is not None:
    print("\n" + "="*40)
    print("AMFI CODE VALIDATION")
    print("="*40)
    fm_codes = set(fm['amfi_code'].unique())
    nav_codes = set(nav['amfi_code'].unique())
    
    mismatch = fm_codes - nav_codes
    print(f"Fund Master unique codes: {len(fm_codes)}")
    print(f"NAV History unique codes: {len(nav_codes)}")
    
    if not mismatch:
        print("Success: All codes in fund_master map to nav_history.")
    else:
        print(f"Mismatch: {len(mismatch)} codes in fund_master are missing in nav_history:")
        print(mismatch)