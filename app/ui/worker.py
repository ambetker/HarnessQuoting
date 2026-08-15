"""Generic background-task runner for QThreadPool.

Fixes the blocking-call-freezes-UI issue flagged in the original project
notes: DigiKey lookups (app.cache.get_or_fetch) run here instead of on the
UI thread, with results delivered back via a Qt signal.
"""

from PySide6.QtCore import QObject, QRunnable, Signal


class WorkerSignals(QObject):
    finished = Signal(object)  # result
    error = Signal(str)


class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
        except Exception as exc:  # noqa: BLE001 - surface any failure to the UI
            self.signals.error.emit(str(exc))
        else:
            self.signals.finished.emit(result)
