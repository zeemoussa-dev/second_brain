"""Signing in, signing out, and the first-Admin bootstrap (REQ-SB-101).

Every route here is public by necessity -- this is the door, and a door
that needs a key to reach is not a door. `auth_guard` lets `/auth/`
through unconditionally, which is why nothing in this module may do
anything a signed-out caller should not be able to do. The one route
that creates an account, `POST /auth/bootstrap`, guards itself on the
store being empty and is the only exception.

**The session is an httponly cookie.** Not a token the frontend keeps in
`localStorage`: anything a plugin's screen can read, a plugin's screen
can exfiltrate, and this install runs third-party plugin code in the same
page (`ADR-022`). `httponly` puts the session out of reach of every
script on the page, including ours.

**`samesite=lax`, and `secure` only when the request arrived over TLS.**
Hard-coding `secure=True` today would break the operator's own
`http://localhost:5173` sign-in; hard-coding it False would keep the
cookie insecure after the move to Azure. Deriving it from the request is
the one form that is correct in both places.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

from app.api.auth_guard import SESSION_COOKIE, current_identity, optional_identity
from app.business.core.users.user import Identity, Role
from app.business.core.users.user_manager import UserError, UserManager

router = APIRouter(prefix="/auth", tags=["auth"])


class SignInBody(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class BootstrapBody(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=8)
    display_name: str = ""


def _user_response(identity: Identity) -> dict:
    user = identity.user
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "role": user.role.value,
        "capabilities": sorted(capability.value for capability in user.capabilities),
        "last_login_at": user.last_login_at,
    }


def _set_session_cookie(response: Response, request: Request, token: str) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,
        samesite="lax",
        secure=request.url.scheme == "https",
        path="/",
    )


@router.get("/state")
def authentication_state(request: Request) -> dict:
    """What the app needs before it can decide which screen to show, and
    the only route that answers usefully to a signed-out caller.

    `needs_bootstrap` is deliberately separate from `signed_in`: a fresh
    install is not "signed out", it is "has nobody to sign in as", and
    collapsing the two would send a new operator to a login form they
    cannot possibly satisfy.
    """
    users = UserManager()
    identity = optional_identity(request)
    return {
        "needs_bootstrap": not users.has_any_user(),
        "signed_in": identity is not None,
        "user": _user_response(identity) if identity else None,
    }


@router.post("/bootstrap")
def bootstrap_first_admin(body: BootstrapBody, request: Request, response: Response) -> dict:
    """Creates the first Admin on an install that has none, and signs
    them in. Refuses the moment any account exists -- this is not a way
    to add users, and leaving it open would be a way to add an Admin
    without being one.

    The check and the create are not atomic, which is a real race on
    paper: two simultaneous callers could both see an empty store. The
    unique index on `username` means they cannot both become the same
    account, and the window exists only on an install with no users at
    all -- it is written down here rather than defended with a lock,
    because a lock across two processes is a bigger mechanism than the
    risk it would remove.
    """
    users = UserManager()
    if users.has_any_user():
        raise HTTPException(
            status_code=409,
            detail=(
                "This install already has at least one account, so the first-Admin "
                "setup is closed. Ask an Admin to create your user."
            ),
        )
    try:
        users.create_user(body.username, body.password, Role.ADMIN, body.display_name)
        user, token = users.authenticate(body.username, body.password)
    except UserError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _set_session_cookie(response, request, token)
    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "role": user.role.value,
        }
    }


@router.post("/sign-in")
def sign_in(body: SignInBody, request: Request, response: Response) -> dict:
    users = UserManager()
    try:
        user, token = users.authenticate(body.username, body.password)
    except UserError as exc:
        # 401, and the Manager's single sentence verbatim: it says the
        # same thing for a wrong name, a wrong password and a disabled
        # account on purpose, and rewording it here per case would undo
        # that.
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    _set_session_cookie(response, request, token)
    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "role": user.role.value,
            "capabilities": sorted(capability.value for capability in user.capabilities),
        }
    }


@router.post("/sign-out")
def sign_out(request: Request, response: Response) -> dict:
    """Ends the session server-side, not only in the browser. Deleting
    the cookie alone would leave a token that still works for anyone who
    captured it."""
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        UserManager().sign_out(token)
    response.delete_cookie(SESSION_COOKIE, path="/")
    return {"signed_out": True}


@router.get("/me")
def who_am_i(identity: Identity = Depends(current_identity)) -> dict:
    return _user_response(identity)


class UpdateMeBody(BaseModel):
    display_name: str


class ChangeMyPasswordBody(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8)


@router.put("/me")
def update_me(body: UpdateMeBody, identity: Identity = Depends(current_identity)) -> dict:
    """The display name, and only that.

    The username is deliberately not editable here: it is what the person
    signs in with and what every attributed record will name, so changing
    it is an Admin's decision about identity rather than a preference.
    The role is not editable for the obvious reason.

    Note these `/auth/me` routes are reachable because the middleware lets
    all of `/auth/` through -- they are guarded by `current_identity`
    alone, which is why it is declared on each one rather than assumed.
    """
    try:
        user = UserManager().set_display_name(identity.user.id, body.display_name)
    except UserError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "role": user.role.value,
    }


@router.put("/me/password")
def change_my_password(
    body: ChangeMyPasswordBody,
    request: Request,
    identity: Identity = Depends(current_identity),
) -> dict:
    """Changing your own password needs your current one, which an
    Admin's reset of someone else's does not: a self-service change is
    reached with nothing but a live session, so without the check a
    stolen session becomes a stolen account.

    Every other session of yours ends; the one you are using survives.
    """
    token = request.cookies.get(SESSION_COOKIE) or ""
    try:
        UserManager().change_own_password(
            identity.user.id,
            body.current_password,
            body.new_password,
            identity.session_token_sha256 if token else "",
        )
    except UserError as exc:
        # 400, not 401: the caller IS authenticated. A 401 would tell the
        # frontend the session had ended and bounce them to sign-in,
        # losing a form they only mistyped one field of.
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"password_changed": True}
