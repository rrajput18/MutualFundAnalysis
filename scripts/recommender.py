import sys
import argparse
import pandas as pd
from pathlib import Path

def get_recommendations(risk_appetite):
    script_dir = Path(__file__).resolve().parent
    processed_dir = script_dir.parent / "data" / "processed"
    perf_path = processed_dir / "clean_performance.csv"
    
    if not perf_path.exists():
        print(f"Error: Required data file not found at {perf_path}")
        print("Please run scripts/etl_pipeline.py and scripts/compute_metrics.py first.")
        sys.exit(1)
        
    df = pd.read_csv(perf_path)
    
    # Map input risk appetite to database risk grades
    risk_mapping = {
        'low': ['Low'],
        'moderate': ['Moderate', 'Moderately High'],
        'high': ['High', 'Very High']
    }
    
    appetite_clean = risk_appetite.strip().lower()
    if appetite_clean not in risk_mapping:
        print(f"Invalid risk appetite: '{risk_appetite}'")
        print("Choose from: Low, Moderate, High")
        sys.exit(1)
        
    matching_grades = risk_mapping[appetite_clean]
    df_filtered = df[df['risk_grade'].isin(matching_grades)].copy()
    
    if df_filtered.empty:
        print(f"No funds found matching the risk grades: {matching_grades}")
        return
        
    # Rank by Sharpe ratio descending and get top 3
    df_sorted = df_filtered.sort_values(by='sharpe_ratio', ascending=False)
    top_funds = df_sorted.head(3).copy()
    
    # Select and rename columns for clean reporting
    report_cols = {
        'scheme_name': 'Scheme Name',
        'risk_grade': 'Risk Grade',
        'sharpe_ratio': 'Sharpe Ratio',
        'return_3yr_pct': '3-Yr CAGR (%)',
        'category': 'Category',
        'plan': 'Plan'
    }
    
    report_df = top_funds[list(report_cols.keys())].rename(columns=report_cols)
    
    print(f"\n==================================================================================")
    print(f"  TOP 3 RECOMMENDED FUNDS - {risk_appetite.upper()} RISK APPETITE  ")
    print(f"==================================================================================")
    print(report_df.to_string(index=False, formatters={
        'Sharpe Ratio': '{:,.2f}'.format,
        '3-Yr CAGR (%)': '{:,.2f}%'.format
    }))
    print(f"==================================================================================\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mutual Fund Recommender Engine")
    parser.add_argument(
        "--risk", 
        type=str, 
        choices=["Low", "Moderate", "High", "low", "moderate", "high"], 
        help="Investor risk appetite (Low / Moderate / High)"
    )
    args = parser.parse_args()
    
    if args.risk:
        get_recommendations(args.risk)
    else:
        # Fallback to interactive CLI mode if no args passed
        try:
            user_input = input("Enter your risk appetite (Low / Moderate / High): ")
            if not user_input.strip():
                print("Error: Input cannot be empty.")
                sys.exit(1)
            get_recommendations(user_input)
        except KeyboardInterrupt:
            print("\nExiting recommender.")
            sys.exit(0)
