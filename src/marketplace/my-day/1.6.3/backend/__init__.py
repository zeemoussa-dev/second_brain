"""My Day -- a Second Brain plugin (`ADR-022`).

Projects captured Threads, Meetings and Tasks down to what My Day's screens
need. Read-only: it writes nothing to the vault.

Everything it needs from the framework arrives through the Plugin API handed to
`register`; this package imports nothing from the framework itself. Customers
come from the Entities plugin's `entities.customers` service when it is
installed; Cockpit's customer field is that plugin's, not My Day's.
"""
from __future__ import annotations

from .day_view import DayView
from .routes import build_router
from .thread_emails import ThreadEmails


def register(api) -> None:
    api.register_router(build_router(DayView(api), ThreadEmails(api)))
