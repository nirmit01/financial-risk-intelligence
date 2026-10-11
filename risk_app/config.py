from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "risk_app" / "data"
SAMPLE_NEWS = DATA_DIR / "sample_news.csv"
SAMPLE_SOCIAL = DATA_DIR / "sample_social.csv"
DB_PATH = Path(os.getenv("RISK_DB_PATH", str(ROOT / "data" / "risk_intelligence.db")))
LOG_PATH = ROOT / "risk_app.log"
