from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.cost_model import line_category, line_unit_price, unit_for_category
from app.models import CATEGORIES, Harness
from app.ui.widgets.card import Card
from app.ui.widgets.table_utils import fit_table_height

COLUMNS = ["#", "Part number", "Source", "Description", "Category", "Qty", "Unit", "Unit price", "Extended", ""]


class PartsTableWidget(Card):
    changed = Signal()
    lookup_requested = Signal(int)  # line index
    lookup_bom_requested = Signal()
    paste_bom_requested = Signal()
    add_line_requested = Signal()
    remove_line_requested = Signal(int)

    def __init__(self, parent=None):
        super().__init__("Parts", "Manufacturer or DigiKey P/N + qty per harness", parent)

        paste_btn = QPushButton("Paste BOM")
        paste_btn.setProperty("variant", "secondary")
        paste_btn.clicked.connect(self.paste_bom_requested.emit)
        lookup_btn = QPushButton("Look up this BOM")
        lookup_btn.setProperty("variant", "secondary")
        lookup_btn.clicked.connect(self.lookup_bom_requested.emit)
        add_btn = QPushButton("Add part")
        add_btn.setProperty("variant", "secondary")
        add_btn.clicked.connect(self.add_line_requested.emit)
        self.add_header_button(paste_btn)
        self.add_header_button(lookup_btn)
        self.add_header_button(add_btn)

        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # Horizontal scroll stays available (unlike the other tables here) —
        # this table's columns can't all fit at once below ~1500px window
        # width, so hiding the scrollbar would strand the last few columns
        # with no way to reach them.
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setMinimumSectionSize(60)
        for col, width in {0: 30, 1: 150, 2: 50, 4: 100, 5: 50, 6: 32, 7: 90, 8: 80, 9: 28}.items():
            self.table.setColumnWidth(col, width)
        self.body.addWidget(self.table)

        footer_row = QWidget()
        footer_layout = QHBoxLayout(footer_row)
        footer_layout.setContentsMargins(0, 4, 0, 0)
        footer_layout.addStretch(1)
        label = QLabel("Material per harness")
        label.setProperty("role", "muted")
        self.material_total_label = QLabel("$0.00")
        self.material_total_label.setStyleSheet("font-size: 14px; font-weight: 600;")
        footer_layout.addWidget(label)
        footer_layout.addWidget(self.material_total_label)
        self.body.addWidget(footer_row)

        self.status_label = QLabel()
        self.status_label.setProperty("role", "muted")
        self.body.addWidget(self.status_label)

        self._pending: set[int] = set()

    def set_pending(self, pending_indices: set[int]) -> None:
        self._pending = pending_indices

    def render(self, harness: Harness) -> None:
        # Collapsing to 0 first guarantees every old cell widget (from a
        # previously rendered harness) is actually torn down before new
        # ones are created at the same row/col — setRowCount() alone left
        # stale widgets visually bleeding through on harness switches.
        self.table.setRowCount(0)
        self.table.setRowCount(len(harness.lines))
        material_total = 0.0

        for i, line in enumerate(harness.lines):
            material_total += line.qty * line_unit_price(line)

            n_item = QTableWidgetItem(str(i + 1))
            n_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            n_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.table.setItem(i, 0, n_item)

            part_edit = QLineEdit(line.part_number)
            part_edit.setPlaceholderText("mfr or DigiKey P/N")
            part_edit.setProperty("bare", "true")
            part_edit.editingFinished.connect(lambda idx=i: self.lookup_requested.emit(idx))
            self.table.setCellWidget(i, 1, part_edit)

            self.table.setCellWidget(i, 2, self._source_pill(line, i in self._pending))

            desc_label = QLabel(self._description_text(line, i in self._pending))
            desc_label.setStyleSheet(f"color: {self._description_color(line)};")
            self.table.setCellWidget(i, 3, desc_label)

            category_combo = QComboBox()
            category_combo.setProperty("bare", "true")
            category_combo.addItems(CATEGORIES)
            current_category = line_category(line)
            if current_category in CATEGORIES:
                category_combo.setCurrentText(current_category)
            category_combo.currentTextChanged.connect(lambda _text, idx=i: self._on_category_changed(idx))
            self.table.setCellWidget(i, 4, category_combo)

            qty_edit = QLineEdit(f"{line.qty:g}")
            qty_edit.setProperty("bare", "true")
            qty_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
            qty_edit.editingFinished.connect(lambda idx=i: self._on_qty_changed(idx))
            self.table.setCellWidget(i, 5, qty_edit)

            unit_item = QTableWidgetItem(unit_for_category(current_category))
            unit_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            unit_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            unit_item.setForeground(QColor("#a3a09a"))
            self.table.setItem(i, 6, unit_item)

            self.table.setCellWidget(i, 7, self._price_cell(line, i))

            ext_item = QTableWidgetItem(_money(line.qty * line_unit_price(line)))
            ext_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            ext_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.table.setItem(i, 8, ext_item)

            delete_btn = QPushButton("×")
            delete_btn.setFixedSize(24, 24)
            delete_btn.setStyleSheet("border: none; color: #c4c1bb; font-size: 14px;")
            delete_btn.clicked.connect(lambda _checked=False, idx=i: self.remove_line_requested.emit(idx))
            self.table.setCellWidget(i, 9, delete_btn)

        fit_table_height(self.table)
        self.material_total_label.setText(_money(material_total))

        priced = sum(1 for line in harness.lines if line.resolved)
        missing = sum(1 for line in harness.lines if line.lookup_attempted and not line.resolved)
        pending = len(self._pending)
        total = len(harness.lines)
        if pending:
            self.status_label.setText(f"{pending} of {total} parts resolving…")
        else:
            suffix = f" · {missing} need manual cost" if missing else ""
            self.status_label.setText(f"{priced} of {total} part numbers priced{suffix}")

    def _source_pill(self, line, is_pending: bool) -> QLabel:
        if line.resolved:
            if line.source == "DK":
                text, bg, fg = "DK", "#eef4f8", "#3a6b8c"
            else:
                text, bg, fg = "Mfr", "#f2f1ec", "#6f6c66"
        elif is_pending:
            text, bg, fg = "···", "#faf3f1", "#a8746a"
        else:
            text, bg, fg = "—", "#faf3f1", "#a8746a"
        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(
            f"background: {bg}; color: {fg}; border-radius: 5px; padding: 2px 7px; font-size: 11px; font-weight: 500;"
        )
        return label

    def _description_text(self, line, is_pending: bool) -> str:
        if line.resolved:
            return line.description or ""
        if is_pending:
            return "Looking up…"
        if line.lookup_attempted:
            return "Not found — enter cost manually"
        if not line.part_number.strip():
            return "Enter a part number"
        return ""

    def _description_color(self, line) -> str:
        return "#1a1917" if line.resolved else "#a09c94"

    def _link_button(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setFlat(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(
            "border: none; background: transparent; color: #a3a09a; "
            "font-size: 10px; text-decoration: underline; padding: 0;"
        )
        return btn

    def _price_cell(self, line, index: int) -> QWidget:
        box = QWidget()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(4, 3, 4, 3)
        layout.setSpacing(1)

        has_catalog_price = line.resolved and line.catalog_price is not None

        if has_catalog_price and not line.manual_override:
            price_label = QLabel(_money4(line.catalog_price))
            price_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            layout.addWidget(price_label)
            if line.price_tier_label:
                tier_label = QLabel(line.price_tier_label)
                tier_label.setAlignment(Qt.AlignmentFlag.AlignRight)
                tier_label.setStyleSheet("font-size: 11px; color: #a3a09a;")
                layout.addWidget(tier_label)

            override_btn = self._link_button("override")
            override_btn.clicked.connect(lambda _checked=False, l=line: self._on_override_toggled(l, True))
            layout.addWidget(override_btn, 0, Qt.AlignmentFlag.AlignRight)
            return box

        edit = QLineEdit(f"{line.manual_cost:g}" if line.manual_cost else "")
        edit.setPlaceholderText("cost")
        edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        edit.setStyleSheet(
            "border: 1px dashed #ddc9a8; background: #fffdf9; border-radius: 6px; padding: 5px 7px;"
        )
        edit.editingFinished.connect(lambda idx=index: self._on_manual_cost_changed(idx))
        layout.addWidget(edit)

        if has_catalog_price:
            # manual_override is True here — offer a way back to the catalog price.
            revert_btn = self._link_button(f"use {_money4(line.catalog_price)}")
            revert_btn.clicked.connect(lambda _checked=False, l=line: self._on_override_toggled(l, False))
            layout.addWidget(revert_btn, 0, Qt.AlignmentFlag.AlignRight)

        return box

    def _on_qty_changed(self, index: int) -> None:
        self.changed.emit()

    def _on_category_changed(self, index: int) -> None:
        self.changed.emit()

    def _on_manual_cost_changed(self, index: int) -> None:
        self.changed.emit()

    def _on_override_toggled(self, line, override: bool) -> None:
        line.manual_override = override
        if override and line.catalog_price is not None:
            line.manual_cost = line.catalog_price  # prefill so the estimator is correcting, not starting blank
        self.changed.emit()

    def read_line_edits(self, harness: Harness) -> None:
        """Pull whatever's currently in the row widgets back into the
        model before a recompute (call before .apply logic reads harness)."""
        for i, line in enumerate(harness.lines):
            part_widget = self.table.cellWidget(i, 1)
            if isinstance(part_widget, QLineEdit):
                line.part_number = part_widget.text()

            category_widget = self.table.cellWidget(i, 4)
            if isinstance(category_widget, QComboBox):
                line.category = category_widget.currentText()

            qty_widget = self.table.cellWidget(i, 5)
            if isinstance(qty_widget, QLineEdit):
                try:
                    line.qty = float(qty_widget.text())
                except ValueError:
                    line.qty = 0.0

            price_container = self.table.cellWidget(i, 7)
            price_edit = price_container.findChild(QLineEdit) if price_container else None
            if price_edit is not None:
                try:
                    line.manual_cost = float(price_edit.text())
                except ValueError:
                    line.manual_cost = 0.0


def _money(value: float) -> str:
    sign = "−" if value < 0 else ""
    return f"{sign}${abs(value):,.2f}"


def _money4(value: float) -> str:
    sign = "−" if value < 0 else ""
    decimals = 3 if abs(value) < 1 else 2
    return f"{sign}${abs(value):,.{decimals}f}"
