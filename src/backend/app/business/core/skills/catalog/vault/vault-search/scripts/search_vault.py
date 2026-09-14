"""search_vault.py -- agent-facing vault search. Asks Second Brain's own
backend for hybrid (keyword + meaning) results and prints them as plain
text for the calling agent to read.

Standalone and stdlib-only, the same deployment model as
vault_manager.py/build_vault_index.py: physically copied into whichever
Hermes profile needs it, no Second Brain package import. Unlike those two,
this one deliberately DOES need the backend running -- the embedding model,
the vector store and the ranking all live there. That is the whole point:
the Hermes-side payload cannot carry an embedding client without taking on
real dependencies (ADR-019's stdlib-only payload rule), so it asks the one
process that already has them.

Backend down is therefore a real, expected state, not a crash: the script
says so on stderr and exits non-zero, and the agent should fall back to
find_by_id/find_by_filename/find_in_folder as it always did.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

# Second Brain's own backend, same default port the app and its launcher
# use. Overridable for an install that moved it.
_DEFAULT_BASE_URL = os.environ.get("SECOND_BRAIN_API_URL", "http://127.0.0.1:8001")
_DEFAULT_LIMIT = 10
_TIMEOUT_SECONDS = 30


def search(base_url: str, query: str, limit: int, mode: str) -> dict:
    url = f"{base_url.rstrip('/')}/vault-search/{mode}?" + urllib.parse.urlencode(
        {"q": query, "limit": limit}
    )
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode("utf-8"))


def render(payload: dict) -> str:
    results = payload.get("results") or []
    if not results:
        return "No matching notes."

    lines = []
    for result in results:
        tags = ", ".join(result.get("tags") or [])
        matched_by = result.get("matched_by") or {}
        # Which ranker found it is real signal for the agent: a
        # keyword-only hit is an exact-name match, a semantic-only hit is a
        # conceptual one that may need reading before it is trusted.
        how = "+".join(sorted(matched_by)) if matched_by else "semantic"
        lines.append(
            f"{result.get('rank')}. {result.get('title') or result.get('stem')} "
            f"[{result.get('kind', 'Unknown')}] ({how})"
            + (f" tags: {tags}" if tags else "")
            + f"\n   stem: {result.get('stem')}"
        )

    if payload.get("semantic_available") is False:
        lines.append(
            "\n(keyword-only: semantic ranking unavailable -- "
            f"{payload.get('semantic_error')})"
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Search the vault by keyword and meaning.")
    parser.add_argument("query", help="What to search for, in plain words.")
    parser.add_argument("--limit", type=int, default=_DEFAULT_LIMIT)
    parser.add_argument(
        "--mode", choices=("hybrid", "semantic", "search"), default="hybrid",
        help="hybrid (default, keyword+meaning), semantic (meaning only), search (keyword only).",
    )
    parser.add_argument("--base-url", default=_DEFAULT_BASE_URL)
    args = parser.parse_args()

    try:
        payload = search(args.base_url, args.query, args.limit, args.mode)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        print(f"Vault search unavailable (HTTP {exc.code}): {detail}", file=sys.stderr)
        return 1
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        print(
            f"Vault search unavailable ({exc}) -- is the Second Brain backend running "
            f"at {args.base_url}? Fall back to a direct vault_manager lookup.",
            file=sys.stderr,
        )
        return 1

    print(render(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
