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

from app.harness_bulk_parser import ParsedHarnessGroup, parse_harness_bulk_text

PROMPT_TEMPLATE = (
    "From the attached engineering drawings, extract every harness and its "
    "material bill of materials. Output only a plain list, one component "
    "per line, in this exact format: HARNESS_NAME, HARNESS_PART_NUMBER, "
    "HARNESS_QTY, COMPONENT_PART_NUMBER, COMPONENT_QTY — repeat the "
    "harness name/part number/qty on every row for that harness's "
    "components. No header, no markdown table, no bullet points. Use "
    "manufacturer part numbers where visible."
)


class PasteHarnessesDialog(QDialog):
    """Paste HARNESS_NAME, HARNESS_PN, HARNESS_QTY, COMPONENT_PN,
    COMPONENT_QTY text — typically an AI-generated multi-harness BOM off a
    set of drawings — and preview the parsed harness groups before adding
    them to the quote (appended, not replacing existing harnesses)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Paste harnesses")
        self.setMinimumSize(680, 480)
        self.parsed_groups: list[ParsedHarnessGroup] = []

        layout = QVBoxLayout(self)

        prompt_row = QHBoxLayout()
        prompt_label = QLabel("Ask an AI chat for every harness's BOM off a set of drawings, then paste the result below.")
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
        left_label = QLabel("Paste text — one component per line: HARNESS_NAME, HARNESS_PN, HARNESS_QTY, COMPONENT_PN, COMPONENT_QTY")
        left_label.setProperty("role", "field-label")
        left_label.setWordWrap(True)
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText(
            "Main engine harness, WH-4412-A, 25, DT04-12PA-L012, 1\n"
            "Main engine harness, WH-4412-A, 25, DT06-6S-E004, 2\n"
            "Sensor jumper, WH-4413-A, 60, DT06-4S-CE06, 1"
        )
        self.text_edit.textChanged.connect(self._on_text_changed)
        left.addWidget(left_label)
        left.addWidget(self.text_edit)
        body.addLayout(left, 1)

        right = QVBoxLayout()
        self.summary_label = QLabel("Preview")
        self.summary_label.setProperty("role", "field-label")
        self.preview_table = QTableWidget(0, 3)
        self.preview_table.setHorizontalHeaderLabels(["Harness", "Component", "Qty"])
        self.preview_table.verticalHeader().setVisible(False)
        self.preview_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.preview_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.preview_table.setColumnWidth(0, 170)
        self.preview_table.setColumnWidth(1, 150)
        right.addWidget(self.summary_label)
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
        n = len(self.parsed_groups)
        self.ok_button.setText(f"Add {n} harness{'es' if n != 1 else ''}" if n else "Add harnesses")

    def _on_text_changed(self) -> None:
        result = parse_harness_bulk_text(self.text_edit.toPlainText())
        self.parsed_groups = result.groups

        rows = [(g.name, line.part_number, line.qty) for g in result.groups for line in g.lines]
        self.preview_table.setRowCount(len(rows))
        for i, (harness_name, part_number, qty) in enumerate(rows):
            self.preview_table.setItem(i, 0, QTableWidgetItem(harness_name))
            self.preview_table.setItem(i, 1, QTableWidgetItem(part_number))
            qty_item = QTableWidgetItem(f"{qty:g}")
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.preview_table.setItem(i, 2, qty_item)

        component_count = sum(len(g.lines) for g in result.groups)
        self.summary_label.setText(
            f"Preview — {len(result.groups)} harness{'es' if len(result.groups) != 1 else ''}, "
            f"{component_count} component line{'s' if component_count != 1 else ''}"
        )

        if result.skipped:
            preview = "; ".join(result.skipped[:3])
            more = f" (+{len(result.skipped) - 3} more)" if len(result.skipped) > 3 else ""
            self.status_label.setText(f"{len(result.skipped)} line(s) couldn't be parsed and will be skipped: {preview}{more}")
        else:
            self.status_label.setText("")

        self.ok_button.setEnabled(bool(self.parsed_groups))
        self._set_ok_text()
