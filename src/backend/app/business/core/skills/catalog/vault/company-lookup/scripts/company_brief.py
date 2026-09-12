"""Where do we stand with this company?

Everything the vault holds about one relationship, gathered in the order
someone walking into a meeting wants it: who they are, what has happened
lately, what we know that outlasts a single email, what we still owe them,
and who we talk to.

Each part comes from the note that owns it -- History for events, `## Captured`
for durable facts, the hub's `## Actions` for commitments -- so this reports
the vault rather than re-deriving it. Read-only: it writes nothing.

    python company_brief.py --company "TAQA" [--history 10] [--captures 10]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from company_shared import (add_engines_to_path, captured_lines, captures_path,
                            dated_lines, history_path, open_actions, people_of,
                            read, vault_from)

add_engines_to_path()

import company_index as ci  # noqa: E402

_PROFILE_FIELDS = ("sector", "hq", "founded", "website", "ownership", "parent_org",
                   "leader", "uae_leader", "entity_type", "enriched")


def _summary_line(body: str) -> str:
    """The one-line abstract the enrichment writes as a callout, if it is there."""
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("> [!abstract]"):
            return stripped.split("]", 1)[1].strip()
    return ""


def brief(vault_path: Path, company: str, history_count: int, captures_count: int) -> dict:
    matches = ci.resolve(vault_path, company)
    if len(matches) != 1:
        # A brief about the wrong company reads exactly like a brief about the
        # right one, so this refuses rather than picking the first match.
        return {
            "status": "ambiguous" if matches else "none",
            "query": company,
            "candidates": [{"name": m["name"], "kind": m["kind"], "parent": m["parent"]}
                           for m in matches],
        }
    record = matches[0]
    hub_md = Path(record["path"])
    frontmatter, body = read(hub_md)
    history = dated_lines(history_path(hub_md))
    captured = captured_lines(captures_path(hub_md))
    return {
        "status": "one",
        "name": record["name"],
        "kind": record["kind"],
        "tag": record["tag"],
        "parent": record["parent"],
        "affiliates": record["affiliates"],
        "summary": _summary_line(body),
        "profile": {field: str(frontmatter.get(field) or "")
                    for field in _PROFILE_FIELDS if str(frontmatter.get(field) or "").strip()},
        "recent_history": [{"date": d, "what": t} for d, t in history[:max(history_count, 0)]],
        "total_engagements": len(history),
        "captured_facts": [{"date": d, "fact": t} for d, t in captured[:max(captures_count, 0)]],
        "total_captured_facts": len(captured),
        "open_actions": open_actions(hub_md),
        "people": people_of(hub_md),
        "path": record["path"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Everything the vault holds about one company.")
    parser.add_argument("--company", required=True)
    parser.add_argument("--history", type=int, default=10, help="How many recent events.")
    parser.add_argument("--captures", type=int, default=10, help="How many recent captured facts.")
    parser.add_argument("--vault-path", default="")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(brief(vault_from(args.vault_path), args.company, args.history, args.captures),
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
