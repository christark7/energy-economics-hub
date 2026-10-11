# model_engine.py
from pathlib import Path
import pandas as pd
import statsmodels.api as sm


def run_model(df=None):
    if df is None:
        print("Loading energy market dataset into model engine...")
        data_path = Path("data/raw_energy_market.csv")
        if not data_path.exists():
            data_path = Path("outputs/energy_hub_data.xlsx")
            if data_path.exists():
                df = pd.read_excel(data_path, sheet_name="market_observations")
            else:
                from scripts.ingest import generate_energy_data

                df = generate_energy_data()
        else:
            df = pd.read_csv(data_path)

    # Define your dependent (y) and independent (X) variables
    target_col = "spot_price_mwh" if "spot_price_mwh" in df.columns else ("price" if "price" in df.columns else df.columns[-1])
    feature_cols = [col for col in ["load_mw", "margin_estimate_pct"] if col in df.columns]

    if not feature_cols:
        feature_cols = list(df.select_dtypes(include=["number"]).columns[:2])

    model_df = df[feature_cols + [target_col]].dropna()

    y = model_df[target_col].astype(float)
    X = model_df[feature_cols].astype(float)

    # --- APPLY MEAN-CENTERING ---
    print("Applying mean-centering to independent variables...")
    X_centered = (X - X.mean()) / X.std()

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
        "P_Value": model.pvalues,
    }).reset_index().rename(columns={"index": "Parameter"})
    
    coef_df.to_csv("outputs/model_coefficients.csv", index=False)

    metrics_df = pd.DataFrame({
        "Metric": ["R-Squared", "Adj R-Squared", "F-Statistic", "AIC", "BIC", "Observations"],
        "Value": [model.rsquared, model.rsquared_adj, model.fvalue, model.aic, model.bic, int(model.nobs)],
    })
    
    metrics_df.to_csv("outputs/model_metrics.csv", index=False)
    with open("outputs/regression_summary.txt", "w") as f:
        f.write(model.summary().as_text())

    print("Model Engine execution completed successfully.")

    return {
        "model": model,
        "coefficients": coef_df,
        "metrics": metrics_df,
    }


if __name__ == "__main__":
    run_model()