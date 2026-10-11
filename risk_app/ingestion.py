"""Bundled sample data, CSV/JSON import, and optional RSS ingestion."""
import json
import logging
import os
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET
import pandas as pd
from .config import SAMPLE_NEWS, SAMPLE_SOCIAL
from .nlp import analyze_text

log = logging.getLogger(__name__)
BASE_COLUMNS = ["published_at","source","title","body","is_synthetic","url"]

def _read_sample(path):
    return pd.read_csv(path).fillna("")

def sample_items():
    news = _read_sample(SAMPLE_NEWS)
    social = _read_sample(SAMPLE_SOCIAL)
    return pd.concat([news, social], ignore_index=True)

def normalize_import(uploaded_file) -> pd.DataFrame:
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    elif name.endswith(".json"):
        raw = json.load(uploaded_file)
        df = pd.DataFrame(raw if isinstance(raw, list) else raw.get("items", []))
    else:
        raise ValueError("Only CSV and JSON files are supported")
    aliases = {"text":"body", "headline":"title", "date":"published_at", "timestamp":"published_at"}
    df = df.rename(columns={k:v for k,v in aliases.items() if k in df.columns and v not in df.columns})
    if "title" not in df: df["title"] = ""
    if "body" not in df: df["body"] = df["title"]
    if "source" not in df: df["source"] = "User import"
    if "published_at" not in df: df["published_at"] = pd.Timestamp.utcnow().isoformat()
    if "is_synthetic" not in df: df["is_synthetic"] = False
    if "url" not in df: df["url"] = ""
    return df[BASE_COLUMNS].fillna("")

def fetch_rss(feeds: str | None = None, timeout=8) -> pd.DataFrame:
    """Fetch public RSS feeds using stdlib XML parsing; failures are isolated per feed."""
    feeds = feeds if feeds is not None else os.getenv("RSS_FEEDS", "")
    rows = []
    for url in [x.strip() for x in feeds.split(",") if x.strip()]:
        try:
            req = Request(url, headers={"User-Agent":"FinancialRiskIntelligenceDemo/1.0"})
            with urlopen(req, timeout=timeout) as response:
                root = ET.fromstring(response.read())
            for item in root.findall(".//item")[:25]:
                rows.append({
                    "published_at": item.findtext("pubDate", default=""),
                    "source": "RSS: " + url.split("/")[2],
                    "title": item.findtext("title", default=""),
                    "body": item.findtext("description", default=""),
                    "is_synthetic": False,
                    "url": item.findtext("link", default=""),
                })
        except Exception as exc:
            log.warning("RSS fetch failed for %s: %s", url, exc)
    return pd.DataFrame(rows, columns=BASE_COLUMNS)

def analyze_items(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return df.copy()
    out = df.copy()
    results = out.apply(lambda r: analyze_text(f"{r.get('title','')} {r.get('body','')}"), axis=1)
    for col in ["sentiment","event_type","impact","model"]:
        out[col] = [x[col] for x in results]
    out["sentiment_label"] = out["sentiment"].map(lambda x: "Positive" if x > .1 else ("Negative" if x < -.1 else "Neutral"))
    return out
