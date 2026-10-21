"""Password hashing, on the standard library alone.

`hashlib.scrypt` + `secrets`, no new dependency. That is a deliberate
choice over argon2-cffi or bcrypt, for three reasons that matter more
here than scrypt-versus-argon2 does: this venv is shared with every
plugin's backend (ADR-040) so a dependency added here is one every plugin
inherits; the install must keep working offline; and REQ-SB-101 says the
destination is Entra on Azure, where this module is deleted rather than
ported -- so the cheapest correct thing wins.

**The parameters are stored with every hash, not assumed.** A digest is
only checkable against the cost that produced it, so raising the cost
later must not lock out existing accounts: the row carries its own `n`,
`r`, `p` and `dklen`, verification uses the row's, and
`needs_rehash` tells the Manager when a correct password should be
re-stored at today's cost. Hard-coding the cost at verification time is
the standard way to make a security improvement an outage.

**`maxmem` must be passed explicitly.** OpenSSL defaults it to 32 MB and
scrypt at `n=2**15, r=8` needs 128*n*r = 33.5 MB, so the stdlib call
raises `ValueError: memory limit exceeded` rather than running -- a real
trap, hit while choosing these numbers. It is set from the parameters
themselves with headroom, never a constant that a future `n` outgrows.

Measured on the operator's machine: `n=2**15` costs ~330 ms,
`n=2**14` ~164 ms. 2**15 is the default because a login is rare and a
third of a second is not felt; tests override it down, which is why the
cost is a parameter rather than a literal.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets

# OWASP's scrypt floor is n=2**14; this is one step above it.
DEFAULT_PARAMETERS = {"n": 2**15, "r": 8, "p": 1, "dklen": 32}

_SALT_BYTES = 16


def _maxmem_for(parameters: dict) -> int:
    """scrypt needs 128 * n * r bytes; OpenSSL refuses above `maxmem`.
    Doubling leaves room for its own working space without inviting a
    caller's absurd `n` to exhaust the machine -- an `n` large enough to
    matter would fail on time long before memory."""
    return 2 * 128 * parameters["n"] * parameters["r"]


def hash_password(password: str, parameters: dict | None = None) -> tuple[bytes, bytes, str]:
    """Returns `(digest, salt, parameters_json)` ready for the three
    columns that store them. A fresh salt every time, so two people
    choosing the same password are not visibly the same in the table."""
    used = dict(parameters or DEFAULT_PARAMETERS)
    salt = secrets.token_bytes(_SALT_BYTES)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=used["n"],
        r=used["r"],
        p=used["p"],
        dklen=used["dklen"],
        maxmem=_maxmem_for(used),
    )
    return digest, salt, json.dumps(used, sort_keys=True)


def verify_password(password: str, digest: bytes, salt: bytes, parameters_json: str) -> bool:
    """Checked at the cost the stored digest was made with, never at
    today's. Compared with `hmac.compare_digest`, so a wrong password
    costs the same time whether its first byte matched or not.

    A row whose parameters do not parse, or name a cost this build
    cannot run, verifies as False rather than raising: an unreadable
    credential must fail closed, and the operator finds it through a
    failed login rather than a 500.
    """
    try:
        used = json.loads(parameters_json)
        candidate = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=used["n"],
            r=used["r"],
            p=used["p"],
            dklen=used["dklen"],
            maxmem=_maxmem_for(used),
        )
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        return False
    return hmac.compare_digest(candidate, digest)


def needs_rehash(parameters_json: str, parameters: dict | None = None) -> bool:
    """True when a stored password was made at a cost below today's, so
    the Manager can re-store it at the moment it has the plaintext --
    the only moment it ever can."""
    target = dict(parameters or DEFAULT_PARAMETERS)
    try:
        used = json.loads(parameters_json)
    except (ValueError, TypeError):
        return True
    return any(used.get(key) != value for key, value in target.items())
