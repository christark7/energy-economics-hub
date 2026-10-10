# calc_spreads.py
import pandas as pd
from db import get_connection

def calculate_and_store_spreads():
    print("Connecting to Azure SQL to fetch market observations...")
    conn = get_connection()
    
    query = """
        SELECT source, market, company, region, commodity, timestamp, price_value, currency, unit, is_stale
        FROM market_observations
        WHERE is_stale = 0 OR is_stale IS NULL
    """
    df = pd.read_sql(query, conn)
    
    if df.empty:
        print("No valid market observations found to compute spreads.")
        conn.close()
        return

    print(f"Loaded {len(df)} active observations. Calculating gross spread opportunities...")

    # Self-merge to find price differences for the same timestamp, market, region, commodity, currency, and unit
    merged = pd.merge(
        df, df,
        on=["market", "region", "commodity", "timestamp", "currency", "unit"],
        suffixes=("_buy", "_sell")
    )

    # Filter out self-comparisons (same source)
    spreads_df = merged[merged["source_buy"] != merged["source_sell"]].copy()

    if spreads_df.empty:
        print("No cross-source spread pairs found.")
        conn.close()
        return

    # Calculate gross spread (sell price minus buy price)
    spreads_df["gross_spread"] = spreads_df["price_value_sell"] - spreads_df["price_value_buy"]

    # Select columns matching the market_spread_opportunities table schema
    result_df = spreads_df[[
        "market", "region", "commodity", "timestamp", 
        "source_buy", "source_sell", "gross_spread", "currency", "unit"
    ]].drop_duplicates()

    print(f"Computed {len(result_df)} spread opportunities. Storing in Azure SQL...")

    cursor = conn.cursor()
    cursor.fast_executemany = True

    insert_query = """
        INSERT INTO market_spread_opportunities 
        (market, region, commodity, timestamp, buy_source, sell_source, gross_spread, currency, unit)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    records = []
    for _, row in result_df.iterrows():
        records.append((
            str(row["market"]),
            str(row["region"]),
            str(row["commodity"]),
            pd.to_datetime(row["timestamp"]),
            str(row["source_buy"]),
            str(row["source_sell"]),
            float(row["gross_spread"]),
            str(row["currency"]),
            str(row["unit"])
        ))

    cursor.executemany(insert_query, records)
    conn.commit()

    cursor.close()
    conn.close()
    print("Market spread opportunities successfully calculated and stored in Azure SQL!")

if __name__ == "__main__":
    calculate_and_store_spreads()