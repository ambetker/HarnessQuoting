import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DIGIKEY_CLIENT_ID = os.environ.get("DIGIKEY_CLIENT_ID")
DIGIKEY_CLIENT_SECRET = os.environ.get("DIGIKEY_CLIENT_SECRET")

CACHE_REFRESH_DAYS = float(os.environ.get("CACHE_REFRESH_DAYS", "7"))

DB_PATH = Path(__file__).resolve().parent.parent / "harness_quoting.db"
