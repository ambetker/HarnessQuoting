from PySide6.QtWidgets import QTableWidget

_MIN_ROW_HEIGHT = 30
_ROW_PADDING = 8


def fit_table_height(table: QTableWidget) -> None:
    """Size a QTableWidget to exactly fit its header + rows, so it never
    scrolls in its own tiny viewport — the outer column's QScrollArea
    handles overflow instead.

    resizeRowsToContents() doesn't reliably account for setCellWidget()
    content (multi-line cells like the parts table's price+tier+override
    stack ended up clipped/overlapping), so row heights are computed
    directly from each cell widget's sizeHint instead.
    """
    for row in range(table.rowCount()):
        needed = _MIN_ROW_HEIGHT
        for col in range(table.columnCount()):
            widget = table.cellWidget(row, col)
            if widget is not None:
                needed = max(needed, widget.sizeHint().height() + _ROW_PADDING)
        table.setRowHeight(row, needed)

    height = table.horizontalHeader().height() + 2 * table.frameWidth()
    for row in range(table.rowCount()):
        height += table.rowHeight(row)
    if table.horizontalScrollBar().isVisible():
        height += table.horizontalScrollBar().sizeHint().height()
    table.setFixedHeight(max(height, table.horizontalHeader().height() + 40))
