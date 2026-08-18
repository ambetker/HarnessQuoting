"""Regression fixture: the two harnesses seeded in
design_handoff_harness_quoting/Harness Quote.dc.html (CATALOG + HARNESSES),
asserted against the exact numbers shown in the design screenshots
(01-harness-view.png, 02-summary-view.png).
"""

import pytest

from app.cost_model import cost_mix_pct, has_unpriced_lines, line_unit_price, price_harness, price_quote
from app.models import Harness, LaborAssumptions, PartLine, Process, Quote

LABOR = LaborAssumptions(
    labor_rate=62.00,
    efficiency=1.00,
    scrap_pct=2.5,
    margin_pct=32,
    times={"cut": 25, "crimp": 12, "conn": 45, "shrink": 20, "label": 15, "insp": 120},
)


def resolved_line(part_number, qty, category, price) -> PartLine:
    return PartLine(
        part_number=part_number,
        qty=qty,
        category=category,
        resolved=True,
        catalog_price=price,
        catalog_category=category,
    )


def default_processes(counts: dict[str, float], off: set[str] = frozenset()) -> list[Process]:
    names = {
        "cut": "Cut and strip",
        "crimp": "Crimp",
        "conn": "Install connector",
        "shrink": "Heat shrink",
        "label": "Labeling",
        "insp": "Inspection",
    }
    return [
        Process(id=pid, name=names[pid], on=pid not in off, count=counts[pid])
        for pid in names
    ]


@pytest.fixture
def main_engine_harness() -> Harness:
    return Harness(
        name="Main engine harness",
        part_no="WH-4412-A",
        order_qty=25,
        setup=450,
        freight=1.75,
        lines=[
            resolved_line("M22759/16-18-9", 14.5, "Wire", 0.42),
            resolved_line("M22759/16-16-2", 9.0, "Wire", 0.51),
            resolved_line("DT04-12PA-L012", 1, "Connector", 11.80),
            resolved_line("WM10254-ND", 2, "Connector", 6.35),
            resolved_line("0462-201-16141", 18, "Terminal", 0.34),
            resolved_line("114017", 6, "Seal / plug", 0.09),
            resolved_line("CLT50N-C", 6.5, "Loom / braid", 0.28),
            resolved_line("PSD-1000", 4, "Label / shrink", 0.22),
        ],
        processes=default_processes({"cut": 2, "crimp": 18, "conn": 3, "shrink": 4, "label": 4, "insp": 1}),
    )


@pytest.fixture
def sensor_jumper_harness() -> Harness:
    return Harness(
        name="Sensor jumper",
        part_no="WH-4413-A",
        order_qty=60,
        setup=180,
        freight=0.85,
        lines=[
            resolved_line("M22759/16-20-0", 3.5, "Wire", 0.31),
            resolved_line("DT06-4S-CE06", 1, "Connector", 4.90),
            resolved_line("0462-201-16141", 4, "Terminal", 0.34),
            resolved_line("114017", 2, "Seal / plug", 0.09),
        ],
        processes=default_processes(
            {"cut": 1, "crimp": 4, "conn": 1, "shrink": 1, "label": 1, "insp": 1}, off={"shrink"}
        ),
    )


def test_main_engine_harness_matches_design_screenshot(main_engine_harness):
    pricing = price_harness(main_engine_harness, LABOR)

    assert pricing.calc.material == pytest.approx(44.54, abs=0.01)
    assert pricing.calc.scrap == pytest.approx(1.11, abs=0.01)
    assert pricing.calc.labor == pytest.approx(11.38, abs=0.01)
    assert pricing.setup_per_unit == pytest.approx(18.00, abs=0.01)
    assert pricing.calc.freight == pytest.approx(1.75, abs=0.01)
    assert pricing.unit_cost == pytest.approx(76.79, abs=0.01)
    assert pricing.unit_price == pytest.approx(112.92, abs=0.01)
    assert pricing.extended == pytest.approx(2823.07, abs=0.01)
    assert pricing.profit == pytest.approx(903.38, abs=0.01)

    material_pct, labor_pct, other_pct = cost_mix_pct(pricing.calc, pricing.unit_cost)
    assert (material_pct, labor_pct, other_pct) == (58, 15, 27)


def test_sensor_jumper_harness_matches_design_summary(sensor_jumper_harness):
    pricing = price_harness(sensor_jumper_harness, LABOR)

    assert pricing.unit_cost == pytest.approx(15.92, abs=0.01)
    assert pricing.unit_price == pytest.approx(23.41, abs=0.01)
    assert pricing.extended == pytest.approx(1404.74, abs=0.01)
    assert pricing.profit == pytest.approx(449.52, abs=0.01)


def test_quote_totals_match_design_summary(main_engine_harness, sensor_jumper_harness):
    quote = Quote(customer="Northwind Controls", labor=LABOR, harnesses=[main_engine_harness, sensor_jumper_harness])

    totals = price_quote(quote)

    assert totals.quote_price == pytest.approx(4227.80, abs=0.01)
    assert totals.quote_cost == pytest.approx(2874.91, abs=0.01)
    assert (totals.quote_price - totals.quote_cost) == pytest.approx(1352.90, abs=0.01)
    assert totals.blended_margin_pct == pytest.approx(32.0, abs=0.05)
    assert totals.quote_material == pytest.approx(1604.13, abs=0.01)
    assert totals.quote_labor == pytest.approx(546.03, abs=0.01)
    assert totals.quote_other == pytest.approx(724.75, abs=0.01)
    assert totals.build_hours == pytest.approx(8.8, abs=0.05)


def test_manual_override_takes_precedence_over_catalog_price():
    # Regression guard: a resolved line priced from a roll/spool listing
    # (e.g. CLT50N-C630, priced per 100' roll rather than per foot) can be
    # wildly wrong; the estimator needs to be able to override it.
    line = PartLine(
        part_number="CLT50N-C630", qty=6.5, category="Loom / braid",
        resolved=True, catalog_price=96.965, manual_override=False,
    )
    assert line_unit_price(line) == pytest.approx(96.965)

    line.manual_override = True
    line.manual_cost = 0.28
    assert line_unit_price(line) == pytest.approx(0.28)


def test_efficiency_floor_applies_below_0_2():
    # efficiency=0.1 is truthy (unlike 0.0, which the source's `|| 1`
    # fallback would replace with 1 before the max(0.2, ...) floor ever
    # applies), so this genuinely exercises the 0.2 floor.
    labor = LaborAssumptions(
        labor_rate=60, efficiency=0.1, scrap_pct=0, margin_pct=0,
        times={"cut": 60, "crimp": 0, "conn": 0, "shrink": 0, "label": 0, "insp": 0},
    )
    harness = Harness(
        name="Edge case", part_no="", order_qty=1, setup=0, freight=0,
        lines=[],
        processes=[Process(id="cut", name="Cut and strip", on=True, count=1)],
    )
    pricing = price_harness(harness, labor)
    # 1 min of raw work / eff-floor 0.2 = 5 minutes -> 5/60*60 = $5.00 labor
    assert pricing.calc.labor == pytest.approx(5.00, abs=0.01)


def test_margin_capped_at_95_percent():
    labor = LaborAssumptions(
        labor_rate=0, efficiency=1, scrap_pct=0, margin_pct=200,
        times={"cut": 0, "crimp": 0, "conn": 0, "shrink": 0, "label": 0, "insp": 0},
    )
    harness = Harness(
        name="Edge case", part_no="", order_qty=1, setup=0, freight=0,
        lines=[PartLine(part_number="X", qty=1, category="Other", manual_cost=10)],
        processes=[],
    )
    pricing = price_harness(harness, labor)
    # margin capped at 95% -> price = cost / (1 - 0.95) = cost / 0.05
    assert pricing.unit_price == pytest.approx(10 / 0.05, abs=0.01)


def test_round_price_to_applies_when_configured():
    labor = LaborAssumptions(
        labor_rate=0, efficiency=1, scrap_pct=0, margin_pct=50,
        times={"cut": 0, "crimp": 0, "conn": 0, "shrink": 0, "label": 0, "insp": 0},
        round_price_to=1.00,
    )
    harness = Harness(
        name="Edge case", part_no="", order_qty=1, setup=0, freight=0,
        lines=[PartLine(part_number="X", qty=1, category="Other", manual_cost=10.10)],
        processes=[],
    )
    pricing = price_harness(harness, labor)
    # cost=10.10, price = 10.10/0.5 = 20.20 -> rounds up to nearest $1 -> 21.00
    assert pricing.unit_price == pytest.approx(21.00, abs=0.001)


def test_has_unpriced_lines_true_when_a_lookup_failed_to_resolve():
    harness = Harness(
        name="H", part_no="", order_qty=1, setup=0, freight=0,
        lines=[PartLine(part_number="X", qty=1, category="Other", lookup_attempted=True, resolved=False)],
        processes=[],
    )
    assert has_unpriced_lines(harness) is True


def test_has_unpriced_lines_false_when_all_resolved_or_not_yet_looked_up():
    harness = Harness(
        name="H", part_no="", order_qty=1, setup=0, freight=0,
        lines=[
            PartLine(part_number="X", qty=1, category="Other", lookup_attempted=True, resolved=True, catalog_price=1.0),
            PartLine(part_number="Y", qty=1, category="Other", lookup_attempted=False, resolved=False),
        ],
        processes=[],
    )
    assert has_unpriced_lines(harness) is False


def test_has_unpriced_lines_false_for_empty_lines():
    harness = Harness(name="H", part_no="", order_qty=1, setup=0, freight=0, lines=[], processes=[])
    assert has_unpriced_lines(harness) is False
