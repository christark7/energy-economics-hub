# model_engine.py
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.linear_model import RidgeCV
from sklearn.preprocessing import StandardScaler

def run_model():
    print("Loading energy market dataset into model engine...")
    data_path = Path("data/raw_energy_market.csv")
    if not data_path.exists():
        data_path = Path("outputs/energy_hub_data.xlsx")
        df = pd.read_excel(data_path, sheet_name="market_observations")
    else:
        df = pd.read_csv(data_path)

    target_col = "price" if "price" in df.columns else df.columns[-1]
    feature_cols = ["load_mw", "margin_estimate_pct"]
    
    model_df = df[feature_cols + [target_col]].dropna()
    
    y = model_df[target_col].values
    X = model_df[feature_cols].values

    # Standardize features (mean=0, std=1) which is critical for Ridge regularization
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    print("Fitting Ridge Regression with automatic alpha cross-validation...")
    # RidgeCV tests multiple alpha penalty values and selects the best one automatically
    alphas = [0.01, 0.1, 1.0, 10.0, 100.0, 1000.0]
    ridge = RidgeCV(alphas=alphas, store_cv_values=True)
    ridge.fit(X_scaled, y)

    print(f"Optimal Alpha selected: {ridge.alpha_}")

    # Export coefficients
    Path("outputs").mkdir(exist_ok=True)
    
    coef_df = pd.DataFrame({
        "Feature": feature_cols,
        "Standardized_Coefficient": ridge.coef_
    })
    # Add intercept row
    intercept_df = pd.DataFrame({
        "Feature": ["Intercept"],
        "Standardized_Coefficient": [ridge.intercept_]
    })
    coef_df = pd.concat([coef_df, intercept_df], ignore_index=True)
    coef_df.to_csv("outputs/model_coefficients.csv", index=False)
    
    # Calculate R-squared for Ridge
    r_squared = ridge.score(X_scaled, y)
    metrics_df = pd.DataFrame({
        "R-squared": [r_squared],
        "Optimal_Alpha": [ridge.alpha_]
    })
    metrics_df.to_csv("outputs/model_metrics.csv", index=False)

    # Save summary text report
    with open("outputs/regression_summary.txt", "w") as f:
        f.write("=== RIDGE REGRESSION SUMMARY ===\n")
        f.write(f"Optimal Alpha: {ridge.alpha_}\n")
        f.write(f"R-squared: {r_squared:.4f}\n\n")
        f.write("Coefficients (on standardized features):\n")
        for feat, coef in zip(feature_cols, ridge.coef_):
            f.write(f"  {feat}: {coef:.4f}\n")
        f.write(f"  Intercept: {ridge.intercept_:.4f}\n")

    print("Ridge Model Engine execution completed successfully.")

if __name__ == "__main__":
    run_model()