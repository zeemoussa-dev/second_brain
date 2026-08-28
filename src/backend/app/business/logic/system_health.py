"""System Health aggregation (REQ-SB-31-US-01) -- composes real signals
from Core Managers, never a retired/stale registry. Recompute fresh on
every call -- no caching (Scenario 7). Moved here from
business/system_health.py (2026-08-28, operator: "this is a logic and
it should communicate with the core and hermes to get the info not
directly") -- cross-domain composition belongs in business/logic/, not
a flat business/ module reaching into a business entity's own store
directly.

2026-08-28: dropped `disabled_agents` entirely -- the old "agent's
selected Provider has no real client" check depended completely on
provider_registry.py's own per-agent assignment tracking, which was
already dead: its self-healing loop wiped every real assignment on
every single read (confirmed live, real on-disk state: `assignments:
{}`) since agent_registry.py (the retired pre-Hermes agent model this
whole mechanism was built for) was emptied 2026-08-22. Hermes owns real
per-agent model/provider config directly now
(AgentManager.update(model=..., reasoning_effort=...)) -- there is no
real equivalent "disabled" concept in that world; every real Hermes
agent has SOME real model configured by construction, so this isn't a
live gap being silently dropped, it's a retired check for a mechanism
that no longer exists. `providers` now sources from the real
`ProviderManager` -- informational only (Compass/Anthropic Claude
credential/endpoint data), no per-agent rollup (that concept is retired
alongside disabled_agents)."""
from __future__ import annotations

from app.business.core.provider.provider_manager import ProviderManager

_provider_manager = ProviderManager()


def get_system_health() -> dict:
    return {
        "providers": [
            {
                "id": p.id, "name": p.name, "endpoint": p.endpoint, "model": p.model,
                "credential_set": p.credential_set, "is_default": p.is_default,
                "has_real_client": p.has_real_client,
            }
            for p in _provider_manager.get_all()
        ],
    }
