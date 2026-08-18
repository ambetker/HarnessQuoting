"""Parses bulk-pasted BOM text — one part per line, "PART_NUMBER, QTY".
Tolerant of a non-parsing first line (treated as a header and silently
skipped) and of extra trailing columns (ignored), but doesn't try to
guess at looser formats — the paste dialog gives the user an exact
prompt to get an AI-generated BOM into this shape in the first place.
"""

from dataclasses import dataclass, field


@dataclass
class ParsedBomLine:
    part_number: str
    qty: float


@dataclass
class BomParseResult:
    lines: list[ParsedBomLine] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)  # raw lines that couldn't be parsed


def _parse_qty(text: str) -> float | None:
    try:
        return float(text.strip())
    except ValueError:
        return None


def parse_bom_text(text: str) -> BomParseResult:
    result = BomParseResult()
    raw_lines = [line for line in text.splitlines() if line.strip()]

    for i, raw in enumerate(raw_lines):
        columns = raw.split(",")
        if len(columns) < 2:
            columns = raw.split("\t")  # tolerate a spreadsheet-style paste too
        if len(columns) < 2:
            result.skipped.append(raw)
            continue

        part_number = columns[0].strip()
        qty = _parse_qty(columns[1])

        if not part_number or qty is None:
            if i == 0:
                continue  # likely a header row ("Part Number, Qty") — skip quietly
            result.skipped.append(raw)
            continue

        result.lines.append(ParsedBomLine(part_number=part_number, qty=qty))

    return result
