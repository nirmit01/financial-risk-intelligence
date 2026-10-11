# RiskLens — Financial Risk Intelligence & Portfolio Stress Testing

A local-first Streamlit MVP that analyzes financial headlines/posts, produces event and sentiment signals, and applies configurable shocks to a synthetic multi-asset portfolio. It is designed to run without paid APIs or model downloads.

## Features
- Two bundled input streams: **Newswire Demo (SYNTHETIC)** and **Social Pulse Demo (SYNTHETIC)**.
- Sentiment in [-1, +1], event classification, impact score (1–10), and a risk-signal-to-scenario mapping.
- Optional FinBERT (`ProsusAI/finbert`) with a deterministic local lexicon fallback. FinBERT is opt-in and requires downloading model files.
- Optional RSS ingestion, CSV/JSON imports, feed search/filter, and CSV/JSON exports.
- 12 synthetic holdings spanning equities, bonds, loans and derivatives.
- Configurable stress severity, holding-level P&L, asset-class contributions, SQLite stress history.
- Automated `unittest` coverage.

## Quick start (Windows PowerShell)
```powershell
cd financial-risk-intelligence
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m unittest discover -s tests -v
streamlit run app.py
```
Python 3.10–3.12 is recommended for broad dependency compatibility. Python 3.13 may work with recent package releases. If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal and activate again.

## Run on Linux/macOS
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests -v
streamlit run app.py
```

## Optional live RSS / FinBERT
1. Copy `.env.example` to `.env` and set `RSS_FEEDS` to comma-separated public RSS URLs. The app does not automatically load `.env`; either export environment variables in PowerShell or use the commands below.
2. Example PowerShell session:
```powershell
$env:RSS_FEEDS = "https://feeds.bbci.co.uk/news/business/rss.xml"
$env:ENABLE_FINBERT = "0"
streamlit run app.py
```
3. To attempt FinBERT:
```powershell
pip install transformers torch
$env:ENABLE_FINBERT = "1"
streamlit run app.py
```
The first FinBERT inference may download the model and needs internet access. If import, download or inference fails, the engine logs a warning and uses the fallback. Keep `ENABLE_FINBERT=0` for a fully offline demo. Do not rely on the lexicon fallback as a production-grade NLP model.

## Input formats
CSV and JSON uploads accept fields such as `title`, `body` or `text`, `source`, `published_at`/`date`, and `url`. A missing `is_synthetic` field is set to `false` for imports; check provenance before using externally sourced data. RSS rows are labeled as real/non-synthetic, but feed contents are not independently verified.

## Financial model assumptions
- All sample holdings and sample feed records are fictional/synthetic.
- Market value = `quantity × unit_price`. Positions and quantities are static through each scenario.
- Scenario shocks are illustrative class-level returns (e.g. Credit crisis: Equity -25%, Bond -16%, Loan -28%, Derivative -20%). Severity multiplies those returns linearly.
- Derivatives use simplified MTM/exposure proxies, not contract-level pricing or Greeks.
- P&L = post-shock value − pre-shock value. Positive P&L is a gain; absolute loss is max(0, −portfolio P&L).
- No transaction costs, liquidity haircuts beyond the scenario proxy, taxes, default recovery, collateral, counterparty netting, dynamic hedging, correlations, or nonlinear effects are modeled.
- Impact scores are transparent keyword heuristics. Sentiment fallback is a small lexicon, not a validated financial model. FinBERT scores are signed positive probability minus negative probability; not a probability of returns.
- Not financial advice. Validate all assumptions before real decisions.

## Architecture
```text
             ┌─────────────────────────────┐
             │ Bundled data / RSS / Import│
             └──────────────┬──────────────┘
                            v
             ┌─────────────────────────────┐
             │ Normalize + NLP risk engine │
             │ FinBERT optional / fallback │
             └──────────────┬──────────────┘
                            v
             ┌─────────────────────────────┐
             │ Event classification +     │
             │ impact + scenario signals  │
             └──────────────┬──────────────┘
                            v
┌────────────────┐  ┌────────────────────────┐
│ Synthetic book │─>│ Stress engine & P&L     │
└────────────────┘  └───────────┬────────────┘
                                v
             ┌─────────────────────────────┐
             │ Streamlit / Plotly dashboard│
             │ SQLite history + exports    │
             └─────────────────────────────┘
```

## Tests
Run `python -m unittest discover -s tests -v`. Tests cover bounded/signed NLP outputs, event classification, impact bounds, portfolio shape, reproducible valuation, zero-severity invariance, invalid severity, class contributions and risk-signal mapping.
