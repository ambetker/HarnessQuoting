"""JSON save/load for Quote state.

Explicit field-by-field (de)serialization rather than dataclasses.asdict()
+ Quote(**data), so loading an older save file with missing/renamed fields
degrades gracefully via .get() defaults instead of raising.
"""

import json
from pathlib import Path

from app.models import Harness, LaborAssumptions, PartLine, Process, Quote


def quote_to_dict(quote: Quote) -> dict:
    return {
        "customer": quote.customer,
        "labor": {
            "labor_rate": quote.labor.labor_rate,
            "efficiency": quote.labor.efficiency,
            "scrap_pct": quote.labor.scrap_pct,
            "margin_pct": quote.labor.margin_pct,
            "times": dict(quote.labor.times),
            "round_price_to": quote.labor.round_price_to,
        },
        "harnesses": [_harness_to_dict(h) for h in quote.harnesses],
    }


def _harness_to_dict(harness: Harness) -> dict:
    return {
        "name": harness.name,
        "part_no": harness.part_no,
        "order_qty": harness.order_qty,
        "setup": harness.setup,
        "freight": harness.freight,
        "lines": [_line_to_dict(line) for line in harness.lines],
        "processes": [_process_to_dict(p) for p in harness.processes],
    }


def _line_to_dict(line: PartLine) -> dict:
    return {
        "part_number": line.part_number,
        "qty": line.qty,
        "category": line.category,
        "manual_cost": line.manual_cost,
        "resolved": line.resolved,
        "catalog_price": line.catalog_price,
        "catalog_category": line.catalog_category,
        "description": line.description,
        "source": line.source,
        "price_tier_label": line.price_tier_label,
        "lookup_attempted": line.lookup_attempted,
        "manual_override": line.manual_override,
    }


def _process_to_dict(process: Process) -> dict:
    return {"id": process.id, "name": process.name, "on": process.on, "count": process.count}


def save_quote(quote: Quote, path: Path) -> None:
    path.write_text(json.dumps(quote_to_dict(quote), indent=2))


def load_quote(path: Path) -> Quote:
    data = json.loads(path.read_text())
    return quote_from_dict(data)


def quote_from_dict(data: dict) -> Quote:
    labor_data = data.get("labor", {})
    labor = LaborAssumptions(
        labor_rate=labor_data.get("labor_rate", 0.0),
        efficiency=labor_data.get("efficiency", 1.0),
        scrap_pct=labor_data.get("scrap_pct", 0.0),
        margin_pct=labor_data.get("margin_pct", 0.0),
        times=dict(labor_data.get("times", {})),
        round_price_to=labor_data.get("round_price_to", 0.0),
    )
    harnesses = [_harness_from_dict(h) for h in data.get("harnesses", [])]
    return Quote(customer=data.get("customer", ""), labor=labor, harnesses=harnesses)


def _harness_from_dict(data: dict) -> Harness:
    return Harness(
        name=data.get("name", ""),
        part_no=data.get("part_no", ""),
        order_qty=data.get("order_qty", 1),
        setup=data.get("setup", 0.0),
        freight=data.get("freight", 0.0),
        lines=[_line_from_dict(l) for l in data.get("lines", [])],
        processes=[_process_from_dict(p) for p in data.get("processes", [])],
    )


def _line_from_dict(data: dict) -> PartLine:
    return PartLine(
        part_number=data.get("part_number", ""),
        qty=data.get("qty", 0.0),
        category=data.get("category", "Other"),
        manual_cost=data.get("manual_cost", 0.0),
        resolved=data.get("resolved", False),
        catalog_price=data.get("catalog_price"),
        catalog_category=data.get("catalog_category"),
        description=data.get("description", ""),
        source=data.get("source", "Mfr"),
        price_tier_label=data.get("price_tier_label", ""),
        lookup_attempted=data.get("lookup_attempted", False),
        manual_override=data.get("manual_override", False),
    )


def _process_from_dict(data: dict) -> Process:
    return Process(
        id=data.get("id", ""),
        name=data.get("name", ""),
        on=data.get("on", True),
        count=data.get("count", 0),
    )
