from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
)

from app.bom_parser import ParsedBomLine, parse_bom_text

PROMPT_TEMPLATE = (
    "From the attached engineering drawing, extract the material bill of "
    "materials. Output only a plain list, one part per line, in this exact "
    "format: PART_NUMBER, QUANTITY — no header, no markdown table, no "
    "bullet points. Use manufacturer part numbers where visible."
)


class PasteBomDialog(QDialog):
    """Paste PART_NUMBER, QTY text (typically from an AI-generated BOM off
    a drawing — see PROMPT_TEMPLATE) and preview the parsed rows before
    replacing the active harness's parts list with them."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Paste BOM")
        self.setMinimumSize(620, 440)
        self.parsed_lines: list[ParsedBomLine] = []

        layout = QVBoxLayout(self)

        prompt_row = QHBoxLayout()
        prompt_label = QLabel("Ask an AI chat for the BOM off a drawing, then paste the result below.")
        prompt_label.setProperty("role", "muted")
        prompt_label.setWordWrap(True)
        copy_prompt_btn = QPushButton("Copy prompt for AI")
        copy_prompt_btn.setProperty("variant", "secondary")
        copy_prompt_btn.clicked.connect(self._copy_prompt)
        prompt_row.addWidget(prompt_label, 1)
        prompt_row.addWidget(copy_prompt_btn)
        layout.addLayout(prompt_row)

        body = QHBoxLayout()
        body.setSpacing(16)

        left = QVBoxLayout()
        left_label = QLabel("Paste text — one part per line: PART_NUMBER, QTY")
        left_label.setProperty("role", "field-label")
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("DT04-12PA-L012, 1\nDT06-6S-E004, 2\n0462-201-16141, 18")
        self.text_edit.textChanged.connect(self._on_text_changed)
        left.addWidget(left_label)
        left.addWidget(self.text_edit)
        body.addLayout(left, 1)

        right = QVBoxLayout()
        right_label = QLabel("Preview")
        right_label.setProperty("role", "field-label")
        self.preview_table = QTableWidget(0, 2)
        self.preview_table.setHorizontalHeaderLabels(["Part number", "Qty"])
        self.preview_table.verticalHeader().setVisible(False)
        self.preview_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.preview_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.preview_table.horizontalHeader().setStretchLastSection(False)
        self.preview_table.setColumnWidth(0, 190)
        self.preview_table.setColumnWidth(1, 60)
        right.addWidget(right_label)
        right.addWidget(self.preview_table)
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #a8443b; font-size: 12px;")
        right.addWidget(self.status_label)
        body.addLayout(right, 1)

        layout.addLayout(body)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        self.ok_button.setEnabled(False)
        self._set_ok_text()
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _copy_prompt(self) -> None:
        QApplication.clipboard().setText(PROMPT_TEMPLATE)

    def _set_ok_text(self) -> None:
        n = len(self.parsed_lines)
        self.ok_button.setText(f"Replace parts list ({n} line{'s' if n != 1 else ''})" if n else "Replace parts list")

    def _on_text_changed(self) -> None:
        result = parse_bom_text(self.text_edit.toPlainText())
        self.parsed_lines = result.lines

        self.preview_table.setRowCount(len(result.lines))
        for i, line in enumerate(result.lines):
            self.preview_table.setItem(i, 0, QTableWidgetItem(line.part_number))
            qty_item = QTableWidgetItem(f"{line.qty:g}")
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.preview_table.setItem(i, 1, qty_item)

        if result.skipped:
            preview = "; ".join(result.skipped[:3])
            more = f" (+{len(result.skipped) - 3} more)" if len(result.skipped) > 3 else ""
            self.status_label.setText(f"{len(result.skipped)} line(s) couldn't be parsed and will be skipped: {preview}{more}")
        else:
            self.status_label.setText("")

        self.ok_button.setEnabled(bool(self.parsed_lines))
        self._set_ok_text()
