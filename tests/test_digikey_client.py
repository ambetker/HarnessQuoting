from unittest.mock import MagicMock, patch

import pytest

from app import digikey_client as dk


@pytest.fixture(autouse=True)
def reset_token_cache():
    dk._token_cache["access_token"] = None
    dk._token_cache["expires_at"] = 0.0
    yield


def _response(status_code=200, json_data=None, text=""):
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    resp.json.return_value = json_data or {}
    resp.raise_for_status = MagicMock()
    return resp


def _token_response():
    return _response(200, {"access_token": "tok-123", "expires_in": 1800})


@patch("app.digikey_client.requests.request")
@patch("app.digikey_client.config")
def test_get_access_token_caches(mock_config, mock_request):
    mock_config.DIGIKEY_CLIENT_ID = "id"
    mock_config.DIGIKEY_CLIENT_SECRET = "secret"
    mock_request.return_value = _token_response()

    token1 = dk.get_access_token()
    token2 = dk.get_access_token()

    assert token1 == "tok-123"
    assert token2 == "tok-123"
    assert mock_request.call_count == 1  # second call served from cache


@patch("app.digikey_client.config")
def test_get_access_token_requires_credentials(mock_config):
    mock_config.DIGIKEY_CLIENT_ID = None
    mock_config.DIGIKEY_CLIENT_SECRET = None

    with pytest.raises(dk.DigiKeyAuthError):
        dk.get_access_token()


@patch("app.digikey_client.time.sleep", lambda *_: None)
@patch("app.digikey_client.requests.request")
@patch("app.digikey_client.config")
def test_retries_on_429_then_succeeds(mock_config, mock_request):
    mock_config.DIGIKEY_CLIENT_ID = "id"
    mock_config.DIGIKEY_CLIENT_SECRET = "secret"
    mock_request.side_effect = [
        _response(429, text="rate limited"),
        _token_response(),
    ]

    token = dk.get_access_token()
    assert token == "tok-123"
    assert mock_request.call_count == 2


@patch("app.digikey_client.requests.request")
@patch("app.digikey_client.config")
def test_401_raises_auth_error_immediately(mock_config, mock_request):
    mock_config.DIGIKEY_CLIENT_ID = "id"
    mock_config.DIGIKEY_CLIENT_SECRET = "secret"
    mock_request.return_value = _response(401, text="bad creds")

    with pytest.raises(dk.DigiKeyAuthError):
        dk.get_access_token()
    assert mock_request.call_count == 1  # no retries on auth failure


def test_select_price_break_picks_largest_tier_at_or_below_qty():
    tiers = [
        dk.PriceBreak(1, 1.00),
        dk.PriceBreak(10, 0.80),
        dk.PriceBreak(100, 0.50),
    ]
    price, tier = dk.select_price_break(tiers, extended_qty=45)
    assert (price, tier) == (0.80, 10)


def test_select_price_break_falls_back_to_smallest_tier_below_range():
    tiers = [dk.PriceBreak(10, 0.80), dk.PriceBreak(100, 0.50)]
    price, tier = dk.select_price_break(tiers, extended_qty=3)
    assert (price, tier) == (0.80, 10)


def test_select_price_break_empty_pricing():
    assert dk.select_price_break([], extended_qty=10) == (None, None)


SAMPLE_SEARCH_RESPONSE = {
    "Products": [
        {
            "ManufacturerProductNumber": "DT04-12PA-L012",
            "Description": {"ProductDescription": "CONN RCPT HSG 12POS"},
            "Category": {"Name": "Connectors, Interconnects"},
            "ProductStatus": {"Status": "Active"},
            "ProductVariations": [
                {
                    "DigiKeyProductNumber": "1734-1362-ND",
                    "StandardPricing": [
                        {"BreakQuantity": 1, "UnitPrice": 9.65},
                        {"BreakQuantity": 10, "UnitPrice": 8.198},
                    ],
                }
            ],
        }
    ]
}


@patch("app.digikey_client.keyword_search")
def test_resolve_part_matches_manufacturer_part_number(mock_search):
    mock_search.return_value = SAMPLE_SEARCH_RESPONSE

    result = dk.resolve_part("dt04-12pa-l012")

    assert result.source == "Mfr"
    assert result.digikey_part_number == "1734-1362-ND"
    assert result.category_raw == "Connectors, Interconnects"
    assert result.standard_pricing == [dk.PriceBreak(1, 9.65), dk.PriceBreak(10, 8.198)]


@patch("app.digikey_client.keyword_search")
def test_resolve_part_matches_digikey_part_number(mock_search):
    mock_search.return_value = SAMPLE_SEARCH_RESPONSE

    result = dk.resolve_part("1734-1362-ND")

    assert result.source == "DK"


@patch("app.digikey_client.keyword_search")
def test_resolve_part_returns_none_when_no_products(mock_search):
    mock_search.return_value = {"Products": []}

    assert dk.resolve_part("NOTHING-MATCHES") is None


@patch("app.digikey_client.keyword_search")
def test_resolve_part_does_not_fuzzy_fallback_to_top_result(mock_search):
    # Regression guard: keyword search can return a plausible but wrong
    # product (e.g. CLT50N-C630, a different variant, for a CLT50N-C query).
    # Silently pricing off a mismatched product is worse than "not found".
    mock_search.return_value = SAMPLE_SEARCH_RESPONSE  # only has DT04-12PA-L012

    assert dk.resolve_part("SOME-OTHER-PART-NOT-IN-RESULTS") is None
