# Project Status and Portfolio Brief

**Prepared:** 2026-10-10  
**Project:** Christark Energy Economics & Margin Intelligence Hub

## Executive Summary

The Python/Streamlit prototype has been expanded into an Azure-hosted market-data monitor. It is deployed on an existing Linux VM as a systemd service, uses a VM managed identity for Azure Blob access, and has successfully written normalized market observations and spread output to a private Blob container. A serverless Azure SQL database has been provisioned with Entra-only administration, but it is not yet populated or connected to the application. The requested Logic App alert workflow is not yet deployed.

The current data setup is a **public-data/demo environment**, not a production trading system. EIA contributes real weekly U.S. retail pump-price data; OilPriceAPI's no-key demo feed is explicitly synthetic. Company rankings remain illustrative. No realized profit, investment outcome, or executable arbitrage has been established.

## Delivered and Verified

- Python analytics pipeline with synthetic operational data, OLS regression, VIF diagnostics, Excel exports, and stakeholder summaries.
- Streamlit dashboard branded for Christark Energy, with company comparisons, feed status, freshness indicators, and model diagnostics.
- Multi-source ingestion adapters for EIA weekly petroleum and retail electricity, ENTSO-E, Commodities-API, OilPriceAPI, and configurable licensed HTTP XML/CSV/JSON feeds.
- Normalized market observations preserve source, timestamps, units, currency, region, market, and stale/synthetic markers.
- Cross-source gross spreads are emitted only when comparison dimensions match; explicitly stale or synthetic rows are excluded.
- Azure VM deployment runs under systemd and binds Streamlit to loopback (`127.0.0.1:8501`); no public web ingress or TLS endpoint has been configured.
- VM managed identity has Blob Data Contributor access. VM ingestion reported HTTP 201 writes for `market-data/market_observations.csv` and `market-data/market_spread_opportunities.csv` in the private `energyblob` container.
- Market ingestion test run collected 80 weekly EIA U.S. gasoline/diesel rows and 20 OilPriceAPI demo quotes. The demo quotes were marked synthetic; no comparable spread was reported.
- Azure SQL server `energysql-christark-20261010-01` and database `marketdata` were created in Central US. SQL uses serverless General Purpose, 1 vCore, 0.5 minimum capacity, 60-minute auto-pause, Entra-only authentication, and a firewall rule limited to the VM's public IP.
- A deployment bundle was staged privately in Blob. Temporary developer upload permission was removed after staging.

## Remaining Work

1. Create the Logic App `energyalertlogic` for the agreed weekly EIA alert: notify when gasoline or diesel changes by at least 5% week over week. The Outlook connector needs user authorization before email delivery works.
2. Define and apply a SQL schema, then connect the app or ingestion pipeline to `marketdata`; the database currently has no application tables and is not used by the dashboard.
3. Decide how to expose the dashboard securely beyond VM loopback. No public NSG rule was opened. Recommended next step is a TLS reverse proxy or managed application gateway with authentication, not exposing Streamlit directly.
4. Configure a personal EIA API key for ongoing service use. The VM test used the public demo key; no private provider keys are stored in the repository or deployment bundle.
5. Obtain licensed station/brand data (for example OPIS) if the business requires actual competitor-level local pump-price comparisons. Current public and demo feeds do not support executable station arbitrage.
6. Configure a GitHub remote and choose repository visibility before publishing.

## Portfolio Positioning

This is suitable to present as a **portfolio project / Azure data-engineering prototype**. It demonstrates Python data ingestion and normalization, API adapter design, time-series comparison safeguards, a Streamlit dashboard, Azure managed identity, Blob Storage, VM systemd deployment, and automated tests.

Suggested CV bullets:

- Built a Python energy-market intelligence pipeline integrating EIA petroleum data and configurable commodity/vendor APIs into a normalized, provenance-preserving dataset.
- Deployed a Streamlit dashboard to an Azure Linux VM and used managed identity plus scoped RBAC to persist ingestion outputs to Azure Blob Storage.
- Implemented cross-source spread checks that enforce matching market, timestamp, product, region, currency, and units while excluding stale or synthetic observations.

Describe company scoring as **illustrative** and spreads as **gross analytical signals**, not proven arbitrage or returns. Do not claim live OPIS/GlobalPetrolPrices data, completed email alerting, or a SQL-backed application until those pieces are implemented and verified.

## GitHub Readiness

The working tree had no commits and no configured Git remote at the time of this report. `.gitignore` now excludes the local feed config, generated outputs, virtual environments, caches, and secret files. Keep `data/market_feeds.json` and all API keys out of Git. Before the first push, review `git status`, scan staged files for credentials, choose public/private visibility, add the intended GitHub remote, and create the initial commit.
