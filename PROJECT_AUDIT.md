# PROJECT_AUDIT.md

Audit date: current session, before Phase 5 work begins.

## Current architecture

```
noteapp/
├── manage.py
├── requirements.txt        (Django==5.2.17 only)
├── .env.example             (SECRET_KEY template; not auto-loaded — no python-dotenv)
├── .cursor/rules/           (security, architecture, workflow, paths — all consistent
│                              with this brief, already enforced in code)
├── config/                  (settings.py, urls.py, wsgi.py, asgi.py)
├── accounts/                (registration, login, logout — Django built-in auth)
├── notes/                   (Note model, dashboard, create/detail/print views)
├── templates/                (base.html, partials/form_field.html)
├── static/
│   ├── css/ (main.css, print.css)
│   └── fonts/vazirmatn/ (Regular/Medium/Bold, local .woff2, no CDN)
└── db.sqlite3                (dev database, BASE_DIR-relative)
```

Two Django apps only, as required. No DRF, no frontend framework, no desktop
or packaging code yet (no `desktop/`, no `.spec` file, no PyInstaller
config) — nothing has skipped ahead of the current phase.

## Completed functionality (verified this session)

- **Authentication**: Django built-in `UserCreationForm`/`AuthenticationForm`
  subclasses with Persian labels/errors. Register → auto-login → dashboard.
  Login/logout via `django.contrib.auth.views`. Passwords hashed by Django
  (no custom hashing).
- **Notes**: `Note(owner FK, content, created_at auto_now_add)`, ordered
  newest-first, indexed on `(owner, -created_at)`.
- **Ownership security**: every note fetch uses
  `get_object_or_404(Note, pk=pk, owner=request.user)`; `owner` is always
  set server-side (`note.owner = request.user`), never from client input.
  All protected views use `@login_required`.
- **Dashboard**: two-panel layout — "متن جدید" (new text form) and
  "متن‌های ذخیره‌شده" (saved list with preview + date), empty state present.
- **Note detail**: full content, date, back button, print button.
- **Persian/RTL**: `lang="fa" dir="rtl"` on every HTML page,
  `LANGUAGE_CODE = 'fa'`, `TIME_ZONE = 'Asia/Tehran'`, all UI strings in
  Persian, local Vazirmatn `.woff2` files (no external font CDN).
- **Visual design**: red/yellow/white palette via CSS custom properties in
  `main.css`; clean card-based layout, not raw Django scaffolding.
- **Print flow**: `note_print.html` already auto-triggers `window.print()`
  on load, listens for `afterprint` to call `window.close()`, and shows a
  manual-close fallback message/button if the window doesn't close after
  500ms. `print.css` hides screen-only elements under `@media print` and
  strips app chrome (no header/nav) from the print document. This is
  further along than a bare "Phase 4" state — the core auto-close problem
  described in the brief is already handled in the browser-dev-server case.
- **Django health**: `python manage.py check` → 0 issues. All migrations
  applied cleanly (`admin`, `auth`, `contenttypes`, `notes`, `sessions`;
  `accounts` app has no models, so no migrations needed).

## Incomplete / not started (expected — future phases)

- **Automated tests**: `accounts/tests.py` and `notes/tests.py` are empty
  stubs. No coverage yet for ownership isolation, print view auth, etc.
- **Print correctness under Qt WebEngine specifically**: the current print
  page relies on `window.print()` / `window.close()` browser semantics.
  This works in a normal dev-server/browser context but Qt WebEngine's
  handling of `window.close()` on a same-tab `window.open()`-less navigation
  needs verification once the desktop shell exists (Phase 11).
- **Security hardening for packaging**: `DEBUG = True`, insecure fallback
  `SECRET_KEY` committed in `settings.py`. Fine for local dev, must be
  revisited before any distribution build.
- **Desktop shell**: no PySide6, no QMainWindow, no QWebEngineView, no
  local server bootstrap/port selection/shutdown logic.
- **Writable data directory**: `DATABASES['default']['NAME']` is hardcoded
  to `BASE_DIR / 'db.sqlite3'`. Must move to a per-user writable directory
  (e.g. `%APPDATA%/NoteApp`) before packaging, since the PyInstaller bundle
  directory can be read-only.
- **Static file / template packaging compatibility**: not yet reviewed for
  PyInstaller path resolution (`sys._MEIPASS`, etc.).
- **Requirements split / pinning for desktop+packaging**: only Django is
  pinned; PySide6/PyInstaller not yet added.
- **PyInstaller build**: no `.spec` file, no build script, no EXE.
- **Shortcuts / distribution / final docs**: none yet (`DESKTOP_BUILD.md`
  doesn't exist).

## Detected issues (minor, non-blocking)

1. `.env.example` documents `SECRET_KEY` but nothing in the project loads a
   `.env` file (no `python-dotenv`) — `os.environ.get('SECRET_KEY', ...)`
   only picks it up if the variable is exported some other way. Not a bug,
   just worth noting; not fixing unless requested, since it's outside the
   current phase's scope.
2. `admin.py` in both apps is an empty stub — `Note` and any custom user
   fields are not registered in Django admin. Not required by the spec, so
   left as-is.
3. `DEBUG = True` and a placeholder `SECRET_KEY` fallback are appropriate
   for the current local-prototype phase but are flagged for Phase 7
   (security review) and must not ship in a packaged build.

## Proposed execution order

Following the phase plan exactly, starting from the first incomplete phase:

1. **Phase 5** — Complete/verify print functionality end-to-end (mostly
   done; verify ownership filtering on `note_print`, confirm no app chrome
   leaks into print output, add focused tests).
2. **Phase 6** — Final UI/UX pass across login, register, dashboard, detail,
   print.
3. **Phase 7** — Security review (CSRF, auth, ownership, SECRET_KEY,
   DEBUG, ALLOWED_HOSTS).
4. **Phase 8–11** — Desktop architecture: PySide6 shell, local Django
   server bootstrap, window UX, Qt-based printing.
5. **Phase 12–14** — Writable data directory, static/packaging
   compatibility, requirements finalization.
6. **Phase 15–17** — PyInstaller packaging, spec file, build & test.
7. **Phase 18–20** — Shortcuts/distribution UX, cleanup, final
   documentation (`DESKTOP_BUILD.md`) and final report.

No working functionality will be rewritten during this process unless a
phase specifically requires a change to it.

---

Starting with **Phase 5** now.
