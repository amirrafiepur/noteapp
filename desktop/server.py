"""Runs the existing Django application locally, on 127.0.0.1 only, inside
a background thread — so the PySide6 desktop shell can embed it in a
QWebEngineView without the user ever seeing a terminal or running
``manage.py runserver`` themselves.

No Django business logic lives here. This module only starts/stops the
server process and applies migrations automatically on startup, since a
packaged desktop app ships no ``manage.py`` for the end user to invoke.
"""

import logging
import socket
import sys
import threading
import time
from pathlib import Path
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

logger = logging.getLogger(__name__)


class _QuietWSGIRequestHandler(WSGIRequestHandler):
    """Suppress the default per-request access log line. A packaged
    desktop app has no console for the end user to see it, and printing to
    a nonexistent/closed stdout under a windowed PyInstaller build can
    raise errors."""

    def log_message(self, format, *args):  # noqa: A002 - matches base signature
        return


class _ThreadingWSGIServer(WSGIServer):
    """WSGIServer with SO_REUSEADDR, so restarting during development
    doesn't intermittently fail with 'Address already in use', and
    daemon_threads so a slow/hanging request never blocks shutdown."""

    allow_reuse_address = True
    daemon_threads = True


class DjangoServer:
    """Owns the lifecycle of the embedded local Django HTTP server.

    Binds only to 127.0.0.1 and never to 0.0.0.0 or a LAN-visible address —
    this server must never be reachable from outside the machine it runs
    on.
    """

    def __init__(self, host: str = '127.0.0.1'):
        self._host = host
        self._httpd = None
        self._thread = None

    @property
    def port(self) -> int:
        if self._httpd is None:
            raise RuntimeError('Server has not been started yet.')
        return self._httpd.server_port

    @property
    def base_url(self) -> str:
        return f'http://{self._host}:{self.port}/'

    def start(self) -> str:
        """Apply migrations, bind a free local port chosen by the OS, and
        start serving in a background thread. Returns the base URL.

        Uses port 0 (let the OS pick) rather than scanning for a free port
        ourselves — this avoids any race between "find a free port" and
        "bind to it", and avoids fragile fixed-port assumptions.
        """
        if self._httpd is not None:
            raise RuntimeError('Server is already running.')

        self._bootstrap_django()

        from django.contrib.staticfiles.handlers import StaticFilesHandler
        from django.core.wsgi import get_wsgi_application

        # StaticFilesHandler serves STATICFILES_DIRS regardless of DEBUG,
        # equivalent to `manage.py runserver --insecure`. This keeps CSS/
        # JS/fonts working under the desktop build's DEBUG=False without
        # adding a new dependency (e.g. whitenoise) or requiring a
        # collectstatic build step.
        application = StaticFilesHandler(get_wsgi_application())

        self._httpd = make_server(
            self._host,
            0,
            application,
            server_class=_ThreadingWSGIServer,
            handler_class=_QuietWSGIRequestHandler,
        )

        self._thread = threading.Thread(
            target=self._httpd.serve_forever,
            name='django-desktop-server',
            daemon=True,
        )
        self._thread.start()

        logger.info('Local Django server started at %s', self.base_url)
        return self.base_url

    def wait_until_ready(self, timeout: float = 10.0) -> bool:
        """Poll the bound port until it accepts TCP connections, or give
        up after `timeout` seconds and return False. The socket is already
        bound by `start()`, so this is normally near-instant — this just
        guards against the tiny window before the accept loop is live."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(0.2)
                try:
                    sock.connect((self._host, self.port))
                    return True
                except OSError:
                    time.sleep(0.05)
        return False

    def stop(self) -> None:
        """Stop serving and release the port. Safe to call from a thread
        other than the one running serve_forever() (e.g. the Qt main
        thread on application shutdown)."""
        if self._httpd is None:
            return
        self._httpd.shutdown()
        self._httpd.server_close()
        if self._thread is not None:
            self._thread.join(timeout=5)
        self._httpd = None
        self._thread = None
        logger.info('Local Django server stopped.')

    @staticmethod
    def _bootstrap_django() -> None:
        """Point Django at its settings module, make sure the project
        package is importable, then apply migrations before serving."""
        import os

        # desktop/server.py -> project root is one parent up. Harmless to
        # add in both dev and frozen builds; PyInstaller's own import hooks
        # normally make bundled packages importable already, but this is a
        # cheap, explicit safeguard against import-order surprises.
        project_root = Path(__file__).resolve().parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))

        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

        import django

        django.setup()

        from django.core.management import call_command

        # The packaged application ships no manage.py for the end user to
        # run themselves, so migrations must be applied automatically on
        # every startup. Fast no-op once the schema is already current.
        call_command('migrate', interactive=False, verbosity=0)
