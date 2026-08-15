from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.cost_model import price_quote
from app.models import Quote
from app.ui.widgets.card import Card


def _row(label_text: str) -> tuple[QWidget, QLabel]:
    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    label = QLabel(label_text)
    label.setStyleSheet("color: #6f6c66;")
    value = QLabel("$0.00")
    layout.addWidget(label)
    layout.addStretch(1)
    layout.addWidget(value)
    return row, value


class QuoteTotalWidget(Card):
    print_requested = Signal()
    reset_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.title_label = QLabel("Quote total")
        self.title_label.setStyleSheet("font-size: 14px; font-weight: 600;")
        self.subtitle_label = QLabel()
        self.subtitle_label.setProperty("role", "muted")
        self.body.addWidget(self.title_label)
        self.body.addWidget(self.subtitle_label)

        cost_row, self.cost_value = _row("Total cost")
        profit_row, self.profit_value = _row("Total profit")
        margin_row, self.margin_value = _row("Blended margin")
        for row in (cost_row, profit_row, margin_row):
            self.body.addWidget(row)

        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background: #f1f1ee; border: none;")
        self.body.addWidget(divider)

        price_row = QWidget()
        price_layout = QHBoxLayout(price_row)
        price_layout.setContentsMargins(0, 0, 0, 0)
        price_label = QLabel("Quote price")
        price_layout.addWidget(price_label)
        price_layout.addStretch(1)
        self.body.addWidget(price_row)

        self.price_value = QLabel("$0.00")
        self.price_value.setStyleSheet("font-size: 26px; font-weight: 600; color: #b45309;")
        self.body.addWidget(self.price_value)

        button_row = QWidget()
        button_layout = QHBoxLayout(button_row)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)
        self.print_btn = QPushButton("Print quote")
        self.print_btn.setProperty("variant", "primary")
        self.print_btn.clicked.connect(self.print_requested.emit)
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setProperty("variant", "secondary")
        self.reset_btn.clicked.connect(self.reset_requested.emit)
        button_layout.addWidget(self.print_btn, 1)
        button_layout.addWidget(self.reset_btn)
        self.body.addWidget(button_row)

    def render(self, quote: Quote) -> None:
        totals = price_quote(quote)
        count = len(quote.harnesses)
        self.subtitle_label.setText(f"{count} harness{'es' if count != 1 else ''}")
        self.cost_value.setText(_money(totals.quote_cost))
        self.profit_value.setText(_money(totals.quote_price - totals.quote_cost))
        self.margin_value.setText(f"{totals.blended_margin_pct:.1f}%")
        self.price_value.setText(_money(totals.quote_price))


def _money(value: float) -> str:
    sign = "−" if value < 0 else ""
    return f"{sign}${abs(value):,.2f}"
