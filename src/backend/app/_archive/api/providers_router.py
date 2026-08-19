from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.business import agent_registry, provider_registry

router = APIRouter(prefix="/providers")


class ProviderCreateBody(BaseModel):
    name: str
    endpoint: str
    credential: str
    model: str


class ProviderUpdateBody(BaseModel):
    name: str | None = None
    endpoint: str | None = None
    credential: str | None = None
    model: str | None = None


def _blocked_removal_message(name: str, blocked_by_agent_ids: list[str]) -> str:
    names = [agent_registry.get_agent(aid)["name"] for aid in blocked_by_agent_ids]
    count = len(names)
    joined = ", ".join(names)
    return (
        f'Can\'t remove "{name}" — {count} agent{"s" if count != 1 else ""} '
        f'({joined}) currently {"select" if count != 1 else "selects"} this '
        "Provider. Switch every agent using it to a different Provider "
        "first, then try again."
    )


@router.get("")
def list_providers() -> list[dict]:
    # provider_registry.list_providers() never includes "credential" —
    # nothing to strip here (ADR-014 point 5).
    return provider_registry.list_providers()


@router.post("")
def create_provider(body: ProviderCreateBody) -> dict:
    provider_registry.create_provider(body.name, body.endpoint, body.credential, body.model)
    # Re-read via list_providers() rather than returning the raw created
    # dict, so the response never includes "credential" either.
    created = next(p for p in provider_registry.list_providers() if p["name"] == body.name)
    return created


@router.patch("/{provider_id}")
def update_provider(provider_id: str, body: ProviderUpdateBody) -> dict:
    updated = provider_registry.update_provider(
        provider_id,
        name=body.name,
        endpoint=body.endpoint,
        credential=body.credential,
        model=body.model,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Unknown provider")
    return next(p for p in provider_registry.list_providers() if p["id"] == provider_id)


@router.delete("/{provider_id}")
def remove_provider(provider_id: str) -> dict:
    providers_by_id = {p["id"]: p for p in provider_registry.list_providers()}
    provider = providers_by_id.get(provider_id)
    if provider is None:
        raise HTTPException(status_code=404, detail="Unknown provider")
    result = provider_registry.remove_provider(provider_id)
    if not result["deleted"]:
        raise HTTPException(
            status_code=409,
            detail=_blocked_removal_message(provider["name"], result["blocked_by_agent_ids"]),
        )
    return {"deleted": True}
