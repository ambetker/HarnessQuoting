"""Maps DigiKey's free-text Category/Family names onto the app's fixed
8-category taxonomy (Wire, Connector, Terminal, Seal / plug, Loom / braid,
Label / shrink, Splice, Other).

Best-effort heuristic — DigiKey's taxonomy doesn't line up 1:1 with a
harness shop's BOM categories. Refine the keyword table as real search
results turn up categories it doesn't handle well.
"""

APP_CATEGORIES = [
    "Wire",
    "Connector",
    "Terminal",
    "Seal / plug",
    "Loom / braid",
    "Label / shrink",
    "Splice",
    "Other",
]

# Checked in order; first keyword match wins.
_KEYWORD_RULES: list[tuple[str, str]] = [
    ("wire", "Wire"),
    ("cable", "Wire"),
    ("terminal", "Terminal"),
    ("contact", "Terminal"),
    ("splice", "Splice"),
    ("seal", "Seal / plug"),
    ("plug", "Seal / plug"),
    ("cavity", "Seal / plug"),
    ("heat shrink", "Label / shrink"),
    ("heatshrink", "Label / shrink"),
    ("sleeving", "Label / shrink"),
    ("label", "Label / shrink"),
    ("loom", "Loom / braid"),
    ("braid", "Loom / braid"),
    ("convoluted tubing", "Loom / braid"),
    ("connector", "Connector"),
    ("housing", "Connector"),
    ("backshell", "Connector"),
]


def map_category(digikey_category: str) -> str:
    lowered = (digikey_category or "").lower()
    for keyword, app_category in _KEYWORD_RULES:
        if keyword in lowered:
            return app_category
    return "Other"
