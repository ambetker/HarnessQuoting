import copy
import json
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QMarginsF, QSizeF, QThreadPool, QTimer, Qt
from PySide6.QtGui import QKeySequence, QPageLayout, QTextDocument
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app import cache, company_profiles, persistence, print_document, quote_numbering, seed_data, settings
from app.cost_model import calc_harness, harness_flag_status, line_category, unit_for_category
from app.digikey_client import select_price_break
from app.models import Harness, PartLine, Quote, default_processes
from app.ui.widgets.cost_price_rail import CostPriceRailWidget
from app.ui.widgets.digikey_panel import DigiKeyPanelWidget
from app.ui.widgets.harness_header import HarnessHeaderWidget
from app.ui.widgets.harness_nav import HarnessNavWidget
from app.ui.widgets.labor_assumptions import LaborAssumptionsWidget
from app.ui.widgets.money_breakdown import MoneyBreakdownWidget
from app.ui.widgets.parts_table import PartsTableWidget
from app.ui.widgets.paste_bom_dialog import PasteBomDialog
from app.ui.widgets.paste_harnesses_dialog import PasteHarnessesDialog
from app.ui.widgets.processes_table import ProcessesTableWidget
from app.ui.widgets.quantity_breaks import QuantityBreaksWidget
from app.ui.widgets.quote_details_dialog import QuoteDetailsDialog
from app.ui.widgets.quote_summary import QuoteSummaryWidget
from app.ui.widgets.quote_total import QuoteTotalWidget
from app.ui.widgets.settings_dialog import SettingsDialog
from app.ui.worker import Worker

LEFT_WIDTH = 300
RIGHT_WIDTH = 350


def _scrollable(widget: QWidget, fixed_width: int | None = None) -> QScrollArea:
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setFrameShape(QScrollArea.Shape.NoFrame)
    area.setWidget(widget)
    if fixed_width:
        area.setFixedWidth(fixed_width)
    return area


def _link_button(text: str) -> QPushButton:
    btn = QPushButton(text)
    btn.setFlat(True)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setStyleSheet(
        "border: none; background: transparent; color: #a3a09a; "
        "font-size: 11px; text-decoration: underline; padding: 0; text-align: left;"
    )
    return btn


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Harness quote")
        self.resize(1440, 900)

        self.quote = seed_data.make_default_quote()
        self._assign_new_quote_identity(self.quote)
        self.active: int | str = 0
        self.pending: dict[int, set[int]] = {}
        self.last_lookup_time: datetime | None = None
        self.thread_pool = QThreadPool.globalInstance()
        self._active_workers: list[Worker] = []  # keep alive; QRunnable has no Python owner otherwise
        self.current_file_path: Path | None = None

        self._build_menu_bar()
        self._build_ui()
        self._update_window_title()
        self.refresh_ui()

        QTimer.singleShot(0, self.start_price_all)

    # ---------------------------------------------------------------- UI

    def _build_menu_bar(self):
        file_menu = self.menuBar().addMenu("&File")

        new_action = file_menu.addAction("New Quote")
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self.new_quote)

        open_action = file_menu.addAction("Open…")
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_quote)

        file_menu.addSeparator()

        save_action = file_menu.addAction("Save")
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_quote)

        save_as_action = file_menu.addAction("Save As…")
        save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_as_action.triggered.connect(self.save_quote_as)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(36, 28, 36, 28)
        body_layout.setSpacing(24)

        body_layout.addWidget(_scrollable(self._build_left_column(), LEFT_WIDTH))
        body_layout.addWidget(_scrollable(self._build_middle_column()), 1)
        body_layout.addWidget(_scrollable(self._build_right_column(), RIGHT_WIDTH))

        root.addWidget(body, 1)

    def _build_header(self) -> QWidget:
        header = QFrame()
        header.setStyleSheet("background: #ffffff; border-bottom: 1px solid #eaeae7;")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(36, 24, 36, 22)

        title_box = QVBoxLayout()
        title_box.setSpacing(3)
        self.title_label = QLabel("Harness quote")
        self.title_label.setProperty("role", "page-title")
        self.subtitle_label = QLabel()
        self.subtitle_label.setProperty("role", "muted")
        title_box.addWidget(self.title_label)
        title_box.addWidget(self.subtitle_label)

        settings_btn = _link_button("Settings…")
        settings_btn.clicked.connect(self.open_settings_dialog)
        title_box.addWidget(settings_btn)

        layout.addLayout(title_box)
        layout.addStretch(1)

        customer_box = QVBoxLayout()
        customer_box.setSpacing(7)
        customer_label = QLabel("Customer")
        customer_label.setProperty("role", "field-label")
        self.customer_edit = QLineEdit()
        self.customer_edit.setFixedWidth(240)
        self.customer_edit.editingFinished.connect(self._on_customer_changed)
        customer_box.addWidget(customer_label)
        customer_box.addWidget(self.customer_edit)

        quote_details_btn = _link_button("Quote details…")
        quote_details_btn.clicked.connect(self.open_quote_details_dialog)
        customer_box.addWidget(quote_details_btn)
        layout.addLayout(customer_box)

        total_box = QVBoxLayout()
        total_box.setSpacing(3)
        total_label = QLabel("Quote total")
        total_label.setProperty("role", "field-label")
        total_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.header_total_value = QLabel("$0.00")
        self.header_total_value.setProperty("role", "money-lg")
        self.header_total_value.setAlignment(Qt.AlignmentFlag.AlignRight)
        total_box.addWidget(total_label)
        total_box.addWidget(self.header_total_value)
        layout.addLayout(total_box)

        return header

    def _build_left_column(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        self.labor_widget = LaborAssumptionsWidget()
        self.labor_widget.changed.connect(self._on_labor_changed)
        layout.addWidget(self.labor_widget)

        self.digikey_panel = DigiKeyPanelWidget()
        self.digikey_panel.price_all_requested.connect(self.start_price_all)
        layout.addWidget(self.digikey_panel)

        layout.addStretch(1)
        return container

    def _build_middle_column(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        # 780, not the pill-tabs-era 620 — the redesigned nav bar (prev/
        # combo/next/Summary/Paste harnesses/Add harness) genuinely needs
        # more room than the old pill row did; measured sizeHint ~740 for
        # a representative harness name, plus buffer.
        container.setMinimumWidth(780)

        self.harness_nav = HarnessNavWidget()
        self.harness_nav.harness_selected.connect(self.select_harness)
        self.harness_nav.summary_selected.connect(self.select_summary)
        self.harness_nav.add_harness_requested.connect(self.add_harness)
        self.harness_nav.paste_harnesses_requested.connect(self.open_paste_harnesses_dialog)
        layout.addWidget(self.harness_nav)

        self.middle_stack = QStackedWidget()
        layout.addWidget(self.middle_stack, 1)

        self.middle_stack.addWidget(self._build_harness_view())
        self.middle_stack.addWidget(self._build_summary_view())

        return container

    def _build_harness_view(self) -> QWidget:
        view = QWidget()
        layout = QVBoxLayout(view)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        self.harness_header = HarnessHeaderWidget()
        self.harness_header.changed.connect(self._on_harness_header_changed)
        self.harness_header.duplicate_requested.connect(self.duplicate_harness)
        self.harness_header.remove_requested.connect(self.remove_harness)
        layout.addWidget(self.harness_header)

        self.parts_table = PartsTableWidget()
        self.parts_table.changed.connect(self._on_parts_changed)
        self.parts_table.lookup_requested.connect(self._on_line_lookup_requested)
        self.parts_table.lookup_bom_requested.connect(self.start_bom_lookup)
        self.parts_table.paste_bom_requested.connect(self.open_paste_bom_dialog)
        self.parts_table.add_line_requested.connect(self.add_part_line)
        self.parts_table.remove_line_requested.connect(self.remove_part_line)
        layout.addWidget(self.parts_table)

        self.processes_table = ProcessesTableWidget()
        self.processes_table.changed.connect(self._on_processes_changed)
        self.processes_table.suggest_counts_requested.connect(self.suggest_counts)
        layout.addWidget(self.processes_table)

        self.quantity_breaks = QuantityBreaksWidget()
        layout.addWidget(self.quantity_breaks)

        return view

    def _build_summary_view(self) -> QWidget:
        view = QWidget()
        layout = QVBoxLayout(view)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        self.quote_summary = QuoteSummaryWidget()
        self.quote_summary.harness_opened.connect(self.select_harness)
        layout.addWidget(self.quote_summary)

        self.money_breakdown = MoneyBreakdownWidget()
        layout.addWidget(self.money_breakdown)

        layout.addStretch(1)
        return view

    def _build_right_column(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        self.cost_price_rail = CostPriceRailWidget()
        layout.addWidget(self.cost_price_rail)

        self.quote_total = QuoteTotalWidget()
        self.quote_total.print_requested.connect(self.print_quote)
        self.quote_total.reset_requested.connect(self.reset_quote)
        layout.addWidget(self.quote_total)

        layout.addStretch(1)
        return container

    # ------------------------------------------------------------ helpers

    def active_harness_index(self) -> int:
        if isinstance(self.active, int):
            return max(0, min(self.active, len(self.quote.harnesses) - 1))
        return 0

    def active_harness(self) -> Harness:
        return self.quote.harnesses[self.active_harness_index()]

    def is_summary_active(self) -> bool:
        return self.active == "sum"

    # -------------------------------------------------------------- render

    def refresh_ui(self):
        n = len(self.quote.harnesses)
        quote_number = self.quote.quote_number or "Draft"
        self.subtitle_label.setText(f"{quote_number} · {n} harness{'es' if n != 1 else ''} · draft")
        self.customer_edit.setText(self.quote.customer)

        self.labor_widget.load(self.quote.labor)

        harness_entries = [
            (h.name, f"×{max(1, round(h.order_qty))}", harness_flag_status(h)) for h in self.quote.harnesses
        ]

        self.quote_total.render(self.quote)
        self.header_total_value.setText(self.quote_total.price_value.text())

        summary_sub = self.quote_total.price_value.text()
        self.harness_nav.rebuild(harness_entries, summary_sub, self.active)

        if self.is_summary_active():
            self.middle_stack.setCurrentIndex(1)
            self.quote_summary.render(self.quote)
            self.money_breakdown.render(self.quote)
            self.cost_price_rail.hide()
        else:
            self.middle_stack.setCurrentIndex(0)
            harness = self.active_harness()
            hi = self.active_harness_index()
            self.harness_header.load(harness)
            self.parts_table.set_pending(self.pending.get(hi, set()))
            self.parts_table.render(harness)
            eff = calc_harness(harness, self.quote.labor).eff
            self.processes_table.render(harness, self.quote.labor, eff)
            self.quantity_breaks.render(harness, self.quote.labor)
            self.cost_price_rail.render(harness, self.quote.labor)
            self.cost_price_rail.show()

        self._refresh_digikey_stats()

    def _refresh_digikey_stats(self):
        keys = set()
        resolved_keys = set()
        for harness in self.quote.harnesses:
            for line in harness.lines:
                key = line.part_number.strip().upper()
                if not key:
                    continue
                keys.add(key)
                if line.resolved:
                    resolved_keys.add(key)
        last_lookup = self.last_lookup_time.strftime("%H:%M:%S") if self.last_lookup_time else "—"
        self.digikey_panel.set_stats(len(keys), len(resolved_keys), last_lookup)

    # ------------------------------------------------------------ actions

    def _on_customer_changed(self):
        self.quote.customer = self.customer_edit.text()
        self.refresh_ui()

    def _on_labor_changed(self):
        self.labor_widget.apply_to(self.quote.labor)
        self.refresh_ui()

    def _on_harness_header_changed(self):
        self.harness_header.apply_to(self.active_harness())
        self.refresh_ui()

    def _on_parts_changed(self):
        self.parts_table.read_line_edits(self.active_harness())
        self.refresh_ui()

    def _on_processes_changed(self):
        self.processes_table.read_back(self.active_harness())
        self.refresh_ui()

    def select_harness(self, index: int):
        self.active = index
        self.refresh_ui()

    def select_summary(self):
        self.active = "sum"
        self.refresh_ui()

    def add_harness(self):
        n = len(self.quote.harnesses) + 1
        new_harness = Harness(
            name=f"Harness {n}",
            part_no="",
            order_qty=25,
            setup=250,
            freight=1.00,
            lines=[PartLine(part_number="", qty=1, category="Other")],
            processes=default_processes(),
        )
        self.quote.harnesses.append(new_harness)
        self.active = len(self.quote.harnesses) - 1
        self.refresh_ui()

    def duplicate_harness(self):
        hi = self.active_harness_index()
        src = self.quote.harnesses[hi]
        clone = copy.deepcopy(src)
        clone.name = f"{src.name} (copy)"
        self.quote.harnesses.insert(hi + 1, clone)
        self.active = hi + 1
        self.refresh_ui()

    def remove_harness(self):
        if len(self.quote.harnesses) == 1:
            return
        hi = self.active_harness_index()
        del self.quote.harnesses[hi]
        self.pending.pop(hi, None)
        self.active = max(0, hi - 1)
        self.refresh_ui()

    def add_part_line(self):
        harness = self.active_harness()
        self.parts_table.read_line_edits(harness)
        harness.lines.append(PartLine(part_number="", qty=1, category="Other"))
        self.refresh_ui()

    def remove_part_line(self, index: int):
        harness = self.active_harness()
        self.parts_table.read_line_edits(harness)
        if 0 <= index < len(harness.lines):
            del harness.lines[index]
        self.refresh_ui()

    def suggest_counts(self):
        harness = self.active_harness()
        self.parts_table.read_line_edits(harness)

        def sum_of(cats):
            return round(sum(l.qty for l in harness.lines if line_category(l) in cats))

        def count_of(cats):
            return sum(1 for l in harness.lines if line_category(l) in cats)

        mapping = {
            "cut": count_of(["Wire"]),
            "crimp": sum_of(["Terminal"]),
            "conn": count_of(["Connector"]),
            "shrink": sum_of(["Label / shrink"]),
            "label": sum_of(["Label / shrink"]),
            "insp": 1,
        }
        for process in harness.processes:
            if process.id in mapping:
                value = mapping[process.id]
                process.count = value
                if value > 0:
                    process.on = True
        self.refresh_ui()

    def reset_quote(self):
        self.quote = seed_data.make_default_quote()
        self._assign_new_quote_identity(self.quote)
        self.active = 0
        self.pending = {}
        self.last_lookup_time = None
        self.refresh_ui()
        QTimer.singleShot(0, self.start_price_all)

    def _assign_new_quote_identity(self, quote: Quote) -> None:
        """Assigns a fresh quote number and the default company snapshot.
        Call exactly once per quote actually created (init, New Quote,
        Reset) — never on Open (which restores the saved number/company
        as-is) or on any refresh/render."""
        quote.quote_number = quote_numbering.next_quote_number(settings.load_settings().initials)
        default_company = company_profiles.get_default_company()
        quote.company_name = default_company.name
        quote.company_address_lines = list(default_company.address_lines)
        quote.company_phone = default_company.phone
        quote.company_email = default_company.email

    # ------------------------------------------------------------- File menu

    def new_quote(self):
        self.quote = seed_data.make_empty_quote()
        self._assign_new_quote_identity(self.quote)
        self.active = 0
        self.pending = {}
        self.last_lookup_time = None
        self.current_file_path = None
        self._update_window_title()
        self.refresh_ui()

    def open_quote(self):
        path_str, _ = QFileDialog.getOpenFileName(self, "Open Quote", "", "Harness Quote Files (*.json)")
        if not path_str:
            return
        path = Path(path_str)
        try:
            quote = persistence.load_quote(path)
        except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
            QMessageBox.critical(self, "Open Quote Failed", f"Couldn't open {path.name}:\n{exc}")
            return

        self.quote = quote
        self.active = 0
        self.pending = {}
        self.last_lookup_time = None
        self.current_file_path = path
        self._update_window_title()
        self.refresh_ui()

    def save_quote(self):
        if self.current_file_path is None:
            self.save_quote_as()
            return
        self._write_quote_to(self.current_file_path)

    def save_quote_as(self):
        default_name = f"{self.quote.customer or 'quote'}.json"
        path_str, _ = QFileDialog.getSaveFileName(self, "Save Quote As", default_name, "Harness Quote Files (*.json)")
        if not path_str:
            return
        path = Path(path_str)
        if path.suffix.lower() != ".json":
            path = path.with_suffix(".json")
        self._write_quote_to(path)

    def _write_quote_to(self, path: Path):
        try:
            persistence.save_quote(self.quote, path)
        except OSError as exc:
            QMessageBox.critical(self, "Save Failed", f"Couldn't save to {path.name}:\n{exc}")
            return
        self.current_file_path = path
        self._update_window_title()
        self.statusBar().showMessage(f"Saved to {path.name}", 3000)

    def _update_window_title(self):
        name = self.current_file_path.name if self.current_file_path else "Untitled"
        self.setWindowTitle(f"Harness quote — {name}")

    def open_quote_details_dialog(self):
        dialog = QuoteDetailsDialog(self.quote, self)
        if dialog.exec() == QuoteDetailsDialog.DialogCode.Accepted:
            dialog.apply_to(self.quote)
            self.refresh_ui()

    def open_settings_dialog(self):
        dialog = SettingsDialog(self)
        if dialog.exec() == SettingsDialog.DialogCode.Accepted:
            dialog.save()

    def open_paste_bom_dialog(self):
        dialog = PasteBomDialog(self)
        if dialog.exec() != PasteBomDialog.DialogCode.Accepted:
            return
        harness = self.active_harness()
        harness.lines = [
            PartLine(part_number=line.part_number, qty=line.qty, category="Other")
            for line in dialog.parsed_lines
        ]
        self.refresh_ui()
        self._launch_lookups(self.active_harness_index(), list(range(len(harness.lines))))

    def open_paste_harnesses_dialog(self):
        dialog = PasteHarnessesDialog(self)
        if dialog.exec() != PasteHarnessesDialog.DialogCode.Accepted:
            return

        first_new_index = len(self.quote.harnesses)
        for group in dialog.parsed_groups:
            harness = Harness(
                name=group.name,
                part_no=group.part_no,
                order_qty=group.qty,
                setup=250,
                freight=1.00,
                lines=[
                    PartLine(part_number=line.part_number, qty=line.qty, category="Other")
                    for line in group.lines
                ],
                processes=default_processes(),
            )
            self.quote.harnesses.append(harness)

        self.active = first_new_index
        self.refresh_ui()

        for hi in range(first_new_index, len(self.quote.harnesses)):
            harness = self.quote.harnesses[hi]
            self._launch_lookups(hi, list(range(len(harness.lines))))

    def print_quote(self):
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPageMargins(QMarginsF(36, 36, 36, 36), QPageLayout.Unit.Point)
        dialog = QPrintDialog(printer, self)
        if dialog.exec() != QPrintDialog.DialogCode.Accepted:
            return

        document = QTextDocument()
        document.setHtml(print_document.build_quote_html(self.quote))
        document.setPageSize(QSizeF(printer.pageRect(QPrinter.Unit.Point).size()))
        document.print_(printer)

    # ------------------------------------------------------- DigiKey lookups

    def _on_line_lookup_requested(self, line_index: int):
        harness = self.active_harness()
        self.parts_table.read_line_edits(harness)
        self._launch_lookups(self.active_harness_index(), [line_index])

    def start_bom_lookup(self):
        harness = self.active_harness()
        self.parts_table.read_line_edits(harness)
        indices = [i for i, l in enumerate(harness.lines) if l.part_number.strip()]
        self._launch_lookups(self.active_harness_index(), indices)

    def start_price_all(self):
        if not self.is_summary_active():
            self.parts_table.read_line_edits(self.active_harness())
        for hi, harness in enumerate(self.quote.harnesses):
            indices = [i for i, l in enumerate(harness.lines) if l.part_number.strip()]
            if indices:
                self._launch_lookups(hi, indices)

    def _launch_lookups(self, harness_index: int, line_indices: list[int]):
        if not line_indices:
            return
        harness = self.quote.harnesses[harness_index]
        pending_set = self.pending.setdefault(harness_index, set())
        launched = False
        for i in line_indices:
            line = harness.lines[i]
            if not line.part_number.strip():
                continue
            pending_set.add(i)
            launched = True
            worker = Worker(cache.get_or_fetch, line.part_number)
            self._active_workers.append(worker)
            worker.signals.finished.connect(
                lambda cached, hi=harness_index, idx=i, w=worker: self._on_lookup_finished(hi, idx, cached, w)
            )
            worker.signals.error.connect(
                lambda message, hi=harness_index, idx=i, w=worker: self._on_lookup_error(hi, idx, message, w)
            )
            self.thread_pool.start(worker)
        if launched:
            self.refresh_ui()

    def _on_lookup_finished(self, harness_index: int, line_index: int, cached, worker: Worker):
        if worker in self._active_workers:
            self._active_workers.remove(worker)
        if harness_index >= len(self.quote.harnesses):
            return
        harness = self.quote.harnesses[harness_index]
        if line_index >= len(harness.lines):
            return
        line = harness.lines[line_index]
        line.lookup_attempted = True

        if cached.found:
            line.resolved = True
            line.description = cached.description
            line.source = cached.source
            line.catalog_category = cached.category_app
            extended_qty = harness.order_qty * line.qty
            unit_price, tier_qty = select_price_break(cached.standard_pricing, extended_qty)
            line.catalog_price = unit_price
            unit_label = unit_for_category(cached.category_app)
            line.price_tier_label = f"{tier_qty} {unit_label} tier" if tier_qty else ""
        else:
            line.resolved = False
            line.catalog_price = None
            line.description = ""
            line.price_tier_label = ""

        self.pending.get(harness_index, set()).discard(line_index)
        self.last_lookup_time = datetime.now()
        self.refresh_ui()

    def _on_lookup_error(self, harness_index: int, line_index: int, message: str, worker: Worker):
        if worker in self._active_workers:
            self._active_workers.remove(worker)
        if harness_index < len(self.quote.harnesses):
            harness = self.quote.harnesses[harness_index]
            if line_index < len(harness.lines):
                harness.lines[line_index].lookup_attempted = True
                harness.lines[line_index].resolved = False
        self.pending.get(harness_index, set()).discard(line_index)
        self.statusBar().showMessage(f"DigiKey lookup failed: {message}", 5000)
        self.refresh_ui()
