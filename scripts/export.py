import os
import pandas as pd

print("Consolidating outputs into Excel workbook for Power BI...")
os.makedirs("outputs", exist_ok=True)

coef = pd.read_csv("outputs/model_coefficients.csv")
metrics = pd.read_csv("outputs/model_metrics.csv")
vif = pd.read_csv("outputs/vif_metrics.csv")

excel_path = "outputs/energy_hub_data.xlsx"
with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
    coef.to_excel(writer, sheet_name="Coefficients", index=False)
    metrics.to_excel(writer, sheet_name="Model_Metrics", index=False)
    vif.to_excel(writer, sheet_name="VIF_Diagnostics", index=False)

print(f"Excel workbook successfully created at {excel_path}")