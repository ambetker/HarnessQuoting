"""Wire harness cost model, ported verbatim from the design prototype's
calcH/priceH logic (design_handoff_harness_quoting/Harness Quote.dc.html).

Pure functions over app.models dataclasses — no UI or I/O here.
"""

import math
from dataclasses import dataclass

from app.models import Harness, LaborAssumptions, PartLine, Quote


def line_unit_price(line: PartLine) -> float:
    if line.resolved and line.catalog_price is not None and not line.manual_override:
        return line.catalog_price
    return line.manual_cost


def line_category(line: PartLine) -> str:
    return line.catalog_category if (line.resolved and line.catalog_category) else line.category


def unit_for_category(category: str) -> str:
    return "ft" if category in ("Wire", "Loom / braid") else "ea"


def has_unpriced_lines(harness: Harness) -> bool:
    """True if any line was looked up but came back with no catalog price
    (and isn't manually overridden) — the same condition the cost/price
    rail's "N parts had no price returned" alert is keyed off."""
    return any(line.lookup_attempted and not line.resolved for line in harness.lines)


def has_missing_cost_lines(harness: Harness) -> bool:
    """True if any line has no price at all in its cost box — neither a
    resolved catalog price nor a manually-entered one. Unlike
    has_unpriced_lines, this counts a line as fine once *any* cost has
    been entered for it, manual or not."""
    return any(line_unit_price(line) == 0 for line in harness.lines)


def has_manual_cost_lines(harness: Harness) -> bool:
    """True if any line's price comes from a manual entry rather than a
    resolved catalog price (never resolved, or resolved but overridden)
    — and that line does have a cost (see has_missing_cost_lines for the
    "no cost at all" case, which takes precedence over this one)."""
    return any(
        (not line.resolved or line.manual_override) and line_unit_price(line) != 0
        for line in harness.lines
    )


def harness_flag_status(harness: Harness) -> str | None:
    """'missing' if any line has no cost entered at all (most severe —
    takes precedence), 'manual' if every line has a cost but at least one
    came from manual entry rather than the catalog, otherwise None."""
    if has_missing_cost_lines(harness):
        return "missing"
    if has_manual_cost_lines(harness):
        return "manual"
    return None


def _round_half_up(value: float) -> int:
    """Matches JS Math.round (half rounds toward +Infinity), unlike
    Python's round() which rounds half to even."""
    return math.floor(value + 0.5)


@dataclass
class HarnessCalc:
    material: float
    scrap: float
    total_minutes: float
    labor: float
    freight: float
    eff: float
    base: float


def calc_harness(harness: Harness, labor: LaborAssumptions) -> HarnessCalc:
    material = sum(line.qty * line_unit_price(line) for line in harness.lines)
    scrap = material * labor.scrap_pct / 100
    eff = max(0.2, labor.efficiency or 1)
    total_minutes = (
        sum(
            (process.count * labor.times.get(process.id, 0) / 60) if process.on else 0
            for process in harness.processes
        )
        / eff
    )
    labor_cost = total_minutes / 60 * labor.labor_rate
    freight = harness.freight
    base = material + scrap + labor_cost + freight
    return HarnessCalc(
        material=material,
        scrap=scrap,
        total_minutes=total_minutes,
        labor=labor_cost,
        freight=freight,
        eff=eff,
        base=base,
    )


def round_price(price: float, round_to: float) -> float:
    if round_to and round_to > 0:
        return math.ceil(price / round_to) * round_to
    return price


@dataclass
class HarnessPricing:
    qty: int
    calc: HarnessCalc
    setup_per_unit: float
    unit_cost: float
    unit_price: float
    profit: float
    extended: float
    extended_cost: float


def price_harness(
    harness: Harness, labor: LaborAssumptions, qty_override: float | None = None
) -> HarnessPricing:
    qty = max(1, _round_half_up(qty_override if qty_override is not None else harness.order_qty))
    calc = calc_harness(harness, labor)
    setup_per_unit = harness.setup / qty
    unit_cost = calc.base + setup_per_unit
    margin = min(labor.margin_pct, 95) / 100
    unit_price = round_price(unit_cost / (1 - margin), labor.round_price_to)
    profit = (unit_price - unit_cost) * qty
    extended = unit_price * qty
    extended_cost = unit_cost * qty
    return HarnessPricing(
        qty=qty,
        calc=calc,
        setup_per_unit=setup_per_unit,
        unit_cost=unit_cost,
        unit_price=unit_price,
        profit=profit,
        extended=extended,
        extended_cost=extended_cost,
    )


def cost_mix_pct(calc: HarnessCalc, unit_cost: float) -> tuple[int, int, int]:
    """(material%, labor%, other%) of unit_cost, rounded; other is the
    remainder, floored at 0."""
    denom = unit_cost or 1
    material_pct = round(calc.material / denom * 100)
    labor_pct = round(calc.labor / denom * 100)
    other_pct = max(0, 100 - material_pct - labor_pct)
    return material_pct, labor_pct, other_pct


def quantity_breaks(
    harness: Harness, labor: LaborAssumptions, order_qty: float
) -> list[HarnessPricing]:
    qtys = sorted({1, 10, max(1, _round_half_up(order_qty)), 100})
    return [price_harness(harness, labor, q) for q in qtys]


@dataclass
class QuoteTotals:
    quote_price: float
    quote_cost: float
    quote_material: float
    quote_labor: float
    quote_other: float
    build_hours: float
    blended_margin_pct: float


def price_quote(quote: Quote) -> QuoteTotals:
    rows = [price_harness(h, quote.labor) for h in quote.harnesses]

    quote_price = sum(r.extended for r in rows)
    quote_cost = sum(r.extended_cost for r in rows)
    quote_material = sum((r.calc.material + r.calc.scrap) * r.qty for r in rows)
    quote_labor = sum(r.calc.labor * r.qty for r in rows)
    quote_other = quote_cost - quote_material - quote_labor
    build_hours = sum(r.calc.total_minutes * r.qty for r in rows) / 60
    blended_margin_pct = (
        (quote_price - quote_cost) / quote_price * 100 if quote_price > 0 else 0.0
    )

    return QuoteTotals(
        quote_price=quote_price,
        quote_cost=quote_cost,
        quote_material=quote_material,
        quote_labor=quote_labor,
        quote_other=quote_other,
        build_hours=build_hours,
        blended_margin_pct=blended_margin_pct,
    )
