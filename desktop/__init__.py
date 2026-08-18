"""Windows desktop shell for NoteApp: runs the existing Django application
locally and displays it inside a PySide6 window via Qt WebEngine.

This package intentionally contains no Django business logic — that all
stays in ``accounts`` and ``notes``, per the project's architecture rules.
This package is only responsible for: starting/stopping the local Django
server, choosing a free localhost port, and providing the desktop window.
"""
