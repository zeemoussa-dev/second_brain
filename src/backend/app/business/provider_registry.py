"""Providers: a new, persisted, user-mutable concern (ADR-014) — which
LLM Provider an agent uses, independent of agent identity/type/actions.
Composed alongside app/business/agent_registry.py, not inside it —
agent_registry.py and app/data_access/compass_client.py are not modified
by this module (the pre-seeded "Compass" entry is a CRUD-editable
representation only; the real Compass call path keeps reading
app.config.settings.compass_* directly, per REQ-SB-19's own Non-Goals).
"""
from app.business import agent_registry
from app.config import settings as app_settings
from app.data_access import vault_writer

_DEFAULT_PROVIDER_ID = "compass"
_ANTHROPIC_PROVIDER_ID = "anthropic-claude"

# Small, hardcoded set — mirrors ADR-011 point 3's "declared but not yet
# backed by a real handler" pattern one layer up (Provider, not action).
# Compass and Anthropic Claude both have real clients this pass
# (ADR-022 point 3).
_REAL_CLIENT_PROVIDER_IDS = {"compass", "anthropic-claude"}


def _seed_state() -> dict:
    compass = {
        "id": _DEFAULT_PROVIDER_ID,
        "name": "Compass",
        "endpoint": app_settings.compass_base_url,
        "credential": app_settings.compass_api_key,
        "model": app_settings.compass_model,
    }
    anthropic_claude = {
        "id": _ANTHROPIC_PROVIDER_ID,
        "name": "Anthropic Claude",
        # Informational only -- anthropic_client.py never reads this
        # field, it constructs anthropic.Anthropic(api_key=...) directly
        # (ADR-022 point 2).
        "endpoint": "https://api.anthropic.com",
        "credential": app_settings.anthropic_api_key,
        "model": app_settings.anthropic_model,
    }
    state = {"providers": [compass, anthropic_claude], "assignments": {}}
    vault_writer.save_providers_state(state)
    return state


def _load_state() -> dict:
    state = vault_writer.load_providers_state()
    if state is None:
        state = _seed_state()
    changed = False
    for agent in agent_registry.list_agents():
        if agent["id"] not in state["assignments"]:
            state["assignments"][agent["id"]] = _DEFAULT_PROVIDER_ID
            changed = True
    if changed:
        vault_writer.save_providers_state(state)
    return state


def _agent_ids_by_provider(state: dict) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for agent_id, provider_id in state["assignments"].items():
        result.setdefault(provider_id, []).append(agent_id)
    return result


def has_real_client(provider_id: str) -> bool:
    return provider_id in _REAL_CLIENT_PROVIDER_IDS


def list_providers() -> list[dict]:
    state = _load_state()
    agent_ids_by_provider = _agent_ids_by_provider(state)
    return [
        {
            "id": p["id"],
            "name": p["name"],
            "endpoint": p["endpoint"],
            "model": p["model"],
            "credential_set": bool(p.get("credential")),
            "is_default": p["id"] == _DEFAULT_PROVIDER_ID,
            "has_real_client": has_real_client(p["id"]),
            "agent_ids": agent_ids_by_provider.get(p["id"], []),
        }
        for p in state["providers"]
    ]


def create_provider(name: str, endpoint: str, credential: str, model: str) -> dict:
    state = _load_state()
    provider_id = vault_writer.tag_slug(name)
    provider = {
        "id": provider_id,
        "name": name,
        "endpoint": endpoint,
        "credential": credential,
        "model": model,
    }
    state["providers"].append(provider)
    vault_writer.save_providers_state(state)
    return provider


def update_provider(
    provider_id: str,
    name: str | None = None,
    endpoint: str | None = None,
    credential: str | None = None,
    model: str | None = None,
) -> dict | None:
    """An omitted (None) credential leaves the stored value untouched —
    lets a user edit endpoint/model without re-pasting the key
    (ADR-014 point 5)."""
    state = _load_state()
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
            vault_writer.save_providers_state(state)
            return provider
    return None


def remove_provider(provider_id: str) -> dict:
    """Never raises for ordinary control flow — returns a result dict
    (ADR-014 point 4), mirroring section_registry.delete_section's own
    shape. The router (T03) translates a blocked removal into HTTP
    409."""
    state = _load_state()
    blocked_by_agent_ids = [
        agent_id for agent_id, pid in state["assignments"].items() if pid == provider_id
    ]
    if blocked_by_agent_ids:
        return {"deleted": False, "blocked_by_agent_ids": blocked_by_agent_ids}
    state["providers"] = [p for p in state["providers"] if p["id"] != provider_id]
    vault_writer.save_providers_state(state)
    return {"deleted": True, "blocked_by_agent_ids": []}


def get_provider(provider_id: str) -> dict | None:
    """A direct by-id lookup, distinct from get_agent_provider's
    per-agent lookup one level down — the web-research skill (T04)
    resolves credentials by a *fixed* Provider id, not by whichever
    agent happens to invoke it (ADR-022 point 3)."""
    state = _load_state()
    return next((p for p in state["providers"] if p["id"] == provider_id), None)


def get_agent_provider(agent_id: str) -> dict | None:
    state = _load_state()
    provider_id = state["assignments"].get(agent_id)
    if provider_id is None:
        return None
    return next((p for p in state["providers"] if p["id"] == provider_id), None)


def set_agent_provider(agent_id: str, provider_id: str) -> bool:
    state = _load_state()
    if not any(p["id"] == provider_id for p in state["providers"]):
        return False
    state["assignments"][agent_id] = provider_id
    vault_writer.save_providers_state(state)
    return True
