from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st


def apply_brand_theme() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Space+Grotesk:wght@400;500;600;700&display=swap');

        :root {
            --ink: #10221d;
            --forest: #153b32;
            --paper: #f1f3ec;
            --panel: #ffffff;
            --muted: #64756d;
            --line: #d7dfd7;
            --teal: #147d72;
            --citron: #d5ef59;
            --coral: #e36d4d;
        }
        .stApp {
            color: var(--ink);
            background:
                repeating-linear-gradient(0deg, transparent 0 35px, rgba(21, 59, 50, .025) 35px 36px),
                linear-gradient(145deg, #f5f6f0 0%, var(--paper) 58%, #e8eee7 100%);
            font-family: 'Space Grotesk', 'Segoe UI', sans-serif;
        }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stMainBlockContainer"] {
            max-width: 1440px;
            padding-top: 1.5rem;
            padding-bottom: 3rem;
        }
        .brand-masthead {
            display: flex;
            align-items: flex-end;
            justify-content: space-between;
            gap: 1rem;
            padding: 1.35rem 1.6rem 1.45rem;
            margin-bottom: 1.35rem;
            color: #f5f7ef;
            background:
                repeating-linear-gradient(135deg, rgba(255,255,255,.035) 0 1px, transparent 1px 11px),
                linear-gradient(112deg, #10221d 0%, #153b32 70%, #1c5548 100%);
            border-left: 5px solid var(--citron);
            border-radius: 3px;
        }
        .brand-kicker, .brand-meta, .section-kicker {
            font-family: 'IBM Plex Mono', Consolas, monospace;
            font-size: .72rem;
            letter-spacing: .08em;
            text-transform: uppercase;
        }
        .brand-kicker { color: var(--citron); margin-bottom: .5rem; }
        .brand-title {
            margin: 0;
            font-size: clamp(1.6rem, 3vw, 2.35rem);
            font-weight: 600;
            line-height: 1.05;
        }
        .brand-subtitle { margin: .5rem 0 0; color: #c2d3ca; font-size: .93rem; }
        .brand-meta { color: #d2e1d8; text-align: right; line-height: 1.8; }
        .section-kicker { color: var(--teal); margin: .25rem 0 .25rem; }
        h2, h3 { color: var(--ink); }
        [data-testid="stMetric"] {
            min-height: 116px;
            padding: 1rem 1.05rem;
            background: var(--panel);
            border: 1px solid var(--line);
            border-top: 3px solid var(--teal);
            border-radius: 4px;
            box-shadow: 0 5px 18px rgba(16, 34, 29, .045);
        }
        [data-testid="stMetricLabel"] p {
            color: var(--muted);
            font-family: 'IBM Plex Mono', Consolas, monospace;
            font-size: .72rem;
            text-transform: uppercase;
        }
        [data-testid="stMetricValue"] { color: var(--ink); }
        [data-testid="stTabs"] [role="tab"] {
            color: var(--muted);
            font-weight: 600;
        }
        [data-testid="stTabs"] [aria-selected="true"] { color: var(--teal); }
        .signal-strip {
            min-height: 112px;
            padding: 1rem 1.1rem;
            background: #fff;
            border: 1px solid var(--line);
            border-radius: 4px;
        }
        .signal-label {
            color: var(--muted);
            font-family: 'IBM Plex Mono', Consolas, monospace;
            font-size: .7rem;
            text-transform: uppercase;
        }
        .signal-name { margin: .35rem 0; color: var(--ink); font-size: 1.2rem; font-weight: 700; }
        .signal-detail { color: var(--muted); font-size: .86rem; }
        .signal-index {
            float: right;
            color: var(--forest);
            font-family: 'IBM Plex Mono', Consolas, monospace;
            font-size: 1.5rem;
            font-weight: 600;
        }
        .prototype-note {
            padding: .7rem .9rem;
            color: #604323;
            background: #fff3dc;
            border-left: 3px solid #d79128;
            font-size: .83rem;
        }
        @media (max-width: 700px) {
            [data-testid="stMainBlockContainer"] { padding: .7rem .8rem 2rem; }
            .brand-masthead { align-items: flex-start; flex-direction: column; padding: 1.1rem; }
            .brand-meta { text-align: left; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def load_dashboard_tables(output_dir: str | Path = "outputs") -> dict[str, pd.DataFrame]:
    outputs_path = Path(output_dir)
    return {
        "coefficients": pd.read_csv(outputs_path / "model_coefficients.csv"),
        "metrics": pd.read_csv(outputs_path / "model_metrics.csv"),
        "vif": pd.read_csv(outputs_path / "vif_metrics.csv"),
    }


def render_dashboard(output_dir: str | Path = "outputs") -> None:
    from market_intelligence import generate_company_market_data

    st.set_page_config(page_title="Christark Energy Enterprise", layout="wide")
    apply_brand_theme()
    outputs_path = Path(output_dir)

    st.markdown(
        """
        <header class="brand-masthead">
            <div>
                <div class="brand-kicker">Christark Energy Enterprise / Energyclean</div>
                <h1 class="brand-title">Market intelligence</h1>
                <p class="brand-subtitle">Margin signals, company benchmarks, and model diagnostics</p>
            </div>
            <div class="brand-meta">STRATEGY DESK<br>MARKET FEED MONITOR</div>
        </header>
        """,
        unsafe_allow_html=True,
    )

    tables = load_dashboard_tables(output_dir)
    metrics = tables["metrics"].set_index("Metric")["Value"]

    r_squared = float(metrics["R-Squared"])
    adj_r2 = float(metrics["Adj R-Squared"])
    f_stat = float(metrics["F-Statistic"])
    observations = int(metrics["Observations"])

    rankings_path = outputs_path / "company_market_rankings.csv"
    if rankings_path.exists():
        company_data = pd.read_csv(rankings_path)
    else:
        company_data = generate_company_market_data()
    company_data = company_data.sort_values("profitability_score", ascending=False).reset_index(drop=True)
    top_company = company_data.iloc[0]
    lowest_company = company_data.iloc[-1]
    high_signal_count = int(company_data["arbitrage_signal"].eq("High").sum())
    mean_renewable_mix = float(company_data["renewable_mix_pct"].mean())

    st.markdown('<div class="section-kicker">01 / Market pulse</div>', unsafe_allow_html=True)
    metric_cols = st.columns(4)
    metric_cols[0].metric("Highest model score", f"{top_company['profitability_score']:.1f}", help=top_company["company_name"])
    metric_cols[1].metric("High signal names", f"{high_signal_count:02d}", help="Illustrative arbitrage signal labels")
    metric_cols[2].metric("Average renewable mix", f"{mean_renewable_mix:.1f}%")
    metric_cols[3].metric("Companies tracked", f"{len(company_data):02d}")

    observations_path = outputs_path / "market_observations.csv"
    spreads_path = outputs_path / "market_spread_opportunities.csv"
    st.markdown('<div class="section-kicker">02 / External market feeds</div>', unsafe_allow_html=True)
    if observations_path.exists():
        feed_observations = pd.read_csv(observations_path, parse_dates=["observed_at"])
        source_count = feed_observations["source"].nunique() if not feed_observations.empty else 0
        latest_observation = feed_observations["observed_at"].max() if not feed_observations.empty else None
        stale_values = feed_observations.get("is_stale", pd.Series(False, index=feed_observations.index))
        synthetic_values = feed_observations.get("is_synthetic", pd.Series(False, index=feed_observations.index))
        stale_count = stale_values.astype("string").str.lower().eq("true").sum()
        synthetic_count = synthetic_values.astype("string").str.lower().eq("true").sum()
        feed_cols = st.columns(4)
        feed_cols[0].metric("Market observations", f"{len(feed_observations):,}")
        feed_cols[1].metric("Active sources", f"{source_count:02d}")
        feed_cols[2].metric("Stale / synthetic", f"{stale_count} / {synthetic_count}")
        feed_cols[3].metric(
            "Latest observation",
            latest_observation.strftime("%Y-%m-%d %H:%M UTC") if pd.notna(latest_observation) else "None",
        )
        if spreads_path.exists():
            spreads = pd.read_csv(spreads_path)
            if not spreads.empty:
                st.markdown("#### Comparable gross price spreads")
                st.caption("Rows require matching commodity, region, timestamp, currency, and unit. Fees, transport, taxes, and execution risk are not included.")
                st.dataframe(spreads.head(20), width="stretch", hide_index=True)
            else:
                st.info("No cross-source spreads matched on all comparison dimensions in this run.")
    else:
        st.info("No observations saved yet. Run scripts/web_data_ingestion.py and review its source-level status messages.")

    st.markdown('<div class="section-kicker">03 / Benchmark leaders</div>', unsafe_allow_html=True)
    leader_cols = st.columns(2)
    with leader_cols[0]:
        st.markdown(
            f'<div class="signal-strip"><span class="signal-index">{top_company["profitability_score"]:.1f}</span>'
            f'<div class="signal-label">Leading model score</div><div class="signal-name">{top_company["company_name"]}</div>'
            f'<div class="signal-detail">{top_company["sector"]} · {top_company["service"]}</div></div>',
            unsafe_allow_html=True,
        )
    with leader_cols[1]:
        st.markdown(
            f'<div class="signal-strip"><span class="signal-index">{lowest_company["profitability_score"]:.1f}</span>'
            f'<div class="signal-label">Lowest model score</div><div class="signal-name">{lowest_company["company_name"]}</div>'
            f'<div class="signal-detail">{lowest_company["sector"]} · {lowest_company["service"]}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-kicker">04 / Company ranking</div>', unsafe_allow_html=True)
    chart_col, table_col = st.columns([0.9, 1.35], gap="large")
    with chart_col:
        st.markdown("### Profitability index")
        st.bar_chart(
            company_data.set_index("company_name")[["profitability_score"]],
            height=360,
            color="#147d72",
        )
    with table_col:
        st.markdown("### Compare companies")
        sectors = ["All sectors", *sorted(company_data["sector"].unique())]
        selected_sector = st.selectbox("Sector", sectors, label_visibility="collapsed")
        filtered_data = company_data
        if selected_sector != "All sectors":
            filtered_data = company_data.loc[company_data["sector"] == selected_sector]

        display_df = filtered_data[[
            "company_name",
            "sector",
            "gross_margin_pct",
            "profitability_score",
            "arbitrage_score",
            "arbitrage_signal",
        ]].rename(columns={
            "company_name": "Company",
            "sector": "Sector",
            "gross_margin_pct": "Margin %",
            "profitability_score": "Profit index",
            "arbitrage_score": "Signal score",
            "arbitrage_signal": "Signal",
        })
        st.dataframe(
            display_df,
            width="stretch",
            hide_index=True,
            height=360,
            column_config={
                "Margin %": st.column_config.NumberColumn(format="%.1f%%"),
                "Profit index": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f"),
                "Signal score": st.column_config.NumberColumn(format="%.1f"),
            },
        )

    st.markdown(
        '<div class="prototype-note"><strong>Interpretation:</strong> company rankings and signal labels are illustrative. '
        'Provider demo observations are explicitly marked synthetic; compare only matching instruments and verify source timestamps. '
        'Displayed gross spreads are not executable returns.</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-kicker">05 / Model diagnostics</div>', unsafe_allow_html=True)
    model_cols = st.columns(4)
    model_cols[0].metric("R-squared", f"{r_squared:.3f}")
    model_cols[1].metric("Adjusted R-squared", f"{adj_r2:.3f}")
    model_cols[2].metric("F-statistic", f"{f_stat:.1f}")
    model_cols[3].metric("Observations", f"{observations}")

    tab1, tab2, tab3 = st.tabs(["Model summary", "Coefficients", "VIF diagnostics"])

    with tab1:
        st.dataframe(metrics.reset_index().rename(columns={"index": "Metric", 0: "Value"}), width="stretch", hide_index=True)

    with tab2:
        st.dataframe(tables["coefficients"], width="stretch", hide_index=True)

    with tab3:
        st.dataframe(tables["vif"], width="stretch", hide_index=True)


if __name__ == "__main__":
    render_dashboard()
