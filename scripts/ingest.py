import os
from datetime import datetime, timezone

import pandas as pd
from azure.core.exceptions import AzureError
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

CONTAINER_NAME = "rawdata"
STORAGE_ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT", "energystoragechris")
STORAGE_ACCOUNT_URL = os.getenv(
    "AZURE_STORAGE_ACCOUNT_URL",
    f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net",
)


def generate_energy_data() -> pd.DataFrame:
    """Return a deterministic synthetic energy market dataset."""
    data = {
        "timestamp": pd.date_range(start="2026-10-01", periods=24, freq="h"),
        "region": ["East-Grid"] * 24,
        "load_mw": [
            1250, 1200, 1150, 1100, 1080, 1120, 1250, 1400, 1550, 1600, 1580, 1550,
            1520, 1500, 1480, 1510, 1650, 1800, 1750, 1600, 1450, 1350, 1280, 1220,
        ],
        "spot_price_mwh": [
            45.5, 42.0, 40.1, 39.5, 41.0, 44.2, 52.8, 68.4, 85.0, 91.2, 88.5, 84.0,
            82.1, 80.5, 79.0, 83.4, 95.0, 115.4, 105.2, 92.0, 75.4, 62.1, 52.0, 48.3,
        ],
        "margin_estimate_pct": [
            18.2, 19.0, 19.5, 19.8, 19.1, 18.5, 15.2, 11.0, 8.4, 7.1, 7.8, 8.5,
            9.0, 9.4, 9.8, 8.9, 6.2, 4.1, 5.0, 7.2, 10.5, 13.1, 16.0, 17.5,
        ],
    }
    return pd.DataFrame(data)


def save_local_dataset(
    df: pd.DataFrame,
    output_dir: str = "data",
    filename: str = "raw_energy_market.csv",
) -> str:
    """Persist the dataset locally and return the output path."""
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, filename)
    df.to_csv(file_path, index=False)
    return file_path


def upload_to_blob_storage(
    file_path: str,
    container_name: str | None = None,
    connection_string: str | None = None,
    blob_name: str | None = None,
) -> str | None:
    """Upload a file with Azure identity, using a connection string only if provided."""
    resolved_connection_string = connection_string or os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    resolved_container_name = container_name or os.getenv("AZURE_STORAGE_CONTAINER", CONTAINER_NAME)
    credential = None
    blob_service_client = None
    try:
        if resolved_connection_string:
            blob_service_client = BlobServiceClient.from_connection_string(resolved_connection_string)
        else:
            credential = DefaultAzureCredential()
            blob_service_client = BlobServiceClient(
                account_url=STORAGE_ACCOUNT_URL,
                credential=credential,
            )

        resolved_blob_name = blob_name or f"raw_energy_market_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
        blob_client = blob_service_client.get_blob_client(container=resolved_container_name, blob=resolved_blob_name)

        with open(file_path, "rb") as data_file:
            blob_client.upload_blob(data_file, overwrite=True)
        return resolved_blob_name
    except (AzureError, OSError) as exc:  # pragma: no cover - failure is operational, not logic.
        print(f"Failed to upload to Azure Storage: {exc}")
        return None
    finally:
        if blob_service_client is not None:
            blob_service_client.close()
        if credential is not None:
            credential.close()


def run_ingestion() -> str:
    """Generate the market dataset, save it locally, and optionally push it to Azure."""
    print("Starting ingestion script...")
    df = generate_energy_data()
    file_path = save_local_dataset(df)
    print(f"Dataset successfully saved locally to {file_path}")

    blob_name = upload_to_blob_storage(file_path)
    if blob_name:
        print(f"Azure upload completed successfully as '{blob_name}'.")
    else:
        print("Azure upload unavailable. Local file is ready for analysis.")

    return file_path


if __name__ == "__main__":
    run_ingestion()
