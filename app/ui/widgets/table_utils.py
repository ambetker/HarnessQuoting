from PySide6.QtWidgets import QTableWidget


def fit_table_height(table: QTableWidget) -> None:
    """Size a QTableWidget to exactly fit its header + rows, so it never
    scrolls in its own tiny viewport — the outer column's QScrollArea
    handles overflow instead."""
    table.resizeRowsToContents()
    height = table.horizontalHeader().height() + 2 * table.frameWidth()
    for row in range(table.rowCount()):
        height += table.rowHeight(row)
    if table.horizontalScrollBar().isVisible():
        height += table.horizontalScrollBar().sizeHint().height()
    table.setFixedHeight(max(height, table.horizontalHeader().height() + 40))
