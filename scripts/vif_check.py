import os
from pathlib import Path

import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor


def load_energy_dataset(data_path: str | os.PathLike[str] = "data/raw_energy_market.csv") -> pd.DataFrame:
    """Load the energy market dataset used in the VIF check."""
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"{path} not found. Run ingest.py first.")
    return pd.read_csv(path)


def calculate_vif(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate VIF values for load and margin variables, including the intercept."""
    X = df[["load_mw", "margin_estimate_pct"]]
    X_const = sm.add_constant(X, has_constant="add")

    vif_data = pd.DataFrame(
        {
            "Variable": X_const.columns,
            "VIF": [variance_inflation_factor(X_const.values, i) for i in range(X_const.shape[1])],
        }
    )
    return vif_data


def export_vif_results(vif_data: pd.DataFrame, output_dir: str = "outputs") -> str:
    """Persist the VIF output to CSV and return the output path."""
    os.makedirs(output_dir, exist_ok=True)
    vif_output_path = os.path.join(output_dir, "vif_metrics.csv")
    vif_data.to_csv(vif_output_path, index=False)
    return vif_output_path


def run_vif_check(data_path: str | os.PathLike[str] = "data/raw_energy_market.csv") -> pd.DataFrame:
    """Run the VIF check pipeline and export results."""
    print("Loading dataset for VIF calculation...")
    df = load_energy_dataset(data_path)

    print("Calculating Variance Inflation Factors (VIF)...")
    vif_data = calculate_vif(df)
    print(vif_data.to_string(index=False))

    vif_output_path = export_vif_results(vif_data)
    print("")
    print(f"VIF metrics successfully exported to {vif_output_path}")
    return vif_data


if __name__ == "__main__":
    run_vif_check()
