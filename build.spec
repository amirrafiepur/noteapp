# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build specification for NoteApp.

Produces a ONE-FOLDER distribution (not one-file). Qt WebEngine ships a
sizeable Chromium runtime (locale files, icudtl.dat, QtWebEngineProcess.exe,
resource .pak files); a one-file build would have to re-extract all of that
to a temp directory on every single launch, which is slower, more fragile,
and more prone to being flagged by antivirus heuristics for a large
self-extracting executable. One-folder ships those files already laid out
on disk, which is the standard, more reliable choice for Qt WebEngine
apps — see DESKTOP_BUILD.md for the full rationale.

Build with:
    pyinstaller build.spec

Output:
    dist/NoteApp/NoteApp.exe   (plus its supporting files in dist/NoteApp/)

IMPORTANT: PyInstaller does not cross-compile. This spec must be run ON
WINDOWS to produce a Windows executable — running it on Linux/macOS
produces a Linux/macOS binary instead. See DESKTOP_BUILD.md.
"""

import sys

from PyInstaller.utils.hooks import collect_submodules

# collect_submodules() below runs immediately as plain Python code while
# this spec file executes — before Analysis() exists — so it needs
# 'config', 'accounts', and 'notes' importable from THIS process's
# sys.path right now. SPECPATH (injected by PyInstaller as the directory
# containing this .spec file) covers that; passing pathex=[SPECPATH] to
# Analysis() below is a separate, additional step and does NOT retroactively
# fix collect_submodules() calls that already ran above it.
if SPECPATH not in sys.path:
    sys.path.insert(0, SPECPATH)

block_cipher = None

# --- Data files ------------------------------------------------------------
# Bundle Django's templates and static assets (fonts, CSS) as plain data
# files, read at runtime via config.runtime.get_resource_dir() /
# sys._MEIPASS. Also bundle each app's own templates/ folder explicitly —
# see the comment in config/settings.py TEMPLATES['DIRS'] for why this is
# necessary in addition to APP_DIRS=True.
datas = [
    ('templates', 'templates'),
    ('static', 'static'),
    ('accounts/templates', 'accounts/templates'),
    ('notes/templates', 'notes/templates'),
]

# --- Hidden imports ----------------------------------------------------------
# Django loads several modules dynamically (by string, e.g. the DB engine
# name, or by scanning a package directory for migrations), which
# PyInstaller's static analysis cannot discover on its own. Explicitly
# collecting these packages' submodules ensures they end up bundled.
hiddenimports = []
for package in (
    'django.db.backends.sqlite3',
    'django.template.backends.django',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'notes',
    'config',
):
    hiddenimports += collect_submodules(package)

a = Analysis(
    ['desktop/main.py'],
    # SPECPATH is injected by PyInstaller as the directory containing this
    # .spec file (the project root). Without this, PyInstaller's own
    # analysis process has no way to import 'config', 'accounts', or
    # 'notes' as local packages (they aren't pip-installed), which
    # silently drops them from collect_submodules() and produces a
    # `ModuleNotFoundError: No module named 'config'` at runtime — caught
    # by actually running the built executable, see DESKTOP_BUILD.md.
    pathex=[SPECPATH],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='NoteApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # windowed app — no terminal window for the end user
    # icon='desktop/icon.ico',  # add an .ico file and uncomment if desired
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='NoteApp',
)
