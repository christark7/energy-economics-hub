# check_sources.py
import sys
print("Starting check_sources.py script...")

try:
    import pandas as pd
    from db import get_connection
    print("Dependencies loaded successfully.")
except Exception as e:
    print(f"Import error: {e}")
    sys.exit(1)

def check_obs():
    print("Opening connection to Azure SQL...")
    try:
        conn = get_connection()
        print("Connected successfully!")
    except Exception as e:
        print(f"Connection failed: {e}")
        return
    
    try:
        query = "SELECT source, commodity, COUNT(*) as observation_count FROM market_observations GROUP BY source, commodity"
        df = pd.read_sql(query, conn)
        conn.close()
        
        print("\n=== MARKET OBSERVATIONS SUMMARY BY SOURCE ===")
        if df.empty:
            print("The market_observations table contains 0 rows.")
        else:
            print(df.to_string(index=False))
    except Exception as e:
        print(f"Query execution failed: {e}")

if __name__ == "__main__":
    check_obs()