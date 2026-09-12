"""Do we have this company, and which one is it?

"Do we work with Mubadala?" is not a yes/no question in this vault: there is
Mubadala, Mubadala Health, and Mubadala Energy, and answering with the first
one found is how a capture ends up against the wrong company. This returns
EVERY company a query could mean and says which match was exact, so the agent
can name them all rather than choose.

Search widens only as far as it has to: the exact hub spelling or alias first,
then the identifying form of the name, then a substring of a name or alias,
then the domain, then the sector. Each result says how it matched.

    python find_company.py --query "mubadala" [--kind partner] [--limit 20]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from company_shared import (add_engines_to_path, dated_lines, history_path,
                            people_of, read, vault_from)

add_engines_to_path()

import company_index as ci  # noqa: E402


def _summarise(record: dict, how: str) -> dict:
    hub_md = Path(record["path"])
    frontmatter, _ = read(hub_md)
    history = dated_lines(history_path(hub_md))
    return {
        "name": record["name"],
        "kind": record["kind"],
        "tag": record["tag"],
        "matched_on": how,
        "parent": record["parent"],
        "affiliates": record["affiliates"],
        "sector": str(frontmatter.get("sector") or ""),
        "hq": str(frontmatter.get("hq") or ""),
        "leader": str(frontmatter.get("leader") or ""),
        "domains": record["domains"],
        "people": len(people_of(hub_md)),
        "engagements": len(history),
        "last_engagement": history[0][0] if history else "",
        "path": record["path"],
    }


def find(vault_path: Path, query: str, kind: str | None) -> dict:
    records = [r for r in ci.hubs(vault_path) if not kind or r["kind"] == kind]
    wanted = str(query or "").strip().lower()
    if not wanted:
        return {"query": query, "status": "none", "matches": []}

    exact = ci.resolve(vault_path, query, records=records)
    if exact:
        how = "name" if any(s.lower() == wanted for r in exact for s in r["spellings"]) else "name form"
        matched = {r["path"] for r in exact}
        # An exact hit ends the search, which would quietly hide "Mubadala
        # Energy" from someone who asked about "Mubadala". Naming the
        # neighbours costs a line and is exactly the confusion this Skill exists
        # to prevent.
        related = sorted(r["name"] for r in records if r["path"] not in matched
                         and any(wanted in s.lower() for s in r["spellings"]))
        answer = {"query": query, "status": "one" if len(exact) == 1 else "several",
                  "matches": [_summarise(r, how) for r in exact]}
        if related:
            answer["others_with_this_in_their_name"] = related[:10]
        return answer

    # Nothing identifies as this name, so the question is probably broader than
    # one company -- "who do we have in energy", "anyone at adnoc.ae".
    partial, by_domain, by_sector = [], [], []
    for record in records:
        hub_md = Path(record["path"])
        frontmatter, _ = read(hub_md)
        if any(wanted in s.lower() for s in record["spellings"]):
            partial.append(_summarise(record, "part of the name"))
        elif any(wanted in d for d in record["domains"]):
            by_domain.append(_summarise(record, "domain"))
        elif wanted in str(frontmatter.get("sector") or "").lower():
            by_sector.append(_summarise(record, "sector"))
    matches = partial + by_domain + by_sector
    return {
        "query": query,
        "status": "one" if len(matches) == 1 else ("several" if matches else "none"),
        "matches": sorted(matches, key=lambda m: (m["matched_on"], m["name"])),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Find the companies a name could mean.")
    parser.add_argument("--query", required=True)
    parser.add_argument("--kind", choices=["customer", "partner"])
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--vault-path", default="")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    answer = find(vault_from(args.vault_path), args.query, args.kind)
    total = len(answer["matches"])
    answer["matches"] = answer["matches"][:max(args.limit, 1)]
    if total > len(answer["matches"]):
        answer["not_shown"] = total - len(answer["matches"])
    print(json.dumps(answer, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
