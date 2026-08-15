import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DIGIKEY_CLIENT_ID = os.environ.get("DIGIKEY_CLIENT_ID")
DIGIKEY_CLIENT_SECRET = os.environ.get("DIGIKEY_CLIENT_SECRET")

CACHE_REFRESH_DAYS = float(os.environ.get("CACHE_REFRESH_DAYS", "7"))

DB_PATH = Path(__file__).resolve().parent.parent / "harness_quoting.db"

# Letterhead for the printed quote (quote design.pdf). Static — doesn't vary
# per quote, so it lives here rather than on the Quote model. Edit directly
# if the business details change.
COMPANY_NAME = "Ambetker Wire & Cable"
COMPANY_ADDRESS_LINES = ["1420 Harborview Industrial Drive", "Ashland, WI 54806"]
COMPANY_PHONE = "715 682 4400"
COMPANY_EMAIL = "sales@ambetker.com"

# The design mockup's quote number/revision are reused as-is for now rather
# than building out a numbering/versioning system — not asked for yet.
QUOTE_NUMBER = "Q-2026-0418"
QUOTE_REVISION = "B"

QUOTE_TERMS = (
    "Net 30 on approved credit. Quotation valid 30 days from the date above. "
    "Prices are FOB Ashland, WI and quoted in USD. Component pricing is based "
    "on current distributor cost and is subject to change with market "
    "conditions and availability; lead times are quoted at order "
    "acknowledgement. Tooling and setup charges are one-time and "
    "non-refundable. Quantities shown are firm — orders released at other "
    "quantities will be requoted. Applicable sales tax is not included. "
    "Acceptance of this quotation constitutes agreement to "
    f"{COMPANY_NAME} standard terms and conditions of sale."
)
