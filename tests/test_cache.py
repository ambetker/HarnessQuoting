from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from app import cache, config
from app.digikey_client import PriceBreak, ResolvedPart


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(config, "CACHE_REFRESH_DAYS", 7)
    yield


SAMPLE_RESOLVED = ResolvedPart(
    manufacturer_part_number="DT04-12PA-L012",
    digikey_part_number="1734-1362-ND",
    description="CONN RCPT HSG 12POS",
    category_raw="Connectors, Interconnects",
    product_status="Active",
    standard_pricing=[PriceBreak(1, 9.65), PriceBreak(10, 8.198)],
    source="Mfr",
)


@patch("app.cache.resolve_part")
def test_get_or_fetch_calls_api_once_then_serves_from_cache(mock_resolve):
    mock_resolve.return_value = SAMPLE_RESOLVED

    first = cache.get_or_fetch("dt04-12pa-l012")
    second = cache.get_or_fetch("DT04-12PA-L012")  # different case

    assert mock_resolve.call_count == 1
    assert first.found is True
    assert first.category_app == "Connector"
    assert second.manufacturer_part_number == "DT04-12PA-L012"


@patch("app.cache.resolve_part")
def test_get_or_fetch_caches_misses(mock_resolve):
    mock_resolve.return_value = None

    result = cache.get_or_fetch("NOT-A-REAL-PART")

    assert result.found is False
    assert mock_resolve.call_count == 1

    cache.get_or_fetch("NOT-A-REAL-PART")
    assert mock_resolve.call_count == 1  # still served from cache


@patch("app.cache.resolve_part")
def test_stale_cache_entry_triggers_refetch(mock_resolve):
    mock_resolve.return_value = SAMPLE_RESOLVED

    cache.get_or_fetch("DT04-12PA-L012")
    stale_time = datetime.now(timezone.utc) - timedelta(days=8)
    cached = cache.get_cached("DT04-12PA-L012")
    cached.last_pulled_at = stale_time
    cache._store("DT04-12PA-L012", cached)

    cache.get_or_fetch("DT04-12PA-L012")

    assert mock_resolve.call_count == 2


@patch("app.cache.resolve_part")
def test_force_refresh_bypasses_fresh_cache(mock_resolve):
    mock_resolve.return_value = SAMPLE_RESOLVED

    cache.get_or_fetch("DT04-12PA-L012")
    cache.get_or_fetch("DT04-12PA-L012", force_refresh=True)

    assert mock_resolve.call_count == 2
