from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ---------------------------------------------------------
# Setup Paths & Load Data
# ---------------------------------------------------------
processed_dir = Path("data/processed")
reports_dir = Path("reports")
reports_dir.mkdir(parents=True, exist_ok=True)

nav = pd.read_csv(processed_dir / "clean_nav.csv")
fm = pd.read_csv(processed_dir / "clean_fund_master.csv")
transactions = pd.read_csv(processed_dir / "clean_transactions.csv")
performance = pd.read_csv(processed_dir / "clean_performance.csv")
portfolio = pd.read_csv(processed_dir / "clean_portfolio_holdings.csv")

nav['date'] = pd.to_datetime(nav['date'])
transactions['transaction_date'] = pd.to_datetime(transactions['transaction_date'])

# ---------------------------------------------------------
# 1. Monte Carlo NAV Projection (Original Code)
# ---------------------------------------------------------
print("Running Monte Carlo simulations...")
sbi_small_cap_code = 119551
fund_nav = nav[nav['amfi_code'] == sbi_small_cap_code].sort_values('date').copy()
fund_nav['daily_return'] = fund_nav['nav'].pct_change()

returns = fund_nav['daily_return'].dropna()
drift = returns.mean()
volatility = returns.std()
latest_nav = fund_nav.iloc[-1]['nav']

n_days = 1260
n_simulations = 1000
sim_nav = np.zeros((n_days, n_simulations))
sim_nav[0, :] = latest_nav

# Set seed for reproducibility
np.random.seed(42)
for t in range(1, n_days):
    shocks = np.random.normal(drift, volatility, n_simulations)
    sim_nav[t, :] = sim_nav[t-1, :] * (1 + shocks)

p5 = np.percentile(sim_nav, 5, axis=1)
p25 = np.percentile(sim_nav, 25, axis=1)
p50 = np.percentile(sim_nav, 50, axis=1)
p75 = np.percentile(sim_nav, 75, axis=1)
p95 = np.percentile(sim_nav, 95, axis=1)

plt.figure(figsize=(10, 6))
plt.plot(p50, label='Median Projection', color='blue', linewidth=2)
plt.fill_between(range(n_days), p25, p75, color='blue', alpha=0.15, label='25th-75th Percentile')
plt.fill_between(range(n_days), p5, p95, color='blue', alpha=0.08, label='5th-95th Percentile')
plt.title("5-Year Monte Carlo NAV Projection")
plt.xlabel("Trading Days")
plt.ylabel("NAV (INR)")
plt.legend(loc='upper left')
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig(reports_dir / "monte_carlo_simulation.png", dpi=150)
plt.close()

# ---------------------------------------------------------
# 2. Portfolio Optimization & Efficient Frontier (Original Code)
# ---------------------------------------------------------
print("Mapping Markowitz Efficient Frontier...")
selected_codes = [119551, 120503, 118632, 119092, 120841]
portfolio_nav = nav[nav['amfi_code'].isin(selected_codes)].pivot(index='date', columns='amfi_code', values='nav')
portfolio_returns = portfolio_nav.pct_change().dropna()

name_mapping = fm.set_index('amfi_code')['scheme_name'].to_dict()
portfolio_returns = portfolio_returns.rename(columns=name_mapping)

mean_returns = portfolio_returns.mean() * 252
cov_matrix = portfolio_returns.cov() * 252

n_portfolios = 5000
results = np.zeros((3, n_portfolios))
weights_record = []
rf = 0.065

for i in range(n_portfolios):
    weights = np.random.random(len(selected_codes))
    weights /= np.sum(weights)
    weights_record.append(weights)
    p_return = np.sum(mean_returns * weights)
    p_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
    p_sharpe = (p_return - rf) / p_volatility
    results[0, i] = p_return
    results[1, i] = p_volatility
    results[2, i] = p_sharpe

max_sharpe_idx = np.argmax(results[2])
msr_ret, msr_vol = results[0, max_sharpe_idx], results[1, max_sharpe_idx]

min_vol_idx = np.argmin(results[1])
mvp_ret, mvp_vol = results[0, min_vol_idx], results[1, min_vol_idx]

plt.figure(figsize=(10, 6))
plt.scatter(results[1], results[0], c=results[2], cmap='viridis', marker='o', s=10, alpha=0.3)
plt.colorbar(label='Sharpe Ratio')
plt.scatter(msr_vol, msr_ret, marker='*', color='red', s=200, label='Max Sharpe')
plt.scatter(mvp_vol, mvp_ret, marker='X', color='black', s=150, label='Min Variance')
plt.title("Portfolio Optimization & Efficient Frontier")
plt.xlabel("Annualized Volatility (Risk)")
plt.ylabel("Annualized Return")
plt.legend()
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig(reports_dir / "efficient_frontier.png", dpi=150)
plt.close()

# ---------------------------------------------------------
# 3. Historical VaR (95%) & CVaR Report
# ---------------------------------------------------------
print("Calculating Historical VaR (95%) and CVaR for all 40 schemes...")
var_results = []
for code, group in nav.groupby('amfi_code'):
    group = group.sort_values('date')
    daily_returns = group['nav'].pct_change().dropna()
    
    var_95 = daily_returns.quantile(0.05)
    cvar_95 = daily_returns[daily_returns <= var_95].mean()
    
    scheme_name = fm[fm['amfi_code'] == code].iloc[0]['scheme_name']
    var_results.append({
        'amfi_code': code,
        'scheme_name': scheme_name,
        'var_95': var_95,
        'cvar_95': cvar_95
    })

df_var = pd.DataFrame(var_results).sort_values('amfi_code')
df_var.to_csv(reports_dir / "var_cvar_report.csv", index=False)
print("Saved Tail Risk report to reports/var_cvar_report.csv")

# ---------------------------------------------------------
# 4. Rolling 90-day Sharpe Ratio
# ---------------------------------------------------------
print("Generating Rolling 90-Day Sharpe Ratio chart...")
plt.figure(figsize=(12, 6))
for code in selected_codes:
    fund_data = nav[nav['amfi_code'] == code].sort_values('date').copy()
    fund_data['daily_return'] = fund_data['nav'].pct_change()
    
    rolling_mean = fund_data['daily_return'].rolling(90).mean()
    rolling_std = fund_data['daily_return'].rolling(90).std()
    rolling_sharpe = (rolling_mean / rolling_std) * np.sqrt(252)
    
    plt.plot(fund_data['date'], rolling_sharpe, label=name_mapping[code], linewidth=1.5)

plt.title("Rolling 90-Day Sharpe Ratio Over Time (Key Large Cap Funds)", fontsize=14, fontweight='bold', pad=15)
plt.xlabel("Date", fontsize=12)
plt.ylabel("Annualized Sharpe Ratio", fontsize=12)
plt.grid(True, linestyle='--', alpha=0.5)
plt.legend(loc='lower left', frameon=True, facecolor='white', edgecolor='none')
plt.tight_layout()
plt.savefig(reports_dir / "rolling_sharpe_chart.png", dpi=150)
plt.close()
print("Saved Sharpe ratio chart to reports/rolling_sharpe_chart.png")

# ---------------------------------------------------------
# 5. Investor Cohort Analysis Summary
# ---------------------------------------------------------
print("\n--- Investor Cohort Analysis Summary ---")
first_tx_dates = transactions.groupby('investor_id')['transaction_date'].min().reset_index()
first_tx_dates.columns = ['investor_id', 'first_tx_date']
first_tx_dates['first_tx_year'] = first_tx_dates['first_tx_date'].dt.year

df_tx_cohort = transactions.merge(first_tx_dates[['investor_id', 'first_tx_year']], on='investor_id', how='left')

for year in sorted(df_tx_cohort['first_tx_year'].unique()):
    group = df_tx_cohort[df_tx_cohort['first_tx_year'] == year]
    avg_sip = group[group['transaction_type'] == 'SIP']['amount_inr'].mean()
    
    invested_tx = group[group['transaction_type'].isin(['SIP', 'Lumpsum'])]
    total_invested = invested_tx['amount_inr'].sum()
    
    fund_totals = invested_tx.groupby('amfi_code')['amount_inr'].sum()
    top_fund_name = name_mapping[fund_totals.idxmax()]
    
    print(f"Cohort {year}:")
    print(f"  Unique Investors: {group['investor_id'].nunique():,}")
    print(f"  Average SIP size: INR {avg_sip:,.2f}")
    print(f"  Total Capital Invested: INR {total_invested:,.2f}")
    print(f"  Top Preference: {top_fund_name}")

# ---------------------------------------------------------
# 6. SIP Continuity & Churn Analysis
# ---------------------------------------------------------
print("\n--- SIP Continuity Analysis Summary ---")
df_sip = transactions[transactions['transaction_type'] == 'SIP'].copy()
sip_counts = df_sip.groupby('investor_id').size()
eligible_investors = sip_counts[sip_counts >= 6].index

at_risk_count = 0
for inv_id in eligible_investors:
    inv_tx = df_sip[df_sip['investor_id'] == inv_id].sort_values('transaction_date')
    gaps = inv_tx['transaction_date'].diff().dropna().dt.days
    if gaps.mean() > 35:
        at_risk_count += 1

print(f"Total investors with 6+ SIP contributions: {len(eligible_investors):,}")
print(f"Investors flagged at-risk (avg gap > 35 days): {at_risk_count:,} ({at_risk_count / len(eligible_investors) * 100:.2f}%)")

# ---------------------------------------------------------
# 7. Sector HHI Concentration
# ---------------------------------------------------------
print("\n--- Sector HHI Concentration (Top Concentrated & Diversified Equity Funds) ---")
equity_codes = fm[fm['category'] == 'Equity']['amfi_code'].unique()
portfolio_eq = portfolio[portfolio['amfi_code'].isin(equity_codes)].copy()

hhi_data = []
for code, group in portfolio_eq.groupby('amfi_code'):
    sector_weights = group.groupby('sector')['weight_pct'].sum()
    hhi_decimal = ((sector_weights / 100) ** 2).sum()
    fund_name = fm[fm['amfi_code'] == code].iloc[0]['scheme_name']
    
    hhi_data.append({
        'scheme_name': fund_name,
        'sector_hhi': hhi_decimal
    })

df_hhi = pd.DataFrame(hhi_data).sort_values('sector_hhi', ascending=False)
print("Most Concentrated:")
for idx, row in df_hhi.head(2).iterrows():
    print(f"  - {row['scheme_name']}: HHI = {row['sector_hhi']:.4f}")
print("Most Diversified:")
for idx, row in df_hhi.tail(2).iterrows():
    print(f"  - {row['scheme_name']}: HHI = {row['sector_hhi']:.4f}")

print("\nAll advanced quantitative analytics run complete successfully.")
