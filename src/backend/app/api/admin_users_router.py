"""The Admin Center's API -- create a user, set a role, reset a
password, disable an account, delete one (REQ-SB-101).

Every route requires `MANAGE_USERS`, declared once on the router rather
than repeated per route, so a route added here is guarded by existing
rather than by its author remembering. That is the same reasoning as
`auth_guard`'s middleware, one level down.

**No route here returns or accepts a password digest.** `User` cannot
carry one (see `user.py`), so a handler that returned the entity
directly still could not leak a credential. Setting a password is a
route of its own that takes a plaintext, uses it once, and returns
nothing.

**The last-Admin protection lives in the Manager, not here.** A refusal
that only exists at the HTTP layer is a refusal a script gets to skip;
this router's job is to turn the Manager's sentence into a 409 without
rewording it.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.auth_guard import current_identity, requires
from app.business.core.users.user import Capability, Identity, Role, User
from app.business.core.users.user_manager import UserError, UserManager

router = APIRouter(
    prefix="/admin/users",
    tags=["admin"],
    dependencies=[Depends(requires(Capability.MANAGE_USERS))],
)


class CreateUserBody(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=8)
    role: Role
    display_name: str = ""


class SetRoleBody(BaseModel):
    role: Role


class SetDisabledBody(BaseModel):
    is_disabled: bool


class SetPasswordBody(BaseModel):
    password: str = Field(min_length=8)


def _as_dict(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "role": user.role.value,
        "is_disabled": user.is_disabled,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "last_login_at": user.last_login_at,
    }


def _refusal(exc: UserError) -> HTTPException:
    """409 and the Manager's own words. The sentences it raises name
    what would have happened and what to do instead, and an Admin
    reading "that is the only active Admin" needs exactly that, not
    "Conflict"."""
    return HTTPException(status_code=409, detail=str(exc))


@router.get("")
def list_users() -> list[dict]:
    """Disabled accounts included -- the Admin Center is the one place
    they have to be visible, since re-enabling one is impossible if it
    cannot be seen."""
    return [_as_dict(user) for user in UserManager().get_all()]


@router.post("", status_code=201)
def create_user(body: CreateUserBody) -> dict:
    try:
        user = UserManager().create_user(
            body.username, body.password, body.role, body.display_name
        )
    except UserError as exc:
        raise _refusal(exc) from exc
    return _as_dict(user)


@router.put("/{user_id}/role")
def set_role(user_id: str, body: SetRoleBody) -> dict:
    try:
        return _as_dict(UserManager().set_role(user_id, body.role))
    except UserError as exc:
        raise _refusal(exc) from exc


@router.put("/{user_id}/disabled")
def set_disabled(
    user_id: str,
    body: SetDisabledBody,
    identity: Identity = Depends(current_identity),
) -> dict:
    """An Admin disabling themselves is refused separately from the
    last-Admin rule: with two Admins the Manager allows it, and the
    person would be signed out mid-click by their own action with no
    way back in except the other Admin. Refusing is kinder than
    explaining."""
    if body.is_disabled and user_id == identity.user.id:
        raise HTTPException(
            status_code=409,
            detail=(
                "You cannot disable your own account: you would be signed out "
                "immediately and would need another Admin to let you back in."
            ),
        )
    try:
        return _as_dict(UserManager().set_disabled(user_id, body.is_disabled))
    except UserError as exc:
        raise _refusal(exc) from exc


@router.put("/{user_id}/password")
def set_password(user_id: str, body: SetPasswordBody) -> dict:
    """Returns nothing about the password, and ends that user's
    sessions (the Manager does it): a reset exists precisely for the
    case where someone else may be holding one."""
    try:
        UserManager().set_password(user_id, body.password)
    except UserError as exc:
        raise _refusal(exc) from exc
    return {"password_set": True}


@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: str, identity: Identity = Depends(current_identity)) -> None:
    if user_id == identity.user.id:
        raise HTTPException(
            status_code=409,
            detail="You cannot delete your own account while signed in as it.",
        )
    try:
        UserManager().delete_user(user_id)
    except UserError as exc:
        raise _refusal(exc) from exc
