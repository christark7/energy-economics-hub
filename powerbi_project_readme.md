# Energy Economics Hub Power BI bridge

This folder keeps the project in a Power BI Project-compatible structure for later desktop use while still allowing immediate VS Code development.

## Immediate option
- Use the workbook at outputs/energy_hub_data.xlsx.
- It contains the following sheets: Coefficients, Model_Metrics, VIF_Diagnostics.

## Later Power BI Desktop option
- Open the folder energy_hub.pbip in Power BI Desktop when installed.
- The project is intentionally lightweight and ready to be expanded with actual report pages and semantic model metadata.

## Refresh flow
- Run the Python pipeline from the repo root to regenerate model outputs and Excel workbook.
- Command: .\.venv\Scripts\python run_pipeline.py
