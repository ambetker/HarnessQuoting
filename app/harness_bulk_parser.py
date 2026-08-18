"""Parses bulk-pasted multi-harness BOM text — one component per line,
"HARNESS_NAME, HARNESS_PN, HARNESS_QTY, COMPONENT_PN, COMPONENT_QTY".
The harness identity/qty repeat on every row belonging to that harness;
rows are grouped by (HARNESS_NAME, HARNESS_PN) to reconstruct which
components belong to which harness. Same tolerance rules as bom_parser:
a non-parsing first line is treated as a header and skipped quietly,
extra trailing columns are ignored, tab-separated is a fallback.
"""

from dataclasses import dataclass, field

from app.bom_parser import ParsedBomLine


@dataclass
class ParsedHarnessGroup:
    name: str
    part_no: str
    qty: float
    lines: list[ParsedBomLine] = field(default_factory=list)


@dataclass
class HarnessBulkParseResult:
    groups: list[ParsedHarnessGroup] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


def _parse_num(text: str) -> float | None:
    try:
        return float(text.strip())
    except ValueError:
        return None


def parse_harness_bulk_text(text: str) -> HarnessBulkParseResult:
    result = HarnessBulkParseResult()
    groups_by_key: dict[tuple[str, str], ParsedHarnessGroup] = {}
    raw_lines = [line for line in text.splitlines() if line.strip()]

    for i, raw in enumerate(raw_lines):
        columns = raw.split(",")
        if len(columns) < 5:
            columns = raw.split("\t")
        if len(columns) < 5:
            if i == 0:
                continue  # likely a header row — skip quietly
            result.skipped.append(raw)
            continue

        name = columns[0].strip()
        part_no = columns[1].strip()
        harness_qty = _parse_num(columns[2])
        component_pn = columns[3].strip()
        component_qty = _parse_num(columns[4])

        if not name or harness_qty is None or not component_pn or component_qty is None:
            if i == 0:
                continue
            result.skipped.append(raw)
            continue

        key = (name, part_no)
        group = groups_by_key.get(key)
        if group is None:
            group = ParsedHarnessGroup(name=name, part_no=part_no, qty=harness_qty)
            groups_by_key[key] = group
            result.groups.append(group)
        group.lines.append(ParsedBomLine(part_number=component_pn, qty=component_qty))

    return result
