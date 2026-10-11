"""NLP risk engine: optional FinBERT, with deterministic lexicon fallback."""
from functools import lru_cache
import logging
import os
import re

log = logging.getLogger(__name__)

EVENT_KEYWORDS = {
    "Geopolitical": ["war", "sanction", "invasion", "conflict", "tariff", "geopolitical"],
    "Macroeconomic": ["inflation", "interest rate", "central bank", "recession", "gdp", "unemployment", "fed "],
    "Credit Event": ["default", "downgrade", "bankruptcy", "missed payment", "credit stress", "insolvency"],
    "M&A": ["acquisition", "merger", "takeover", "buyout"],
    "Earnings": ["earnings", "revenue", "profit warning", "guidance", "quarterly results"],
    "Market / Liquidity": ["liquidity", "sell-off", "volatility", "market crash", "margin call"],
    "Regulatory": ["regulator", "antitrust", "lawsuit", "fine", "investigation", "regulation"],
    "Cyber / Operations": ["cyberattack", "ransomware", "outage", "data breach", "operational disruption"],
}
POSITIVE = {"beat", "growth", "surge", "record", "upgrade", "profit", "strong", "rally", "rebound", "approval", "resilient", "outperform", "cuts"}
NEGATIVE = {"miss", "loss", "crash", "default", "downgrade", "fraud", "war", "sanction", "recession", "fall", "drop", "weak", "risk", "sell-off", "bankruptcy", "breach", "inflation", "layoff", "warning", "decline", "plunge"}

def classify_event(text: str) -> str:
    lower = str(text).lower()
    scores = {event: sum(1 for kw in kws if kw in lower) for event, kws in EVENT_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] else "Other"

def _lexicon_sentiment(text: str) -> float:
    words = re.findall(r"[a-z]+(?:-[a-z]+)?", str(text).lower())
    if not words:
        return 0.0
    pos = sum(1 for w in words if w in POSITIVE)
    neg = sum(1 for w in words if w in NEGATIVE)
    # Smoothly scaled, bounded, deterministic and dependency-free.
    return round(max(-1.0, min(1.0, (pos - neg) / max(3.0, (pos + neg) * 1.5))), 3)

@lru_cache(maxsize=1)
def _finbert_pipeline():
    if os.getenv("ENABLE_FINBERT", "0").lower() not in {"1", "true", "yes"}:
        return None
    try:
        from transformers import pipeline
        return pipeline("text-classification", model="ProsusAI/finbert", tokenizer="ProsusAI/finbert", top_k=None)
    except Exception as exc:
        log.warning("FinBERT unavailable; using fallback: %s", exc)
        return None

def sentiment_score(text: str) -> tuple[float, str]:
    """Return signed sentiment and method. FinBERT model is downloaded only when opted in."""
    pipe = _finbert_pipeline()
    if pipe:
        try:
            result = pipe(str(text)[:2000])[0]
            # Transformers versions may return either a list of dicts or nested list.
            if isinstance(result, dict):
                result = [result]
            scores = {str(x["label"]).lower(): float(x["score"]) for x in result}
            positive = scores.get("positive", 0.0)
            negative = scores.get("negative", 0.0)
            return round(max(-1.0, min(1.0, positive - negative)), 3), "FinBERT"
        except Exception as exc:
            log.warning("FinBERT inference failed; using fallback: %s", exc)
    return _lexicon_sentiment(text), "Lexicon fallback"

def impact_score(text: str, sentiment: float | None = None) -> int:
    """Heuristic severity score 1–10; this is a transparent proxy, not a prediction."""
    lower = str(text).lower()
    high = ["default", "bankruptcy", "war", "invasion", "market crash", "cyberattack", "fraud", "emergency", "insolvency", "sanction"]
    medium = ["inflation", "interest rate", "downgrade", "acquisition", "merger", "profit warning", "recession", "outage", "investigation", "layoff"]
    score = 2
    score += min(5, sum(2 for term in high if term in lower))
    score += min(3, sum(1 for term in medium if term in lower))
    if sentiment is not None and abs(sentiment) >= 0.6:
        score += 1
    return int(max(1, min(10, score)))

def analyze_text(text: str) -> dict:
    score, method = sentiment_score(text)
    event = classify_event(text)
    impact = impact_score(text, score)
    return {"sentiment": score, "event_type": event, "impact": impact, "model": method}
