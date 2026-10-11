"""SQLite persistence for analyzed feed items and saved stress-test runs."""
import json
import sqlite3
from pathlib import Path
import pandas as pd

def connect(db_path):
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("""CREATE TABLE IF NOT EXISTS feed_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT, published_at TEXT, source TEXT, title TEXT,
        body TEXT, is_synthetic INTEGER, sentiment REAL, event_type TEXT, impact INTEGER,
        model TEXT, url TEXT, inserted_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS stress_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        scenario TEXT, severity REAL, before_value REAL, after_value REAL, pnl REAL,
        loss_pct REAL, details_json TEXT)""")
    conn.commit()
    return conn

def save_feed_items(df, db_path):
    if df.empty: return
    conn = connect(db_path)
    try:
        for _, r in df.iterrows():
            conn.execute("""INSERT INTO feed_items
            (published_at,source,title,body,is_synthetic,sentiment,event_type,impact,model,url)
            VALUES (?,?,?,?,?,?,?,?,?,?)""", (
                str(r.get("published_at","")), str(r.get("source","")), str(r.get("title","")),
                str(r.get("body","")), int(bool(r.get("is_synthetic", True))),
                float(r.get("sentiment",0)), str(r.get("event_type","Other")), int(r.get("impact",1)),
                str(r.get("model","")), str(r.get("url",""))))
        conn.commit()
    finally: conn.close()

def load_history(db_path):
    conn = connect(db_path)
    try:
        return pd.read_sql_query("SELECT * FROM stress_runs ORDER BY id DESC", conn)
    finally: conn.close()

def save_stress_run(summary, details, db_path):
    conn = connect(db_path)
    try:
        conn.execute("""INSERT INTO stress_runs
        (scenario,severity,before_value,after_value,pnl,loss_pct,details_json)
        VALUES (?,?,?,?,?,?,?)""", (
            summary["scenario"], summary["severity"], summary["before_value"], summary["after_value"],
            summary["pnl"], summary["loss_pct"], details.to_json(orient="records")))
        conn.commit()
    finally: conn.close()
