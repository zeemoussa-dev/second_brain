"""One-time interactive sign-in for this Skill's DELEGATED Graph access.

Run this once per machine (and again whenever capture starts failing with
`invalid_grant`, which means the refresh token was revoked). It prints a code,
the operator enters it at Microsoft's own page, and the resulting refresh token
is stored so every later run is unattended.

    python authorize_graph.py

No password is ever handled here. The operator authenticates directly with
Microsoft; this script only learns the outcome.

Why an interactive step exists at all: this tenant grants Graph permissions as
Delegated only, so there is no app-only path -- see graph_lib's module
docstring. `--status` reports what is stored without signing in.
"""
from __future__ import annotations

import argparse
import sys

import graph_lib


def _status() -> int:
    try:
        path = graph_lib._token_store_path()
    except graph_lib.GraphUnavailable as exc:
        print("cannot locate the token store:", exc)
        return 2
    print("token store :", path)
    if not path.is_file():
        print("state       : NOT AUTHORIZED -- run this script with no arguments")
        return 1
    import json
    try:
        stored = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print("state       : UNREADABLE --", exc)
        return 2
    # Deliberately never prints the token itself, only that one is present.
    print("state       :", "authorized" if stored.get("refresh_token") else "NO REFRESH TOKEN")
    print("signed in as:", stored.get("signed_in_as") or "<unknown>")
    print("updated at  :", stored.get("updated_at") or "<unknown>")
    return 0


def _authorize() -> int:
    started = graph_lib.begin_device_code()
    print()
    print("  SIGN IN HERE :", started.get("verification_uri"))
    print("  CODE         :", started.get("user_code"))
    print("  valid for    :", round(int(started.get("expires_in", 900)) / 60), "minutes")
    print()
    print("  Sign in as the account that has access to the target mailbox.")
    print("  Waiting ...", flush=True)

    graph_lib.complete_device_code(
        started["device_code"],
        interval=int(started.get("interval", 5)),
        expires_in=int(started.get("expires_in", 900)),
    )
    print()
    print("  signed in; refresh token stored at", graph_lib._token_store_path())
    # Prove the stored token actually works rather than trusting the sign-in --
    # a token that cannot be redeemed is the failure this script exists to
    # prevent, and finding out now beats finding out on the next cron run.
    graph_lib._cached_access_token = None
    graph_lib._access_token()
    print("  verified: the stored token redeems for an access token.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--status", action="store_true",
                        help="report what is stored, without signing in")
    args = parser.parse_args()
    try:
        return _status() if args.status else _authorize()
    except graph_lib.GraphUnavailable as exc:
        print("FAILED:", exc)
        return 2


if __name__ == "__main__":
    sys.exit(main())
