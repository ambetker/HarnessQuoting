from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app import config
from app.ui.style import COLORS
from app.ui.widgets.card import Card


class DigiKeyPanelWidget(Card):
    price_all_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        status_row = QWidget()
        status_layout = QHBoxLayout(status_row)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(8)

        self.dot = QLabel()
        self.dot.setFixedSize(8, 8)
        status_layout.addWidget(self.dot)

        title = QLabel("DigiKey pricing")
        title.setStyleSheet("font-size: 13.5px; font-weight: 600;")
        status_layout.addWidget(title)
        status_layout.addStretch(1)
        self.body.addWidget(status_row)

        self.status_text = QLabel()
        self.status_text.setProperty("role", "muted")
        self.status_text.setWordWrap(True)
        self.body.addWidget(self.status_text)

        stats_frame = QFrame()
        stats_frame.setStyleSheet("border-top: 1px solid #f1f1ee; border-bottom: 1px solid #f1f1ee;")
        stats_layout = QVBoxLayout(stats_frame)
        stats_layout.setContentsMargins(0, 12, 0, 12)
        stats_layout.setSpacing(6)

        self.unique_label = self._stat_row(stats_layout, "Unique part numbers")
        self.cached_label = self._stat_row(stats_layout, "Priced from cache")
        self.last_lookup_label = self._stat_row(stats_layout, "Last lookup")
        self.body.addWidget(stats_frame)

        self.price_all_btn = QPushButton("Price all harnesses")
        self.price_all_btn.setProperty("variant", "primary")
        self.price_all_btn.clicked.connect(self.price_all_requested.emit)
        self.body.addWidget(self.price_all_btn)

        connected = bool(config.DIGIKEY_CLIENT_ID and config.DIGIKEY_CLIENT_SECRET)
        self.set_connected(connected)

    def _stat_row(self, layout: QVBoxLayout, label_text: str) -> QLabel:
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel(label_text)
        label.setProperty("role", "muted")
        value = QLabel("—")
        row_layout.addWidget(label)
        row_layout.addStretch(1)
        row_layout.addWidget(value)
        layout.addWidget(row)
        return value

    def set_connected(self, connected: bool) -> None:
        color = COLORS["status_connected"] if connected else COLORS["status_disconnected"]
        self.dot.setStyleSheet(f"background: {color}; border-radius: 4px;")
        self.status_text.setText(
            "Connected. Each unique part number resolves once and is reused across every harness on the quote."
            if connected
            else "DIGIKEY_CLIENT_ID / DIGIKEY_CLIENT_SECRET not set — add them to .env to enable live pricing."
        )
        self.price_all_btn.setEnabled(connected)

    def set_stats(self, unique_count: int, cached_count: int, last_lookup: str) -> None:
        self.unique_label.setText(str(unique_count))
        self.cached_label.setText(str(cached_count))
        self.last_lookup_label.setText(last_lookup)

    def set_busy(self, busy: bool) -> None:
        self.price_all_btn.setEnabled(not busy)
        self.price_all_btn.setText("Pricing…" if busy else "Price all harnesses")
