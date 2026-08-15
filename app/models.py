from dataclasses import dataclass, field

# (id, name) in the fixed display order used throughout the UI.
PROCESS_DEFS: list[tuple[str, str]] = [
    ("cut", "Cut and strip"),
    ("crimp", "Crimp"),
    ("conn", "Install connector"),
    ("shrink", "Heat shrink"),
    ("label", "Labeling"),
    ("insp", "Inspection"),
]

CATEGORIES = [
    "Wire",
    "Connector",
    "Terminal",
    "Seal / plug",
    "Loom / braid",
    "Label / shrink",
    "Splice",
    "Other",
]


def default_processes() -> list["Process"]:
    return [Process(id=pid, name=name, on=True, count=0) for pid, name in PROCESS_DEFS]


@dataclass
class PartLine:
    part_number: str
    qty: float
    category: str
    manual_cost: float = 0.0
    resolved: bool = False
    catalog_price: float | None = None
    catalog_category: str | None = None
    description: str = ""
    source: str = "Mfr"  # "DK" or "Mfr", mirrors digikey_client.ResolvedPart.source
    price_tier_label: str = ""
    lookup_attempted: bool = False  # True once a lookup has run, whether or not it found a match
    manual_override: bool = False  # user has overridden a resolved line's catalog price


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
    customer_attn: str = ""
    customer_address: str = ""  # multi-line, newline-separated; shown on the printed quote's bill-to block
