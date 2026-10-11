from pathlib import Path
import logging
import sys
import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from risk_app.config import DB_PATH
from risk_app.logging_config import configure_logging
from risk_app.ingestion import sample_items, analyze_items, fetch_rss, normalize_import
from risk_app.nlp import analyze_text
from risk_app.portfolio import default_portfolio, SCENARIOS, stress_portfolio, class_contributions
from risk_app.signals import generate_risk_signal
from risk_app.storage import save_feed_items, save_stress_run, load_history

configure_logging()
log = logging.getLogger(__name__)
st.set_page_config(page_title="RiskLens | Financial Risk Intelligence", page_icon="◈", layout="wide")
st.markdown("""<style>
.block-container{padding-top:1.5rem;max-width:1500px}
[data-testid="stMetric"]{background:linear-gradient(135deg,#111c31,#172844);padding:16px 18px;border:1px solid #293e5d;border-radius:14px}
[data-testid="stMetricLabel"]{color:#a9bdd8}
h1,h2,h3{letter-spacing:-.03em}
div[data-testid="stTabs"] button{font-weight:600}
.risk-note{background:#172844;border-left:4px solid #57c8b5;padding:12px 16px;border-radius:8px}
</style>""", unsafe_allow_html=True)

st.title("◈ RiskLens")
st.caption("FINANCIAL RISK INTELLIGENCE  /  EVENT-DRIVEN PORTFOLIO STRESS TESTING")
st.markdown('<div class="risk-note">Demo environment: bundled headlines and social posts are explicitly <b>SYNTHETIC</b>. Scores are decision-support heuristics, not investment advice or calibrated forecasts.</div>', unsafe_allow_html=True)

@st.cache_data
def get_demo_feed():
    return analyze_items(sample_items())

if "feed" not in st.session_state:
    st.session_state.feed = get_demo_feed()
if "portfolio" not in st.session_state:
    st.session_state.portfolio = default_portfolio()

feed = st.session_state.feed
portfolio = st.session_state.portfolio

with st.sidebar:
    st.header("Data controls")
    st.caption("No API keys required for the bundled demo.")
    if st.button("↻ Reset to bundled demo data", use_container_width=True):
        st.session_state.feed = get_demo_feed()
        st.session_state.portfolio = default_portfolio()
        st.rerun()
    rss_url = st.text_input("Optional RSS feed URL", placeholder="https://example.com/rss.xml")
    if st.button("Fetch RSS feed", use_container_width=True):
        rss = fetch_rss(rss_url)
        if rss.empty:
            st.warning("No RSS items fetched. Check URL/network; bundled demo remains available.")
        else:
            st.session_state.feed = pd.concat([feed, analyze_items(rss)], ignore_index=True)
            st.success(f"Fetched {len(rss)} real RSS items.")
            st.rerun()
    uploaded = st.file_uploader("Import CSV or JSON", type=["csv","json"])
    if uploaded and st.button("Import and analyze", use_container_width=True):
        try:
            imported = analyze_items(normalize_import(uploaded))
            st.session_state.feed = pd.concat([feed, imported], ignore_index=True)
            st.success(f"Imported {len(imported)} records.")
            st.rerun()
        except Exception as exc:
            st.error(f"Import failed: {exc}")
    st.divider()
    st.caption("Storage: SQLite local file")
    st.code(str(DB_PATH), language=None)

tab_overview, tab_feed, tab_nlp, tab_portfolio, tab_stress, tab_history = st.tabs([
    "Overview", "News & Social Feed", "Manual NLP", "Portfolio", "Stress Test Lab", "History & Exports"
])

with tab_overview:
    total_value = float(portfolio["market_value"].sum())
    negative = int((feed["sentiment"] < -.1).sum()) if not feed.empty else 0
    high = int((feed["impact"] >= 7).sum()) if not feed.empty else 0
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Portfolio market value", f"${total_value/1e6:,.2f}M")
    c2.metric("Analyzed signals", f"{len(feed):,}")
    c3.metric("High-impact events", f"{high}", help="Impact score ≥ 7/10")
    c4.metric("Negative sentiment", f"{negative}", help="Signed sentiment below -0.1")
    left,right = st.columns([1.1,1])
    with left:
        st.subheader("Signal landscape")
        if not feed.empty:
            ev = feed.groupby("event_type", as_index=False).size().sort_values("size", ascending=False)
            st.plotly_chart(px.bar(ev, x="event_type", y="size", color="event_type", title="Events by category"), use_container_width=True)
    with right:
        st.subheader("Portfolio allocation")
        alloc = portfolio.groupby("asset_class", as_index=False)["market_value"].sum()
        st.plotly_chart(px.pie(alloc, names="asset_class", values="market_value", hole=.58, title="Synthetic holdings mix"), use_container_width=True)
    st.subheader("Highest-impact signals")
    if not feed.empty:
        show = feed.sort_values(["impact","published_at"], ascending=[False,False]).head(5)
        st.dataframe(show[["published_at","source","title","event_type","sentiment","impact","is_synthetic"]], use_container_width=True, hide_index=True)

with tab_feed:
    st.subheader("Newswire + social pulse")
    f1,f2,f3 = st.columns([1,1,1.4])
    events = ["All"] + sorted(feed["event_type"].dropna().astype(str).unique().tolist())
    event_filter = f1.selectbox("Event type", events)
    sentiment_filter = f2.selectbox("Sentiment", ["All","Negative","Neutral","Positive"])
    query = f3.text_input("Search headlines / text")
    filtered = feed.copy()
    if event_filter != "All": filtered = filtered[filtered["event_type"] == event_filter]
    if sentiment_filter != "All": filtered = filtered[filtered["sentiment_label"] == sentiment_filter]
    if query.strip():
        mask = filtered[["title","body","source"]].astype(str).agg(" ".join, axis=1).str.contains(query, case=False, na=False)
        filtered = filtered[mask]
    st.caption(f"{len(filtered)} records · synthetic sample data is labeled; RSS/imported records are marked non-synthetic by default.")
    if not filtered.empty:
        st.dataframe(filtered[["published_at","source","title","event_type","sentiment","sentiment_label","impact","model","is_synthetic","url"]], use_container_width=True, hide_index=True)
    else: st.info("No records match these filters.")
    st.download_button("Download filtered feed CSV", filtered.to_csv(index=False).encode(), "risk_feed.csv", "text/csv")
    st.download_button("Download filtered feed JSON", filtered.to_json(orient="records", indent=2).encode(), "risk_feed.json", "application/json")

with tab_nlp:
    st.subheader("Analyze a headline or post")
    text = st.text_area("Headline / post text", "Regional lender faces downgrade as defaults rise and credit stress spreads.", height=110)
    if st.button("Analyze text", type="primary"):
        result = analyze_text(text)
        signal = generate_risk_signal(result)
        a,b,c = st.columns(3)
        a.metric("Sentiment", f"{result['sentiment']:+.3f}")
        b.metric("Event classification", result["event_type"])
        c.metric("Impact score", f"{result['impact']}/10")
        st.write(f"**Model path:** {result['model']}")
        st.json(signal)
        if signal["scenario"]:
            st.info(f"Suggested stress scenario: **{signal['scenario']}** · Suggested severity multiplier {signal['suggested_severity']}×")
    st.caption("FinBERT is optional and opt-in via ENABLE_FINBERT=1. If unavailable, a deterministic lexicon fallback runs locally.")

with tab_portfolio:
    st.subheader("Synthetic portfolio holdings")
    st.caption("All positions are fictional. Market values are quantity × unit price; derivatives are represented by simplified marked-to-market exposure proxies.")
    edited = st.data_editor(portfolio, num_rows="dynamic", use_container_width=True, key="portfolio_editor",
                            column_config={"market_value": st.column_config.NumberColumn("Market value", disabled=True)})
    if st.button("Apply portfolio edits"):
        edited = edited.copy()
        edited["market_value"] = pd.to_numeric(edited["quantity"], errors="coerce").fillna(0) * pd.to_numeric(edited["unit_price"], errors="coerce").fillna(0)
        st.session_state.portfolio = edited
        st.success("Portfolio updated.")
        st.rerun()
    st.download_button("Export holdings CSV", portfolio.to_csv(index=False).encode(), "portfolio_holdings.csv", "text/csv")
    alloc = portfolio.groupby("asset_class", as_index=False)["market_value"].sum()
    st.plotly_chart(px.bar(alloc, x="asset_class", y="market_value", color="asset_class", title="Market value by asset class"), use_container_width=True)

with tab_stress:
    st.subheader("Scenario workbench")
    left,right = st.columns([1,1.7])
    with left:
        scenario = st.selectbox("Stress scenario", list(SCENARIOS.keys()))
        severity = st.slider("Severity multiplier", 0.0, 2.0, 1.0, 0.1)
        st.caption("1.0× = base shocks. A 2.0× multiplier doubles the percentage shocks; it does not model nonlinear market dynamics.")
        shock_table = pd.DataFrame([{"Asset class": k, "Base shock": f"{v:+.0%}"} for k,v in SCENARIOS[scenario].items()])
        st.dataframe(shock_table, hide_index=True, use_container_width=True)
        run = st.button("Run stress test", type="primary", use_container_width=True)
    with right:
        st.markdown("**Assumptions**")
        st.markdown("- Static positions; no trading, hedging or rebalancing during the shock.\n- Asset-class shocks are fixed illustrative returns, not estimated from history.\n- No taxes, transaction costs, convexity, default recovery, margin calls or counterparty netting.\n- Loans and derivatives use simplified market-value proxies.")
    if run:
        stressed, summary = stress_portfolio(portfolio, scenario, severity)
        save_stress_run(summary, stressed, DB_PATH)
        st.session_state.last_stress = (stressed, summary)
    if "last_stress" in st.session_state:
        stressed, summary = st.session_state.last_stress
        a,b,c,d = st.columns(4)
        a.metric("Before shock", f"${summary['before_value']:,.0f}")
        b.metric("After shock", f"${summary['after_value']:,.0f}", delta=f"{summary['pnl']:+,.0f}")
        c.metric("Absolute loss", f"${summary['absolute_loss']:,.0f}")
        d.metric("Portfolio return", f"{summary['return_pct']:+.2f}%")
        chart = stressed.melt(id_vars=["asset_name","asset_class"], value_vars=["before_value","after_value"], var_name="valuation", value_name="value")
        st.plotly_chart(px.bar(chart, x="asset_name", y="value", color="valuation", barmode="group", title="Holding values before and after shock"), use_container_width=True)
        contributions = class_contributions(stressed)
        st.plotly_chart(px.bar(contributions, x="asset_class", y="pnl", color="asset_class", title="P&L contribution by asset class"), use_container_width=True)
        st.subheader("Affected holdings")
        st.dataframe(stressed[["asset_id","asset_name","asset_class","before_value","shock_pct","after_value","pnl"]].sort_values("pnl"), use_container_width=True, hide_index=True)
        st.download_button("Export stress details CSV", stressed.to_csv(index=False).encode(), "stress_test_details.csv", "text/csv")
        st.download_button("Export stress summary JSON", pd.Series(summary).to_json(indent=2).encode(), "stress_test_summary.json", "application/json")

with tab_history:
    st.subheader("Persistent history and exports")
    try:
        history = load_history(DB_PATH)
        if history.empty: st.info("No saved stress tests yet. Run a scenario in Stress Test Lab.")
        else: st.dataframe(history.drop(columns=["details_json"], errors="ignore"), use_container_width=True, hide_index=True)
        st.download_button("Export history CSV", history.drop(columns=["details_json"], errors="ignore").to_csv(index=False).encode(), "stress_history.csv", "text/csv")
        st.download_button("Export history JSON", history.to_json(orient="records", indent=2).encode(), "stress_history.json", "application/json")
    except Exception as exc:
        log.exception("Unable to load history")
        st.error(f"History unavailable: {exc}")
    if st.button("Save current feed to SQLite"):
        try:
            save_feed_items(feed, DB_PATH)
            st.success("Feed records saved to SQLite.")
        except Exception as exc:
            st.error(f"Save failed: {exc}")

st.divider()
st.caption("RiskLens demo · Not financial advice · Scores and stress scenarios are illustrative and should be independently validated before real-world use.")
