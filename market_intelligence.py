from __future__ import annotations

from pathlib import Path

import pandas as pd


def generate_company_market_data() -> pd.DataFrame:
    """Generate a 10-company market sample with energy pricing and profit signals.

    This represents a realistic benchmark layer before live website extraction is
    added. It supports comparison across energy suppliers, traders, and service
    providers, with metrics that can be mapped to future external data feeds.
    """
    companies = [
        {
            "company_name": "Christark Energy",
            "sector": "Utilities",
            "service": "Grid transition and commercial energy procurement",
            "energy_cost_per_mwh": 72.6,
            "avg_sale_price_per_mwh": 118.5,
            "gross_margin_pct": 28.4,
            "market_share_pct": 17.4,
            "renewable_mix_pct": 64.0,
            "demand_growth_pct": 9.1,
            "cost_variance_pct": 6.8,
            "arbitrage_signal": "High",
            "profitability_score": 93.1,
            "service_reliability_score": 91.2,
        },
        {
            "company_name": "NorthArc Power",
            "sector": "Power trading",
            "service": "Short-term power arbitrage and balancing",
            "energy_cost_per_mwh": 68.2,
            "avg_sale_price_per_mwh": 111.2,
            "gross_margin_pct": 25.8,
            "market_share_pct": 15.1,
            "renewable_mix_pct": 58.0,
            "demand_growth_pct": 8.3,
            "cost_variance_pct": 7.2,
            "arbitrage_signal": "High",
            "profitability_score": 89.7,
            "service_reliability_score": 88.6,
        },
        {
            "company_name": "BluePeak Energy",
            "sector": "Renewables",
            "service": "Utility-scale renewable supply contracts",
            "energy_cost_per_mwh": 60.4,
            "avg_sale_price_per_mwh": 104.1,
            "gross_margin_pct": 24.9,
            "market_share_pct": 13.6,
            "renewable_mix_pct": 86.0,
            "demand_growth_pct": 11.2,
            "cost_variance_pct": 5.6,
            "arbitrage_signal": "Moderate",
            "profitability_score": 86.4,
            "service_reliability_score": 90.1,
        },
        {
            "company_name": "Solstice Grid",
            "sector": "Distributed energy",
            "service": "Commercial rooftop and storage optimization",
            "energy_cost_per_mwh": 59.8,
            "avg_sale_price_per_mwh": 99.0,
            "gross_margin_pct": 22.1,
            "market_share_pct": 12.7,
            "renewable_mix_pct": 81.0,
            "demand_growth_pct": 10.6,
            "cost_variance_pct": 6.2,
            "arbitrage_signal": "Moderate",
            "profitability_score": 82.3,
            "service_reliability_score": 87.4,
        },
        {
            "company_name": "Horizon FuelWorks",
            "sector": "Energy services",
            "service": "Industrial energy management and optimization",
            "energy_cost_per_mwh": 74.9,
            "avg_sale_price_per_mwh": 116.4,
            "gross_margin_pct": 25.1,
            "market_share_pct": 11.9,
            "renewable_mix_pct": 52.0,
            "demand_growth_pct": 7.4,
            "cost_variance_pct": 8.1,
            "arbitrage_signal": "Moderate",
            "profitability_score": 80.9,
            "service_reliability_score": 85.7,
        },
        {
            "company_name": "Summit Gas & Power",
            "sector": "Gas-to-power",
            "service": "Integrated generation and retail supply",
            "energy_cost_per_mwh": 81.5,
            "avg_sale_price_per_mwh": 120.7,
            "gross_margin_pct": 23.0,
            "market_share_pct": 10.8,
            "renewable_mix_pct": 38.0,
            "demand_growth_pct": 6.9,
            "cost_variance_pct": 10.1,
            "arbitrage_signal": "Moderate",
            "profitability_score": 77.5,
            "service_reliability_score": 83.5,
        },
        {
            "company_name": "TerraVolt",
            "sector": "Clean energy",
            "service": "Battery-backed energy resale and peak shaving",
            "energy_cost_per_mwh": 67.8,
            "avg_sale_price_per_mwh": 97.6,
            "gross_margin_pct": 20.8,
            "market_share_pct": 9.4,
            "renewable_mix_pct": 79.0,
            "demand_growth_pct": 12.5,
            "cost_variance_pct": 7.9,
            "arbitrage_signal": "High",
            "profitability_score": 74.6,
            "service_reliability_score": 86.9,
        },
        {
            "company_name": "Cinderline Renewables",
            "sector": "Generation",
            "service": "Flexible generation and industrial power hedging",
            "energy_cost_per_mwh": 88.1,
            "avg_sale_price_per_mwh": 121.3,
            "gross_margin_pct": 19.5,
            "market_share_pct": 8.9,
            "renewable_mix_pct": 44.0,
            "demand_growth_pct": 5.7,
            "cost_variance_pct": 11.4,
            "arbitrage_signal": "Low",
            "profitability_score": 70.2,
            "service_reliability_score": 79.3,
        },
        {
            "company_name": "DeltaLoad Energy",
            "sector": "Retail",
            "service": "Regional energy retail and demand response",
            "energy_cost_per_mwh": 79.0,
            "avg_sale_price_per_mwh": 102.4,
            "gross_margin_pct": 18.7,
            "market_share_pct": 8.1,
            "renewable_mix_pct": 46.0,
            "demand_growth_pct": 6.3,
            "cost_variance_pct": 9.0,
            "arbitrage_signal": "Low",
            "profitability_score": 67.8,
            "service_reliability_score": 81.2,
        },
        {
            "company_name": "PulseGrid Ltd",
            "sector": "Infrastructure",
            "service": "Urban load balancing and backup power",
            "energy_cost_per_mwh": 92.3,
            "avg_sale_price_per_mwh": 114.8,
            "gross_margin_pct": 17.8,
            "market_share_pct": 7.2,
            "renewable_mix_pct": 33.0,
            "demand_growth_pct": 4.8,
            "cost_variance_pct": 12.2,
            "arbitrage_signal": "Low",
            "profitability_score": 62.4,
            "service_reliability_score": 76.8,
        },
    ]

    df = pd.DataFrame(companies)
    df["arbitrage_score"] = (
        df["gross_margin_pct"] * 0.5 + df["renewable_mix_pct"] * 0.3 + df["demand_growth_pct"] * 0.2
    )
    return df


def build_market_rankings(companies: pd.DataFrame) -> pd.DataFrame:
    """Rank companies by profitability and identify unusual arbitrage opportunities."""
    rankings = companies.copy()
    rankings = rankings.sort_values(["profitability_score", "arbitrage_score"], ascending=[False, False]).reset_index(drop=True)
    return rankings


def export_market_rankings(
    output_dir: str | Path = "outputs",
    filename: str = "company_market_rankings.csv",
) -> Path:
    """Persist ranked company market intelligence to CSV."""
    outputs_path = Path(output_dir)
    outputs_path.mkdir(parents=True, exist_ok=True)
    rankings = build_market_rankings(generate_company_market_data())
    output_path = outputs_path / filename
    rankings.to_csv(output_path, index=False)
    return output_path


if __name__ == "__main__":
    export_market_rankings()
