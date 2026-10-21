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

import hmac
import logging
import re
import secrets

from fastapi import Depends, HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.business.core.users.agent_token import AgentCaller, looks_like_an_agent_token
from app.business.core.users.agent_token_manager import AgentTokenManager
from app.business.core.users.user import Capability, Identity
from app.business.core.users.user_manager import UserManager

_logger = logging.getLogger(__name__)

SESSION_COOKIE = "second_brain_session"


def _bearer_or_cookie(request: Request) -> str:
    """The credential this request carries, whatever kind it is. One
    reader for both so a person's cookie and a worker's bearer header
    cannot drift into being read by different rules."""
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        return token
    # A non-browser caller (a script, a Hermes worker) sends its
    # credential as a bearer header rather than a cookie.
    header = request.headers.get("authorization", "")
    if header.lower().startswith("bearer "):
        return header[7:].strip()
    return ""

# The Action gate performs an `http` implementation by calling THIS app
# in process (`action_invocation._request_this_apps_own_route`), which
# runs the real middleware stack -- so default-deny refused the app's
# own dispatch and every `http` Action answered "the operation did NOT
# happen" on any install with an account (`ESC-081`, found by
# `REQ-SB-95-US-05-T05` on 2026-10-21, introduced by this file on
# 2026-10-19).
#
# The marker is a random value minted once per process and never
# written anywhere: not a config value, not a setting, not on disk. A
# caller on a socket cannot know it, and it changes every restart, so
# it authenticates "this request was constructed inside this process"
# and nothing else.
#
# It says the request is INTERNAL, not that it is privileged. The
# dispatch is only reached after the Action gate has already checked
# `allowed_callers`, the declared inputs and any confirmation, so the
# authorisation has happened -- one layer up, against the agent, where
# `ADR-033` puts it. A route behind `requires()` still refuses, because
# a capability is about a person and this sub-request has none; an
# Action naming such a route SHOULD be refused rather than quietly run
# with more authority than its caller.
INTERNAL_DISPATCH_HEADER = "x-second-brain-internal-dispatch"
INTERNAL_DISPATCH_TOKEN = secrets.token_urlsafe(32)


def is_internal_dispatch(request: Request) -> bool:
    sent = request.headers.get(INTERNAL_DISPATCH_HEADER, "")
    return bool(sent) and hmac.compare_digest(sent, INTERNAL_DISPATCH_TOKEN)

# Always open, signed in or not. Each entry earns its place:
#   /health      -- liveness, read by tooling that has no account
#   /boot-status -- the boot screen renders before anything else exists
#   /auth/...    -- sign in, sign out, and "who am I"; the door itself
_ALWAYS_PUBLIC_EXACT = frozenset({"/health"})
#   /branding    -- the sign-in screen renders this install's own name
#                   and logo, so a caller who cannot read it cannot be
#                   shown the door they are meant to come through. It is
#                   deliberately the ONLY thing an anonymous caller
#                   learns about this install, and it is what the
#                   operator chose to show.
_ALWAYS_PUBLIC_PREFIXES = ("/boot-status", "/auth/", "/branding")

# Open only while the install has no users at all (see the docstring).
_UNBOOTSTRAPPED_ONLY_PREFIXES = ("/setup",)

# What a Hermes worker may CHANGE (`REQ-SB-103`, `ADR-062`). Reads are
# open to an authenticated agent -- serving what this install knows is
# what the agents are for -- but a write matches a pattern here or it
# is refused.
#
# **Exact patterns, not prefixes, and that is load-bearing.** `POST
# /actions` creates an Action and `PUT /actions/{id}` edits one, and
# NEITHER carries a `requires()` today (see the note below), so a
# prefix of `/actions/` would have handed every worker the ability to
# author the very catalogue that bounds it. A pattern that names the
# route cannot acquire a new meaning because a new route was added
# beside it.
#
# Each entry earns its place:
#   POST /actions/{id}/call        -- the Action gate itself.
#       `allowed_callers`, the declared inputs and the confirmation
#       rule all still apply; `ADR-033` decides what this agent may
#       actually call, and this only decides that it may ask.
#   POST /workflows/{id}/run
#   POST /workflows/runs/{id}/next-step
#   POST /workflows/runs/{id}/steps/{id}/outcome
#       -- stepping through documented handling, which is the one thing
#       a Workflow is for.
#   POST /workflows/runs/{id}/steps/{id}/answer
#       -- relaying what a PERSON said. The route resolves WHO from the
#       door it came through; an agent cannot name a person.
#
# Deliberately absent: confirming or declining an Action call
# (`/actions/calls/{id}/confirm`). That is the operator answering, and
# an agent that could confirm its own pending call would be the whole
# gate undone. It is left out by not being listed, which is why the
# list is of what is allowed.
_AGENT_MAY_WRITE = (
    re.compile(r"^/actions/[^/]+/call$"),
    re.compile(r"^/workflows/[^/]+/run$"),
    re.compile(r"^/workflows/runs/[^/]+/next-step$"),
    re.compile(r"^/workflows/runs/[^/]+/steps/[^/]+/outcome$"),
    re.compile(r"^/workflows/runs/[^/]+/steps/[^/]+/answer$"),
)
_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


def _an_agent_may_write_here(path: str) -> bool:
    return any(pattern.match(path) for pattern in _AGENT_MAY_WRITE)


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
        self._agent_tokens = AgentTokenManager()

    def identity_for(self, request: Request) -> Identity | None:
        token = _bearer_or_cookie(request)
        if not token:
            return None
        if looks_like_an_agent_token(token):
            # An agent's credential, which is NOT a person and must not
            # be looked up as one. Returning None here is what keeps
            # `requires()` closed to a worker: a capability is about a
            # person, and a machine holding a key has none.
            return None
        try:
            return self._users.identity_for_token(token)
        except Exception:
            # A broken user store must not become a 500 on every route
            # in the app. Refusing is correct and recoverable; crashing
            # the request pipeline is neither.
            _logger.exception("Could not resolve a session token")
            return None

    def agent_caller_for(self, request: Request) -> AgentCaller | None:
        """The agent a request proved it is, or None. Separate from
        `identity_for` and never merged with it: the whole value of this
        type is that it cannot be mistaken for a person."""
        token = _bearer_or_cookie(request)
        if not token or not looks_like_an_agent_token(token):
            return None
        return self._agent_tokens.caller_for_token(token)

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
        request.state.agent_caller = None

        if identity is not None or _is_always_public(request.url.path):
            return await call_next(request)

        # A Hermes worker, holding a credential bound to one agent
        # (`REQ-SB-103`). It is not a person and never becomes one:
        # `request.state.identity` stays None, so every `requires()`
        # route still refuses it.
        agent_caller = self._reader.agent_caller_for(request)
        if agent_caller is not None:
            request.state.agent_caller = agent_caller
            if request.method in _SAFE_METHODS or _an_agent_may_write_here(request.url.path):
                return await call_next(request)
            return JSONResponse(
                status_code=403,
                content={
                    "detail": (
                        f"Agent {agent_caller.agent_id!r} is authenticated, but this app does "
                        f"not accept {request.method} {request.url.path} from an agent. An agent "
                        "reads what this install knows and acts through the Action gate and "
                        "documented Workflows; everything else is a person's to do."
                    ),
                    "reason": "not_for_agents",
                },
            )

        # The app calling itself to perform an `http` Action (ESC-081).
        # Authorisation already happened at the Action gate, one layer
        # up and against the agent; this only says the request was
        # built inside this process.
        if is_internal_dispatch(request):
            return await call_next(request)

        if _is_open_while_unbootstrapped(request.url.path) and not self._reader.has_any_user():
            return await call_next(request)

        return JSONResponse(
            status_code=401,
            content={
                "detail": "You are not signed in. Sign in to continue.",
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


def agent_caller_from_request(request: Request) -> AgentCaller | None:
    """The agent a request proved it is, resolved from the request
    itself when the middleware has not already done it -- the same
    self-sufficiency `identity_from_request` has, for the same reason: a
    guard whose correctness depends on middleware ordering is a guard
    that fails quietly."""
    cached = getattr(request.state, "agent_caller", None)
    if cached is not None:
        return cached
    return _AuthenticationReader().agent_caller_for(request)


def optional_agent_caller(request: Request) -> AgentCaller | None:
    """For a route that serves both a person and a worker and answers
    differently. The route decides; this only reports."""
    return agent_caller_from_request(request)


def the_agent_really_calling(request: Request, claimed_agent_id: str) -> str:
    """Which agent a call is really from (`REQ-SB-103`).

    `ADR-033` authorises an Action call against `caller_agent_id`, and
    until now that id was simply **claimed**: `call_action.py`'s own
    help text said "the app believes the id it is given". A worker
    holding a token for one agent must not be able to act as another by
    typing a different id, or the token buys nothing.

    So: from an agent, the token decides, and a body naming a different
    agent is refused rather than silently corrected -- a caller that
    asked to act as somebody else has either a bug or an intention, and
    quietly doing something else would hide both.

    From a PERSON, the claim stands. An operator driving the app names
    the agent they are acting for, the gate still checks
    `allowed_callers`, and nothing about that changes here.
    """
    agent = agent_caller_from_request(request)
    if agent is None:
        return claimed_agent_id
    claimed = (claimed_agent_id or "").strip()
    if claimed and claimed != agent.agent_id:
        raise HTTPException(
            status_code=403,
            detail=(
                f"this credential is for agent {agent.agent_id!r}, and this call named "
                f"{claimed!r} as its caller. Nothing was performed. An agent acts as itself; "
                "if this worker really is both, it needs the other agent's own token."
            ),
        )
    return agent.agent_id


def current_identity(request: Request) -> Identity:
    """The signed-in caller, for a route that needs to know who it is
    acting for. Raises 401 on a public route reached anonymously, so a
    handler can depend on this and never receive `None`."""
    identity = identity_from_request(request)
    if identity is None:
        raise HTTPException(
            status_code=401,
            detail="You are not signed in. Sign in to continue.",
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
