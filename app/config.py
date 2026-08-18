import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DIGIKEY_CLIENT_ID = os.environ.get("DIGIKEY_CLIENT_ID")
DIGIKEY_CLIENT_SECRET = os.environ.get("DIGIKEY_CLIENT_SECRET")

CACHE_REFRESH_DAYS = float(os.environ.get("CACHE_REFRESH_DAYS", "7"))

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = _PROJECT_ROOT / "harness_quoting.db"
SETTINGS_PATH = _PROJECT_ROOT / "settings.json"
COMPANIES_PATH = _PROJECT_ROOT / "companies.json"
QUOTE_COUNTER_PATH = _PROJECT_ROOT / "quote_counter.json"

QUOTE_REVISION = "B"


def quote_terms(company_name: str) -> str:
    return (
        "Net 30 on approved credit. Quotation valid 30 days from the date above. "
        "Prices are FOB origin and quoted in USD. Component pricing is based "
        "on current distributor cost and is subject to change with market "
        "conditions and availability; lead times are quoted at order "
        "acknowledgement. Tooling and setup charges are one-time and "
        "non-refundable. Quantities shown are firm — orders released at other "
        "quantities will be requoted. Applicable sales tax is not included. "
        "Acceptance of this quotation constitutes agreement to "
        f"{company_name} standard terms and conditions of sale."
    )
