from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QHeaderView, QPushButton, QTableWidget, QTableWidgetItem

from app.cost_model import price_harness, price_quote
from app.models import Quote
from app.ui.widgets.card import Card
from app.ui.widgets.table_utils import fit_table_height

COLUMNS = ["Harness", "P/N", "Qty", "Unit cost", "Unit price", "Extended", "Margin $"]


class QuoteSummaryWidget(Card):
    harness_opened = Signal(int)

    def __init__(self, parent=None):
        super().__init__("Quote summary", "Every harness on this quote at its own order quantity", parent)
        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        # Column 0 is Stretch, so the rest need explicit widths — otherwise
        # Qt's default ~100px-per-column for columns 1-6 ate all the space
        # before the stretch column got a chance, collapsing "Harness" to
        # a sliver.
        for col, width in {1: 100, 2: 55, 3: 90, 4: 90, 5: 90, 6: 90}.items():
            self.table.setColumnWidth(col, width)
        self.body.addWidget(self.table)

    def render(self, quote: Quote) -> None:
        rows = [(h, price_harness(h, quote.labor)) for h in quote.harnesses]
        totals = price_quote(quote)

        # See parts_table.render() — collapsing to 0 first avoids stale
        # cell widgets bleeding through on re-render.
        self.table.setRowCount(0)
        self.table.setRowCount(len(rows) + 1)

        for i, (harness, pricing) in enumerate(rows):
            open_btn = QPushButton(harness.name)
            open_btn.setFlat(True)
            open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            open_btn.setStyleSheet("color: #b45309; text-align: left; border: none; background: transparent;")
            open_btn.clicked.connect(lambda _checked=False, idx=i: self.harness_opened.emit(idx))
            self.table.setCellWidget(i, 0, open_btn)

            values = [
                harness.part_no or "—",
                str(pricing.qty),
                _money(pricing.unit_cost),
                _money(pricing.unit_price),
                _money(pricing.extended),
                _money(pricing.profit),
            ]
            for col, value in enumerate(values, start=1):
                item = QTableWidgetItem(value)
                item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(i, col, item)

        total_row = len(rows)
        total_item = QTableWidgetItem("Quote total")
        total_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        total_item.setFont(_bold_font())
        self.table.setItem(total_row, 0, total_item)
        self.table.setSpan(total_row, 0, 1, 3)

        total_values = {3: _money(totals.quote_cost), 5: _money(totals.quote_price), 6: _money(totals.quote_price - totals.quote_cost)}
        for col in range(1, len(COLUMNS)):
            text = total_values.get(col, "")
            item = QTableWidgetItem(text)
            item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item.setFont(_bold_font())
            if col == 5:
                item.setForeground(QColor("#8a4007"))
            self.table.setItem(total_row, col, item)

        fit_table_height(self.table)


def _bold_font():
    from PySide6.QtGui import QFont

    font = QFont()
    font.setBold(True)
    return font


def _money(value: float) -> str:
    sign = "−" if value < 0 else ""
    return f"{sign}${abs(value):,.2f}"
