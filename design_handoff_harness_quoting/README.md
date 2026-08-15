# Handoff: Wire Harness Quoting Tool

## Overview
A single-screen quoting application for wire harness manufacturing. An estimator enters part numbers (manufacturer or DigiKey) and quantities for one or more harnesses, selects which build processes each harness needs, and the tool calculates unit cost, customer price at a target margin, and rolled-up totals for the whole quote. Part pricing is intended to come from the DigiKey Product Information API; the prototype mocks that call against a small local catalog.

## About the Design Files
The files in this bundle are **design references created in HTML** — a working prototype showing intended look, math, and behavior. They are not production code to copy directly. The task is to **recreate this design in the target codebase's existing environment** (React, Vue, SwiftUI, native, etc.) using its established patterns, component library, and styling approach. If no environment exists yet, pick the framework best suited to the project and implement there.

`Harness Quote.dc.html` uses a small in-house prototyping runtime (`support.js`) with a template + logic-class split. Treat the template as markup structure and the logic class as the calculation and state model. Neither should be ported literally; the calculation logic, however, is authoritative — see **Cost model** below.

## Fidelity
**High fidelity.** Colors, typography, spacing, and interactions are final-intent. Recreate the UI closely using the codebase's existing libraries. The prototype is desktop-only (min useful width ~1300px); responsive behavior was not designed.

## Layout

Full-height page, background `#f6f7f7`.

**Header bar** — white, `1px solid #eaeae7` bottom border, padding `24px 36px 22px`. Flex row, `space-between`, `align-items: flex-end`.
- Left: title "Harness quote" (19px/600, `-0.01em`), sub-line `Q-2026-0418 · {n} harnesses · draft` (13px, `#83807a`).
- Right: Customer text input (240px) and a right-aligned "Quote total" label with the quote price (22px/600, `#b45309`).

**Body** — CSS grid, `grid-template-columns: 290px minmax(620px, 1fr) 340px`, `gap: 24px`, `padding: 28px 36px`, `align-items: start`.

### Card shell (used by every card)
`background:#fff; border:1px solid #eaeae7; border-radius:12px; box-shadow:0 1px 2px rgba(26,25,23,0.04), 0 6px 16px rgba(26,25,23,0.03); overflow:hidden`.
Card header: `padding:16px 20px 14px; border-bottom:1px solid #f1f1ee`; title 14px/600; optional sub-line 12.5px `#8b887f`.
Right-rail cards use a stronger shadow: `0 1px 2px rgba(26,25,23,0.04), 0 10px 28px rgba(26,25,23,0.05)` and `padding: 22px` with no separate header rule.

## Screens / Views

There is one screen. The middle column swaps between a **harness view** and a **summary view** via a tab row.

### Left column (global, always visible)

**1. Labor assumptions card**
Header: "Labor assumptions" / "Global — applied to every harness".
Body `padding:18px 20px`, vertical flex, `gap:14px`. Every row is a `grid-template-columns: 1fr 92px` label + right-aligned numeric input.
- Labor rate — `$/hr loaded` — default `62.00`
- Efficiency factor — `×` — default `1.00`
- Material scrap — `%` — default `2.5`
- 1px `#f1f1ee` divider
- Section label row: "TIME PER PROCESS" (12px/600, `0.04em`, uppercase, `#8b887f`) with "sec each" (12px, `#a3a09a`) right-aligned
- One input per process, in this order and with these defaults:
  - Cut and strip — `25`
  - Crimp — `12`
  - Install connector — `45`
  - Heat shrink — `20`
  - Labeling — `15`
  - Inspection — `120`
- 1px divider
- Desired margin — `%` — default `32`. Emphasized: `border:1px solid #b45309; background:#fdf7f0; color:#8a4007; font-weight:600`.
- Footnote 12.5px `#8b887f`: "Times apply to every harness. Setup and freight are set per harness. Margin is on sell price."

Standard input style: `padding:9px 11px; border:1px solid #e0e0dc; border-radius:8px; background:#fff; font-size:14px; text-align:right; color:#1a1917; font-variant-numeric:tabular-nums`. Focus: `outline:2px solid #b45309; outline-offset:-1px`.

**2. DigiKey pricing card**
`padding:18px 20px`, flex column `gap:13px`.
- Status row: 8px dot (`#2f8f5b` connected / `#d1a24a` not connected) + "DigiKey pricing" (13.5px/600).
- Status paragraph (12.5px, `#8b887f`, line-height 1.5). Disconnected copy: "Not connected — sample prices. Once the API key is set, each unique part number is requested once and cached for the whole quote." Connected copy: "Connected. Each unique part number resolves once and is reused across every harness on the quote."
- Stats block bounded top and bottom by `1px #f1f1ee`, `padding:12px 0`, rows: Unique part numbers / Priced from cache / Last lookup.
- Primary button "Price all harnesses" (`background:#b45309; color:#fff; border-radius:8px; padding:9px 12px; 13px/600`; hover `#9a460a`).
- Secondary button "Connect DigiKey API" ↔ "Disconnect API" (white, `1px solid #e0e0dc`; hover border and text `#b45309`).

### Middle column

**Tab row** — flex, `gap:8px`, wrapping. One pill per harness plus a "Summary" pill plus a dashed "+ Add harness" button.
Pill: `padding:9px 14px; border-radius:9px; 13px/500`. Inactive: transparent background, `1px solid #e4e3df`, text `#6f6c66`. Active: white background, `1px solid #b45309`, text `#1a1917`, `box-shadow:0 1px 2px rgba(26,25,23,0.06)`. Hover border `#c9a06a`. Each pill carries a secondary label — harness pills show `×{orderQty}` , the Summary pill shows the quote price — 12px, `#b45309` when active else `#a3a09a`.
Add button: `1px dashed #d5d3cd`, text `#8b887f`; hover `#b45309`.

**3. Harness header strip** (harness view) — card, `padding:18px 20px`, flex row `align-items:flex-end; gap:18px; flex-wrap:wrap`. Fields: Harness name (flex 1, min 160px), Harness P/N (150px), Qty (80px, right-aligned), Setup $ (88px), Freight $/ea (88px). Then Duplicate and Remove buttons (white, `1px solid #e0e0dc`, 13px; Remove hover border `#c08a80`, text `#a8443b`). Field labels are 12px/500 `#83807a` above the input, `gap:7px`.

**4. Parts card**
Header "Parts" / "Manufacturer or DigiKey P/N + qty per harness", with two secondary buttons: "Look up this BOM" and "Add part".
Table, 13.5px, `border-collapse: collapse`. Header cells: 12px/500 `#8b887f`, `padding:11px 8px`, bottom border `1px solid #f1f1ee`; first cell has `padding-left:20px`, last `padding-right:20px`. Rows: bottom border `1px solid #f6f6f4`, cell padding `5px 8px`.

Columns (width): `#` (24), Part number (158), Source (58), Description (auto), Category (104), Qty (62), Unit (28), Unit price (94), Extended (86), delete (26).

- **Part number** — borderless input, placeholder "mfr or DigiKey P/N"; hover reveals `1px solid #eaeae7` and `#fbfbfa` background. Blur triggers a lookup for that part number.
- **Source** — pill, `padding:2px 7px; border-radius:5px; 11px/500`. `DK` = bg `#eef4f8`, fg `#3a6b8c`. `Mfr` = bg `#f2f1ec`, fg `#6f6c66`. Unresolved (`—` or `···` while loading) = bg `#faf3f1`, fg `#a8746a`.
- **Description** — read-only, from the lookup. Placeholder states: "Looking up…", "Not found — enter cost manually", "Enter a part number", all `#a09c94`.
- **Category** — select, borderless with the same hover treatment. Options: Wire, Connector, Terminal, Seal / plug, Loom / braid, Label / shrink, Splice, Other. Lookup overrides this when a part resolves.
- **Qty** — borderless numeric input, right-aligned. Quantity per single harness; for wire and loom it is a length.
- **Unit** — derived, read-only: `ft` for Wire and Loom / braid, `ea` otherwise.
- **Unit price** — when the part resolved: read-only price (2 decimals, 3 when under $1) with a small price-break note underneath (11px `#a3a09a`, e.g. "100 ft tier"). When unresolved: a manual-cost input styled `1px dashed #ddc9a8; background:#fffdf9`.
- **Extended** — qty × unit price, read-only.
- **Delete** — 24×24 `×` button, `#c4c1bb`; hover bg `#f7eeee`, fg `#a8443b`.

Footer row inside the table: right-aligned "Material per harness" label spanning the first 8 columns, then the material total (14px/600).
Card footer bar: `padding:12px 20px 14px; border-top:1px solid #f1f1ee; background:#fbfbfa`, 12.5px `#8b887f`, showing e.g. "6 of 8 part numbers priced · 2 need manual cost" or "3 of 8 parts resolving…".

**5. Processes used card**
Header "Processes used" / "Select what this harness needs and enter counts; times come from labor assumptions", plus a secondary button "Suggest counts from parts".
Table columns: checkbox (34), Process (auto), Count (88, editable), Sec each (104, **read-only**), Minutes (88, read-only), Cost (96, read-only).
Rows for the six processes in order: Cut and strip, Crimp, Install connector, Heat shrink, Labeling, Inspection.
- Checkbox: 15×15, `accent-color:#b45309`.
- Unchecked row: background `#fcfcfb`, text `#b3b0aa`, count input disabled, and the row contributes zero time.
- Sec each is displayed text (`#8b887f` on, `#c4c1bb` off) pulled from the global Labor assumptions.
- Footer row: "Labor per harness" with total minutes and total labor cost (14px/600).

**6. Quantity breaks card** (harness view, toggleable)
Header "Quantity breaks" / "This harness, setup amortized across the run". Columns: Qty, Unit cost, Unit price, Extended, Margin $. Cell padding `13px 20px`. Rows are the sorted unique set of `[1, 10, thisHarnessQty, 100]`. Unit price is `#8a4007`/600.

**7. Quote summary card** (summary view)
Header "Quote summary" / "Every harness on this quote at its own order quantity". Columns: Harness (name is a text button, `#b45309`, click switches to that harness's tab), P/N, Qty, Unit cost, Unit price, Extended, Margin $. Cell padding `12px 8px` (20px on the outer edges).
Total row: background `#fdf7f0`, "Quote total" label spanning three columns, then total cost, blank, quote price (14px/600 `#8a4007`), total profit.

**8. Where the money goes card** (summary view)
Header "Where the money goes" / "Extended across the whole quote". 4-column grid, `gap:20px; padding:20px`. Tiles: Material, Labor, Setup & freight, Build hours. Label 12.5px `#8b887f`, value 19px/600.

### Right column (sticky, `top: 28px`)

**9. Harness cost & price card** (harness view only)
- Title: harness name (14px/600); sub-line "Per harness at qty {n}".
- Cost stack rows (13.5px, label `#6f6c66`, value tabular): Material, Scrap, Labor, Setup amortized, Freight & pack.
- 1px divider, then "Unit cost" (13.5px/600) with the value at 22px/600.
- Cost-mix bar: 8px tall, `border-radius:4px`, track `#f1f1ee`, `gap:3px` between segments — material `#b45309`, labor `#e0a463`, other `#e6e5e1` — widths are the percentage of unit cost. Below it, three 12px `#8b887f` labels: `material {n}%`, `labor {n}%`, `other {n}%`.
- Price block: `padding:16px 18px; border-radius:10px; background:#fdf7f0; border:1px solid #f2e6d6`. Row "Margin at {n}%" with margin dollars; then "Customer price" with the price at 28px/600 `#b45309`, `-0.015em`.
- Rows: Extended price (bold value), Line profit.
- If any part is unpriced: alert block `padding:11px 13px; border-radius:8px; background:#fdf3f1; border:1px solid #f2ded9; color:#8a4237; 12.5px` — "{n} parts had no price returned. Manual costs are included in the total."

**10. Quote total card** (always visible)
Title "Quote total" / "{n} harnesses". Rows: Total cost, Total profit, Blended margin (one decimal, `%`). Divider. "Quote price" with value at 26px/600 `#b45309`. Buttons: primary "Print quote" (fills width, `#b45309`) and secondary "Reset".

## Cost model

All money is per harness unless stated. `N(v)` parses a numeric field, treating blanks and junk as 0.

```
unitPrice(line)  = resolved ? catalogPrice : manualCost
material         = Σ over lines of qty × unitPrice
scrap            = material × scrapPct / 100
eff              = max(0.2, efficiencyFactor || 1)
processMinutes   = enabled ? count × secEach / 60 : 0
totalMinutes     = (Σ processMinutes) / eff
labor            = totalMinutes / 60 × laborRate
freight          = per-harness freight $/ea
base             = material + scrap + labor + freight

setupPerUnit(q)  = harnessSetup / q                 // q = order qty, min 1, rounded
unitCost(q)      = base + setupPerUnit(q)
margin           = min(marginPct, 95) / 100
unitPrice(q)     = roundUp(unitCost(q) / (1 - margin), roundPriceTo)
profit(q)        = (unitPrice(q) - unitCost(q)) × q
extended(q)      = unitPrice(q) × q
```

Quote rollups sum each harness at its own order quantity:
```
quotePrice     = Σ extended
quoteCost      = Σ unitCost × qty
quoteMaterial  = Σ (material + scrap) × qty
quoteLabor     = Σ labor × qty
quoteOther     = quoteCost - quoteMaterial - quoteLabor
buildHours     = Σ totalMinutes × qty / 60
blendedMargin  = (quotePrice - quoteCost) / quotePrice
```

Cost-mix percentages are each component divided by `unitCost`, rounded; "other" is `100 - material% - labor%`, floored at 0.

Money format: `$` + `toLocaleString('en-US')` with 2 decimals; unit prices under $1 show 3 decimals. Negative values use a minus sign `−` before the symbol. All numeric cells use `font-variant-numeric: tabular-nums`.

## Interactions & Behavior

- **Tab switching** — clicking a harness pill sets it active; the middle column and the top-right rail card show that harness. Clicking "Summary" hides the harness cards and the harness rail card (Quote total stays).
- **Add harness** — appends `{ name: "Harness {n+1}", partNo: "", orderQty: "25", setup: "250", freight: "1.00", lines: [one blank line], processes: all six with count 0 }` and activates it.
- **Duplicate** — deep-copies the active harness, inserts it after, names it "{name} (copy)", activates it.
- **Remove** — deletes the active harness and activates the previous one. No-op when only one harness remains.
- **Part lookup** — blurring a part-number field resolves that one part number. "Look up this BOM" resolves every part number in the active harness. "Price all harnesses" resolves every unique part number in the quote. Resolution is **deduplicated and cached quote-wide**: a part number already in the cache is never requested again, and every harness that uses it reads the same cached record. In the prototype this is a 380ms `setTimeout` against a local catalog object; in production it is the DigiKey Product Information API. Parts move through pending → resolved (cache hit) or missing.
- **Suggest counts from parts** — derives process counts from the active harness's BOM categories: Cut and strip = number of Wire lines; Crimp = summed qty of Terminal lines; Install connector = number of Connector lines; Heat shrink and Labeling = summed qty of Label / shrink lines; Inspection = 1. A process whose derived count is greater than 0 is switched on; a process already on stays on.
- **Process toggle off** — disables the count input, grays the row, and drops the row's time from the total.
- **Print quote** — `window.print()`. No print stylesheet was designed; a real implementation should produce a customer-facing quote sheet.
- **Reset** — restores the seeded harnesses, active tab 0, and margin 32.
- Hover-reveal borders on in-table inputs are the only motion in the design; there are no transitions or animations.

## State Management

Global (quote-level):
- `customer`
- `laborRate`, `efficiency`, `scrapPct`, `marginPct`
- `times` — map of processId → seconds, keys `cut, crimp, conn, shrink, label, insp`
- `dkConnected`, `lastLookup`
- `cache` — partNumberKey → `{ desc, cat, price, tier, src }`; `pending` — partNumberKey → true; `missing` — partNumberKey → true
- `harnesses[]`, `active` (index or `'sum'`)

Per harness:
- `name`, `partNo`, `orderQty`, `setup`, `freight`
- `lines[]` — `{ part, qty, cat, cost }` where `cost` is the manual fallback price
- `processes[]` — `{ id, name, on, count }`; **no per-harness time** (times are global)

Part numbers are normalized with `trim().toUpperCase()` before cache lookups so manufacturer and DigiKey numbers key consistently.

### DigiKey integration notes
The prototype's `CATALOG` object stands in for the API and is indexed by both manufacturer P/N and DigiKey P/N, with a `src` flag distinguishing the two. A real implementation needs: OAuth2 client-credentials token handling, keyword/part search to resolve a manufacturer P/N to a DigiKey product, price-break selection based on the extended quantity for the run (order qty × per-harness qty) rather than the per-harness qty, stock/lead-time surfacing, and per-quote caching so a repeated part number costs one request. The prototype's "tier" string (e.g. "100 ft tier") is a placeholder for the selected price break.

## Design Tokens

Colors
- Page background `#f6f7f7`; surface `#fff`; inset/zebra `#fbfbfa`, `#fcfcfb`, `#fafaf9`
- Borders `#eaeae7` (card), `#f1f1ee` (inner rule), `#f6f6f4` (table row), `#e0e0dc` (input), `#e4e3df` (inactive pill), `#d5d3cd` (dashed)
- Text `#1a1917` primary, `#3d3b37` / `#5c5952` secondary, `#6f6c66` label, `#8b887f` muted, `#a3a09a` / `#b3b0aa` / `#c4c1bb` disabled
- Accent `#b45309`; accent hover `#9a460a`; accent text `#8a4007`; accent tint `#fdf7f0`; accent tint border `#f2e6d6`; accent hover border `#c9a06a`
- Chart segments: material `#b45309`, labor `#e0a463`, other `#e6e5e1`
- Source pills: DK `#eef4f8` / `#3a6b8c`; Mfr `#f2f1ec` / `#6f6c66`; unresolved `#faf3f1` / `#a8746a`
- Warning `#fdf3f1` bg / `#f2ded9` border / `#8a4237` text; destructive hover `#f7eeee` / `#a8443b`
- Status dot: connected `#2f8f5b`, disconnected `#d1a24a`

Typography — `'Helvetica Neue', Helvetica, Arial, sans-serif` throughout, `-webkit-font-smoothing: antialiased`.
- 19px/600 page title · 22–30px/600 money figures · 14px/600 card title · 13.5px body · 13px table input · 12.5px muted sub-line · 12px table header and field label · 11px source pill and price-break note
- All numeric output uses `font-variant-numeric: tabular-nums`

Spacing — 3, 5, 7, 8, 9, 11, 12, 14, 18, 20, 22, 24, 28, 36 px. Card body padding `18px 20px`; card header `16px 20px 14px`; table cells `5px 8px` (11px for headers, 20px on outer edges); column gap 24; card stack gap 20.

Radius — 12 card · 10 price block · 9 tab pill · 8 input and button · 6 in-table input · 5 source pill · 4 chart bar.

Shadows — card `0 1px 2px rgba(26,25,23,0.04), 0 6px 16px rgba(26,25,23,0.03)`; rail card `0 1px 2px rgba(26,25,23,0.04), 0 10px 28px rgba(26,25,23,0.05)`; active tab `0 1px 2px rgba(26,25,23,0.06)`; primary button `0 1px 2px rgba(26,25,23,0.12)`.

## Assets
None. No images, icons, or icon fonts — the design is type and rules only. The one graphic element is the CSS cost-mix bar.

## Sample data
The prototype seeds two harnesses ("Main engine harness" WH-4412-A ×25, "Sample jumper" WH-4413-A ×60) and a ten-item catalog of Deutsch DT connectors, M22759/16 wire, contacts, cavity plugs, split loom, and heatshrink labels. This is illustrative only — replace with real data.

## Files
- `screenshots/01-harness-view.png` — the harness tab: labor assumptions, parts, processes, per-harness cost and price rail.
- `screenshots/02-summary-view.png` — the Summary tab: per-harness rollup and quote totals.
- `Harness Quote.dc.html` — the full design: markup in the `<x-dc>` block, calculation and state in the `class Component` script below it.
- `support.js` — the prototyping runtime. Included only so the HTML opens and runs in a browser. Do not port it.

Open `Harness Quote.dc.html` directly in a browser to interact with the design.
