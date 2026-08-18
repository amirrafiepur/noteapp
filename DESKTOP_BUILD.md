# DESKTOP_BUILD.md

How NoteApp's Windows desktop build works, how to run it in development,
and how to package it into a distributable EXE.

## 1. Architecture

```
NoteApp.exe (Windows)
    -> PySide6 QApplication / QMainWindow          (desktop/main.py)
    -> QWebEngineView
    -> http://127.0.0.1:<OS-assigned free port>    (desktop/server.py)
    -> Django (accounts, notes)                     (unchanged business logic)
    -> SQLite                                       (writable per-user data dir)
```

`desktop/` contains zero Django business logic. It only starts/stops the
local server and provides the window. All auth, models, views, forms,
templates, and static assets are exactly the same code whether running via
`manage.py runserver` or inside the packaged desktop app.

## 2. Development startup (unchanged)

```
python manage.py runserver
```

Behaves exactly as before this work began — `DEBUG=True`, database at
`BASE_DIR/db.sqlite3`, templates/static resolved from the project checkout.
None of the desktop work changes this path.

## 3. Running the desktop shell in development

```
pip install -r requirements.txt
python desktop/main.py
```

This starts Django in a background thread on `127.0.0.1` (OS-assigned free
port — never a fixed port, never LAN-visible), applies migrations
automatically, waits for the port to accept connections, then opens the
PySide6 window and loads the app inside `QWebEngineView`. Closing the window
stops the embedded server cleanly.

## 4. How PySide6 starts Django

`desktop/server.py`'s `DjangoServer`:

1. Adds the project root to `sys.path`, points `DJANGO_SETTINGS_MODULE` at
   `config.settings`, calls `django.setup()`.
2. Runs `migrate --noinput` automatically (the packaged app ships no
   `manage.py` for the end user to run themselves).
3. Wraps the WSGI app in `StaticFilesHandler` (equivalent to
   `runserver --insecure`) so CSS/JS/fonts serve correctly even with
   `DEBUG=False`, without adding a new dependency like whitenoise.
4. Binds to `127.0.0.1` port `0` (OS picks a free port — no fixed-port
   assumptions, no race condition) and serves in a background thread.
5. `stop()` shuts the server down and joins the thread.

`desktop/main.py`'s `MainWindow` shows a loading label until the first page
load finishes, then swaps to the live `QWebEngineView`, and stops the
server in `closeEvent`.

## 5. Database location

- **Development** (`manage.py runserver`, or `desktop/main.py` run directly
  without `sys.frozen`): `BASE_DIR/db.sqlite3` — unchanged from before.
- **Packaged/frozen build**: `%APPDATA%\NoteApp\db.sqlite3` on Windows. If
  `APPDATA` isn't set (e.g. testing a frozen build on Linux/macOS), falls
  back to `~/.noteapp/db.sqlite3`.
- Can be overridden explicitly for testing via the `NOTEAPP_DATA_DIR`
  environment variable.

This logic lives in `config/runtime.py` and is wired into
`config/settings.py`'s `DATABASES` — see that file for the exact code.

## 6. Static/template handling for packaging

- `config/runtime.py`'s `get_resource_dir()` returns the project checkout
  in development, or `sys._MEIPASS` (PyInstaller's bundle directory) when
  frozen.
- `TEMPLATES[0]['DIRS']` and `STATICFILES_DIRS` in `config/settings.py`
  resolve through this, so templates/CSS/fonts are found correctly either
  way.
- `accounts/templates/` and `notes/templates/` are listed explicitly in
  `TEMPLATES[0]['DIRS']` in addition to Django's `APP_DIRS=True`
  auto-discovery — the latter depends on each app's on-disk path, which is
  unreliable once the app's Python source is frozen into a PyInstaller
  archive. Listing them explicitly (resolved through the same
  `RESOURCE_DIR`) makes this robust in both modes without removing the
  normal `APP_DIRS` behavior.

## 7. PyInstaller packaging

**One-folder, not one-file.** Qt WebEngine ships a sizeable Chromium
runtime (locale files, `icudtl.dat`, `QtWebEngineProcess.exe`, resource
`.pak` files). A one-file build would re-extract all of that to a temp
directory on every single launch — slower, more fragile, and more likely to
be flagged by antivirus heuristics for a large self-extracting executable.
One-folder ships those files already laid out on disk, which is the
standard, more reliable choice for Qt WebEngine apps.

`build.spec`:

- Bundles `templates/`, `static/`, `accounts/templates/`,
  `notes/templates/` as data files.
- Explicitly collects submodules of `accounts`, `notes`, and `config` (and
  the Django contrib apps in use) via `collect_submodules()`, because
  Django loads some modules dynamically by string (the DB engine name,
  migration files by filename) in ways PyInstaller's static analysis can't
  discover on its own.
- **Important, non-obvious gotcha we hit and fixed**: `collect_submodules()`
  calls run immediately as plain Python code while the spec file is being
  read — *before* the `Analysis()` object exists. Passing `pathex=[...]` to
  `Analysis()` does **not** retroactively fix those earlier calls. The spec
  file therefore adds the project root (`SPECPATH`) to `sys.path` directly,
  at the top, before any `collect_submodules()` call. Without this, PyInstaller
  silently drops `config`, `accounts`, and `notes` from the bundle entirely, and
  the packaged app fails at startup with
  `ModuleNotFoundError: No module named 'config'`. This was caught by
  actually running the built executable, not just by a successful
  `pyinstaller` exit code.

### Build command

```
pip install -r requirements.txt -r requirements-build.txt
pyinstaller build.spec
```

### Output location

```
dist/NoteApp/NoteApp.exe        (plus its supporting files in dist/NoteApp/)
```

## 8. Distribution

Zip the entire `dist/NoteApp/` folder and give that to the customer — not
just the `.exe` alone, since it depends on the sibling files/folders
PyInstaller placed next to it (the `_internal/` folder holding Django,
PySide6, Qt WebEngine, templates, static files, etc.).

### Customer requirements

None of the following need to be installed: Python, pip, Django, PySide6,
Git, VS Code. Just Windows itself.

### Creating a shortcut

No installer is included yet (per project rules, not introduced
prematurely). To create a desktop shortcut manually: right-click
`NoteApp.exe` inside the extracted `dist/NoteApp/` folder → **Send to** →
**Desktop (create shortcut)**.

## 9. Known limitations

- **Not yet tested on real Windows.** Everything in this document was
  built and validated on Linux — including actually running the frozen
  executable, confirming it starts, migrates, serves HTTP, and serves
  static files correctly — but Qt WebEngine's real window rendering, the
  native `QPrintDialog` print flow, and the packaged `.exe` launching
  correctly on Windows have not been verified on an actual Windows
  machine. PyInstaller does not cross-compile: a Windows `.exe` can only
  be produced by running `pyinstaller build.spec` **on Windows**.
- **No installer / Start Menu shortcut automation yet** — manual shortcut
  creation only, per the "don't introduce an installer prematurely" rule.
- No automated GUI/print testing (would require a Windows CI runner with a
  display).
- `DEBUG` defaults to `False` only when frozen; if you ever run
  `desktop/main.py` directly outside of `manage.py runserver`,
  double-check `sys.frozen` detection behaves as expected for your build
  tool if you change how the entry point is invoked.
