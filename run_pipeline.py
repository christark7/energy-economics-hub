# run_pipeline.py
import subprocess
import sys
from pathlib import Path


def run_step(script_path: str) -> None:
    script = Path(script_path).resolve()
    print(f"\n---> Executing {script}...")
    result = subprocess.run([sys.executable, str(script)], check=False)
    if result.returncode != 0:
        print(f"Pipeline Error: {script} failed with exit code {result.returncode}.")
        raise SystemExit(result.returncode)
    print(f"--- Completed {script} successfully ---")


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent
    print("==================================================")
    print("Starting Energy Economics Hub Pipeline Orchestration")
    print("==================================================")

    # 1. Ingestion & Market Data Collection
    run_step(project_root / "scripts" / "ingest.py")
    run_step(project_root / "scripts" / "web_data_ingestion.py")
    run_step(project_root / "market_intelligence.py")

    # 2. Azure SQL Persistence & Arbitrage Spread Calculations
    run_step(project_root / "load.py")
    run_step(project_root / "calc_spreads.py")

    # 3. Econometric Modeling & Diagnostics
    run_step(project_root / "scripts" / "model_engine.py")
    run_step(project_root / "scripts" / "vif_check.py")
    
    # 4. Reporting & Stakeholder Packaging
    run_step(project_root / "export.py")
    run_step(project_root / "stakeholder_packager.py")

    print("\n==================================================")
    print("All pipeline stages completed successfully!")
    print("Fresh econometric, Excel, Azure SQL, and stakeholder outputs are ready!")
    print("==================================================")