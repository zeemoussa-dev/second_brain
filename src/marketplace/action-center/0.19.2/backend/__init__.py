"""Action Center -- a Second Brain plugin (`ADR-022`).

What the CBO asked of whom, and whether it happened. Reads the Task notes in
`Work/Tasks/` and serves them as a follow-up list: open by owner, overdue
first, each with the evidence that closed it.

The Tasks are written from two sides: the Hermes Skills in the install's own
repository (reading sent mail, judging completion -- the Plugin API carries no
way to ship or run a Hermes agent) and this plugin's own screens, where the
operator adds, edits, closes, reopens and annotates an action. Both write the
same note the same way. My Day lists the same notes as plain to-dos.

Everything it needs from the framework arrives through the Plugin API handed to
`register`; this package imports nothing from the framework itself.
"""
from __future__ import annotations

from .action_view import ActionView
from .chasing import REQUESTS
from .owner_book import BOOK
from .routes import build_router
from .task_writer import TaskWriter


def register(api) -> None:
    # Who an owner really is, decided once and read by the install's Skills
    # before they ask a model again.
    api.register_seed_data_file(BOOK)
    # The tray the Chase button leaves addresses in for the Hermes job.
    api.register_seed_data_file(REQUESTS)
    api.register_router(build_router(ActionView(api), TaskWriter(api)))
