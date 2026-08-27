from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.business import vault_entities, vault_index_config, vault_indexing, vault_templates

router = APIRouter(prefix="/vault")


@router.get("/overview")
def get_overview() -> dict:
    return vault_indexing.get_overview()


@router.get("/index-config")
def get_index_config() -> dict:
    return vault_index_config.get_index_config()


class UpdateIndexConfigBody(BaseModel):
    included: bool


@router.patch("/index-config/{folder_name}")
def update_index_config(folder_name: str, body: UpdateIndexConfigBody) -> dict:
    return vault_index_config.set_folder_included(folder_name, body.included)


@router.get("/templates")
def list_templates() -> dict:
    return {"templates": vault_templates.list_templates()}


@router.get("/entities")
def list_entities() -> dict:
    return {"entities": vault_entities.list_entities()}


class CreateEntityBody(BaseModel):
    name: str
    section: str
    domain: str = ""
    aliases: str = ""
    affiliate_of: str = ""


@router.post("/entities")
def create_entity(body: CreateEntityBody) -> dict:
    try:
        return vault_entities.create_entity(body.name, body.section, body.domain, body.aliases, body.affiliate_of)
    except vault_entities.DuplicateEntityError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


class UpdateEntityBody(BaseModel):
    name: str | None = None
    section: str | None = None
    aliases: str | None = None
    affiliate_of: str | None = None
    domain: str | None = None
    ignore: bool | None = None


@router.patch("/entities/{name}")
def update_entity(name: str, body: UpdateEntityBody) -> dict:
    try:
        return vault_entities.update_entity(name, body.model_dump(exclude_none=True))
    except vault_entities.EntityNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except vault_entities.DuplicateEntityError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.delete("/entities/{name}")
def delete_entity(name: str) -> dict:
    try:
        vault_entities.delete_entity(name)
    except vault_entities.EntityNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"deleted": True}
