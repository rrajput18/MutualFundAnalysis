from pathlib import Path
import pandas as pd
import requests

raw_dir = Path("./data/raw")
raw_dir.mkdir(parents=True, exist_ok=True)

# Schemes to download
schemes = {
    "125497": "HDFC_Top_100_Direct",
    "119551": "SBI_Bluechip",
    "120503": "ICICI_Bluechip",
    "118632": "Nippon_Large_Cap",
    "119092": "Axis_Bluechip",
    "120841": "Kotak_Bluechip"
}

print("Fetching NAV data from mfapi.in...")

for code, name in schemes.items():
    url = f"https://api.mfapi.in/mf/{code}"
    print(f"Fetching {name} (Code: {code})...")
    
    try:
        res = requests.get(url, timeout=15)
        res.raise_for_status()
        
        json_data = res.json()
        if "data" not in json_data:
            print(f"Error: Missing data array for code {code}")
            continue
            
        # Parse list of dicts to DataFrame
        df = pd.DataFrame(json_data["data"])
        
        # Save output to raw directory
        output_file = raw_dir / f"{code}_raw.csv"
        df.to_csv(output_file, index=False)
        print(f"Saved {len(df)} records to {output_file}")
        
    except Exception as e:
        print(f"Error fetching code {code}: {e}")

print("All fetches complete!")