from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class ClickableFrame(QFrame):
    """QPushButton doesn't size itself to fit an arbitrary child layout
    (its sizeHint is based on text/icon metrics, not child widgets), which
    caused the pill's two-line label to overflow its bounds. QFrame sizes
    to its layout correctly, so we add click behavior manually instead."""

    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class HarnessTabsWidget(QWidget):
    harness_selected = Signal(int)
    summary_selected = Signal()
    add_harness_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout_ = QHBoxLayout(self)
        self.layout_.setContentsMargins(0, 0, 0, 0)
        self.layout_.setSpacing(8)

    def _pill(self, label: str, sub: str, active: bool) -> ClickableFrame:
        frame = ClickableFrame()
        frame.setProperty("card", "false")
        border = "#b45309" if active else "#e4e3df"
        bg = "#ffffff" if active else "transparent"
        frame.setStyleSheet(
            f"QFrame {{ background: {bg}; border: 1px solid {border}; border-radius: 9px; }}"
        )

        inner = QVBoxLayout(frame)
        inner.setContentsMargins(14, 8, 14, 8)
        inner.setSpacing(1)
        title = QLabel(label)
        title.setStyleSheet("background: transparent; font-size: 13px; border: none;")
        sub_label = QLabel(sub)
        sub_color = "#b45309" if active else "#a3a09a"
        sub_label.setStyleSheet(f"background: transparent; font-size: 12px; color: {sub_color}; border: none;")
        inner.addWidget(title)
        inner.addWidget(sub_label)
        return frame

    def rebuild(self, harness_labels: list[tuple[str, str]], summary_sub: str, active) -> None:
        """harness_labels: list of (name, '×{qty}') per harness. active is an
        int index, or 'sum'."""
        while self.layout_.count():
            item = self.layout_.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i, (name, sub) in enumerate(harness_labels):
            is_active = active == i
            pill = self._pill(name, sub, is_active)
            pill.clicked.connect(lambda idx=i: self.harness_selected.emit(idx))
            self.layout_.addWidget(pill)

        summary_pill = self._pill("Summary", summary_sub, active == "sum")
        summary_pill.clicked.connect(lambda: self.summary_selected.emit())
        self.layout_.addWidget(summary_pill)

        add_btn = QPushButton("+ Add harness")
        add_btn.setProperty("variant", "dashed")
        add_btn.clicked.connect(self.add_harness_requested.emit)
        self.layout_.addWidget(add_btn)

        self.layout_.addStretch(1)
