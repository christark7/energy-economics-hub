from __future__ import annotations

from pathlib import Path

import pandas as pd
from openpyxl.styles import Font


def export_energy_hub_data(
    output_dir: str | Path = "outputs",
    workbook_name: str = "energy_hub_data.xlsx",
) -> Path:
    """Bundle core Power BI-ready tables into a single Excel workbook.

    The workbook includes these sheets:
    - Coefficients
    - Model_Metrics
    - VIF_Diagnostics
    """
    outputs_path = Path(output_dir)
    outputs_path.mkdir(parents=True, exist_ok=True)

    file_map = {
        "Coefficients": outputs_path / "model_coefficients.csv",
        "Model_Metrics": outputs_path / "model_metrics.csv",
        "VIF_Diagnostics": outputs_path / "vif_metrics.csv",
    }

    missing_files = [name for name, path in file_map.items() if not path.exists()]
    if missing_files:
        missing = ", ".join(missing_files)
        raise FileNotFoundError(
            f"Missing required export tables: {missing}. Run the model pipeline first."
        )

    excel_path = outputs_path / workbook_name
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        for sheet_name, csv_path in file_map.items():
            df = pd.read_csv(csv_path)
            df.columns = [str(col).strip() for col in df.columns]
            df.to_excel(writer, sheet_name=sheet_name, index=False)

            worksheet = writer.sheets[sheet_name]
            worksheet.freeze_panes = "A2"
            for cell in worksheet[1]:
                cell.font = Font(bold=True)

            for column_cells in worksheet.columns:
                current_column = column_cells[0].column_letter
                max_length = max(
                    len(str(cell.value)) if cell.value is not None else 0
                    for cell in column_cells
                )
                worksheet.column_dimensions[current_column].width = min(max_length + 2, 30)

    print(f"Power BI-ready Excel workbook created at {excel_path}")
    return excel_path


if __name__ == "__main__":
    export_energy_hub_data()
