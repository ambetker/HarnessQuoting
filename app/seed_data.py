"""Default quote seeded at app startup / Reset — mirrors the two sample
harnesses from the design prototype (same real manufacturer part numbers,
which resolve against the live DigiKey API)."""

from app.models import Harness, LaborAssumptions, PartLine, Process, Quote, default_processes

DEFAULT_TIMES = {"cut": 25, "crimp": 12, "conn": 45, "shrink": 20, "label": 15, "insp": 120}


def _processes(counts: dict[str, float], off: set[str] = frozenset()) -> list[Process]:
    from app.models import PROCESS_DEFS

    return [
        Process(id=pid, name=name, on=pid not in off, count=counts.get(pid, 0))
        for pid, name in PROCESS_DEFS
    ]


def _line(part_number: str, qty: float, category: str) -> PartLine:
    return PartLine(part_number=part_number, qty=qty, category=category)


def make_default_quote() -> Quote:
    labor = LaborAssumptions(
        labor_rate=62.00,
        efficiency=1.00,
        scrap_pct=2.5,
        margin_pct=32,
        times=dict(DEFAULT_TIMES),
    )

    main_engine = Harness(
        name="Main engine harness",
        part_no="WH-4412-A",
        order_qty=25,
        setup=450,
        freight=1.75,
        lines=[
            _line("M22759/16-18-9", 14.5, "Wire"),
            _line("M22759/16-16-2", 9.0, "Wire"),
            _line("DT04-12PA-L012", 1, "Connector"),
            _line("DT06-6S-E004", 2, "Connector"),
            _line("0462-201-16141", 18, "Terminal"),
            _line("114017", 6, "Seal / plug"),
            _line("CLT50N-C", 6.5, "Loom / braid"),
            _line("PSD-1000", 4, "Label / shrink"),
        ],
        processes=_processes({"cut": 2, "crimp": 18, "conn": 3, "shrink": 4, "label": 4, "insp": 1}),
    )

    sensor_jumper = Harness(
        name="Sensor jumper",
        part_no="WH-4413-A",
        order_qty=60,
        setup=180,
        freight=0.85,
        lines=[
            _line("M22759/16-20-0", 3.5, "Wire"),
            _line("DT06-4S-CE06", 1, "Connector"),
            _line("0462-201-16141", 4, "Terminal"),
            _line("114017", 2, "Seal / plug"),
        ],
        processes=_processes(
            {"cut": 1, "crimp": 4, "conn": 1, "shrink": 1, "label": 1, "insp": 1}, off={"shrink"}
        ),
    )

    return Quote(customer="Northwind Controls", labor=labor, harnesses=[main_engine, sensor_jumper])


def make_empty_quote() -> Quote:
    """A genuinely blank starting point for File > New Quote — distinct
    from Reset, which restores the design's fictional sample harnesses."""
    labor = LaborAssumptions(
        labor_rate=62.00,
        efficiency=1.00,
        scrap_pct=2.5,
        margin_pct=32,
        times=dict(DEFAULT_TIMES),
    )
    blank_harness = Harness(
        name="Harness 1",
        part_no="",
        order_qty=25,
        setup=250,
        freight=1.00,
        lines=[PartLine(part_number="", qty=1, category="Other")],
        processes=default_processes(),
    )
    return Quote(customer="", labor=labor, harnesses=[blank_harness])
