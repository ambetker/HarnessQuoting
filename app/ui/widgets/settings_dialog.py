from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QLineEdit, QVBoxLayout

from app import settings


class SettingsDialog(QDialog):
    """App-level preferences — currently just initials, used in generated
    quote numbers (Q-{initials}{date}{sequence})."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)

        label = QLabel("Your initials")
        label.setProperty("role", "field-label")
        note = QLabel("Used in quote numbers, e.g. Q-AB26081601")
        note.setProperty("role", "muted")
        note.setWordWrap(True)

        self.initials_edit = QLineEdit(settings.load_settings().initials)
        self.initials_edit.setMaxLength(4)

        layout.addWidget(label)
        layout.addWidget(self.initials_edit)
        layout.addWidget(note)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def save(self) -> None:
        initials = self.initials_edit.text().strip().upper()
        settings.save_settings(settings.AppSettings(initials=initials))
