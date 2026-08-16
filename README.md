# Harness Quote

A desktop app for quoting wire harness manufacturing jobs. Enter part numbers and quantities for one or more harnesses, pick which build processes each one needs, and it calculates unit cost, customer price at a target margin, and rolled-up totals for the whole quote — with live part pricing from DigiKey's Product Information API.

## Requirements

- macOS (the double-click launcher below is macOS-specific; the app itself, being PySide6, runs on Windows/Linux too via `python main.py`)
- Python 3.11+
- A DigiKey developer account (free) for API access

## Setup

**1. Clone the repo**

```
git clone https://github.com/ambetker/HarnessQuoting.git
cd HarnessQuoting
```

**2. Create a virtual environment and install dependencies**

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**3. Get DigiKey API credentials**

- Sign up / log in at [developer.digikey.com](https://developer.digikey.com)
- Create an app under "My Apps" and select the **Product Information API v4**
- Uses the 2-legged OAuth (client credentials) flow — no DigiKey account login is needed at runtime, just the app's Client ID and Client Secret
- New DigiKey developer apps are typically sandboxed until DigiKey approves production access — check your app's status if lookups aren't returning real results

**4. Configure environment**

```
cp .env.example .env
```

Edit `.env` and fill in `DIGIKEY_CLIENT_ID` and `DIGIKEY_CLIENT_SECRET`. `CACHE_REFRESH_DAYS` controls how long a looked-up part's price is cached locally before it's re-fetched (default 7 days).

**5. Run it**

```
python main.py
```

## Optional: a double-clickable app icon (macOS)

```
./scripts/make_desktop_launcher.sh
```

This creates **Harness Quote.app** on your Desktop, wired to this project's venv — launch it from Finder, Spotlight, or Launchpad instead of the terminal. Re-run the script if you move the project folder.

## Using the app

- The app opens with two sample harnesses and immediately starts looking up their part numbers against DigiKey.
- **Parts table**: enter a manufacturer or DigiKey part number per line; it resolves on blur. Unresolved parts (no exact catalog match) need a manual cost — click **override** next to any resolved price if the auto-priced value looks wrong (e.g. a part priced per roll/spool rather than per foot).
- **File menu**: New Quote, Open…, Save, Save As… — quotes save as readable JSON.
- **Print quote**: opens the system print dialog with a formatted quote document (use "Save as PDF" there to export one).
- Company letterhead and quote numbering shown on the printed quote are set in `app/config.py` — edit those constants for your business details.

## Running tests

```
pip install -r requirements-dev.txt
pytest tests/
```

## Project layout

```
app/
  digikey_client.py   DigiKey OAuth + search + price-break resolution
  cache.py             SQLite read-through cache for part lookups
  cost_model.py         Cost/pricing formulas
  models.py             Data model (Quote, Harness, PartLine, ...)
  persistence.py         Save/load quote state as JSON
  print_document.py      Builds the printable quote document
  ui/                    PySide6 widgets and main window
tests/                  pytest suite
scripts/                 make_desktop_launcher.sh
```
