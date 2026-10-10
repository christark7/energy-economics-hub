# query_spreads.py
import pandas as pd
from db import get_connection

def inspect_spreads():
    print("Connecting to Azure SQL to query market spread opportunities...")
    conn = get_connection()
    
    query = """
        SELECT TOP 10 
            market, 
            region, 
            commodity, 
            timestamp, 
            buy_source, 
            sell_source, 
            gross_spread, 
            currency, 
            unit
        FROM market_spread_opportunities
        ORDER BY ABS(gross_spread) DESC
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    if df.empty:
        print("No market spread opportunities found in the database.")
    else:
        print("\n=== TOP MARKET SPREAD OPPORTUNITIES (Ranked by Spread) ===")
        print(df.to_string(index=False))

if __name__ == "__main__":
    inspect_spreads()
