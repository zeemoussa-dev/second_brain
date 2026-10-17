"""Prove the Graph credentials work, without ever revealing them.

    python check_graph_auth.py                 # read GRAPH_* from the environment
    python check_graph_auth.py --env-file PATH # or from a specific .env

Written because "I have a few keys and don't know which is the secret" is the
normal situation, and guessing wastes a round trip through an admin. This asks
Microsoft instead.

It NEVER prints a secret. Every credential is shown masked (first 3 chars, a
length, nothing else), and the only full values printed come back FROM the
token: the app id it was issued to, when it expires, and -- the useful part --
the `roles` claim, which is the definitive list of application permissions
actually granted. That answers "is this app-only Mail.Read, or delegated?"
without opening the Entra portal.

Exit code 0 = a token was issued. Non-zero = it was not, with the real reason.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

AUTHORITY = "https://login.microsoftonline.com"
REQUIRED = ("GRAPH_TENANT_ID", "GRAPH_CLIENT_ID", "GRAPH_CLIENT_SECRET")

# The corporate TLS middlebox reliably resets the FIRST request over a cold
# connection (MEMORY.md: "the immediate retry succeeds"). It surfaces as a
# TRANSPORT error, not an HTTP status -- [WinError 10054], or an SSL
# UNEXPECTED_EOF_WHILE_READING when the cut lands mid-handshake.
RETRY_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 1.5


def mask(value: str) -> str:
    """Enough to tell two candidates apart, never enough to use one."""
    if not value:
        return "<empty>"
    return f"{value[:3]}...({len(value)} chars)"


def looks_like_guid(value: str) -> bool:
    return len(value) == 36 and len(value.split("-")) == 5


def load_env_file(path: str) -> dict:
    values = {}
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            values[key.strip()] = val.strip().strip('"').strip("'")
    return values


def decode_claims(token: str) -> dict:
    """Read the JWT payload. It is base64, not encrypted -- this is inspection
    of a token we were just issued, not an attempt to forge or crack one."""
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload))
    except Exception:
        return {}


def request_token(url: str, body: bytes):
    """Returns (payload, http_error, transport_error).

    Only transport errors are retried. An HTTPError is a real answer -- the
    AADSTS code IS the diagnosis -- and must surface immediately.
    """
    transport_error = None
    for attempt in range(RETRY_ATTEMPTS):
        try:
            request = urllib.request.Request(url, data=body)
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.loads(response.read()), None, None
        except urllib.error.HTTPError as exc:
            return None, exc, None
        except Exception as exc:
            transport_error = exc
            print(f"  attempt {attempt + 1}: transport reset ({type(exc).__name__}) -- retrying")
            if attempt < RETRY_ATTEMPTS - 1:
                time.sleep(RETRY_BACKOFF_SECONDS * (attempt + 1))
    return None, None, transport_error


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", default=os.path.join(
        os.environ.get("LOCALAPPDATA", ""), "hermes", ".env"))
    args = parser.parse_args()

    values = dict(os.environ)
    if os.path.isfile(args.env_file):
        for key, val in load_env_file(args.env_file).items():
            values.setdefault(key, val)   # the environment wins over the file
        print(f"reading    : {args.env_file}")
    else:
        print(f"note       : no .env at {args.env_file}, using the environment only")

    creds = {name: (values.get(name) or "").strip() for name in REQUIRED}

    print("")
    print("credentials found (masked):")
    for name in REQUIRED:
        print(f"  {name:<22} {mask(creds[name])}")

    missing = [n for n in REQUIRED if not creds[n]]
    if missing:
        print("")
        print(f"FAIL: not set -> {', '.join(missing)}")
        return 2

    # The single most common mistake: the secret's ID used instead of its value.
    if looks_like_guid(creds["GRAPH_CLIENT_SECRET"]):
        print("")
        print("FAIL: GRAPH_CLIENT_SECRET looks like a GUID.")
        print("      That is almost certainly the secret's *ID*, not its *value*.")
        print("      In Entra the value is ~40 chars and usually contains a '~'.")
        print("      It is shown once, at creation -- if it was not saved, create")
        print("      a new secret; that does not disturb the existing grant.")
        return 3

    body = urllib.parse.urlencode({
        "client_id": creds["GRAPH_CLIENT_ID"],
        "client_secret": creds["GRAPH_CLIENT_SECRET"],
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials",
    }).encode()
    url = f"{AUTHORITY}/{creds['GRAPH_TENANT_ID']}/oauth2/v2.0/token"

    print("")
    print(f"requesting a token from {AUTHORITY}/<tenant>/oauth2/v2.0/token ...")
    payload, http_error, transport_error = request_token(url, body)

    if http_error is not None:
        detail = {}
        try:
            detail = json.loads(http_error.read() or b"{}")
        except Exception:
            pass
        print("")
        print(f"FAIL: {http_error.code} {detail.get('error', '')}")
        print(f"      {str(detail.get('error_description', ''))[:400]}")
        print("")
        print("  AADSTS7000215 = wrong secret value (or the ID was used)")
        print("  AADSTS700016  = client id not found in this tenant")
        print("  AADSTS90002   = tenant id not found")
        print("  AADSTS7000222 = the secret has EXPIRED -- create a new one")
        return 4

    if payload is None:
        print("")
        print(f"FAIL: could not reach the token endpoint after {RETRY_ATTEMPTS} attempts.")
        print(f"      {transport_error}")
        print("")
        print("  This is the corporate TLS middlebox, NOT your credentials -- the")
        print("  same reset that hits every cold connection on this network. Try")
        print("  again; if it never gets through, run it from a shell that is")
        print("  definitely behind the proxy.")
        return 5

    token = payload.get("access_token", "")
    if not token:
        print("")
        print("FAIL: no access_token in the response")
        return 6

    claims = decode_claims(token)
    roles = claims.get("roles") or []

    print("")
    print("OK: a token was issued. The credentials are correct.")
    print("")
    print(f"  app id  : {claims.get('appid') or claims.get('azp') or '?'}")
    print(f"  tenant  : {claims.get('tid') or '?'}")
    if claims.get("exp"):
        print(f"  expires : {datetime.fromtimestamp(claims['exp'], timezone.utc):%Y-%m-%d %H:%M:%SZ}")

    print("")
    print(f"  application permissions actually granted ({len(roles)}):")
    for role in sorted(roles):
        print(f"    - {role}")
    if not roles:
        print("    <none>")
        print("")
        print("  WARNING: no `roles` claim. This token carries NO application")
        print("  permissions, which usually means the grant is DELEGATED rather")
        print("  than application. Delegated needs a signed-in user and cannot")
        print("  drive a cron job -- ask for application Mail.Read instead.")
        return 7

    if not any(r.lower().startswith("mail.read") for r in roles):
        print("")
        print("  WARNING: no Mail.Read* role. Reading the mailbox will 403.")
        return 8

    print("")
    print("  Mail.Read present -- ready for the capture pipeline.")
    print("")
    print("  Still worth confirming with your admin: an Application Access")
    print("  Policy scoped to the one mailbox. Without it, app-only Mail.Read")
    print("  can read EVERY mailbox in the tenant.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
