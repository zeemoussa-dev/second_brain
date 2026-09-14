from __future__ import annotations

from dataclasses import dataclass, field

LOADED = "loaded"
REFUSED = "refused"
DISABLED = "disabled"
INVALID = "invalid"


@dataclass
class Plugin:
    """One installed plugin and what happened when the host tried to load it.

    `refused` means the host declined to import it (a `framework_api` that does
    not match); `disabled` means its own code failed while importing or
    registering; `invalid` means its install on disk is unusable (bad id,
    unreadable or mismatched manifest). Only `loaded` plugins serve routes."""

    id: str
    name: str
    version: str
    framework_api: int | None
    requires: list[str] = field(default_factory=list)
    status: str = INVALID
    reason: str | None = None
    routes_prefix: str | None = None
