from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

processed_dir = Path("data/processed")
reports_dir = Path("reports")
reports_dir.mkdir(parents=True, exist_ok=True)

nav = pd.read_csv(processed_dir / "clean_nav.csv")
fm = pd.read_csv(processed_dir / "clean_fund_master.csv")
nav['date'] = pd.to_datetime(nav['date'])

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
