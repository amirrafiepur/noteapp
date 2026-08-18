"""PySide6 desktop entry point for NoteApp.

Architecture (see PROJECT_SPEC.md / DESKTOP_BUILD.md):

    Windows EXE
        -> QApplication / QMainWindow
        -> QWebEngineView
        -> http://127.0.0.1:<free-port>  (desktop.server.DjangoServer)
        -> Django (accounts, notes)
        -> SQLite

No Django business logic lives here. This module only owns: the window,
the loading state while the local server starts, printing integration, and
clean startup/shutdown of the embedded server.

IMPORTANT — testing status:
Object construction in this file has been verified to run without error
under PySide6 6.11 with QT_QPA_PLATFORM=offscreen on Linux (no display).
That confirms the Qt API is being used correctly at the construction
level. It does NOT confirm real window rendering, the native Windows
print dialog, or window.close()/target="_blank" popup behaviour under a
real Windows desktop session — those require running this on an actual
Windows machine (see DESKTOP_BUILD.md).
"""

import logging
import sys

from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QStackedWidget

from desktop.server import DjangoServer

logger = logging.getLogger(__name__)

WINDOW_TITLE = 'یادداشت‌ها'
MIN_WIDTH = 760
MIN_HEIGHT = 560
DEFAULT_WIDTH = 1080
DEFAULT_HEIGHT = 760
SERVER_READY_TIMEOUT_SECONDS = 10.0


class PrintWindow(QMainWindow):
    """A small, dedicated window that hosts the existing print-friendly
    note page (``notes/templates/notes/note_print.html``).

    The Django/JS side is untouched: that template still calls
    ``window.print()`` on load and ``window.close()`` on ``afterprint``,
    exactly as it does when opened as a plain browser tab. What changes
    here is that Qt WebEngine gives the host application two signals that
    correspond to those two JS calls:

    - ``QWebEnginePage.printRequested`` fires when the page calls
      ``window.print()``. We use it to show the native Windows print
      dialog (``QPrintDialog``) and hand off to
      ``QWebEnginePage.print()``/``printToPdf()`` instead of relying on
      Chromium's own print preview UI, per the "prefer Qt WebEngine's
      native printing/PDF capabilities" requirement.
    - ``QWebEnginePage.windowCloseRequested`` fires when the page calls
      ``window.close()``. We use it to close this window, which is what
      returns the user to Note Detail underneath. This also covers the
      browser-JS `afterprint` fallback path if the native dialog above is
      ever skipped for any reason.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('چاپ یادداشت')
        self.resize(560, 760)

        self.view = QWebEngineView(self)
        self.setCentralWidget(self.view)

        page = self.view.page()
        page.printRequested.connect(self._on_print_requested)
        page.windowCloseRequested.connect(self.close)

    def page(self) -> QWebEnginePage:
        return self.view.page()

    def _on_print_requested(self) -> None:
        """window.print() was called on the print page — show the native
        Windows print dialog (which also covers "save as PDF" via the
        standard Windows/Qt printer list) instead of a browser print
        preview."""
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dialog = QPrintDialog(printer, self)
        if dialog.exec() == QPrintDialog.DialogCode.Accepted:
            self.view.page().print(printer, self._on_print_finished)
        else:
            # User cancelled the native dialog. Close the temporary print
            # window ourselves, since there is now no print job whose
            # completion callback would do it for us — mirrors the
            # browser-JS fallback behaviour in note_print.html.
            self.close()

    def _on_print_finished(self, success: bool) -> None:
        """Called once Qt has finished the print job (or it failed).
        Either way, the temporary print window's job is done."""
        if not success:
            logger.warning('Qt WebEngine print job did not complete successfully.')
        self.close()


class MainWebEnginePage(QWebEnginePage):
    """The main application page. Overrides ``createWindow`` so that the
    existing print link (``note_detail.html``: ``target="_blank"`` to
    ``note_print``) opens inside a dedicated :class:`PrintWindow` instead
    of being silently dropped — Qt WebEngine does not create a popup for
    ``target="_blank"``/``window.open()`` unless the host app implements
    this hook."""

    def __init__(self, profile: QWebEngineProfile, parent=None):
        super().__init__(profile, parent)
        self._print_window: PrintWindow | None = None

    def createWindow(self, _window_type) -> QWebEnginePage:
        self._print_window = PrintWindow(self.parent())
        self._print_window.show()
        return self._print_window.page()


class MainWindow(QMainWindow):
    """The main NoteApp window: dedicated Windows application window, no
    address bar / tabs / browser chrome — just the app."""

    def __init__(self, server: DjangoServer):
        super().__init__()
        self._server = server

        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumSize(MIN_WIDTH, MIN_HEIGHT)
        self.resize(DEFAULT_WIDTH, DEFAULT_HEIGHT)

        self._loading_label = QLabel('در حال آماده‌سازی برنامه…', self)
        self._loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._loading_label.setStyleSheet('font-size: 16px; color: #6f6f6f;')

        self.view = QWebEngineView(self)
        self.view.setPage(MainWebEnginePage(QWebEngineProfile.defaultProfile(), self.view))
        self.view.loadFinished.connect(self._on_load_finished)

        self._stack = QStackedWidget(self)
        self._stack.addWidget(self._loading_label)
        self._stack.addWidget(self.view)
        self._stack.setCurrentWidget(self._loading_label)
        self.setCentralWidget(self._stack)

    def load_app(self) -> None:
        self.view.load(QUrl(self._server.base_url))

    def show_error(self, message: str) -> None:
        self._loading_label.setText(message)
        self._stack.setCurrentWidget(self._loading_label)

    def _on_load_finished(self, ok: bool) -> None:
        if ok:
            self._stack.setCurrentWidget(self.view)
        else:
            self.show_error('بارگذاری برنامه با خطا مواجه شد.')

    def closeEvent(self, event: QCloseEvent) -> None:
        # Stop the embedded Django server before the window actually
        # closes, so no background thread/socket is left dangling.
        self._server.stop()
        super().closeEvent(event)


def main() -> int:
    logging.basicConfig(level=logging.INFO)

    app = QApplication(sys.argv)
    app.setApplicationName('NoteApp')
    app.setOrganizationName('NoteApp')

    server = DjangoServer()

    window = MainWindow(server)
    window.show()

    try:
        server.start()
    except Exception:
        logger.exception('Failed to start the local Django server.')
        window.show_error('راه‌اندازی برنامه با خطا مواجه شد. لطفاً برنامه را دوباره اجرا کنید.')
        return app.exec()

    if not server.wait_until_ready(timeout=SERVER_READY_TIMEOUT_SECONDS):
        logger.error('Local Django server did not become ready in time.')
        window.show_error('راه‌اندازی برنامه بیش از حد طول کشید. لطفاً دوباره تلاش کنید.')
        return app.exec()

    window.load_app()

    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
