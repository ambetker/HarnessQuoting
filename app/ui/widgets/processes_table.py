from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from app.models import Harness, LaborAssumptions
from app.ui.widgets.card import Card
from app.ui.widgets.table_utils import fit_table_height

COLUMNS = ["", "Process", "Count", "Sec each", "Minutes", "Cost"]


class ProcessesTableWidget(Card):
    changed = Signal()
    suggest_counts_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(
            "Processes used",
            "Select what this harness needs and enter counts; times come from labor assumptions",
            parent,
        )
        suggest_btn = QPushButton("Suggest counts from parts")
        suggest_btn.setProperty("variant", "secondary")
        suggest_btn.clicked.connect(self.suggest_counts_requested.emit)
        self.add_header_button(suggest_btn)

        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for col, width in {0: 34, 2: 88, 3: 104, 4: 88, 5: 96}.items():
            self.table.setColumnWidth(col, width)
        self.body.addWidget(self.table)

        footer_row = QWidget()
        footer_layout = QHBoxLayout(footer_row)
        footer_layout.setContentsMargins(0, 4, 0, 0)
        footer_layout.addStretch(1)
        label = QLabel("Labor per harness")
        label.setProperty("role", "muted")
        self.total_label = QLabel("0.0 min · $0.00")
        self.total_label.setStyleSheet("font-size: 14px; font-weight: 600;")
        footer_layout.addWidget(label)
        footer_layout.addWidget(self.total_label)
        self.body.addWidget(footer_row)

    def render(self, harness: Harness, labor: LaborAssumptions, eff: float) -> None:
        # See parts_table.render() — collapsing to 0 first avoids stale
        # cell widgets bleeding through when switching harnesses.
        self.table.setRowCount(0)
        self.table.setRowCount(len(harness.processes))
        total_minutes = 0.0
        total_cost = 0.0

        for i, process in enumerate(harness.processes):
            sec_each = labor.times.get(process.id, 0)
            minutes = (process.count * sec_each / 60 / eff) if process.on else 0.0
            cost = minutes / 60 * labor.labor_rate
            total_minutes += minutes
            total_cost += cost

            checkbox = QCheckBox()
            checkbox.setChecked(process.on)
            checkbox.stateChanged.connect(lambda _state, idx=i: self._on_toggle(idx))
            checkbox_holder = QWidget()
            layout = QHBoxLayout(checkbox_holder)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(checkbox)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setCellWidget(i, 0, checkbox_holder)

            text_color = "#1a1917" if process.on else "#b3b0aa"
            name_item = QTableWidgetItem(process.name)
            name_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            name_item.setForeground(QColor(text_color))
            self.table.setItem(i, 1, name_item)

            count_edit = QLineEdit(f"{process.count:g}")
            count_edit.setEnabled(process.on)
            count_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
            count_edit.editingFinished.connect(lambda idx=i: self._on_count_changed(idx))
            self.table.setCellWidget(i, 2, count_edit)

            sec_color = "#8b887f" if process.on else "#c4c1bb"
            sec_item = QTableWidgetItem(f"{sec_each:g}")
            sec_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            sec_item.setForeground(QColor(sec_color))
            sec_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(i, 3, sec_item)

            min_item = QTableWidgetItem(f"{minutes:.1f}")
            min_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            min_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(i, 4, min_item)

            cost_item = QTableWidgetItem(_money(cost))
            cost_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            cost_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(i, 5, cost_item)

        fit_table_height(self.table)
        self.total_label.setText(f"{total_minutes:.1f} min · {_money(total_cost)}")

    def _on_toggle(self, index: int) -> None:
        self.changed.emit()

    def _on_count_changed(self, index: int) -> None:
        self.changed.emit()

    def read_back(self, harness: Harness) -> None:
        for i, process in enumerate(harness.processes):
            checkbox_holder = self.table.cellWidget(i, 0)
            if checkbox_holder:
                checkbox = checkbox_holder.findChild(QCheckBox)
                if checkbox:
                    process.on = checkbox.isChecked()

            count_widget = self.table.cellWidget(i, 2)
            if isinstance(count_widget, QLineEdit):
                try:
                    process.count = float(count_widget.text())
                except ValueError:
                    process.count = 0.0


def _money(value: float) -> str:
    sign = "−" if value < 0 else ""
    return f"{sign}${abs(value):,.2f}"
