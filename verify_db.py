# verify_db.py
import pandas as pd
from db import get_connection

def verify_database():
    print("Connecting to Azure SQL for database verification...")
    conn = get_connection()
    
    # 1. Check row counts for both tables
    print("\n--- Table Row Counts ---")
    counts_query = """
        SELECT 'market_observations' AS table_name, COUNT(*) AS row_count FROM market_observations
        UNION ALL
        SELECT 'market_spread_opportunities' AS table_name, COUNT(*) AS row_count FROM market_spread_opportunities
    """
    counts_df = pd.read_sql(counts_query, conn)
    print(counts_df.to_string(index=False))
    
    # 2. Fetch sample market observations
    print("\n--- Sample Market Observations (Top 5) ---")
    sample_query = """
        SELECT TOP 5 source, market, commodity, price_value, currency, unit, timestamp 
        FROM market_observations 
        ORDER BY timestamp DESC
    """
    sample_df = pd.read_sql(sample_query, conn)
    print(sample_df.to_string(index=False))
    
    # 3. Summary statistics grouped by commodity
    print("\n--- Average Price Summary by Commodity ---")
    summary_query = """
        SELECT commodity, COUNT(*) AS observations, ROUND(AVG(price_value), 2) AS avg_price, currency, unit 
        FROM market_observations 
        GROUP BY commodity, currency, unit
    """
    summary_df = pd.read_sql(summary_query, conn)
    print(summary_df.to_string(index=False))
    
    conn.close()
    print("\nDatabase verification completed successfully!")

if __name__ == "__main__":
    verify_database()