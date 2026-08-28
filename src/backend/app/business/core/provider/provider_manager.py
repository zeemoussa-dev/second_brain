"""ProviderManager -- the sole gateway onto Provider data (mirrors
Section/Agent/Pipeline/Vault/Template/Index Manager's own "one real
gateway" rule). A Provider is a real LLM credential source (endpoint/
model/credential) Second Brain knows about -- Compass and Anthropic
Claude today, hand-seeded on first read.

Formalized as a real Core entity 2026-08-28 (operator: "Provider is a
key entity for me... collecting the providers data will help us to
provision Hermes when it's brand new installation") -- settles the
"Provider's status (Core entity, or infrastructure alongside Tool) is
still an open question" note from the earlier Core-entity pass. Nothing
consumes per-agent provider assignment anymore (Hermes owns that
directly, per-profile, via AgentManager.update(model=..., reasoning_
effort=...)) -- but the credential/endpoint DATA itself is worth
keeping as a real, structured store for a not-yet-built future use:
provisioning a brand-new Hermes install with known-good provider
credentials.

Folds in and retires provider_registry.py -- but deliberately NOT its
own dead per-agent assignment tracking (`assignments`,
get_agent_provider/set_agent_provider, the self-healing reconciliation
loop against agent_registry.list_agents()). That whole mechanism
depended on agent_registry.py, the retired pre-Hermes agent model
(confirmed empty since 2026-08-22) -- its self-healing loop deleted
every real assignment on every single read since the day agent_registry
was emptied, confirmed live (real on-disk state before this fix:
`assignments: {}`). Dropped entirely, not ported forward -- a genuinely
dead mechanism, not a migration target. `agent_registry.py` itself is
deleted alongside this (its only two real callers were
provider_registry.py and system_health.py, both retired/fixed the same
pass). Delete is now unconditional too -- no more blocked-by-agent-ids
check, since there is no real assignment left to block on.

Raw I/O lives in data_access/providers.py, per the 2026-08-28 layering
correction -- this file holds zero raw file calls.
"""
from __future__ import annotations

from app.business.core.provider.provider import Provider
from app.config import settings as app_settings
from app.data_access import providers as providers_data
from app.obsidian.tags import tag_slug

_DEFAULT_PROVIDER_ID = "compass"
_ANTHROPIC_PROVIDER_ID = "anthropic-claude"

# Small, hardcoded set -- Compass and Anthropic Claude both have real
# clients (ADR-022 point 3); a Provider record with no matching real
# client is still stored/listed, just flagged has_real_client=False.
_REAL_CLIENT_PROVIDER_IDS = {"compass", "anthropic-claude"}


class ProviderManager:
    def _seed_state(self) -> dict:
        compass = {
            "id": _DEFAULT_PROVIDER_ID, "name": "Compass",
            "endpoint": app_settings.compass_base_url,
            "credential": app_settings.compass_api_key,
            "model": app_settings.compass_model,
        }
        anthropic_claude = {
            "id": _ANTHROPIC_PROVIDER_ID, "name": "Anthropic Claude",
            "endpoint": "https://api.anthropic.com",
            "credential": app_settings.anthropic_api_key,
            "model": app_settings.anthropic_model,
        }
        state = {"providers": [compass, anthropic_claude]}
        providers_data.save_state(state)
        return state

    def _load_state(self) -> dict:
        state = providers_data.load_state()
        return state if state is not None else self._seed_state()

    def _to_provider(self, data: dict) -> Provider:
        return Provider(
            id=data["id"], name=data["name"], endpoint=data["endpoint"], model=data["model"],
            credential_set=bool(data.get("credential")),
            is_default=data["id"] == _DEFAULT_PROVIDER_ID,
            has_real_client=data["id"] in _REAL_CLIENT_PROVIDER_IDS,
        )

    def get_all(self) -> list[Provider]:
        state = self._load_state()
        return [self._to_provider(p) for p in state["providers"]]

    def get_by_id(self, provider_id: str) -> Provider | None:
        return next((p for p in self.get_all() if p.id == provider_id), None)

    def create(self, name: str, endpoint: str, credential: str, model: str) -> Provider:
        state = self._load_state()
        provider_id = tag_slug(name)
        state["providers"].append({
            "id": provider_id, "name": name, "endpoint": endpoint,
            "credential": credential, "model": model,
        })
        providers_data.save_state(state)
        return self.get_by_id(provider_id)

    def update(
        self, provider_id: str, *, name: str | None = None, endpoint: str | None = None,
        credential: str | None = None, model: str | None = None,
    ) -> Provider | None:
        """`None` (omitted) = leave unchanged, same convention every
        other Manager's own update() uses -- an omitted credential
        leaves the stored value untouched, letting a caller edit
        endpoint/model without re-pasting the key."""
        state = self._load_state()
        for provider in state["providers"]:
            if provider["id"] == provider_id:
                if name is not None:
                    provider["name"] = name
                if endpoint is not None:
                    provider["endpoint"] = endpoint
                if credential is not None:
                    provider["credential"] = credential
                if model is not None:
                    provider["model"] = model
                providers_data.save_state(state)
                return self.get_by_id(provider_id)
        return None

    def delete(self, provider_id: str) -> dict:
        state = self._load_state()
        state["providers"] = [p for p in state["providers"] if p["id"] != provider_id]
        providers_data.save_state(state)
        return {"deleted": True}
