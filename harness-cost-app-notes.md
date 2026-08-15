# Harness Cost App — Project Notes

## Goal
Python desktop app that links to DigiKey's API to search parts/pricing, feeding into a cost model for manufacturing wire harnesses.

## Stack decisions
- **Language:** Python
- **UI:** PySide6 (chosen over Tkinter/Streamlit for a more polished, native desktop feel)
- **Storage (planned, not yet built):** local SQLite or Postgres cache for DigiKey product/pricing data, to avoid hitting rate limits and to keep the UI fast

## DigiKey API integration
- Using **Product Information API v4** (developer.digikey.com)
- Auth: **2-legged OAuth (client_credentials grant)** — no user login needed, since we only need public catalog/pricing data, not order history or account-specific pricing
- Credentials (`DIGIKEY_CLIENT_ID`, `DIGIKEY_CLIENT_SECRET`) stored in a `.env` file at the project root, loaded via `python-dotenv` (`load_dotenv()`), kept out of git via `.gitignore`
- Token is cached in memory with expiry tracking (~30 min tokens, refreshed ~60s early) to avoid re-authenticating on every call
- `keyword_search()` function built out — POSTs to `/products/v4/search/keyword`, returns a `Products` list with fields like `ManufacturerProductNumber`, `Description`, `UnitPrice`, `QuantityAvailable`, `StandardPricing` (qty price breaks)

### Key data considerations for cost modeling
- **Price breaks matter more than unit price** — DigiKey returns tiered pricing (e.g. qty 1/10/100/500); harness costing should use the break matching expected production volume, not qty-1 price
- **Wire is priced differently** than discrete parts (terminals/connectors) — often per-foot/meter, sometimes cut-to-length vs. spool
- **`ProductStatus` field** flags discontinued/inactive parts — relevant for long-term part number reliability
- Should cache pricing/product data locally with a refresh policy (e.g. refresh if >24h old) rather than live-fetching every calculation

## Code built so far
`digikey_client.py` — handles OAuth token caching + `keyword_search()` function (see chat for full code)

`main.py` (PySide6 starter) — basic window with:
- Search box + button (Enter key also triggers search)
- Results table (Part Number, Description, Unit Price, Qty Available columns)
- Calls `keyword_search()` from `digikey_client.py` on search, populates table with results

**Known issue to fix before hardening:** `keyword_search()` is a blocking network call — currently freezes the UI during search (patched temporarily with `QApplication.processEvents()`). Should move to `QThread` / `QThreadPool` before this goes beyond prototype stage.

## Cost model (not yet built — conceptual only so far)
Typical wire harness cost buildup discussed:
- **Materials:** wire (gauge/length/type), connectors, terminals, seals, heat shrink, tape/loom, backshells — this is where DigiKey pricing feeds in
- **Labor:** cut/strip time, crimp time per termination, assembly/routing time, testing — modeled separately as time-per-operation × labor rate (not from DigiKey)
- **Overhead/margin:** scrap factor, setup/NRE (tooling for custom connectors), yield/rework allowance

## Next steps (as of this chat)
1. User is planning UI/UX separately (using another tool)
2. Still to do: BOM table + cost rollup logic, threading fix for API calls, local caching layer for DigiKey data
