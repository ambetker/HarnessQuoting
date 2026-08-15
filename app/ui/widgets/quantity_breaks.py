from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem

from app.cost_model import quantity_breaks
from app.models import Harness, LaborAssumptions
from app.ui.widgets.card import Card
from app.ui.widgets.table_utils import fit_table_height

COLUMNS = ["Qty", "Unit cost", "Unit price", "Extended", "Margin $"]


class QuantityBreaksWidget(Card):
    def __init__(self, parent=None):
        super().__init__("Quantity breaks", "This harness, setup amortized across the run", parent)
        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.body.addWidget(self.table)

    def render(self, harness: Harness, labor: LaborAssumptions) -> None:
        breaks = quantity_breaks(harness, labor, harness.order_qty)
        self.table.setRowCount(len(breaks))
        for i, pricing in enumerate(breaks):
            values = [
                str(pricing.qty),
                _money(pricing.unit_cost),
                _money(pricing.unit_price),
                _money(pricing.extended),
                _money(pricing.profit),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if col == 2:
                    item.setForeground(QColor("#8a4007"))
                self.table.setItem(i, col, item)

        fit_table_height(self.table)


def _money(value: float) -> str:
    sign = "−" if value < 0 else ""
    return f"{sign}${abs(value):,.2f}"
