"""DigiKey Product Information API v4 client.

OAuth2 client-credentials auth, keyword search, and price-break resolution.
No UI or caching concerns here — see app/cache.py for the read-through cache
that wraps this module.
"""

import time
from dataclasses import dataclass, field

import requests

from app import config

TOKEN_URL = "https://api.digikey.com/v1/oauth2/token"
SEARCH_URL = "https://api.digikey.com/products/v4/search/keyword"

_MAX_RETRIES = 3
_BACKOFF_BASE = 0.5  # seconds; doubles each retry

_token_cache = {"access_token": None, "expires_at": 0.0}


class DigiKeyError(Exception):
    """Base class for DigiKey client errors."""


class DigiKeyAuthError(DigiKeyError):
    """Missing credentials, or the API rejected them (401)."""


class DigiKeyAPIError(DigiKeyError):
    """Request failed after retries, for reasons other than auth."""


@dataclass
class PriceBreak:
    break_quantity: int
    unit_price: float


@dataclass
class ResolvedPart:
    manufacturer_part_number: str
    digikey_part_number: str | None
    description: str
    category_raw: str
    product_status: str
    standard_pricing: list[PriceBreak] = field(default_factory=list)
    source: str = "Mfr"  # "DK" if the query matched a DigiKey part number, else "Mfr"


def _require_credentials():
    if not config.DIGIKEY_CLIENT_ID or not config.DIGIKEY_CLIENT_SECRET:
        raise DigiKeyAuthError(
            "DIGIKEY_CLIENT_ID / DIGIKEY_CLIENT_SECRET not set (check .env)"
        )


def _request_with_retry(method, url, **kwargs):
    last_error = None
    for attempt in range(_MAX_RETRIES):
        try:
            resp = requests.request(method, url, timeout=10, **kwargs)
        except requests.RequestException as exc:
            last_error = exc
            time.sleep(_BACKOFF_BASE * (2**attempt))
            continue

        if resp.status_code == 401:
            raise DigiKeyAuthError(f"DigiKey rejected credentials (401): {resp.text[:300]}")
        if resp.status_code == 429 or resp.status_code >= 500:
            last_error = DigiKeyAPIError(f"{resp.status_code}: {resp.text[:300]}")
            time.sleep(_BACKOFF_BASE * (2**attempt))
            continue

        resp.raise_for_status()
        return resp

    raise DigiKeyAPIError(f"DigiKey request failed after {_MAX_RETRIES} attempts: {last_error}")


def get_access_token() -> str:
    _require_credentials()
    if _token_cache["access_token"] and time.time() < _token_cache["expires_at"]:
        return _token_cache["access_token"]

    resp = _request_with_retry(
        "POST",
        TOKEN_URL,
        data={
            "client_id": config.DIGIKEY_CLIENT_ID,
            "client_secret": config.DIGIKEY_CLIENT_SECRET,
            "grant_type": "client_credentials",
        },
    )
    data = resp.json()
    _token_cache["access_token"] = data["access_token"]
    _token_cache["expires_at"] = time.time() + data["expires_in"] - 60
    return _token_cache["access_token"]


def keyword_search(keyword: str, record_count: int = 10) -> dict:
    token = get_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "X-DIGIKEY-Client-Id": config.DIGIKEY_CLIENT_ID,
        "X-DIGIKEY-Locale-Site": "US",
        "X-DIGIKEY-Locale-Language": "en",
        "X-DIGIKEY-Locale-Currency": "USD",
        "Content-Type": "application/json",
    }
    body = {"Keywords": keyword, "RecordCount": record_count}
    resp = _request_with_retry("POST", SEARCH_URL, headers=headers, json=body)
    return resp.json()


def _extract_pricing(product: dict) -> list[PriceBreak]:
    # v4 nests pricing under ProductVariations[].StandardPricing; some
    # responses/older assumptions had it flat on the product. Handle both.
    variations = product.get("ProductVariations") or []
    for variation in variations:
        tiers = variation.get("StandardPricing")
        if tiers:
            return [
                PriceBreak(t["BreakQuantity"], t["UnitPrice"])
                for t in tiers
                if "BreakQuantity" in t and "UnitPrice" in t
            ]

    flat_tiers = product.get("StandardPricing")
    if flat_tiers:
        return [
            PriceBreak(t["BreakQuantity"], t["UnitPrice"])
            for t in flat_tiers
            if "BreakQuantity" in t and "UnitPrice" in t
        ]

    unit_price = product.get("UnitPrice")
    if unit_price is not None:
        return [PriceBreak(1, unit_price)]

    return []


def _extract_digikey_part_number(product: dict) -> str | None:
    variations = product.get("ProductVariations") or []
    if variations and variations[0].get("DigiKeyProductNumber"):
        return variations[0]["DigiKeyProductNumber"]
    return product.get("DigiKeyPartNumber")


def _to_resolved_part(product: dict, source: str) -> ResolvedPart:
    description = product.get("Description")
    if isinstance(description, dict):
        description = description.get("ProductDescription", "")
    category = product.get("Category")
    if isinstance(category, dict):
        category = category.get("Name", "")
    status = product.get("ProductStatus")
    if isinstance(status, dict):
        status = status.get("Status", "")

    return ResolvedPart(
        manufacturer_part_number=product.get("ManufacturerProductNumber", ""),
        digikey_part_number=_extract_digikey_part_number(product),
        description=description or "",
        category_raw=category or "",
        product_status=status or "",
        standard_pricing=_extract_pricing(product),
        source=source,
    )


def resolve_part(part_number: str) -> ResolvedPart | None:
    """Resolve a manufacturer or DigiKey part number to a single product.

    Returns None if nothing matches (caller should fall back to a manual
    cost entry), rather than raising.
    """
    normalized = part_number.strip().upper()
    if not normalized:
        return None

    data = keyword_search(normalized, record_count=10)
    products = data.get("Products", [])
    if not products:
        return None

    for product in products:
        if product.get("ManufacturerProductNumber", "").strip().upper() == normalized:
            return _to_resolved_part(product, source="Mfr")
        digikey_pn = _extract_digikey_part_number(product)
        if digikey_pn and digikey_pn.strip().upper() == normalized:
            return _to_resolved_part(product, source="DK")

    # No exact match; best-effort fall back to the top search result.
    return _to_resolved_part(products[0], source="Mfr")


def select_price_break(
    standard_pricing: list[PriceBreak], extended_qty: float
) -> tuple[float | None, int | None]:
    """Pick the price-break tier for a given extended quantity.

    Picks the largest break quantity <= extended_qty; if extended_qty is
    below the smallest break, uses the smallest break. Returns
    (unit_price, break_quantity), or (None, None) if there's no pricing.
    """
    if not standard_pricing:
        return None, None

    tiers = sorted(standard_pricing, key=lambda t: t.break_quantity)
    chosen = tiers[0]
    for tier in tiers:
        if tier.break_quantity <= extended_qty:
            chosen = tier
        else:
            break
    return chosen.unit_price, chosen.break_quantity


if __name__ == "__main__":
    import sys

    query = " ".join(sys.argv[1:]) or "2-position terminal housing"
    result = resolve_part(query)
    if result is None:
        print(f"No match for {query!r}")
    else:
        print(result)
        print("price breaks:", result.standard_pricing)
