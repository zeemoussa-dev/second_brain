"""Business-layer wrapper over the Hermes library's Profile (Agent) CRUD
-- the only real job here is turning dataclasses into plain dicts for
the API layer (ADR-005 point 5's own router-never-reaches-into-
data_access split)."""
from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Any, Iterable

from app.business.hermes.client import get_client

_logger = logging.getLogger(__name__)


def without_duplicate_ids(profiles: Iterable[Any], id_of=None) -> list[Any]:
    """The same profiles with each id appearing once, in the order
    Hermes gave them.

    **Hermes really does report a profile twice.** On the operator's
    install `default` (Primary) comes back two times, byte-identical in
    both copies -- `<HERMES_HOME>` *is* the default profile's directory
    and it is also enumerated among the profiles, so the install's own
    agent is counted from both ends. Measured, not assumed: 42 profiles
    returned, `default` x2.

    Passing that through is what made one specialist look like two. A
    duplicate agent duplicates every edge drawn to it, so the Flow map
    showed one link on two copies of the same node and the operator
    reasonably read it as "it added it twice" (2026-10-24).

    **One helper rather than a de-duplication at each reader**, because
    every reader has the same problem and the first one to forget would
    show it again -- `AgentManager.get_all()` reaches the Hermes client
    directly and does not come through `get_all()` below, which is
    exactly how a second copy of this rule would drift.

    The first copy wins: they are identical, so which one is arbitrary,
    and keeping the first preserves Hermes' own ordering. It is logged
    rather than silent -- this collapses a display problem, it does not
    make the upstream duplicate untrue.
    """
    read_id = id_of or (lambda profile: profile.get("id"))
    seen: set[str] = set()
    unique: list[Any] = []
    duplicated: list[str] = []
    for profile in profiles:
        profile_id = read_id(profile)
        if profile_id in seen:
            duplicated.append(str(profile_id))
            continue
        seen.add(profile_id)
        unique.append(profile)
    if duplicated:
        _logger.info(
            "Hermes reported %d profile(s) more than once (%s); each is listed once here",
            len(duplicated), ", ".join(sorted(set(duplicated))),
        )
    return unique


def get_all() -> list[dict]:
    """Every Hermes profile, each id appearing ONCE.

    See `without_duplicate_ids` for why that is not a no-op.
    """
    return without_duplicate_ids(
        asdict(agent) for agent in get_client().profiles.get_all()
    )


def find_by_id(agent_id: str) -> dict | None:
    agent = get_client().profiles.find_by_id(agent_id)
    return asdict(agent) if agent is not None else None
