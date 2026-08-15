from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QTextEdit,
    QVBoxLayout,
)

from app.models import Quote


class BillToDialog(QDialog):
    """Attn / address block shown on the printed quote's bill-to section.
    Kept out of the main header (which only has room for the customer name)
    to avoid cluttering the everyday working view."""

    def __init__(self, quote: Quote, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bill-to details")
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)

        attn_label = QLabel("Attn")
        self.attn_edit = QLineEdit(quote.customer_attn)
        layout.addWidget(attn_label)
        layout.addWidget(self.attn_edit)

        address_label = QLabel("Address")
        self.address_edit = QTextEdit()
        self.address_edit.setPlainText(quote.customer_address)
        self.address_edit.setFixedHeight(80)
        layout.addWidget(address_label)
        layout.addWidget(self.address_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def apply_to(self, quote: Quote) -> None:
        quote.customer_attn = self.attn_edit.text()
        quote.customer_address = self.address_edit.toPlainText()
