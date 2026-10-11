# Five-minute demo script

**0:00–0:30 | Set context.** Open RiskLens and explain that bundled feed records and all holdings are synthetic. The MVP requires no keys.

**0:30–1:15 | Executive overview.** Point to portfolio market value, signal count, high-impact event count and negative sentiment. Explain that charts are calculated from the current feed and holdings.

**1:15–2:00 | News/social feed.** Filter to Credit Event, search for “downgrade”, inspect sentiment, impact, source provenance and model path. Mention RSS and CSV/JSON imports are optional.

**2:00–2:40 | Manual NLP.** Paste “Regional lender reports missed payment as credit stress spreads.” Run analysis. Explain sentiment is signed, event type is categorical, and impact is a transparent heuristic. If FinBERT is not configured, fallback is shown explicitly.

**2:40–4:15 | Stress test lab.** Choose “Credit crisis”, set severity to 1.0×, run. Read before value, after value, absolute loss and return. Inspect asset-class contribution chart and holding-level P&L. Change severity to 1.5× and rerun.

**4:15–4:45 | History & exports.** Open History & Exports, show saved run, export stress summary/details and filtered feed. Note SQLite is local.

**4:45–5:00 | Close with limitations.** Emphasize synthetic input, illustrative shocks, simplified derivative/loan marks, no calibration or investment advice. Next steps: validate signals, calibrate shocks on historical data, add authenticated data providers and governance.
