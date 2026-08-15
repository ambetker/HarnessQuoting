from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from app.models import Harness
from app.ui.widgets.card import Card


def _field(label_text: str, width: int | None = None) -> tuple[QWidget, QLineEdit]:
    box = QWidget()
    layout = QVBoxLayout(box)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(7)
    label = QLabel(label_text)
    label.setProperty("role", "field-label")
    edit = QLineEdit()
    if width:
        edit.setFixedWidth(width)
    layout.addWidget(label)
    layout.addWidget(edit)
    return box, edit


class HarnessHeaderWidget(Card):
    changed = Signal()
    duplicate_requested = Signal()
    remove_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(18)

        name_box, self.name_edit = _field("Harness name")
        pn_box, self.part_no_edit = _field("Harness P/N", 150)
        qty_box, self.qty_edit = _field("Qty", 80)
        setup_box, self.setup_edit = _field("Setup $", 88)
        freight_box, self.freight_edit = _field("Freight $/ea", 88)

        row_layout.addWidget(name_box, 1)
        row_layout.addWidget(pn_box)
        row_layout.addWidget(qty_box)
        row_layout.addWidget(setup_box)
        row_layout.addWidget(freight_box)

        self.duplicate_btn = QPushButton("Duplicate")
        self.duplicate_btn.setProperty("variant", "secondary")
        self.duplicate_btn.clicked.connect(self.duplicate_requested.emit)
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.setProperty("variant", "destructive")
        self.remove_btn.clicked.connect(self.remove_requested.emit)

        row_layout.addWidget(self.duplicate_btn)
        row_layout.addWidget(self.remove_btn)

        self.body.addWidget(row)

        for edit in [self.name_edit, self.part_no_edit, self.qty_edit, self.setup_edit, self.freight_edit]:
            edit.editingFinished.connect(self.changed.emit)

    def load(self, harness: Harness) -> None:
        self.name_edit.setText(harness.name)
        self.part_no_edit.setText(harness.part_no)
        self.qty_edit.setText(f"{harness.order_qty:g}")
        self.setup_edit.setText(f"{harness.setup:g}")
        self.freight_edit.setText(f"{harness.freight:g}")

    def apply_to(self, harness: Harness) -> None:
        harness.name = self.name_edit.text() or harness.name
        harness.part_no = self.part_no_edit.text()
        harness.order_qty = _num(self.qty_edit.text()) or 1
        harness.setup = _num(self.setup_edit.text())
        harness.freight = _num(self.freight_edit.text())


def _num(text: str) -> float:
    try:
        return float(text)
    except ValueError:
        return 0.0
