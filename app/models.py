from dataclasses import dataclass, field


@dataclass
class PartLine:
    part_number: str
    qty: float
    category: str
    manual_cost: float = 0.0
    resolved: bool = False
    catalog_price: float | None = None
    catalog_category: str | None = None


@dataclass
class Process:
    id: str
    name: str
    on: bool
    count: float


@dataclass
class LaborAssumptions:
    labor_rate: float
    efficiency: float
    scrap_pct: float
    margin_pct: float
    times: dict[str, float]  # process id -> seconds
    round_price_to: float = 0.0  # 0 = no rounding, matches the design's default


@dataclass
class Harness:
    name: str
    part_no: str
    order_qty: float
    setup: float
    freight: float
    lines: list[PartLine] = field(default_factory=list)
    processes: list[Process] = field(default_factory=list)


@dataclass
class Quote:
    customer: str
    labor: LaborAssumptions
    harnesses: list[Harness] = field(default_factory=list)
