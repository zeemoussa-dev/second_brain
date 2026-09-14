"""My Day -- a Second Brain plugin (`ADR-022`).

Projects captured Threads, Meetings and Tasks down to what My Day's screens
need. Read-only: it writes nothing to the vault.

Everything it needs from the framework arrives through the Plugin API handed to
`register`; this package imports nothing from the framework itself.
"""
from __future__ import annotations

from .day_view import DayView
from .routes import build_router


def register(api) -> None:
    view = DayView(api)
    api.register_router(build_router(view))
    # A Thread carries only its `customer/<slug>` tag; Cockpit (framework)
    # shows the customer by asking enrichers, never by importing this plugin.
    api.register_subject_enricher(view.customer_subject_enricher)
