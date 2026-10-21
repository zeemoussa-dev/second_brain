"""Raw data access for the user store -- the first SQLite database in a
codebase that is otherwise entirely files (ADR-003's api -> business ->
data_access layering; see ADR-041 for why a database rather than JSON).

Location: `<SECOND_BRAIN_DATA_PATH>/auth/users.db`, the operator's config
folder (REQ-SB-101, operator's instruction 2026-10-21). Its own top-level
`auth/` child rather than a file loose in the root, so excluding it from
anything that sweeps that folder is one directory name, not a filename
pattern that a second file would escape.

Zero business interpretation here, the same contract every other module in
this package keeps: no password is hashed here, no role is validated here,
no session is judged expired here, and "disabled" is an integer column
this module neither sets nor consults. UserManager owns all of that.
Applying any of it here would make the answer depend on which door the
read came through.

**Two things this module stores deliberately hashed, and never in the
clear.** A password is written as a digest plus its salt and the KDF
parameters that produced it -- this module never sees a plaintext
password, because `password_hashing.py` runs before it. A session is
keyed by the SHA-256 of its token, never the token: whoever holds the
database can then invalidate a session but cannot become its owner, which
is the whole difference between a stolen backup and a stolen login.

**Timestamps are ISO-8601 UTC strings, not SQLite dates.** The rest of
this codebase reads and writes ISO strings everywhere (frontmatter,
Action ledger, Workflow runs) and `capture_freshness._parsed` is the
house convention for reading them back. A TEXT column keeps the database
honest about what it holds and keeps the vault and the database speaking
the same format.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.config import settings

_AUTH_SUBPATH = ("auth", "users.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id              TEXT PRIMARY KEY,
    username        TEXT NOT NULL UNIQUE COLLATE NOCASE,
    display_name    TEXT NOT NULL DEFAULT '',
    role            TEXT NOT NULL,
    password_digest BLOB NOT NULL,
    password_salt   BLOB NOT NULL,
    password_params TEXT NOT NULL,
    is_disabled     INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    last_login_at   TEXT
);

CREATE TABLE IF NOT EXISTS sessions (
    token_sha256 TEXT PRIMARY KEY,
    user_id      TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at   TEXT NOT NULL,
    expires_at   TEXT NOT NULL,
    last_seen_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS sessions_by_user ON sessions(user_id);
"""


def users_db_path() -> Path:
    return settings.second_brain_data_path.joinpath(*_AUTH_SUBPATH)


def database_exists() -> bool:
    """Whether this install has ever had a user store. The Manager needs
    this to tell "no users yet, bootstrap the first Admin" from "a store
    with every account disabled" -- two states an empty table and an
    absent file would otherwise collapse into one."""
    return users_db_path().is_file()


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    """One connection per operation, committed on a clean exit and rolled
    back on any exception. Not a pool and not a module-level singleton:
    the one place a long-lived connection would help is also the one place
    it would keep a file handle open across a data-path move, which
    `system_settings.py` performs while the app is running.

    `foreign_keys` is ON per connection because SQLite defaults it OFF --
    without it the sessions -> users cascade silently does nothing, and
    deleting a user would leave their sessions valid.
    """
    path = users_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, isolation_level=None)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("BEGIN")
        yield connection
        connection.execute("COMMIT")
    except BaseException:
        connection.execute("ROLLBACK")
        raise
    finally:
        connection.close()


def initialise() -> None:
    """Creates the schema if it is absent. Safe to call on every boot:
    every statement is `IF NOT EXISTS`, and it is deliberately NOT a
    migration runner -- when a column has to change, that is a real
    schema version and a real decision, not something a boot call does
    quietly to the operator's accounts.

    The statements are executed one at a time rather than through
    `executescript`, which issues its own COMMIT before it runs and so
    ends the transaction `connect` opened -- leaving `connect`'s own
    COMMIT to fail with "cannot commit - no transaction is active".
    """
    with connect() as connection:
        for statement in filter(None, (part.strip() for part in _SCHEMA.split(";"))):
            connection.execute(statement)


def insert_user(record: dict) -> None:
    """Raises sqlite3.IntegrityError when the username is already taken
    -- never swallowed and never turned into an update, so a create can
    only ever create."""
    with connect() as connection:
        connection.execute(
            """INSERT INTO users (id, username, display_name, role, password_digest,
                                  password_salt, password_params, is_disabled,
                                  created_at, updated_at, last_login_at)
               VALUES (:id, :username, :display_name, :role, :password_digest,
                       :password_salt, :password_params, :is_disabled,
                       :created_at, :updated_at, :last_login_at)""",
            record,
        )


def read_user_by_username(username: str) -> dict | None:
    """None when there is no such user. The column is `COLLATE NOCASE`,
    so this matches the way a person actually types their own name."""
    with connect() as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
    return dict(row) if row else None


def read_user_by_id(user_id: str) -> dict | None:
    with connect() as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    return dict(row) if row else None


def list_users() -> list[dict]:
    """Every user, disabled ones included. Filtering them out is a
    business decision and the Admin Center needs to see them."""
    with connect() as connection:
        rows = connection.execute(
            "SELECT * FROM users ORDER BY username COLLATE NOCASE"
        ).fetchall()
    return [dict(row) for row in rows]


def count_users() -> int:
    with connect() as connection:
        return connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]


def update_user_fields(user_id: str, fields: dict) -> int:
    """Updates only the named columns and returns the number of rows
    changed, so the caller can tell "no such user" from "nothing to
    change". Column names are checked against the table rather than
    interpolated blind -- this is the one place in the module where a
    caller's keys reach SQL text."""
    if not fields:
        return 0
    unknown = set(fields) - _USER_COLUMNS
    if unknown:
        raise ValueError(f"not columns of users: {sorted(unknown)}")
    assignments = ", ".join(f"{name} = :{name}" for name in fields)
    with connect() as connection:
        cursor = connection.execute(
            f"UPDATE users SET {assignments} WHERE id = :id",
            {**fields, "id": user_id},
        )
        return cursor.rowcount


def delete_user(user_id: str) -> int:
    """Returns rows deleted. The sessions cascade goes with it, which is
    why `foreign_keys` is ON in `connect`."""
    with connect() as connection:
        return connection.execute("DELETE FROM users WHERE id = ?", (user_id,)).rowcount


def insert_session(record: dict) -> None:
    with connect() as connection:
        connection.execute(
            """INSERT INTO sessions (token_sha256, user_id, created_at, expires_at, last_seen_at)
               VALUES (:token_sha256, :user_id, :created_at, :expires_at, :last_seen_at)""",
            record,
        )


def read_session(token_sha256: str) -> dict | None:
    """The row as stored, expiry included and unjudged -- whether
    `expires_at` has passed is the Manager's call, not this module's."""
    with connect() as connection:
        row = connection.execute(
            "SELECT * FROM sessions WHERE token_sha256 = ?", (token_sha256,)
        ).fetchone()
    return dict(row) if row else None


def touch_session(token_sha256: str, last_seen_at: str, expires_at: str) -> int:
    """Both columns move together because the session is rolling: it
    expires after a period of inactivity, not at a fixed hour, so every
    request that proves the session is in use pushes its expiry out.
    Writing `last_seen_at` without `expires_at` would record the activity
    and still log the person out mid-task."""
    with connect() as connection:
        return connection.execute(
            "UPDATE sessions SET last_seen_at = ?, expires_at = ? WHERE token_sha256 = ?",
            (last_seen_at, expires_at, token_sha256),
        ).rowcount


def delete_session(token_sha256: str) -> int:
    with connect() as connection:
        return connection.execute(
            "DELETE FROM sessions WHERE token_sha256 = ?", (token_sha256,)
        ).rowcount


def delete_sessions_for_user(user_id: str) -> int:
    """Every session a user holds. Disabling an account, changing its
    role and resetting its password all need this: a live session would
    otherwise keep the old answer until it expired."""
    with connect() as connection:
        return connection.execute(
            "DELETE FROM sessions WHERE user_id = ?", (user_id,)
        ).rowcount


def delete_sessions_expiring_before(moment: str) -> int:
    with connect() as connection:
        return connection.execute(
            "DELETE FROM sessions WHERE expires_at < ?", (moment,)
        ).rowcount


_USER_COLUMNS = {
    "username",
    "display_name",
    "role",
    "password_digest",
    "password_salt",
    "password_params",
    "is_disabled",
    "created_at",
    "updated_at",
    "last_login_at",
}
