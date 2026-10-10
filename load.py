# load.py
import os
import pandas as pd
from db import get_connection

def load_market_observations():
    csv_path = "outputs/market_observations.csv"
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found. Run ingestion first.")
        return

    print(f"Loading data from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    # Ensure timestamp column is parsed properly
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])

    conn = get_connection()
    cursor = conn.cursor()
    
    # Enable high-speed bulk inserts in pyodbc
    cursor.fast_executemany = True

    insert_query = """
        INSERT INTO market_observations 
        (source, market, company, region, commodity, timestamp, price_value, currency, unit, is_stale)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    # Convert dataframe rows into a list of tuples
    records = []
    for _, row in df.iterrows():
        records.append((
            str(row.get("source", "")),
            str(row.get("market", "")),
            str(row.get("company", "")),
            str(row.get("region", "")),
            str(row.get("commodity", "")),
            row.get("timestamp"),
            float(row.get("price_value", 0.0)),
            str(row.get("currency", "USD")),
            str(row.get("unit", "")),
            bool(row.get("is_stale", False))
        ))

    print(f"Inserting {len(records)} records into Azure SQL market_observations...")
    cursor.executemany(insert_query, records)
    conn.commit()
    
    cursor.close()
    conn.close()
    print("Data successfully loaded into Azure SQL!")

if __name__ == "__main__":
    load_market_observations()