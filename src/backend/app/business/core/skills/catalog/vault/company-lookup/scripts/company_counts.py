"""How many companies, and how many of them are real relationships.

"How many partners do we have?" has a number in it, and a number an agent
arrives at by reading notes it happened to open is wrong in a way nobody
notices. This counts the vault.

It separates three things a single total would hide: companies we have
CLASSIFIED (a hub exists), companies we have actually ENGAGED with (their
History has at least one dated line), and companies that have been ENRICHED
(someone or something filled in the profile). A partner list of 224 where 60
have ever appeared in an engagement is the honest answer to "how many
partners", and the difference is the interesting part.

    python company_counts.py [--kind customer|partner] [--sectors] [--list]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from company_shared import (add_engines_to_path, dated_lines, history_path,
                            people_of, read, vault_from)

add_engines_to_path()

import company_index as ci  # noqa: E402


def tally(vault_path: Path, kind: str | None) -> tuple[dict, dict, dict]:
    """(counts, sector breakdown, names) -- the caller decides how much to print."""
    records = [r for r in ci.hubs(vault_path) if not kind or r["kind"] == kind]
    groups: dict[str, dict] = {}
    sectors: dict[str, Counter] = {}
    spellings: dict[str, Counter] = {}
    names: dict[str, list[str]] = {}
    for record in records:
        hub_md = Path(record["path"])
        frontmatter, _ = read(hub_md)
        bucket = groups.setdefault(record["kind"], {
            "companies": 0, "affiliates": 0, "hubs": 0, "engaged": 0, "enriched": 0, "people": 0})
        bucket["affiliates" if record["parent"] else "companies"] += 1
        # `engaged` and `enriched` are counted over affiliates as well, so this
        # is the denominator they are out of -- without it, "81 companies, 86
        # enriched" looks like an error.
        bucket["hubs"] += 1
        if dated_lines(history_path(hub_md)):
            bucket["engaged"] += 1
        if str(frontmatter.get("enriched") or "").strip():
            bucket["enriched"] += 1
        bucket["people"] += len(people_of(hub_md))
        sector = str(frontmatter.get("sector") or "").strip()
        if sector:
            # The field is free text and the same sector is written with
            # different capitalisation across hubs; two entries differing only
            # in a capital letter is noise, not a breakdown.
            sectors.setdefault(record["kind"], Counter())[sector.casefold()] += 1
            spellings.setdefault(sector.casefold(), Counter())[sector] += 1
        names.setdefault(record["kind"], []).append(record["name"])

    answer = {kind_name: dict(counts) for kind_name, counts in sorted(groups.items())}
    answer["totals"] = {
        field: sum(counts[field] for counts in groups.values())
        for field in ("companies", "affiliates", "hubs", "engaged", "enriched", "people")
    }
    answer["people_not_filed_under_a_company"] = len(
        list((vault_path / "Work" / "People").glob("*.md"))
        if (vault_path / "Work" / "People").is_dir() else [])
    readable = {kind_name: Counter({spellings[key].most_common(1)[0][0]: count
                                    for key, count in counter.items()})
                for kind_name, counter in sectors.items()}
    return answer, readable, names


def main() -> int:
    parser = argparse.ArgumentParser(description="Count the companies in the vault.")
    parser.add_argument("--kind", choices=["customer", "partner"],
                        help="Only this kind. Omit for both.")
    parser.add_argument("--sectors", action="store_true", help="Add the sector breakdown.")
    parser.add_argument("--list", action="store_true", dest="list_names",
                        help="Add every company name -- long; only when the question needs them.")
    parser.add_argument("--vault-path", default="")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    answer, sectors, names = tally(vault_from(args.vault_path), args.kind)
    if args.sectors:
        answer["sectors"] = {k: dict(counter.most_common()) for k, counter in sorted(sectors.items())}
    if args.list_names:
        answer["names"] = {k: sorted(v) for k, v in sorted(names.items())}
    print(json.dumps(answer, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
