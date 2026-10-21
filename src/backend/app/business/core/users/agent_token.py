"""How a Hermes worker proves which agent it is (`REQ-SB-103`,
`ADR-062`).

**An agent is not a person, and this type exists so the app can never
confuse the two.** `REQ-SB-101` made every route default-deny against
an `Identity`, which carries a `User` and a `Role`. A worker given one
of those would be a person as far as every capability check, every
ledger record and every attribution block is concerned -- so "the
WhatsApp agent approved this" and "the Admin approved this" would be
the same sentence in the record. An `AgentCaller` is a separate type
for that reason, and nothing turns one into an `Identity`.

**It authenticates the agent id, which until now was merely claimed.**
`ADR-033` authorises an Action call against `caller_agent_id`, and
`call_action.py`'s own help text says it plainly: "the app believes the
id it is given." A token bound to one agent closes that: the body may
still name a caller, and the app refuses it unless it is the agent the
token is for.

**The plaintext is shown once and stored nowhere.** Only its SHA-256
is kept, exactly as a session token is, so the store cannot leak a
working credential even to someone who can read it.
"""
from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass

# A recognisable prefix, so a token that turns up in a log, a paste or a
# config file is identifiable as this install's agent credential at a
# glance -- and greppable when one has to be hunted down.
TOKEN_PREFIX = "sba_"
_TOKEN_ENTROPY_BYTES = 32


def mint_token_text() -> str:
    return TOKEN_PREFIX + secrets.token_urlsafe(_TOKEN_ENTROPY_BYTES)


def looks_like_an_agent_token(text: str) -> bool:
    """Whether a bearer value is meant for this table at all. Lets the
    reader tell an agent token from a person's session token WITHOUT a
    database lookup, so a worker's expired credential is never reported
    as "no such session" and a person's cookie is never looked up as an
    agent key."""
    return text.startswith(TOKEN_PREFIX)


def digest_of(token_text: str) -> str:
    return hashlib.sha256(token_text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class AgentCaller:
    """A verified machine caller: the agent a request proved it is.

    Deliberately NOT an `Identity`, and deliberately carrying no role.
    A route that needs a capability needs a person, and an
    `AgentCaller` reaching one must be refused rather than mapped onto
    some default role -- "what may this machine do" is answered by which
    routes accept an agent at all, not by giving it a rank among people.
    """

    agent_id: str
    token_sha256: str
    label: str = ""


@dataclass(frozen=True)
class AgentTokenRecord:
    """One issued credential, as the operator sees it. Never carries the
    token text: after the one moment it is shown, this install cannot
    produce it again, and a record that could would make "stored hashed"
    a claim rather than a fact."""

    token_sha256: str
    agent_id: str
    label: str
    created_at: str
    created_by: str
    last_seen_at: str | None
    revoked_at: str | None

    @property
    def is_revoked(self) -> bool:
        return bool(self.revoked_at)

    @property
    def has_ever_been_used(self) -> bool:
        """Shown to the operator as its own fact. A key issued and never
        used usually means it never reached the worker, which looks
        identical to "the agent is quiet" unless the app says which."""
        return bool(self.last_seen_at)
