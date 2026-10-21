"""The sole gateway onto the user store (REQ-SB-101) -- accounts, roles,
passwords and sessions. Nothing above `data_access` touches `users_db`
except through here, the same contract `OperatorProfileManager` keeps
over `data_access/operator_profile.py`.

**The last Admin cannot be disabled, demoted or deleted.** Not a policy
decision so much as the only protection against an install nobody can
administer: there is no console, no recovery flag and no second door.
Refused with a sentence that names what would have happened, the way
every other refusal in this codebase reads (MEMORY.md, 2026-10-17).

**A credential change ends the sessions it was true for.** Resetting a
password, changing a role or disabling an account all drop that user's
sessions. A role is read from the session's user row on every request,
so a live session would otherwise carry the OLD answer until it expired
-- and "I removed their access an hour ago" has to be true the moment it
is said.

**Sessions are opaque random tokens, not signed claims.** A JWT would
let the server skip a lookup and would also make revocation a lie: the
token stays valid until it expires however many times it is revoked.
This store is local and a lookup is a single indexed read, so there is
nothing to buy and a real property to lose.

**Timing.** A login for a username that does not exist still pays for a
hash, against the obvious oracle. `_UNKNOWN_USER_DIGEST` exists only to
be compared against and never matches anything.
"""
from __future__ import annotations

import hashlib
import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from app.business.core.users import password_hashing
from app.business.core.users.user import Identity, Role, User
from app.data_access import users_db

_logger = logging.getLogger(__name__)

# Rolling, not fixed (operator's choice, 2026-10-21): a session dies after
# this much INACTIVITY, and every authenticated request pushes it out again,
# so a long piece of work is never interrupted by the clock. There is
# deliberately no absolute cap on top: a tab left open and used once a day
# stays signed in indefinitely. That is the cost of the choice and it is
# written here rather than discovered -- add a `created_at + N` ceiling in
# `identity_for_token` if it ever stops being acceptable.
SESSION_IDLE_TIMEOUT = timedelta(hours=8)
_TOKEN_BYTES = 32

_UNKNOWN_USER_DIGEST, _UNKNOWN_USER_SALT, _UNKNOWN_USER_PARAMETERS = (
    password_hashing.hash_password(secrets.token_urlsafe(32))
)


class UserError(Exception):
    """A refusal the caller should see verbatim. Carries its own
    sentence; the router turns it into a 4xx without rewording it."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _user_from_row(row: dict) -> User:
    return User(
        id=row["id"],
        username=row["username"],
        display_name=row["display_name"],
        role=Role(row["role"]),
        is_disabled=bool(row["is_disabled"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        last_login_at=row["last_login_at"],
    )


class UserManager:
    def __init__(self, password_parameters: dict | None = None) -> None:
        """`password_parameters` exists so tests can hash at a cost that
        does not make a suite of fifty logins take half a minute. It is
        never set in the app."""
        self._password_parameters = password_parameters

    # -- the store itself -------------------------------------------------

    def initialise(self) -> None:
        users_db.initialise()

    def has_any_user(self) -> bool:
        """False means this install has never had an account and the
        first-Admin bootstrap is open. Deliberately distinct from "the
        database file is absent": a store whose users were all deleted
        is also unbootstrapped, and must be, or the install is bricked."""
        if not users_db.database_exists():
            return False
        return users_db.count_users() > 0

    # -- accounts ---------------------------------------------------------

    def create_user(
        self,
        username: str,
        password: str,
        role: Role,
        display_name: str = "",
    ) -> User:
        username = username.strip()
        if not username:
            raise UserError("A username is required.")
        if not password:
            raise UserError("A password is required.")
        self.initialise()
        if users_db.read_user_by_username(username) is not None:
            raise UserError(
                f"The username {username!r} is already taken; nothing was created."
            )
        digest, salt, parameters = password_hashing.hash_password(
            password, self._password_parameters
        )
        moment = _now()
        record = {
            "id": str(uuid.uuid4()),
            "username": username,
            "display_name": display_name.strip(),
            "role": Role(role).value,
            "password_digest": digest,
            "password_salt": salt,
            "password_params": parameters,
            "is_disabled": 0,
            "created_at": moment,
            "updated_at": moment,
            "last_login_at": None,
        }
        users_db.insert_user(record)
        return _user_from_row(record)

    def get_all(self) -> list[User]:
        if not users_db.database_exists():
            return []
        return [_user_from_row(row) for row in users_db.list_users()]

    def get_by_id(self, user_id: str) -> User | None:
        if not users_db.database_exists():
            return None
        row = users_db.read_user_by_id(user_id)
        return _user_from_row(row) if row else None

    def set_role(self, user_id: str, role: Role) -> User:
        user = self._require(user_id)
        if user.role == Role.ADMIN and role != Role.ADMIN:
            self._refuse_if_last_admin(user, "have its role changed")
        users_db.update_user_fields(
            user_id, {"role": Role(role).value, "updated_at": _now()}
        )
        users_db.delete_sessions_for_user(user_id)
        return self._require(user_id)

    def set_disabled(self, user_id: str, is_disabled: bool) -> User:
        user = self._require(user_id)
        if is_disabled and user.role == Role.ADMIN:
            self._refuse_if_last_admin(user, "be disabled")
        users_db.update_user_fields(
            user_id, {"is_disabled": 1 if is_disabled else 0, "updated_at": _now()}
        )
        if is_disabled:
            users_db.delete_sessions_for_user(user_id)
        return self._require(user_id)

    def set_password(self, user_id: str, password: str) -> None:
        if not password:
            raise UserError("A password is required.")
        self._require(user_id)
        digest, salt, parameters = password_hashing.hash_password(
            password, self._password_parameters
        )
        users_db.update_user_fields(
            user_id,
            {
                "password_digest": digest,
                "password_salt": salt,
                "password_params": parameters,
                "updated_at": _now(),
            },
        )
        users_db.delete_sessions_for_user(user_id)

    # -- a person acting on their own account ----------------------------

    def set_display_name(self, user_id: str, display_name: str) -> User:
        """The one field a person may change about themselves. The
        username is not: it is what they sign in with and what every
        attributed record names, so changing it is an Admin's decision
        about identity rather than a preference."""
        self._require(user_id)
        users_db.update_user_fields(
            user_id, {"display_name": display_name.strip(), "updated_at": _now()}
        )
        return self._require(user_id)

    def change_own_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str,
        keep_session_sha256: str,
    ) -> None:
        """Requires the current password, which `set_password` does not.

        An Admin resetting someone else's password has already proved
        who they are and is acting deliberately on another account. A
        self-service change is reached with nothing but a live session,
        so without this check a stolen session becomes a stolen account:
        whoever holds it sets a new password and the owner is locked out
        of their own install. The check is what keeps a session from
        being as good as a credential.

        Every OTHER session of this user ends; the one making the
        request survives. The reason to change a password is usually
        that someone else may hold a session, and signing the person out
        of the browser they just secured would punish the right move.
        """
        if not new_password:
            raise UserError("A new password is required.")
        row = users_db.read_user_by_id(user_id)
        if row is None:
            raise UserError(f"There is no user with id {user_id!r}.")
        if not password_hashing.verify_password(
            current_password, row["password_digest"], row["password_salt"], row["password_params"]
        ):
            raise UserError("That is not your current password; nothing was changed.")
        digest, salt, parameters = password_hashing.hash_password(
            new_password, self._password_parameters
        )
        users_db.update_user_fields(
            user_id,
            {
                "password_digest": digest,
                "password_salt": salt,
                "password_params": parameters,
                "updated_at": _now(),
            },
        )
        users_db.delete_sessions_for_user_except(user_id, keep_session_sha256)

    def delete_user(self, user_id: str) -> None:
        user = self._require(user_id)
        if user.role == Role.ADMIN:
            self._refuse_if_last_admin(user, "be deleted")
        users_db.delete_user(user_id)

    # -- signing in -------------------------------------------------------

    def authenticate(self, username: str, password: str) -> tuple[User, str]:
        """Returns the user and a fresh session token. Raises `UserError`
        with ONE message for every failure -- wrong name, wrong password,
        disabled account -- because distinguishing them tells an attacker
        which half they got right."""
        self.initialise()
        row = users_db.read_user_by_username(username.strip())
        if row is None:
            password_hashing.verify_password(
                password, _UNKNOWN_USER_DIGEST, _UNKNOWN_USER_SALT, _UNKNOWN_USER_PARAMETERS
            )
            raise UserError("That username and password do not match an active account.")
        correct = password_hashing.verify_password(
            password, row["password_digest"], row["password_salt"], row["password_params"]
        )
        if not correct or row["is_disabled"]:
            raise UserError("That username and password do not match an active account.")

        if password_hashing.needs_rehash(row["password_params"], self._password_parameters):
            digest, salt, parameters = password_hashing.hash_password(
                password, self._password_parameters
            )
            users_db.update_user_fields(
                row["id"],
                {"password_digest": digest, "password_salt": salt, "password_params": parameters},
            )
            _logger.info("Re-stored %s's password at the current cost", row["username"])

        moment = datetime.now(timezone.utc)
        users_db.update_user_fields(row["id"], {"last_login_at": moment.isoformat()})
        token = secrets.token_urlsafe(_TOKEN_BYTES)
        users_db.insert_session(
            {
                "token_sha256": _sha256(token),
                "user_id": row["id"],
                "created_at": moment.isoformat(),
                "expires_at": (moment + SESSION_IDLE_TIMEOUT).isoformat(),
                "last_seen_at": moment.isoformat(),
            }
        )
        return self._require(row["id"]), token

    def identity_for_token(self, token: str) -> Identity | None:
        """None for absent, unknown, expired, or belonging to a user who
        has since been disabled or deleted. An expired row is removed on
        the way past, so the table does not grow forever without a
        sweeper."""
        if not token or not users_db.database_exists():
            return None
        token_sha256 = _sha256(token)
        session = users_db.read_session(token_sha256)
        if session is None:
            return None
        moment = datetime.now(timezone.utc)
        if datetime.fromisoformat(session["expires_at"]) <= moment:
            users_db.delete_session(token_sha256)
            return None
        row = users_db.read_user_by_id(session["user_id"])
        if row is None or row["is_disabled"]:
            users_db.delete_session(token_sha256)
            return None
        users_db.touch_session(
            token_sha256,
            moment.isoformat(),
            (moment + SESSION_IDLE_TIMEOUT).isoformat(),
        )
        return Identity(user=_user_from_row(row), session_token_sha256=token_sha256)

    def sign_out(self, token: str) -> None:
        if token and users_db.database_exists():
            users_db.delete_session(_sha256(token))

    # -- internals --------------------------------------------------------

    def _require(self, user_id: str) -> User:
        user = self.get_by_id(user_id)
        if user is None:
            raise UserError(f"There is no user with id {user_id!r}.")
        return user

    def _refuse_if_last_admin(self, user: User, what_would_happen: str) -> None:
        other_admins = [
            candidate
            for candidate in self.get_all()
            if candidate.role == Role.ADMIN
            and not candidate.is_disabled
            and candidate.id != user.id
        ]
        if not other_admins:
            raise UserError(
                f"{user.username!r} is the only active Admin on this install, so it cannot "
                f"{what_would_happen}: nobody would be able to manage users, settings or "
                "plugins afterwards. Make another account an Admin first."
            )
