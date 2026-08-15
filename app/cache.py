"""SQLite read-through cache for DigiKey part lookups.

This is the layer the UI/cost model calls — it never talks to
digikey_client directly. A part already fetched within
config.CACHE_REFRESH_DAYS is served from disk instead of re-querying
DigiKey; the API's own token cache
(digikey_client._token_cache) is a separate, in-memory concern.
"""

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from app import category_map, config
from app.digikey_client import PriceBreak, resolve_part

_SCHEMA = """
CREATE TABLE IF NOT EXISTS parts (
    part_key TEXT PRIMARY KEY,
    found INTEGER NOT NULL,
    manufacturer_part_number TEXT,
    digikey_part_number TEXT,
    description TEXT,
    category_raw TEXT,
    category_app TEXT,
    product_status TEXT,
    source TEXT,
    standard_pricing_json TEXT,
    last_pulled_at TEXT NOT NULL
);
"""


@dataclass
class CachedPart:
    part_key: str
    found: bool
    last_pulled_at: datetime
    manufacturer_part_number: str = ""
    digikey_part_number: str | None = None
    description: str = ""
    category_raw: str = ""
    category_app: str = "Other"
    product_status: str = ""
    source: str = "Mfr"
    standard_pricing: list[PriceBreak] = field(default_factory=list)


def _normalize(part_number: str) -> str:
    return part_number.strip().upper()


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DB_PATH)
    conn.execute(_SCHEMA)
    return conn


def _row_to_cached_part(row: sqlite3.Row) -> CachedPart:
    pricing_json = row["standard_pricing_json"]
    pricing = (
        [PriceBreak(**tier) for tier in json.loads(pricing_json)] if pricing_json else []
    )
    return CachedPart(
        part_key=row["part_key"],
        found=bool(row["found"]),
        last_pulled_at=datetime.fromisoformat(row["last_pulled_at"]),
        manufacturer_part_number=row["manufacturer_part_number"] or "",
        digikey_part_number=row["digikey_part_number"],
        description=row["description"] or "",
        category_raw=row["category_raw"] or "",
        category_app=row["category_app"] or "Other",
        product_status=row["product_status"] or "",
        source=row["source"] or "Mfr",
        standard_pricing=pricing,
    )


def get_cached(part_number: str) -> CachedPart | None:
    """Look up a part in the cache without ever hitting the API."""
    part_key = _normalize(part_number)
    conn = _connect()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT * FROM parts WHERE part_key = ?", (part_key,)
        ).fetchone()
    finally:
        conn.close()
    return _row_to_cached_part(row) if row else None


def _is_stale(last_pulled_at: datetime) -> bool:
    age = datetime.now(timezone.utc) - last_pulled_at
    return age > timedelta(days=config.CACHE_REFRESH_DAYS)


def _store(part_key: str, cached: CachedPart) -> None:
    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO parts (
                part_key, found, manufacturer_part_number, digikey_part_number,
                description, category_raw, category_app, product_status, source,
                standard_pricing_json, last_pulled_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(part_key) DO UPDATE SET
                found=excluded.found,
                manufacturer_part_number=excluded.manufacturer_part_number,
                digikey_part_number=excluded.digikey_part_number,
                description=excluded.description,
                category_raw=excluded.category_raw,
                category_app=excluded.category_app,
                product_status=excluded.product_status,
                source=excluded.source,
                standard_pricing_json=excluded.standard_pricing_json,
                last_pulled_at=excluded.last_pulled_at
            """,
            (
                part_key,
                int(cached.found),
                cached.manufacturer_part_number,
                cached.digikey_part_number,
                cached.description,
                cached.category_raw,
                cached.category_app,
                cached.product_status,
                cached.source,
                json.dumps([tier.__dict__ for tier in cached.standard_pricing]),
                cached.last_pulled_at.isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_or_fetch(part_number: str, force_refresh: bool = False) -> CachedPart:
    """Read-through cache: serve a fresh cached record, or fetch from
    DigiKey (via digikey_client.resolve_part), cache it, and return it.

    Caches misses too, so a not-found part number isn't re-queried on
    every keystroke — it's still subject to the same refresh window.
    """
    part_key = _normalize(part_number)
    if not force_refresh:
        cached = get_cached(part_key)
        if cached and not _is_stale(cached.last_pulled_at):
            return cached

    resolved = resolve_part(part_key)
    now = datetime.now(timezone.utc)

    if resolved is None:
        cached = CachedPart(part_key=part_key, found=False, last_pulled_at=now)
    else:
        cached = CachedPart(
            part_key=part_key,
            found=True,
            last_pulled_at=now,
            manufacturer_part_number=resolved.manufacturer_part_number,
            digikey_part_number=resolved.digikey_part_number,
            description=resolved.description,
            category_raw=resolved.category_raw,
            category_app=category_map.map_category(resolved.category_raw),
            product_status=resolved.product_status,
            source=resolved.source,
            standard_pricing=resolved.standard_pricing,
        )

    _store(part_key, cached)
    return cached
