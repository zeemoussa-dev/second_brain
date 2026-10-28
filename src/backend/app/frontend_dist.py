"""Where the built UI is, if this install serves one (production, 2026-10-28).

Its own module because two places need the answer and neither may import the
other: `main.py` mounts the files, and `auth_guard.py` answers a signed-out
navigation with the shell instead of a JSON refusal. `main.py` already imports
the guard, so the guard cannot import `main`.

In development there is no `dist/` -- the UI is Vite on its own port -- and
every function here answers "no UI", which is what keeps the development
behaviour and the whole test suite exactly as they were.
"""
from __future__ import annotations

from pathlib import Path

#: `src/frontend/dist`, from `src/backend/app/frontend_dist.py`.
DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"


#: The shell and the files it loads itself. Exact paths, and the two mounted
#: prefixes -- nothing here is an API route, so these stay reachable on an
#: install that is signed out or not yet configured.
_SHELL_PATHS = frozenset({"/", "/index.html", "/favicon.svg", "/icons.svg"})
_SHELL_PREFIXES = ("/assets/", "/fonts/")


def frontend_shell() -> Path | None:
    """`index.html`, or None when this process is not serving the UI."""
    index = DIST / "index.html"
    return index if index.is_file() else None


def is_user_interface_path(path: str) -> bool:
    """Whether this path is the web interface itself rather than the API.

    Deliberately a fixed list and not "anything that is not an API route":
    a gate that let every unmatched path through would also let through an
    API route that simply has not been registered yet, and plugin routers
    register late.
    """
    return path in _SHELL_PATHS or path.startswith(_SHELL_PREFIXES)
