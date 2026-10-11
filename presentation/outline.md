# RiskLens presentation outline (7 slides max)

1. **Problem & objective** — financial news and social posts move faster than manual risk reviews; turn unstructured text into a traceable stress-testing workflow.
2. **Solution at a glance** — ingestion → NLP/event/impact → risk signal → portfolio stress → dashboard/history.
3. **System architecture** — include architecture diagram from README; highlight local demo data and optional external integrations.
4. **NLP risk engine** — sentiment [-1,+1], event labels, impact [1,10], optional FinBERT and explicit fallback; disclose heuristic limitations.
5. **Portfolio & stress model** — 12 fictional positions across four asset classes; configurable shocks and severity; show before/after and contributions.
6. **Dashboard walkthrough & controls** — filters, manual analysis, portfolio editor, saved runs, exports, provenance labels.
7. **Validation, limits & roadmap** — automated tests, SQLite persistence, assumptions; future calibrated impact model, historical scenario calibration, real portfolio connectors and audit trail.
