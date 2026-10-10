import os

import pandas as pd
import statsmodels.api as sm


def run_econometric_model():
    file_path = os.path.join("data", "raw_energy_market.csv")
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found. Run ingest.py first.")
        return

    print("Loading energy dataset for econometric analysis...")
    df = pd.read_csv(file_path)

    # Define dependent variable (Y) and independent variables (X)
    # Example: estimating spot price drivers based on load and margin
    y = df["spot_price_mwh"]
    x = df[["load_mw", "margin_estimate_pct"]]

    # Add a constant for OLS intercept
    x = sm.add_constant(x)

    print("\nFitting Ordinary Least Squares (OLS) Econometric Model...")
    model = sm.OLS(y, x).fit()

    print("\n=== ECONOMETRIC MODEL RESULTS ===")
    print(model.summary())

    os.makedirs("outputs", exist_ok=True)
    summary_path = os.path.join("outputs", "regression_summary.txt")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(model.summary().as_text())
    print(f"\nModel summary saved to {summary_path}")


if __name__ == "__main__":
    run_econometric_model()