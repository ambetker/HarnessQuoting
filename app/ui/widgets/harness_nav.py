from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QPushButton, QWidget


class HarnessNavWidget(QWidget):
    """Harness picker (dropdown + prev/next arrows) plus fixed-position
    Summary/Paste harnesses/Add harness buttons. Replaces the old pill-per-
    harness tab row, which became unusable well before ~10+ harnesses and
    had "Add harness" shift position as the list grew."""

    harness_selected = Signal(int)
    summary_selected = Signal()
    add_harness_requested = Signal()
    paste_harnesses_requested = Signal()

    FLAG_COLOR = "#a8443b"

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.prev_btn = QPushButton("◀")
        self.prev_btn.setProperty("variant", "secondary")
        self.prev_btn.setFixedWidth(34)
        self.prev_btn.clicked.connect(self._on_prev)
        layout.addWidget(self.prev_btn)

        self.harness_combo = QComboBox()
        self.harness_combo.setMinimumWidth(240)
        self.harness_combo.currentIndexChanged.connect(self._on_combo_changed)
        layout.addWidget(self.harness_combo)

        self.next_btn = QPushButton("▶")
        self.next_btn.setProperty("variant", "secondary")
        self.next_btn.setFixedWidth(34)
        self.next_btn.clicked.connect(self._on_next)
        layout.addWidget(self.next_btn)

        self.summary_btn = QPushButton("Summary")
        self.summary_btn.clicked.connect(self.summary_selected.emit)
        layout.addWidget(self.summary_btn)

        layout.addStretch(1)

        paste_btn = QPushButton("Paste harnesses")
        paste_btn.setProperty("variant", "secondary")
        paste_btn.clicked.connect(self.paste_harnesses_requested.emit)
        layout.addWidget(paste_btn)

        add_btn = QPushButton("+ Add harness")
        add_btn.setProperty("variant", "dashed")
        add_btn.clicked.connect(self.add_harness_requested.emit)
        layout.addWidget(add_btn)

        self._suppress_combo_signal = False

    def rebuild(self, harness_entries: list[tuple[str, str, bool]], summary_sub: str, active) -> None:
        """harness_entries: list of (name, sub_label e.g. '×25', flagged)
        per harness, in order. active is an int index, or 'sum'."""
        self._suppress_combo_signal = True
        model = QStandardItemModel(self.harness_combo)
        for name, sub, flagged in harness_entries:
            prefix = "⚠ " if flagged else ""
            item = QStandardItem(f"{prefix}{name}   {sub}")
            if flagged:
                item.setForeground(QColor(self.FLAG_COLOR))
            model.appendRow(item)
        self.harness_combo.setModel(model)

        n = len(harness_entries)
        if isinstance(active, int) and n:
            self.harness_combo.setCurrentIndex(max(0, min(active, n - 1)))
        self._suppress_combo_signal = False

        is_summary = active == "sum"
        self.summary_btn.setProperty("variant", "pill-active" if is_summary else "pill")
        self.summary_btn.setText(f"Summary   {summary_sub}")
        self.summary_btn.style().unpolish(self.summary_btn)
        self.summary_btn.style().polish(self.summary_btn)

        self.prev_btn.setEnabled(isinstance(active, int) and active > 0)
        self.next_btn.setEnabled(isinstance(active, int) and active < n - 1)

    def _on_combo_changed(self, index: int) -> None:
        if self._suppress_combo_signal or index < 0:
            return
        self.harness_selected.emit(index)

    def _on_prev(self) -> None:
        idx = self.harness_combo.currentIndex()
        if idx > 0:
            self.harness_combo.setCurrentIndex(idx - 1)

    def _on_next(self) -> None:
        idx = self.harness_combo.currentIndex()
        if idx < self.harness_combo.count() - 1:
            self.harness_combo.setCurrentIndex(idx + 1)
