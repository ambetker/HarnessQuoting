from PySide6.QtWidgets import QGridLayout, QLabel, QVBoxLayout, QWidget

from app.cost_model import price_quote
from app.models import Quote
from app.ui.widgets.card import Card


class MoneyBreakdownWidget(Card):
    def __init__(self, parent=None):
        super().__init__("Where the money goes", "Extended across the whole quote", parent)
        grid = QGridLayout()
        grid.setSpacing(20)
        self.body.addLayout(grid)

        self.tiles: dict[str, QLabel] = {}
        for col, key in enumerate(["Material", "Labor", "Setup & freight", "Build hours"]):
            tile = QWidget()
            tile_layout = QVBoxLayout(tile)
            tile_layout.setContentsMargins(0, 0, 0, 0)
            tile_layout.setSpacing(6)
            label = QLabel(key)
            label.setProperty("role", "muted")
            value = QLabel("—")
            value.setStyleSheet("font-size: 19px; font-weight: 600;")
            tile_layout.addWidget(label)
            tile_layout.addWidget(value)
            grid.addWidget(tile, 0, col)
            self.tiles[key] = value

    def render(self, quote: Quote) -> None:
        totals = price_quote(quote)
        self.tiles["Material"].setText(_money(totals.quote_material))
        self.tiles["Labor"].setText(_money(totals.quote_labor))
        self.tiles["Setup & freight"].setText(_money(totals.quote_other))
        self.tiles["Build hours"].setText(f"{totals.build_hours:.1f} h")


def _money(value: float) -> str:
    sign = "−" if value < 0 else ""
    return f"{sign}${abs(value):,.2f}"
