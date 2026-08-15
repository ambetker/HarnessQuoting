from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QWidget

from app.models import PROCESS_DEFS, LaborAssumptions
from app.ui.widgets.card import Card


def _divider() -> QFrame:
    line = QFrame()
    line.setFixedHeight(1)
    line.setStyleSheet("background: #f1f1ee; border: none;")
    return line


def _field_row(label_text: str) -> tuple[QWidget, QLineEdit]:
    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    label = QLabel(label_text)
    label.setProperty("role", "field-label")
    edit = QLineEdit()
    edit.setFixedWidth(92)
    edit.setAlignment(Qt.AlignmentFlag.AlignRight)
    layout.addWidget(label, 1)
    layout.addWidget(edit)
    return row, edit


class LaborAssumptionsWidget(Card):
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__("Labor assumptions", "Global — applied to every harness", parent)

        rate_row, self.rate_edit = _field_row("Labor rate — $/hr loaded")
        eff_row, self.efficiency_edit = _field_row("Efficiency factor — ×")
        scrap_row, self.scrap_edit = _field_row("Material scrap — %")
        for row in (rate_row, eff_row, scrap_row):
            self.body.addWidget(row)

        self.body.addWidget(_divider())

        section_row = QWidget()
        section_layout = QHBoxLayout(section_row)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_label = QLabel("TIME PER PROCESS")
        section_label.setProperty("role", "section-label")
        sec_each_label = QLabel("sec each")
        sec_each_label.setProperty("role", "muted")
        section_layout.addWidget(section_label)
        section_layout.addStretch(1)
        section_layout.addWidget(sec_each_label)
        self.body.addWidget(section_row)

        self.time_edits: dict[str, QLineEdit] = {}
        for process_id, name in PROCESS_DEFS:
            row, edit = _field_row(name)
            self.time_edits[process_id] = edit
            self.body.addWidget(row)

        self.body.addWidget(_divider())

        margin_row, self.margin_edit = _field_row("Desired margin — %")
        self.margin_edit.setProperty("emphasized", "true")
        self.body.addWidget(margin_row)

        footnote = QLabel(
            "Times apply to every harness. Setup and freight are set per harness. Margin is on sell price."
        )
        footnote.setProperty("role", "muted")
        footnote.setWordWrap(True)
        self.body.addWidget(footnote)

        for edit in [self.rate_edit, self.efficiency_edit, self.scrap_edit, self.margin_edit, *self.time_edits.values()]:
            edit.editingFinished.connect(self.changed.emit)

    def load(self, labor: LaborAssumptions) -> None:
        self.rate_edit.setText(f"{labor.labor_rate:.2f}")
        self.efficiency_edit.setText(f"{labor.efficiency:.2f}")
        self.scrap_edit.setText(f"{labor.scrap_pct:g}")
        self.margin_edit.setText(f"{labor.margin_pct:g}")
        for process_id, edit in self.time_edits.items():
            edit.setText(f"{labor.times.get(process_id, 0):g}")

    def apply_to(self, labor: LaborAssumptions) -> None:
        labor.labor_rate = _num(self.rate_edit.text())
        labor.efficiency = _num(self.efficiency_edit.text())
        labor.scrap_pct = _num(self.scrap_edit.text())
        labor.margin_pct = _num(self.margin_edit.text())
        for process_id, edit in self.time_edits.items():
            labor.times[process_id] = _num(edit.text())


def _num(text: str) -> float:
    try:
        return float(text)
    except ValueError:
        return 0.0
