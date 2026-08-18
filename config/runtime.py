"""Runtime environment helpers shared by ``config.settings`` and the
``desktop`` package.

This module answers two questions the rest of the project needs, without
duplicating the logic in more than one place:

1. Are we running as plain Python (``manage.py runserver`` during
   development), or as a PyInstaller-frozen executable?
2. Given that, where should we read *bundled, read-only* resources
   (templates, static files) from, and where should we write *persistent,
   user* data (the SQLite database)?

Nothing here imports Django, so it is safe to import from ``settings.py``
before Django has finished configuring itself.
"""

import os
import sys
from pathlib import Path

# ``config/runtime.py`` -> project root is two parents up.
BASE_DIR = Path(__file__).resolve().parent.parent

#: True when running inside a PyInstaller-built executable.
FROZEN = bool(getattr(sys, 'frozen', False))


def get_resource_dir() -> Path:
    """Directory that contains bundled, read-only resources.

    In development this is the project checkout (``BASE_DIR``). When frozen
    by PyInstaller, bundled data files are extracted (one-file mode) or
    shipped alongside the executable (one-folder mode) under
    ``sys._MEIPASS``.
    """
    if FROZEN:
        return Path(getattr(sys, '_MEIPASS', BASE_DIR))
    return BASE_DIR


def get_data_dir() -> Path:
    """Directory where persistent, writable user data (the database) lives.

    - In development: the project checkout, so ``db.sqlite3`` keeps living
      next to ``manage.py`` exactly as before — no change to existing
      developer workflow.
    - When frozen: a per-user, per-app directory outside the (potentially
      read-only) PyInstaller bundle. On Windows this is
      ``%APPDATA%\\NoteApp``. If ``APPDATA`` isn't set (e.g. testing a
      frozen build on Linux/macOS), fall back to ``~/.noteapp``.

    Can be overridden explicitly via the ``NOTEAPP_DATA_DIR`` environment
    variable, which is mainly useful for testing the packaged build without
    touching a real user's AppData.
    """
    override = os.environ.get('NOTEAPP_DATA_DIR')
    if override:
        return Path(override)

    if not FROZEN:
        return BASE_DIR

    appdata = os.environ.get('APPDATA')
    if appdata:
        return Path(appdata) / 'NoteApp'

    return Path.home() / '.noteapp'


def ensure_data_dir() -> Path:
    """Return the data directory, creating it if necessary."""
    data_dir = get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir
