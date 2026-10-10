from __future__ import annotations

from pathlib import Path

import pandas as pd
from docx import Document


def load_outputs(output_dir: str | Path = "outputs") -> dict[str, pd.DataFrame]:
    """Read the model tables used by stakeholders and business users."""
    outputs_path = Path(output_dir)
    files = {
        "coefficients": outputs_path / "model_coefficients.csv",
        "metrics": outputs_path / "model_metrics.csv",
        "vif": outputs_path / "vif_metrics.csv",
    }

    missing = [name for name, path in files.items() if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Missing required stakeholder files: " + ", ".join(missing) + ". Run the model pipeline first."
        )

    return {
        "coefficients": pd.read_csv(files["coefficients"]),
        "metrics": pd.read_csv(files["metrics"]),
        "vif": pd.read_csv(files["vif"]),
    }


def build_summary_text(dataframes: dict[str, pd.DataFrame]) -> str:
    """Create a simple executive summary in plain language."""
    metrics = dataframes["metrics"].set_index("Metric")["Value"]
    vif = dataframes["vif"].copy()
    high_vif = vif[vif["VIF"] > 5]

    r_squared = float(metrics["R-Squared"])
    f_stat = float(metrics["F-Statistic"])
    adj_r2 = float(metrics["Adj R-Squared"])
    observations = int(metrics["Observations"])

    summary = [
        "Energy Economics & Margin Intelligence Hub stakeholder summary",
        "",
        f"The model explains {r_squared:.2%} of the variability in spot prices using load and margin estimates.",
        f"The adjusted R-squared is {adj_r2:.3f}, indicating a strong fit across {observations} observations.",
        f"The overall model significance is supported by an F-statistic of {f_stat:.2f}.",
    ]

    if not high_vif.empty:
        summary.append(
            "The VIF diagnostics indicate some multicollinearity risk in the current explanatory variables, "
            "which should be reviewed before making final pricing decisions."
        )
    else:
        summary.append("The VIF diagnostics do not indicate material multicollinearity in the current specification.")

    summary.append(
        "This output is intended to support non-technical stakeholder review and can be refreshed automatically as the data pipeline updates."
    )
    return "\n".join(summary)


def generate_stakeholder_excel(output_dir: str | Path = "outputs", workbook_name: str = "stakeholder_summary.xlsx") -> Path:
    """Write a simplified executive workbook for business stakeholders."""
    outputs_path = Path(output_dir)
    outputs_path.mkdir(parents=True, exist_ok=True)
    workbook_path = outputs_path / workbook_name

    data = load_outputs(outputs_path)
    coeff = data["coefficients"].copy()
    metrics = data["metrics"].copy()
    vif = data["vif"].copy()

    with pd.ExcelWriter(workbook_path, engine="openpyxl") as writer:
        coeff.to_excel(writer, sheet_name="Executive_Coefficients", index=False)
        metrics.to_excel(writer, sheet_name="Executive_Metrics", index=False)
        vif.to_excel(writer, sheet_name="Executive_VIF", index=False)

    return workbook_path


def generate_stakeholder_docx(output_dir: str | Path = "outputs", doc_name: str = "stakeholder_summary.docx") -> Path:
    """Write a plain-language stakeholder brief in Word format."""
    outputs_path = Path(output_dir)
    outputs_path.mkdir(parents=True, exist_ok=True)
    doc_path = outputs_path / doc_name

    data = load_outputs(outputs_path)
    summary_text = build_summary_text(data)

    document = Document()
    document.add_heading("Energy Economics & Margin Intelligence Hub", level=1)
    document.add_heading("Stakeholder Brief", level=2)

    for paragraph in summary_text.splitlines():
        if paragraph.strip():
            document.add_paragraph(paragraph)

    coefficients = data["coefficients"].copy()
    metrics = data["metrics"].copy()
    vif = data["vif"].copy()

    table = document.add_table(rows=1, cols=2)
    table.style = "Table Grid"
    headers = ["Metric", "Value"]
    for idx, header in enumerate(headers):
        table.rows[0].cells[idx].text = header

    for _, row in metrics.iterrows():
        cells = table.add_row().cells
        cells[0].text = str(row["Metric"])
        cells[1].text = str(row["Value"])

    document.add_heading("Model coefficients", level=2)
    coeff_table = document.add_table(rows=1, cols=3)
    coeff_table.style = "Table Grid"
    coeff_headers = ["Parameter", "Coefficient", "P_Value"]
    for idx, header in enumerate(coeff_headers):
        coeff_table.rows[0].cells[idx].text = header

    for _, row in coefficients.iterrows():
        cells = coeff_table.add_row().cells
        cells[0].text = str(row["Parameter"])
        cells[1].text = f"{row['Coefficient']:.4f}"
        cells[2].text = f"{row['P_Value']:.4f}"

    document.add_heading("VIF diagnostic", level=2)
    vif_table = document.add_table(rows=1, cols=2)
    vif_table.style = "Table Grid"
    vif_headers = ["Variable", "VIF"]
    for idx, header in enumerate(vif_headers):
        vif_table.rows[0].cells[idx].text = header

    for _, row in vif.iterrows():
        cells = vif_table.add_row().cells
        cells[0].text = str(row["Variable"])
        cells[1].text = f"{row['VIF']:.2f}"

    document.save(doc_path)
    return doc_path


def generate_stakeholder_package(output_dir: str | Path = "outputs") -> dict[str, Path]:
    """Create the business-facing files for stakeholders and decision-makers."""
    outputs_path = Path(output_dir)
    outputs_path.mkdir(parents=True, exist_ok=True)

    excel_path = generate_stakeholder_excel(outputs_path)
    doc_path = generate_stakeholder_docx(outputs_path)

    return {
        "xlsx": excel_path,
        "docx": doc_path,
    }


if __name__ == "__main__":
    generate_stakeholder_package()
