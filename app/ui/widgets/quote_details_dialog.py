from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from app import company_profiles
from app.company_profiles import CompanyProfile
from app.models import Quote
from app.ui.widgets.manage_companies_dialog import ManageCompaniesDialog


class QuoteDetailsDialog(QDialog):
    """"From" (which saved company letterhead) and "Bill to" (Attn/address)
    — the two blocks on the printed quote that aren't part of the everyday
    working view, so they're kept in one dialog reachable from the header
    rather than cluttering it directly."""

    def __init__(self, quote: Quote, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Quote details")
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)

        from_label = QLabel("From")
        from_label.setStyleSheet("font-weight: 600;")
        layout.addWidget(from_label)

        from_row = QHBoxLayout()
        self.company_combo = QComboBox()
        from_row.addWidget(self.company_combo, 1)
        manage_btn = QPushButton("Manage companies…")
        manage_btn.setProperty("variant", "secondary")
        manage_btn.clicked.connect(self._open_manage_companies)
        from_row.addWidget(manage_btn)
        layout.addLayout(from_row)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: #eaeae7;")
        layout.addWidget(divider)

        bill_to_label = QLabel("Bill to")
        bill_to_label.setStyleSheet("font-weight: 600;")
        layout.addWidget(bill_to_label)

        attn_label = QLabel("Attn")
        attn_label.setProperty("role", "field-label")
        self.attn_edit = QLineEdit(quote.customer_attn)
        layout.addWidget(attn_label)
        layout.addWidget(self.attn_edit)

        address_label = QLabel("Address")
        address_label.setProperty("role", "field-label")
        self.address_edit = QTextEdit()
        self.address_edit.setPlainText(quote.customer_address)
        self.address_edit.setFixedHeight(70)
        layout.addWidget(address_label)
        layout.addWidget(self.address_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._company_options: list[CompanyProfile] = []
        self._populate_companies(quote)

    def _populate_companies(self, quote: Quote | None = None) -> None:
        if quote is not None:
            target_name = quote.company_name
            fallback = CompanyProfile(
                name=quote.company_name,
                address_lines=list(quote.company_address_lines),
                phone=quote.company_phone,
                email=quote.company_email,
            )
        else:
            # re-populating after Manage Companies closed — preserve whatever
            # was selected before, from the options list we already had
            current_index = self.company_combo.currentIndex()
            fallback = self._company_options[current_index] if 0 <= current_index < len(self._company_options) else None
            target_name = fallback.name if fallback else ""

        companies, _default_index = company_profiles.load_companies()
        options = list(companies)
        if target_name and fallback and not any(c.name == target_name for c in companies):
            # the selected company isn't in the saved list (renamed/removed
            # via Manage Companies) — keep it selectable so nothing silently
            # changes just from reopening this dialog
            options.insert(0, fallback)

        self._company_options = options
        self.company_combo.clear()
        self.company_combo.addItems([c.name for c in options])

        selected_index = next((i for i, c in enumerate(options) if c.name == target_name), 0)
        self.company_combo.setCurrentIndex(selected_index)

    def _open_manage_companies(self) -> None:
        dialog = ManageCompaniesDialog(self)
        if dialog.exec() == ManageCompaniesDialog.DialogCode.Accepted:
            dialog.save()
            self._populate_companies()

    def apply_to(self, quote: Quote) -> None:
        selected = self._company_options[self.company_combo.currentIndex()]
        quote.company_name = selected.name
        quote.company_address_lines = list(selected.address_lines)
        quote.company_phone = selected.phone
        quote.company_email = selected.email
        quote.customer_attn = self.attn_edit.text()
        quote.customer_address = self.address_edit.toPlainText()
