# Energy Economics & Margin Intelligence Hub

## Overview
This project creates a market intelligence workflow for energy economics, margin analysis, company benchmarking, and arbitrage opportunity detection. It combines synthetic and extensible data, econometric analysis, Excel-ready exports, stakeholder summaries, and a vibrant dashboard interface.

## Business use case
The platform is designed to support:
- comparison across multiple energy companies and suppliers
- analysis of market cost exposures and pricing spread
- detection of short-run and long-run arbitrage opportunities
- review of profitability, reliability, and service quality across competitor groups
- stakeholder readouts for business leaders, investors, and internal decision-makers

## Core workflow
1. Generate local market and operational data.
2. Fit an OLS model for spot price vs. load and margin.
3. Run VIF diagnostics to test multicollinearity.
4. Compare multiple company profiles and model profitability/risk.
5. Export the Power BI-ready workbook.
6. Package a stakeholder summary in Excel and Word.
7. Open a branded dashboard for quick operational review.

## Run the pipeline
```powershell
cd "C:/Users/USER/Documents/energy-economics-hub"
.\.venv\Scripts\python run_pipeline.py
```

## Open the dashboard
```powershell
cd "C:/Users/USER/Documents/energy-economics-hub"
.\.venv\Scripts\streamlit run dashboard.py
```

## Stakeholder outputs
Generated files live in the outputs folder:
- energy_hub_data.xlsx
- stakeholder_summary.xlsx
- stakeholder_summary.docx
- company_market_rankings.csv

## Azure Deployment Status
The Streamlit application is deployed as a systemd service on an existing Linux VM. It listens on `127.0.0.1:8501` on the VM; public ingress, TLS termination, and user authentication have not been configured. The VM's system-assigned managed identity has **Storage Blob Data Contributor** at the storage-account scope.

The service uses `AZURE_STORAGE_ACCOUNT=energystoragechris`, `AZURE_STORAGE_CONTAINER=energyblob`, and `AZURE_STORAGE_UPLOADS=true`. Market ingestion writes `market-data/market_observations.csv` and `market-data/market_spread_opportunities.csv` with managed identity. The latest VM ingestion logged successful Blob writes. The local developer config and provider credentials are not included in this repository.

The `marketdata` Azure SQL database exists on a low-cost serverless SQL server with Entra-only administration and a firewall rule limited to the VM's public IP. The database is not yet populated with a schema, and the application is not yet connected to SQL. The `energyalertlogic` workflow has not yet been created; the requested weekly 5% EIA gasoline/diesel alert still needs its Outlook connector authorized and deployed.

The VM bootstrap in `deploy/vm_bootstrap.sh` verifies systemd service activation rather than blocking on an immediate HTTP request. From inside the VM, the optional health URL is `http://127.0.0.1:8501/_stcore/health`.

## Multi-source data strategy
The source adapter supports EIA monthly U.S. retail electricity prices, EIA weekly U.S. gasoline/diesel retail prices, ENTSO-E day-ahead prices, Commodities-API latest commodity quotes, and authenticated HTTP JSON/CSV/XML feeds such as OilPriceAPI and licensed GlobalPetrolPrices/OPIS feeds.

EIA Petroleum uses the verified `petroleum/pri/gnd` series. `EPMR` is regular gasoline, `EPD2D` is No. 2 diesel, `PTE` is retail sales, and `NUS` is the U.S. geography code. Other valid areas include PADD and selected state/city codes; query EIA's facet endpoint for the current catalogue. This series is **weekly retail pump pricing**, not intraday spot data, and its response provides units such as `$/GAL`.

OilPriceAPI provides source-timestamped crude and refined-product benchmark codes such as `BRENT_CRUDE_USD`, `WTI_USD`, and `GASOLINE_USD`; check `stale`, `synthetic`, `as_of`, and `unit` before interpretation. Its current docs describe a 7-day trial with 10,000 requests and then a free quota of 50 requests/day; verify current plan terms at signup. Commodities-API provides plan-dependent symbol/quote access. Its commodity rates are inverse ratios, so this adapter applies the documented reciprocal and preserves the API's returned unit. Futures and spot quotes remain distinct instruments.

For retail petrol prices, **GlobalPetrolPrices** offers a licensed XML API covering national fuel prices across 135 countries, weekly series, and state/city data for selected markets; access is subscription-based, with a two-week trial. **OPIS** is the better fit for granular station/brand competition and custom regional prices/margins, but those are licensed commercial products and OPIS must supply the feed format and access details.

Request a GlobalPetrolPrices feed/trial at https://www.globalpetrolprices.com/data_access.php. For OPIS custom retail feeds, start at https://www.opis.com/product/pricing/retail/customized-retail-fuel-prices/ or contact its sales team. Do not scrape either site's pages; use the licensed feed and comply with its terms.

Copy `data/market_feeds.example.json` to `data/market_feeds.json`, set `enabled` to `true` only for feeds you have configured, and replace placeholders with provider-issued URLs/schema. The example entries are all disabled to prevent accidental requests to placeholder URLs. EIA uses `EPMR`/`EPD2D` products and `NUS` for national U.S.; OilPriceAPI and Commodities-API codes must be selected from each provider's catalog. GlobalPetrolPrices provides country and selected state/city data; OPIS supplies its region/station identifiers with the licensed feed. These are not ENTSO-E EIC codes. Set credentials in environment variables; local config and `.env` files are ignored by Git.

Example PowerShell setup:
```powershell
Copy-Item data/market_feeds.example.json data/market_feeds.json
$env:EIA_API_KEY = "your-eia-key"
$env:ENTSOE_API_TOKEN = "your-entsoe-token"
$env:COMMODITIES_API_KEY = "your-commodities-api-key"
$env:OILPRICEAPI_KEY = "your-oilpriceapi-key"
$env:FUEL_FEED_USERNAME = "your-provider-username"
$env:FUEL_FEED_PASSWORD = "your-provider-password"
\.\.venv\Scripts\python scripts/web_data_ingestion.py
```

The normalized `outputs/market_observations.csv` records source, underlying source detail, market, company, region, commodity, timestamp, currency, unit, and freshness flags. `outputs/market_spread_opportunities.csv` excludes explicitly stale/synthetic observations and only compares records matching market, timestamp, commodity, region, currency, and unit. These are **gross observed spreads**, not executable arbitrage: tariffs, transport, fees, taxes, capacity, timing, and execution constraints still need to be modeled. EIA weekly values and crude/product benchmarks are not equivalent to station-level competitor quotes.

The pipeline runs configured feed ingestion when `data/market_feeds.json` exists and skips external feeds cleanly otherwise. The dashboard shows feed status and comparable spreads when output data is available.

Company rankings currently use illustrative synthetic records, not live company disclosures, quotes, or realized returns. Scores are comparative prototype metrics and do not imply a guaranteed profit, including a 70% return. Connect and validate licensed/current feeds before using results for trading or investment decisions.

## Energyclean brand vision
The dashboard theme uses a Christark Energy Enterprise energyclean aesthetic with a dark green, teal, and gold-inspired interface to highlight operational performance, margin strength, and opportunity signals.

## Feed adapter reference
The adapter implementation is in `scripts/web_data_ingestion.py`. Official references:
- EIA API key signup: https://www.eia.gov/opendata/register.php
- https://www.eia.gov/opendata/documentation.php
- EIA Petroleum route browser: https://www.eia.gov/opendata/browser/petroleum/pri
- Commodities-API documentation and symbols: https://commodities-api.com/documentation and https://commodities-api.com/symbols
- OilPriceAPI quick start: https://docs.oilpriceapi.com/quick-start/
- https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html

