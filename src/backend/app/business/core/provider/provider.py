from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Provider:
    id: str
    name: str
    endpoint: str
    model: str
    # Never the raw secret -- read-side listings only ever say WHETHER a
    # credential is set, matching provider_registry.py's own original
    # convention. `create`/`update` accept the raw value as a write-only
    # parameter.
    credential_set: bool
    is_default: bool
    # Whether Second Brain has a real client implementation for this
    # provider id today -- Compass and Anthropic Claude only, a small
    # hardcoded set (ADR-022 point 3), not a property of the stored data.
    has_real_client: bool
