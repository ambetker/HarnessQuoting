from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app import company_profiles
from app.company_profiles import CompanyProfile


class _CompanyRow(QFrame):
    def __init__(self, profile: CompanyProfile, parent=None):
        super().__init__(parent)
        self.setProperty("card", "true")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        top_row = QHBoxLayout()
        self.default_radio = QRadioButton("Default")
        top_row.addWidget(self.default_radio)
        top_row.addStretch(1)
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.setProperty("variant", "destructive")
        top_row.addWidget(self.remove_btn)
        layout.addLayout(top_row)

        self.name_edit = QLineEdit(profile.name)
        self.name_edit.setPlaceholderText("Company name")
        layout.addWidget(self.name_edit)

        # QTextEdit(str) treats its argument as HTML, silently collapsing
        # "\n" into spaces — must use the empty constructor + setPlainText.
        self.address_edit = QTextEdit()
        self.address_edit.setPlainText("\n".join(profile.address_lines))
        self.address_edit.setPlaceholderText("Address (one line per row)")
        self.address_edit.setFixedHeight(60)
        layout.addWidget(self.address_edit)

        contact_row = QHBoxLayout()
        self.phone_edit = QLineEdit(profile.phone)
        self.phone_edit.setPlaceholderText("Phone")
        self.email_edit = QLineEdit(profile.email)
        self.email_edit.setPlaceholderText("Email")
        contact_row.addWidget(self.phone_edit)
        contact_row.addWidget(self.email_edit)
        layout.addLayout(contact_row)

    def to_profile(self) -> CompanyProfile:
        return CompanyProfile(
            name=self.name_edit.text().strip(),
            address_lines=[line for line in self.address_edit.toPlainText().splitlines() if line.strip()],
            phone=self.phone_edit.text().strip(),
            email=self.email_edit.text().strip(),
        )


class ManageCompaniesDialog(QDialog):
    """Add/edit/remove the small pool of company letterhead profiles and
    pick which is the default for new quotes. Only a handful expected, so
    a flat stack of editable cards rather than a list+detail split view."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage companies")
        self.setMinimumWidth(420)

        self.layout_ = QVBoxLayout(self)
        self.rows_container = QVBoxLayout()
        self.rows_container.setSpacing(10)
        self.layout_.addLayout(self.rows_container)

        # QButtonGroup (not a manual toggled-listener) guarantees the radios
        # are mutually exclusive regardless of the order setChecked() and
        # signal connections happen in — a manual approach here previously
        # let two rows end up "checked" if setChecked ran before connect().
        self.default_group = QButtonGroup(self)
        self.rows: list[_CompanyRow] = []

        companies, default_index = company_profiles.load_companies()
        for i, profile in enumerate(companies):
            self._add_row(profile, is_default=(i == default_index))

        add_btn = QPushButton("+ Add company")
        add_btn.setProperty("variant", "dashed")
        add_btn.clicked.connect(lambda: self._add_row(CompanyProfile(name="New company"), is_default=False))
        self.layout_.addWidget(add_btn)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.layout_.addWidget(buttons)

    def _add_row(self, profile: CompanyProfile, is_default: bool) -> None:
        row = _CompanyRow(profile)
        self.default_group.addButton(row.default_radio)
        row.default_radio.setChecked(is_default)
        row.remove_btn.clicked.connect(lambda: self._remove_row(row))
        self.rows_container.addWidget(row)
        self.rows.append(row)

    def _remove_row(self, row: "_CompanyRow") -> None:
        if len(self.rows) <= 1:
            return  # keep at least one company profile
        was_default = row.default_radio.isChecked()
        self.default_group.removeButton(row.default_radio)
        self.rows.remove(row)
        row.setParent(None)
        row.deleteLater()
        if was_default and self.rows:
            self.rows[0].default_radio.setChecked(True)

    def save(self) -> None:
        profiles = [row.to_profile() for row in self.rows]
        default_index = next((i for i, row in enumerate(self.rows) if row.default_radio.isChecked()), 0)
        company_profiles.save_companies(profiles, default_index)
