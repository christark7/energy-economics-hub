"""Fetch configurable energy-price feeds and normalize them for comparison."""

from __future__ import annotations

import json
import logging
import os
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from io import StringIO
from pathlib import Path
from typing import Any

import pandas as pd
import requests

LOGGER = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

EIA_RETAIL_URL = "https://api.eia.gov/v2/electricity/retail-sales/data/"
EIA_PETROLEUM_URL = "https://api.eia.gov/v2/petroleum/pri/gnd/data/"
COMMODITIES_API_LATEST_URL = "https://commodities-api.com/api/latest"
ENTSOE_URL = "https://web-api.tp.entsoe.eu/api"
REQUEST_TIMEOUT_SECONDS = 30
MARKET_COLUMNS = [
    "observed_at",
    "source",
    "market",
    "region",
    "commodity",
    "price",
    "currency",
    "unit",
    "company",
    "source_detail",
    "is_stale",
    "is_synthetic",
]


def supported_sources() -> list[str]:
    """Return implemented and configurable source adapters."""
    return [
        "EIA retail electricity",
        "EIA weekly petroleum retail prices",
        "ENTSO-E day-ahead electricity",
        "Commodities-API latest rates",
        "Authenticated HTTP CSV/JSON/XML feeds",
    ]


def source_inventory() -> list[dict[str, str]]:
    """Describe supported source types and the data they provide."""
    return [
        {"source": "EIA retail electricity", "purpose": "Monthly U.S. retail electricity prices by state and sector"},
        {"source": "EIA petroleum", "purpose": "Weekly U.S. retail gasoline and diesel prices by area"},
        {"source": "ENTSO-E day-ahead electricity", "purpose": "European day-ahead electricity prices by bidding zone"},
        {"source": "Commodities-API", "purpose": "Crude and other commodity benchmarks with provider symbols and units"},
        {"source": "HTTP feeds", "purpose": "Configurable licensed supplier, fuel, petrol, or market feeds"},
    ]


def empty_market_data() -> pd.DataFrame:
    """Return an empty frame with the normalized market-data schema."""
    return pd.DataFrame(columns=MARKET_COLUMNS)


def normalize_market_records(
    records: list[dict[str, Any]],
    source_name: str,
    field_map: dict[str, str | list[str]],
    defaults: dict[str, Any] | None = None,
    value_maps: dict[str, dict[str, str]] | None = None,
) -> pd.DataFrame:
    """Map source-specific records into a validated common schema.

    `field_map` maps canonical field names to their names in the source record.
    Timestamp and price are required; missing or invalid values fail loudly.
    """
    if not records:
        return empty_market_data()
    missing_map = {"observed_at", "price"}.difference(field_map)
    if missing_map:
        raise ValueError(f"{source_name} field_map must define: {', '.join(sorted(missing_map))}")

    source_frame = pd.DataFrame.from_records(records)
    normalized = pd.DataFrame(index=source_frame.index)
    for column in MARKET_COLUMNS:
        source_columns = field_map.get(column)
        default_value = (defaults or {}).get(column)
        if isinstance(source_columns, str):
            source_columns = [source_columns]
        mapped_values = None
        for source_column in source_columns or []:
            if source_column in source_frame:
                current_values = source_frame[source_column]
                mapped_values = current_values if mapped_values is None else mapped_values.fillna(current_values)
        if mapped_values is not None:
            normalized[column] = mapped_values
        elif column == "source":
            normalized[column] = source_name
        else:
            normalized[column] = default_value

    for column, value_map in (value_maps or {}).items():
        if column in normalized:
            normalized[column] = normalized[column].replace(value_map)

    normalized["observed_at"] = pd.to_datetime(normalized["observed_at"], utc=True, errors="coerce")
    normalized["price"] = pd.to_numeric(normalized["price"], errors="coerce")
    invalid_rows = normalized["observed_at"].isna() | normalized["price"].isna()
    if invalid_rows.any():
        bad_indexes = normalized.index[invalid_rows].tolist()
        raise ValueError(f"{source_name} has invalid timestamp or price values at rows {bad_indexes}")

    for column in ("source", "market", "region", "commodity", "currency", "unit"):
        normalized[column] = normalized[column].fillna("unspecified").astype(str)
    normalized["company"] = normalized["company"].where(normalized["company"].notna(), None)
    for column in ("is_stale", "is_synthetic"):
        normalized[column] = normalized[column].map(_parse_optional_bool).astype("boolean")
    return normalized[MARKET_COLUMNS].reset_index(drop=True)


def _parse_optional_bool(value: Any) -> Any:
    if pd.isna(value):
        return pd.NA
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"true", "1", "yes", "stale", "synthetic"}:
        return True
    if normalized in {"false", "0", "no", "current", "fresh", "real"}:
        return False
    return pd.NA


def _redact_secrets(message: str) -> str:
    return re.sub(r"(?i)(api_key|access_key)=([^&\s]+)", r"\1=[REDACTED]", message)


def fetch_eia_retail_prices(
    api_key: str,
    start: str,
    end: str,
    state: str | None = None,
    sector: str | None = None,
) -> pd.DataFrame:
    """Fetch EIA monthly retail electricity prices (source units are retained)."""
    if not api_key:
        raise ValueError("An EIA API key is required")
    params: dict[str, Any] = {
        "api_key": api_key,
        "frequency": "monthly",
        "data[0]": "price",
        "start": start,
        "end": end,
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "offset": 0,
        "length": 5000,
    }
    if state:
        params["facets[stateid][]"] = state
    if sector:
        params["facets[sectorid][]"] = sector

    response = requests.get(EIA_RETAIL_URL, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    payload = response.json()
    try:
        records = payload["response"]["data"]
    except (KeyError, TypeError) as exc:
        raise ValueError("EIA response did not contain response.data") from exc
    return normalize_market_records(
        records,
        "EIA",
        {"observed_at": "period", "price": "price", "region": "stateid", "unit": "price-units"},
        {"market": "retail", "commodity": "electricity", "currency": "USD"},
    )


def fetch_eia_petroleum_prices(
    api_key: str,
    product_code: str,
    region_code: str = "NUS",
    start: str | None = None,
    end: str | None = None,
    commodity: str | None = None,
) -> pd.DataFrame:
    """Fetch weekly EIA retail gasoline/diesel prices for one product and area."""
    if not api_key:
        raise ValueError("An EIA API key is required")
    if not product_code or not region_code:
        raise ValueError("EIA product_code and region_code are required")
    params: dict[str, Any] = {
        "api_key": api_key,
        "frequency": "weekly",
        "data[0]": "value",
        "facets[duoarea][]": region_code,
        "facets[product][]": product_code,
        "facets[process][]": "PTE",
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "length": 5000,
    }
    if start:
        params["start"] = start
    if end:
        params["end"] = end

    response = requests.get(EIA_PETROLEUM_URL, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    payload = response.json()
    try:
        records = payload["response"]["data"]
    except (KeyError, TypeError) as exc:
        raise ValueError("EIA petroleum response did not contain response.data") from exc
    return normalize_market_records(
        records,
        "EIA petroleum",
        {
            "observed_at": "period",
            "price": "value",
            "region": "area-name",
            "commodity": "product",
            "unit": "units",
            "source_detail": "series-description",
        },
        {"market": "retail", "currency": "USD", "commodity": commodity or product_code},
        {"commodity": {
            "EPMR": "gasoline_regular",
            "EPD2D": "diesel_no2",
            "EPD2DXL0": "diesel_ultra_low_sulfur",
            "EPD2DM10": "diesel_low_sulfur",
        }},
    )


def fetch_commodities_api_latest(
    api_key: str,
    symbols: list[str],
    base_currency: str = "USD",
    region: str = "global benchmark",
    commodity_aliases: dict[str, str] | None = None,
    market: str = "commodity benchmark",
) -> pd.DataFrame:
    """Fetch Commodities-API latest rates and convert inverse rates to quote prices."""
    if not api_key:
        raise ValueError("A Commodities-API access key is required")
    if not symbols:
        raise ValueError("At least one Commodities-API symbol is required")
    response = requests.get(
        COMMODITIES_API_LATEST_URL,
        params={"access_key": api_key, "base": base_currency, "symbols": ",".join(symbols)},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("success") is not True:
        raise ValueError("Commodities-API returned an unsuccessful response")
    rates = payload.get("rates")
    if not isinstance(rates, dict):
        raise ValueError("Commodities-API response did not contain a rates object")

    timestamp = payload.get("timestamp")
    if timestamp is not None:
        observed_at = pd.to_datetime(timestamp, unit="s", utc=True)
    else:
        observed_at = pd.to_datetime(payload.get("date"), utc=True, errors="coerce")
    if pd.isna(observed_at):
        raise ValueError("Commodities-API response did not contain a valid timestamp or date")

    units = payload.get("unit", {})
    aliases = commodity_aliases or {}
    records = []
    for symbol in symbols:
        if symbol not in rates:
            continue
        inverse_rate = float(rates[symbol])
        if inverse_rate <= 0:
            raise ValueError(f"Commodities-API returned a non-positive rate for {symbol}")
        unit = units.get(symbol, "unspecified") if isinstance(units, dict) else units
        records.append({
            "observed_at": observed_at,
            "commodity": aliases.get(symbol, symbol),
            "price": 1.0 / inverse_rate,
            "currency": payload.get("base", base_currency),
            "unit": unit,
        })
    if not records:
        raise ValueError("Commodities-API returned none of the requested symbols")
    return normalize_market_records(
        records,
        "Commodities-API",
        {"observed_at": "observed_at", "price": "price", "commodity": "commodity", "currency": "currency", "unit": "unit"},
        {"market": market, "region": region},
    )


def _local_name(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _child_text(element: ET.Element, name: str, default: str | None = None) -> str | None:
    for child in element.iter():
        if _local_name(child) == name and child.text:
            return child.text
    return default


def fetch_entsoe_day_ahead_prices(
    api_token: str,
    in_domain: str,
    period_start: datetime,
    period_end: datetime,
    out_domain: str | None = None,
) -> pd.DataFrame:
    """Fetch ENTSO-E day-ahead price points, returning timestamps in UTC."""
    if not api_token or not in_domain:
        raise ValueError("ENTSO-E API token and in_domain are required")
    if period_start.tzinfo is None or period_end.tzinfo is None:
        raise ValueError("ENTSO-E period_start and period_end must include a timezone")

    params = {
        "securityToken": api_token,
        "documentType": "A44",
        "in_Domain": in_domain,
        "out_Domain": out_domain or in_domain,
        "periodStart": period_start.astimezone(timezone.utc).strftime("%Y%m%d%H%M"),
        "periodEnd": period_end.astimezone(timezone.utc).strftime("%Y%m%d%H%M"),
    }
    response = requests.get(ENTSOE_URL, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    try:
        root = ET.fromstring(response.content)
    except ET.ParseError as exc:
        raise ValueError("ENTSO-E returned invalid XML") from exc

    records: list[dict[str, Any]] = []
    for series in (item for item in root.iter() if _local_name(item) == "TimeSeries"):
        currency = _child_text(series, "currency_Unit.name", "EUR") or "EUR"
        for period in (item for item in series if _local_name(item) == "Period"):
            interval_start = _child_text(period, "start")
            resolution = _child_text(period, "resolution", "PT60M") or "PT60M"
            if not interval_start:
                continue
            start_time = pd.Timestamp(interval_start)
            if start_time.tzinfo is None:
                start_time = start_time.tz_localize("UTC")
            else:
                start_time = start_time.tz_convert("UTC")
            unit_minutes = {"PT15M": 15, "PT30M": 30, "PT60M": 60}.get(resolution)
            if unit_minutes is None:
                raise ValueError(f"Unsupported ENTSO-E resolution: {resolution}")
            for point in (item for item in period if _local_name(item) == "Point"):
                position = _child_text(point, "position")
                amount = _child_text(point, "price.amount")
                if position is None or amount is None:
                    continue
                observed_at = start_time + timedelta(minutes=(int(position) - 1) * unit_minutes)
                records.append({"observed_at": observed_at, "price": amount, "currency": currency})

    normalized = normalize_market_records(
        records,
        "ENTSO-E",
        {"observed_at": "observed_at", "price": "price", "currency": "currency"},
        {"market": "day-ahead", "region": in_domain, "commodity": "electricity", "unit": "MWh"},
    )
    return normalized


def fetch_http_market_data(source: dict[str, Any]) -> pd.DataFrame:
    """Fetch and normalize a configured JSON, CSV, or XML price feed."""
    source_name = source.get("name")
    url = source.get("url")
    response_format = source.get("format", "json").lower()
    if not source_name or not url:
        raise ValueError("HTTP feed requires name and url")

    headers = dict(source.get("headers", {}))
    params = dict(source.get("params", {}))
    request_auth = None
    username_env = source.get("username_env")
    password_env = source.get("password_env")
    if username_env or password_env:
        if not username_env or not password_env:
            raise ValueError(f"HTTP feed {source_name} must configure both username_env and password_env")
        username = os.getenv(username_env)
        password = os.getenv(password_env)
        if not username or not password:
            raise ValueError(f"HTTP feed {source_name} requires environment variables {username_env} and {password_env}")
        request_auth = (username, password)

    token_env = source.get("token_env")
    if token_env:
        token = os.getenv(token_env)
        if not token:
            raise ValueError(f"HTTP feed {source_name} requires environment variable {token_env}")
        header_name = source.get("auth_header", "Authorization")
        prefix = source.get("auth_prefix", "Bearer ")
        headers[header_name] = f"{prefix}{token}"

    api_key_env = source.get("api_key_env")
    if api_key_env:
        api_key = os.getenv(api_key_env)
        if not api_key:
            raise ValueError(f"HTTP feed {source_name} requires environment variable {api_key_env}")
        params[source.get("api_key_param", "access_key")] = api_key

    response = requests.get(
        url,
        params=params,
        headers=headers,
        auth=request_auth,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    if response_format == "csv":
        records = pd.read_csv(StringIO(response.text)).to_dict(orient="records")
    elif response_format == "json":
        payload = response.json()
        records_path = source.get("records_path")
        if records_path:
            for part in records_path.split("."):
                payload = payload[part]
        elif isinstance(payload, dict):
            payload = payload.get("data", payload.get("results", payload))
        if isinstance(payload, dict):
            payload = [payload]
        if not isinstance(payload, list):
            raise ValueError(f"HTTP feed {source_name} did not return a list of records")
        records = payload
    elif response_format == "xml":
        try:
            root = ET.fromstring(response.content)
        except ET.ParseError as exc:
            raise ValueError(f"HTTP feed {source_name} returned invalid XML") from exc
        record_tag = source.get("record_tag")
        if not record_tag:
            raise ValueError(f"HTTP feed {source_name} must configure record_tag for XML")
        records = []
        for element in root.iter():
            if _local_name(element) != record_tag:
                continue
            record = {key: value for key, value in element.attrib.items()}
            for child in element.iter():
                if child is element or child.text is None or len(child) > 0:
                    continue
                record[_local_name(child)] = child.text.strip()
            if record:
                records.append(record)
        records_path = source.get("records_path")
        if records_path:
            raise ValueError("records_path is not supported for XML; select the repeated node with record_tag")
    else:
        raise ValueError(f"Unsupported feed format '{response_format}' for {source_name}; use json, csv, or xml")

    return normalize_market_records(
        records,
        source_name,
        source.get("field_map", {}),
        source.get("defaults", {}),
    )


def load_feed_config(config_path: str | Path) -> list[dict[str, Any]]:
    """Read source descriptors from JSON; credentials are referenced by env var."""
    with Path(config_path).open(encoding="utf-8") as config_file:
        config = json.load(config_file)
    sources = config.get("sources") if isinstance(config, dict) else None
    if not isinstance(sources, list):
        raise ValueError("Feed config must be a JSON object with a 'sources' list")
    return sources


def fetch_configured_sources(sources: list[dict[str, Any]]) -> tuple[pd.DataFrame, list[str]]:
    """Fetch each configured source independently and retain usable feeds on failures."""
    frames: list[pd.DataFrame] = []
    errors: list[str] = []
    for source in sources:
        name = str(source.get("name", source.get("type", "unnamed source")))
        if source.get("enabled", True) is False:
            LOGGER.info("Market feed disabled: %s", name)
            continue
        try:
            source_type = source.get("type")
            if source_type == "eia_retail":
                key_env = source.get("api_key_env", "EIA_API_KEY")
                api_key = os.getenv(key_env)
                if not api_key:
                    raise ValueError(f"missing environment variable {key_env}")
                frame = fetch_eia_retail_prices(
                    api_key,
                    source["start"],
                    source["end"],
                    source.get("state"),
                    source.get("sector"),
                )
            elif source_type == "eia_petroleum":
                key_env = source.get("api_key_env", "EIA_API_KEY")
                api_key = os.getenv(key_env)
                if not api_key:
                    raise ValueError(f"missing environment variable {key_env}")
                frame = fetch_eia_petroleum_prices(
                    api_key,
                    source["product_code"],
                    source.get("region_code", "NUS"),
                    source.get("start"),
                    source.get("end"),
                    source.get("commodity"),
                )
            elif source_type == "entsoe_day_ahead":
                token_env = source.get("token_env", "ENTSOE_API_TOKEN")
                api_token = os.getenv(token_env)
                if not api_token:
                    raise ValueError(f"missing environment variable {token_env}")
                frame = fetch_entsoe_day_ahead_prices(
                    api_token,
                    source["in_domain"],
                    pd.Timestamp(source["period_start"]).to_pydatetime(),
                    pd.Timestamp(source["period_end"]).to_pydatetime(),
                    source.get("out_domain"),
                )
            elif source_type == "commodities_api_latest":
                key_env = source.get("api_key_env", "COMMODITIES_API_KEY")
                api_key = os.getenv(key_env)
                if not api_key:
                    raise ValueError(f"missing environment variable {key_env}")
                frame = fetch_commodities_api_latest(
                    api_key,
                    source["symbols"],
                    source.get("base_currency", "USD"),
                    source.get("region", "global benchmark"),
                    source.get("commodity_aliases"),
                    source.get("market", "commodity benchmark"),
                )
            elif source_type == "http":
                frame = fetch_http_market_data(source)
            else:
                raise ValueError(f"unsupported source type {source_type!r}")
            frames.append(frame)
        except (KeyError, ValueError, requests.RequestException, ET.ParseError) as exc:
            message = f"{name}: {_redact_secrets(str(exc))}"
            LOGGER.warning("Market feed failed: %s", message)
            errors.append(message)

    if not frames:
        return empty_market_data(), errors
    return pd.concat(frames, ignore_index=True)[MARKET_COLUMNS], errors


def build_cross_source_spreads(observations: pd.DataFrame) -> pd.DataFrame:
    """Find comparable gross price spreads without implying executable arbitrage."""
    columns = [
        "observed_at",
        "market",
        "commodity",
        "region",
        "unit",
        "currency",
        "buy_from_source",
        "buy_company",
        "buy_price",
        "sell_to_source",
        "sell_company",
        "sell_price",
        "gross_spread",
        "gross_spread_pct",
        "source_count",
        "quote_count",
    ]
    if observations.empty:
        return pd.DataFrame(columns=columns)

    normalized = observations.copy()
    normalized["observed_at"] = pd.to_datetime(normalized["observed_at"], utc=True, errors="coerce")
    normalized["price"] = pd.to_numeric(normalized["price"], errors="coerce")
    normalized = normalized.dropna(subset=["observed_at", "price"])
    for flag_column in ("is_stale", "is_synthetic"):
        if flag_column in normalized:
            normalized[flag_column] = normalized[flag_column].map(_parse_optional_bool).astype("boolean")
        else:
            normalized[flag_column] = pd.Series(pd.NA, index=normalized.index, dtype="boolean")
    normalized = normalized.loc[~normalized["is_stale"].fillna(False) & ~normalized["is_synthetic"].fillna(False)]
    if normalized.empty:
        return pd.DataFrame(columns=columns)
    group_columns = ["observed_at", "market", "commodity", "region", "unit", "currency"]
    opportunities: list[dict[str, Any]] = []
    for keys, group in normalized.groupby(group_columns, dropna=False):
        group = group.copy()
        group["quote_name"] = group["company"].where(group["company"].notna(), group["source"])
        quote_prices = group.groupby("quote_name", as_index=False)["price"].mean()
        if len(quote_prices) < 2:
            continue
        low_index = quote_prices["price"].idxmin()
        high_index = quote_prices["price"].idxmax()
        low_quote = quote_prices.loc[low_index]
        high_quote = quote_prices.loc[high_index]
        low = group.loc[group["quote_name"] == low_quote["quote_name"]].iloc[0]
        high = group.loc[group["quote_name"] == high_quote["quote_name"]].iloc[0]
        low_price = float(low_quote["price"])
        high_price = float(high_quote["price"])
        spread = high_price - low_price
        opportunities.append({
            **dict(zip(group_columns, keys)),
            "buy_from_source": low["source"],
            "buy_company": low["company"],
            "buy_price": low_price,
            "sell_to_source": high["source"],
            "sell_company": high["company"],
            "sell_price": high_price,
            "gross_spread": spread,
            "gross_spread_pct": spread / low_price * 100 if low_price else None,
            "source_count": int(group["source"].nunique()),
            "quote_count": int(len(quote_prices)),
        })
    return pd.DataFrame(opportunities, columns=columns).sort_values(
        "gross_spread_pct", ascending=False, na_position="last"
    ).reset_index(drop=True)


def run_configured_ingestion(
    config_path: str | Path = "data/market_feeds.json",
    output_dir: str | Path = "outputs",
) -> tuple[Path | None, Path | None]:
    """Fetch configured feeds and persist normalized observations and gross spreads."""
    config_file = Path(config_path)
    if not config_file.is_absolute() and not config_file.exists():
        config_file = PROJECT_ROOT / config_file
    if not config_file.exists():
        LOGGER.info("No market feed config at %s; skipping external ingestion", config_file)
        return None, None

    sources = load_feed_config(config_file)
    observations, errors = fetch_configured_sources(sources)
    for error in errors:
        LOGGER.error("Market feed error: %s", error)
    if observations.empty:
        LOGGER.warning("No external market observations were collected")
        return None, None

    output_path = Path(output_dir)
    if not output_path.is_absolute():
        output_path = PROJECT_ROOT / output_path
    output_path.mkdir(parents=True, exist_ok=True)
    observations_path = output_path / "market_observations.csv"
    spreads_path = output_path / "market_spread_opportunities.csv"
    observations.to_csv(observations_path, index=False)
    build_cross_source_spreads(observations).to_csv(spreads_path, index=False)

    if os.getenv("AZURE_STORAGE_UPLOADS", "").lower() in {"1", "true", "yes"}:
        from scripts.ingest import upload_to_blob_storage

        container_name = os.getenv("AZURE_STORAGE_CONTAINER", "energyblob")
        for output_file in (observations_path, spreads_path):
            uploaded_blob = upload_to_blob_storage(
                str(output_file),
                container_name=container_name,
                blob_name=f"market-data/{output_file.name}",
            )
            if uploaded_blob:
                LOGGER.info("Uploaded %s to Azure Blob container %s", uploaded_blob, container_name)
            else:
                LOGGER.error("Could not upload %s to Azure Blob container %s", output_file.name, container_name)

    LOGGER.info("Saved %s observations from %s source(s)", len(observations), observations["source"].nunique())
    return observations_path, spreads_path


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    config_path = os.getenv("ENERGY_FEED_CONFIG", "data/market_feeds.json")
    run_configured_ingestion(config_path)