from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.cost_model import cost_mix_pct, price_harness
from app.models import Harness, LaborAssumptions
from app.ui.widgets.card import Card


def _cost_row(label_text: str) -> tuple[QWidget, QLabel]:
    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    label = QLabel(label_text)
    label.setStyleSheet("color: #6f6c66; font-size: 13.5px;")
    value = QLabel("$0.00")
    value.setStyleSheet("font-size: 13.5px;")
    layout.addWidget(label)
    layout.addStretch(1)
    layout.addWidget(value)
    return row, value


class CostMixBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(8)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(3)
        self._segments = []
        for color in ("#b45309", "#e0a463", "#e6e5e1"):
            seg = QFrame()
            seg.setStyleSheet(f"background: {color}; border-radius: 4px;")
            self._layout.addWidget(seg, 1)
            self._segments.append(seg)

    def set_percentages(self, material_pct: int, labor_pct: int, other_pct: int) -> None:
        for seg, pct in zip(self._segments, (material_pct, labor_pct, other_pct)):
            self._layout.setStretchFactor(seg, max(pct, 1))
            seg.setVisible(pct > 0)


class CostPriceRailWidget(Card):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-size: 14px; font-weight: 600;")
        self.subtitle_label = QLabel()
        self.subtitle_label.setProperty("role", "muted")
        self.body.addWidget(self.title_label)
        self.body.addWidget(self.subtitle_label)

        material_row, self.material_value = _cost_row("Material")
        scrap_row, self.scrap_value = _cost_row("Scrap")
        labor_row, self.labor_value = _cost_row("Labor")
        setup_row, self.setup_value = _cost_row("Setup amortized")
        freight_row, self.freight_value = _cost_row("Freight & pack")
        for row in (material_row, scrap_row, labor_row, setup_row, freight_row):
            self.body.addWidget(row)

        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background: #f1f1ee; border: none;")
        self.body.addWidget(divider)

        unit_cost_row = QWidget()
        unit_cost_layout = QHBoxLayout(unit_cost_row)
        unit_cost_layout.setContentsMargins(0, 0, 0, 0)
        unit_cost_label = QLabel("Unit cost")
        unit_cost_label.setStyleSheet("font-size: 13.5px; font-weight: 600;")
        self.unit_cost_value = QLabel("$0.00")
        self.unit_cost_value.setStyleSheet("font-size: 22px; font-weight: 600;")
        unit_cost_layout.addWidget(unit_cost_label)
        unit_cost_layout.addStretch(1)
        unit_cost_layout.addWidget(self.unit_cost_value)
        self.body.addWidget(unit_cost_row)

        self.mix_bar = CostMixBar()
        self.body.addWidget(self.mix_bar)

        mix_labels_row = QWidget()
        mix_labels_layout = QHBoxLayout(mix_labels_row)
        mix_labels_layout.setContentsMargins(0, 0, 0, 0)
        self.mix_material_label = QLabel()
        self.mix_labor_label = QLabel()
        self.mix_other_label = QLabel()
        for label in (self.mix_material_label, self.mix_labor_label, self.mix_other_label):
            label.setStyleSheet("font-size: 12px; color: #8b887f;")
            mix_labels_layout.addWidget(label)
        mix_labels_layout.addStretch(1)
        self.body.addWidget(mix_labels_row)

        self.price_block = QFrame()
        self.price_block.setStyleSheet(
            "background: #fdf7f0; border: 1px solid #f2e6d6; border-radius: 10px;"
        )
        price_layout = QVBoxLayout(self.price_block)
        price_layout.setContentsMargins(18, 16, 18, 16)
        price_layout.setSpacing(6)

        margin_row = QWidget()
        margin_layout = QHBoxLayout(margin_row)
        margin_layout.setContentsMargins(0, 0, 0, 0)
        self.margin_label = QLabel("Margin at 0%")
        self.margin_label.setStyleSheet("background: transparent;")
        self.margin_value = QLabel("$0.00")
        self.margin_value.setStyleSheet("background: transparent;")
        margin_layout.addWidget(self.margin_label)
        margin_layout.addStretch(1)
        margin_layout.addWidget(self.margin_value)
        price_layout.addWidget(margin_row)

        price_row = QWidget()
        price_row_layout = QHBoxLayout(price_row)
        price_row_layout.setContentsMargins(0, 0, 0, 0)
        price_label = QLabel("Customer price")
        price_label.setStyleSheet("background: transparent;")
        price_row_layout.addWidget(price_label)
        price_row_layout.addStretch(1)
        price_layout.addWidget(price_row)

        self.price_value = QLabel("$0.00")
        self.price_value.setStyleSheet(
            "background: transparent; font-size: 28px; font-weight: 600; color: #b45309;"
        )
        price_layout.addWidget(self.price_value)

        self.body.addWidget(self.price_block)

        ext_row, self.ext_price_value = _cost_row("Extended price")
        self.ext_price_value.setStyleSheet("font-weight: 600;")
        profit_row, self.profit_value = _cost_row("Line profit")
        self.body.addWidget(ext_row)
        self.body.addWidget(profit_row)

        self.alert_box = QLabel()
        self.alert_box.setWordWrap(True)
        self.alert_box.setStyleSheet(
            "background: #fdf3f1; border: 1px solid #f2ded9; color: #8a4237; "
            "border-radius: 8px; padding: 11px 13px; font-size: 12.5px;"
        )
        self.alert_box.hide()
        self.body.addWidget(self.alert_box)

    def render(self, harness: Harness, labor: LaborAssumptions) -> None:
        pricing = price_harness(harness, labor)
        c = pricing.calc

        self.title_label.setText(harness.name)
        self.subtitle_label.setText(f"Per harness at qty {pricing.qty}")

        self.material_value.setText(_money(c.material))
        self.scrap_value.setText(_money(c.scrap))
        self.labor_value.setText(_money(c.labor))
        self.setup_value.setText(_money(pricing.setup_per_unit))
        self.freight_value.setText(_money(c.freight))
        self.unit_cost_value.setText(_money(pricing.unit_cost))

        material_pct, labor_pct, other_pct = cost_mix_pct(c, pricing.unit_cost)
        self.mix_bar.set_percentages(material_pct, labor_pct, other_pct)
        self.mix_material_label.setText(f"material {material_pct}%")
        self.mix_labor_label.setText(f"labor {labor_pct}%")
        self.mix_other_label.setText(f"other {other_pct}%")

        self.margin_label.setText(f"Margin at {labor.margin_pct:g}%")
        self.margin_value.setText(_money(pricing.unit_price - pricing.unit_cost))
        self.price_value.setText(_money(pricing.unit_price))
        self.ext_price_value.setText(_money(pricing.extended))
        self.profit_value.setText(_money(pricing.profit))

        unpriced = sum(1 for line in harness.lines if line.lookup_attempted and not line.resolved)
        if unpriced:
            plural = "s" if unpriced != 1 else ""
            self.alert_box.setText(
                f"{unpriced} part{plural} had no price returned. Manual costs are included in the total."
            )
            self.alert_box.show()
        else:
            self.alert_box.hide()


def _money(value: float) -> str:
    sign = "−" if value < 0 else ""
    return f"{sign}${abs(value):,.2f}"
