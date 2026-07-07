# Mutual Fund Analytics Platform

An end-to-end data pipeline, performance engine, and dashboard suite for Indian mutual fund analysis.

🚀 **Live Interactive Dashboard**: [rrajput18-mutualfundanalysis-app-ln9lo9.streamlit.app](https://rrajput18-mutualfundanalysis-app-ln9lo9.streamlit.app/)

## Project Structure

```text
 E:/MutualFundAnalysis/
 ├── data/
 │   ├── raw/                 # Original CSVs and raw API downloads
 │   ├── processed/           # Cleaned, forward-filled CSV files
 │   └── db/                  # SQLite database location (bluestock_mf.db)
 ├── scripts/
 │   ├── etl_pipeline.py      # Automated Ingestion -> Cleaning -> SQL Loading pipeline
 │   ├── live_nav_fetch.py    # AMFI API live downloader
 │   ├── compute_metrics.py   # Performance calculator (CAGR, Sharpe, Sortino, Alpha, Beta)
 │   └── recommender.py       # Simple risk-grade based fund recommendation engine
 ├── notebooks/
 │   ├── 01_data_ingestion.ipynb
 │   ├── 02_data_cleaning.ipynb
 │   ├── 03_eda_analysis.ipynb
 │   ├── 04_performance_analytics.ipynb
 │   └── 05_advanced_analytics.ipynb
 ├── dashboard/
 │   └── bluestock_mf.pbix    # 4-page interactive Power BI dashboard
 ├── sql/
 │   ├── schema.sql           # Database schema definition (DDL)
 │   └── queries.sql          # 10 core business queries
 ├── reports/                 # Exported charts, scorecards, and PDF deliverables
 └── README.md
 ```
 
 ## Setup & Execution
 
 ### 1. Environment Setup
 Clone the repository, set up a virtual environment, and install dependencies:
 ```cmd
 python -m venv venv
 venv\Scripts\activate
 pip install -r requirements.txt
 pip install streamlit
 ```
 
 ### 2. Run the Data Pipeline (ETL)
 Ingest raw files, apply weekends/holidays forward-filling, and build the SQLite database schema:
 ```cmd
 python scripts/etl_pipeline.py
 ```
 
 ### 3. Compute Performance Analytics
 Calculate annualized CAGR (trading-day basis), Sharpe, Sortino, Alpha, and Beta metrics, exporting scorecards and regression tables to the `reports/` folder:
 ```cmd
 python scripts/compute_metrics.py
 ```
 
 ### 4. Run Advanced Quantitative Models
 Execute the advanced analytics Jupyter Notebook to run Monte Carlo NAV projections, portfolio optimization, VaR/CVaR calculations, cohort analyses, and sector concentration:
 Open and execute all cells in `notebooks/05_advanced_analytics.ipynb`.
 
 ### 5. Launch the Streamlit Web Application
 View the interactive Python-based web dashboard locally in your browser:
 ```cmd
 streamlit run app.py
 ```
 
 ## Deliverables & Verification
 * **Database**: `data/db/bluestock_mf.db` (Contains star-schema tables and `dim_date` dimension).
 * **Power BI**: `dashboard/bluestock_mf.pbix` (Interactive dashboards matching the 4 required pages).
 * **Analytical CSVs**: `reports/fund_scorecard.csv`, `reports/alpha_beta.csv`, and `reports/var_cvar_report.csv`.
 * **Visual Plots**: `reports/benchmark_comparison_chart.png`, `reports/monte_carlo_simulation.png`, `reports/efficient_frontier.png`, and `reports/rolling_sharpe_chart.png`.
 * **Final Report**: `reports/Final_Report.pdf`.
