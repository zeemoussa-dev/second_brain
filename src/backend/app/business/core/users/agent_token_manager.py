"""The sole gateway onto agent credentials (`REQ-SB-103`, `ADR-062`).

Mints, resolves and revokes. Every rule about what a token means lives
here; `users_db.py` stores rows and interprets none of them.
"""
from __future__ import annotations

import hmac
import logging
from datetime import datetime, timezone

from app.business.core.users.agent_token import (
    AgentCaller,
    AgentTokenRecord,
    digest_of,
    looks_like_an_agent_token,
    mint_token_text,
)
from app.data_access import users_db

_logger = logging.getLogger(__name__)


class AgentTokenError(Exception):
    """Carries the sentence the caller reads. The router turns it into a
    status without rewording it."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _record_from_row(row: dict) -> AgentTokenRecord:
    return AgentTokenRecord(
        token_sha256=row["token_sha256"],
        agent_id=row["agent_id"],
        label=row.get("label") or "",
        created_at=row["created_at"],
        created_by=row.get("created_by") or "",
        last_seen_at=row.get("last_seen_at"),
        revoked_at=row.get("revoked_at"),
    )


class AgentTokenManager:
    def mint(self, agent_id: str, label: str = "", created_by: str = "") -> tuple[AgentTokenRecord, str]:
        """Issues one credential for one agent and answers
        `(record, the token text)`.

        **The text is returned here and never again.** Only its digest
        is stored, so this is the one moment it can be put into a
        worker's environment; an install that could show it later could
        also leak it later.

        An agent id is NOT checked against the live roster. A token is
        routinely issued for an agent before that agent is deployed --
        which is the normal order of a provisioning run -- and refusing
        it would make the credential depend on Hermes being reachable at
        the moment an Admin happens to click. An id that matches no
        agent simply never authorises anything, because the Action gate
        checks `allowed_callers` against the catalogue of its own.
        """
        agent_id = (agent_id or "").strip()
        if not agent_id:
            raise AgentTokenError(
                "a token is issued to one named agent, and this request named none. Nothing was "
                "issued: a credential belonging to nobody could not be revoked by anybody."
            )

        token_text = mint_token_text()
        record = {
            "token_sha256": digest_of(token_text),
            "agent_id": agent_id,
            "label": (label or "").strip(),
            "created_at": _now(),
            "created_by": created_by or "",
            "last_seen_at": None,
            "revoked_at": None,
        }
        users_db.insert_agent_token(record)
        return _record_from_row(record), token_text

    def caller_for_token(self, token_text: str) -> AgentCaller | None:
        """The agent this token proves, or `None`.

        `None` covers an unknown token, a revoked one and a value that
        is not an agent token at all. They are one answer on purpose:
        telling a caller which of the three it was is telling an
        attacker whether a guessed key exists.
        """
        if not token_text or not looks_like_an_agent_token(token_text):
            return None
        try:
            row = users_db.read_agent_token(digest_of(token_text))
        except Exception:
            # A broken store must refuse, not 500 every agent request.
            _logger.exception("Could not resolve an agent token")
            return None
        if row is None or row.get("revoked_at"):
            return None

        # Compared rather than trusted from the lookup: the digest is
        # the primary key, so a row can only come back on an exact
        # match, and this makes that an assertion instead of an
        # assumption about SQLite's comparison rules.
        if not hmac.compare_digest(row["token_sha256"], digest_of(token_text)):
            return None

        self._note_it_was_used(row)
        return AgentCaller(
            agent_id=row["agent_id"],
            token_sha256=row["token_sha256"],
            label=row.get("label") or "",
        )

    def _note_it_was_used(self, row: dict) -> None:
        """Last-seen, written on every call and failing quietly.

        Quietly is deliberate and is the opposite of the rule elsewhere
        in this app: this is bookkeeping for the operator's benefit, and
        an unwritable column must not be the reason an agent cannot
        reach the app. It is logged, so a store that stopped accepting
        writes is still visible.
        """
        try:
            users_db.touch_agent_token(row["token_sha256"], _now())
        except Exception:
            _logger.warning(
                "could not record that agent token for %r was used", row.get("agent_id"),
                exc_info=True,
            )

    def get_all(self) -> list[AgentTokenRecord]:
        return [_record_from_row(row) for row in users_db.list_agent_tokens()]

    def revoke(self, token_sha256: str) -> AgentTokenRecord:
        """Dated, not deleted. Revoking twice is refused rather than
        reported as success: "it was already revoked, on this date" is
        the answer the second caller actually needs."""
        row = users_db.read_agent_token(token_sha256)
        if row is None:
            raise AgentTokenError(
                f"this install has issued no agent token {token_sha256!r}, so nothing was revoked"
            )
        if row.get("revoked_at"):
            raise AgentTokenError(
                f"the token for agent {row['agent_id']!r} was already revoked on "
                f"{row['revoked_at']}, and nothing was changed"
            )
        users_db.revoke_agent_token(token_sha256, _now())
        return _record_from_row(users_db.read_agent_token(token_sha256) or row)
