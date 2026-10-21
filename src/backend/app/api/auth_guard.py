"""Default-deny authentication for every route in the app (REQ-SB-101).

**Middleware, not a dependency on each route, for two reasons.** The
first is that a guard you have to remember is a guard that gets
forgotten: 26 routers exist today, the pipeline adds more most weeks, and
four escalations in the week before this was written were each caused by
a new thing needing a line in a file nobody's task listed. The second is
decisive on its own -- **plugin routers are mounted at runtime**
(`main.py`'s lifespan, `ADR-022`), so a decorator in this repository
cannot reach them. Middleware runs before routing and covers a plugin's
routes without the plugin's author doing anything.

**Deny is the default and the list is of what is open**, never the other
way round. A new route is protected the moment it exists; making one
public is a deliberate edit here, visible in a diff, with a reason beside
it.

**Two layers, deliberately.** This middleware answers "who is calling",
and refuses an unauthenticated caller. It does NOT decide what that
caller may do -- that is `requires()`, a per-route dependency naming the
capability, because the capability varies by route and the identity does
not. A route with no `requires()` is reachable by any signed-in person,
which is the right default for reading and the wrong one for acting;
`test_route_capabilities.py` is what holds the second half honest.

**The chicken and egg of a fresh install.** Setup and the first-Admin
bootstrap cannot require a sign-in, because on a new machine there is
nobody to sign in as. So while the user store holds NO users, the setup
routes and the bootstrap route are open; the moment one account exists
they close and need `MANAGE_SETTINGS` and a sign-in respectively. The
consequence is worth stating plainly rather than discovering: on a fresh
install, whoever reaches the port first can claim the first Admin. That
is true of every self-hosted first-run flow and is the reason the window
is closed by the first account rather than by a timer.
"""
from __future__ import annotations

import logging

from fastapi import Depends, HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.business.core.users.user import Capability, Identity
from app.business.core.users.user_manager import UserManager

_logger = logging.getLogger(__name__)

SESSION_COOKIE = "second_brain_session"

# Always open, signed in or not. Each entry earns its place:
#   /health      -- liveness, read by tooling that has no account
#   /boot-status -- the boot screen renders before anything else exists
#   /auth/...    -- sign in, sign out, and "who am I"; the door itself
_ALWAYS_PUBLIC_EXACT = frozenset({"/health"})
_ALWAYS_PUBLIC_PREFIXES = ("/boot-status", "/auth/")

# Open only while the install has no users at all (see the docstring).
_UNBOOTSTRAPPED_ONLY_PREFIXES = ("/setup",)


def _is_always_public(path: str) -> bool:
    return path in _ALWAYS_PUBLIC_EXACT or path.startswith(_ALWAYS_PUBLIC_PREFIXES)


def _is_open_while_unbootstrapped(path: str) -> bool:
    return path.startswith(_UNBOOTSTRAPPED_ONLY_PREFIXES)


class _AuthenticationReader:
    """Turns a request into an `Identity`, or into None. Shared by the
    middleware and by `identity_from_request`, so the two can never
    disagree about what counts as signed in -- which they would, as two
    copies, the first time one of them learned about a new header."""

    def __init__(self, user_manager: UserManager | None = None) -> None:
        self._users = user_manager or UserManager()

    def identity_for(self, request: Request) -> Identity | None:
        token = request.cookies.get(SESSION_COOKIE)
        if not token:
            # A non-browser caller (a script, a Hermes worker) sends the
            # same token as a bearer header rather than a cookie.
            header = request.headers.get("authorization", "")
            if header.lower().startswith("bearer "):
                token = header[7:].strip()
        if not token:
            return None
        try:
            return self._users.identity_for_token(token)
        except Exception:
            # A broken user store must not become a 500 on every route
            # in the app. Refusing is correct and recoverable; crashing
            # the request pipeline is neither.
            _logger.exception("Could not resolve a session token")
            return None

    def has_any_user(self) -> bool:
        try:
            return self._users.has_any_user()
        except Exception:
            # Fail CLOSED: if we cannot tell whether the install is
            # bootstrapped, assume it is, so an unreadable store never
            # re-opens the setup routes to an anonymous caller.
            _logger.exception("Could not tell whether this install has any user")
            return True


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Attaches `request.state.identity` for a signed-in caller and
    refuses everyone else with 401 before the route runs.

    `request.state.identity` is always set -- to `None` for a public
    route reached without a session -- so a route handler never has to
    ask whether the attribute exists."""

    def __init__(self, app, user_manager: UserManager | None = None) -> None:
        super().__init__(app)
        self._reader = _AuthenticationReader(user_manager)

    async def dispatch(self, request: Request, call_next):
        # A CORS preflight carries no cookie by design and must be
        # answered, or the browser never sends the real request and the
        # failure looks like CORS rather than auth.
        if request.method == "OPTIONS":
            return await call_next(request)

        identity = self._reader.identity_for(request)
        request.state.identity = identity

        if identity is not None or _is_always_public(request.url.path):
            return await call_next(request)

        if _is_open_while_unbootstrapped(request.url.path) and not self._reader.has_any_user():
            return await call_next(request)

        return JSONResponse(
            status_code=401,
            content={
                "detail": "You are not signed in. Sign in to use Second Brain.",
                "reason": "not_authenticated",
            },
        )


def identity_from_request(request: Request) -> Identity | None:
    """Resolves the caller from the request itself when the middleware
    has not already done it.

    The dependency below could just read `request.state`, and does when
    it is set -- but then it would silently answer "nobody" wherever the
    middleware is not installed, which is both the window while this
    feature is being built and any test that mounts one router alone. A
    guard whose correctness depends on middleware ordering is a guard
    that fails quietly, so this makes the dependency self-sufficient and
    the middleware an optimisation plus the default-deny sweep, rather
    than the only thing that works.
    """
    cached = getattr(request.state, "identity", None)
    if cached is not None:
        return cached
    return _AuthenticationReader().identity_for(request)


def current_identity(request: Request) -> Identity:
    """The signed-in caller, for a route that needs to know who it is
    acting for. Raises 401 on a public route reached anonymously, so a
    handler can depend on this and never receive `None`."""
    identity = identity_from_request(request)
    if identity is None:
        raise HTTPException(
            status_code=401,
            detail="You are not signed in. Sign in to use Second Brain.",
        )
    return identity


def optional_identity(request: Request) -> Identity | None:
    """For the handful of routes that answer differently when signed in
    but do not require it.

    Goes through `identity_from_request` for the same reason
    `current_identity` does, and this is not hypothetical: reading
    `request.state` directly made `GET /auth/state` report
    `signed_in: false` immediately after a successful bootstrap that had
    just set the cookie, because the middleware is not installed yet.
    Two accessors, one of them middleware-dependent, is exactly the
    quiet disagreement the shared reader exists to prevent.
    """
    return identity_from_request(request)


def requires(capability: Capability):
    """A dependency that refuses a caller whose role does not carry
    `capability`, with a sentence naming what was required -- the house
    rule that a refusal explains itself (`MEMORY.md`, 2026-10-17), and
    the difference between "this is broken" and "ask an Admin".

        @router.post("", dependencies=[Depends(requires(Capability.MANAGE_PLUGINS))])

    403, not 404: hiding a route's existence from someone who is signed
    in buys nothing here -- the screens are in the same bundle for
    everyone -- and costs the person any way of understanding why.
    """

    def dependency(identity: Identity = Depends(current_identity)) -> Identity:
        if not identity.may(capability):
            raise HTTPException(
                status_code=403,
                detail=(
                    f"This needs the {capability.value!r} capability, which the "
                    f"{identity.user.role.value!r} role does not have. Ask an Admin."
                ),
            )
        return identity

    return dependency
