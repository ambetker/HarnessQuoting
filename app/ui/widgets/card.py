from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class Card(QFrame):
    """Reusable card shell: optional header (title/subtitle + right-side
    buttons), then a body layout callers add content to."""

    def __init__(self, title: str | None = None, subtitle: str | None = None, parent=None):
        super().__init__(parent)
        self.setProperty("card", "true")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.header_extra = QHBoxLayout()
        self.header_extra.setSpacing(8)

        if title:
            header = QWidget()
            header.setProperty("card", "false")
            header_layout = QHBoxLayout(header)
            header_layout.setContentsMargins(20, 16, 20, 14)
            header_layout.setSpacing(8)
            header.setStyleSheet(f"border-bottom: 1px solid #f1f1ee;")

            title_box = QVBoxLayout()
            title_box.setSpacing(2)
            title_label = QLabel(title)
            title_label.setProperty("role", "card-title")
            title_box.addWidget(title_label)
            if subtitle:
                sub_label = QLabel(subtitle)
                sub_label.setProperty("role", "card-subtitle")
                title_box.addWidget(sub_label)
            header_layout.addLayout(title_box)
            header_layout.addStretch(1)
            header_layout.addLayout(self.header_extra)
            outer.addWidget(header)

        self.body = QVBoxLayout()
        self.body.setContentsMargins(18, 18, 18, 18)
        self.body.setSpacing(14)
        outer.addLayout(self.body)

    def add_header_button(self, button):
        self.header_extra.addWidget(button)
