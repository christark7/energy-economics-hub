# model_engine.py
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from pathlib import Path

def run_model():
    print("Loading energy market dataset into model engine...")
    data_path = Path("data/raw_energy_market.csv")
    if not data_path.exists():
        # Fallback to output or database extract if raw doesn't exist
        data_path = Path("outputs/energy_hub_data.xlsx")
        df = pd.read_excel(data_path, sheet_name="market_observations")
    else:
        df = pd.read_csv(data_path)

    # Define your dependent (y) and independent (X) variables
    # Adjust column names to match your exact dataset schema
    target_col = "price" if "price" in df.columns else df.columns[-1]
    feature_cols = ["load_mw", "margin_estimate_pct"]
    
    # Drop rows with missing values in target or features
    model_df = df[feature_cols + [target_col]].dropna()
    
    y = model_df[target_col]
    X = model_df[feature_cols].copy()

    # --- APPLY MEAN-CENTERING ---
    print("Applying mean-centering to independent variables...")
    X_centered = (X - X.mean()) / X.std()  # Optional: Standardized (mean=0, std=1) or just (X - X.mean())
    # If you only want pure mean-centering without scaling, use:
    # X_centered = X - X.mean()

    # Add constant for OLS intercept
    X_design = sm.add_constant(X_centered)

    print("Fitting Ordinary Least Squares (OLS) regression model...")
    model = sm.OLS(y, X_design).fit()

    # Export coefficients and performance metrics
    Path("outputs").mkdir(exist_ok=True)
    
    coef_df = pd.DataFrame({
        "Coefficient": model.params,
        "Std Error": model.bse,
        "t-value": model.tvalues,
        "p-value": model.pvalues
    })
    coef_df.to_csv("outputs/model_coefficients.csv")
    
    metrics_df = pd.DataFrame({
        "R-squared": [model.rsquared],
        "Adj R-squared": [model.rsquared_adj],
        "F-statistic": [model.fvalue],
        "AIC": [model.aic],
        "BIC": [model.bic]
    })
    metrics_df.to_csv("outputs/model_metrics.csv", index=False)

    with open("outputs/regression_summary.txt", "w") as f:
        f.write(model.summary().as_text())

    print("Model Engine execution completed successfully.")

if __name__ == "__main__":
    run_model()