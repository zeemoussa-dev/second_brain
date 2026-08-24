"""CLI entry point: applies ONE operator decision to ONE existing
Entities.md entry -- the mechanical half of the WhatsApp approval loop
(2026-08-21). find_new_entities.py's own job is discovery + a safe
`Ignore: Yes` default; this script is what an operator's real reply
("make Simplai a partner", "X is an affiliate of G42", "ignore that
one") turns into once a live Hermes chat session has parsed the
company name/domain and the intent out of it -- this script never does
any of that parsing/judgment itself, only the mechanical, safe file
edit, mirroring apply_thread_review.py's own "the agent decides, the
script applies" split.

Usage:
    python apply_entity_decision.py --vault-path P --company NAME_OR_DOMAIN \\
        --decision customer|partner|affiliate|ignore \\
        [--affiliate-of PARENT_NAME] [--aliases "extra alias text"]

Matches --company against an entry's own Company Name OR any of its own
(comma-split) Domain values, case-insensitive. `affiliate` and `partner`/
`customer` both set Ignore: No (the entry is now decided, real); `ignore`
sets Ignore: Yes (reverts to "known, but not a real relationship" --
never deletes the entry, matching this project's own archive-not-delete
discipline applied to Entities.md's own entries). `--affiliate-of` can be
combined with any non-ignore decision (an Affiliate can be filed under
either ## Companies or ## Partners -- create-companies-partners.py's own
Pass 2 keys off a non-blank `Affiliate of` field, not the section).

Prints {"matched": bool, "name", "domain", "section", "ignore",
"affiliate_of", "aliases"} or {"error": str} if no entry matched.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from find_new_entities import parse_entities, render_entities


def apply_entity_decision(
    vault_path: Path, entities_path: Path, company: str, decision: str,
    affiliate_of: str | None = None, aliases: str | None = None,
) -> dict:
    content = entities_path.read_text(encoding="utf-8-sig")
    entries = parse_entities(content)

    key = company.strip().lower()
    target = None
    for entry in entries:
        name = (entry["fields"].get("Company Name") or entry["heading"]).strip().lower()
        domains = [d.strip().lower() for d in (entry["fields"].get("Domain") or "").split(",") if d.strip()]
        if name == key or key in domains:
            target = entry
            break

    if target is None:
        return {"error": f"no Entities.md entry matches {company!r}"}

    fields = target["fields"]
    if decision == "ignore":
        fields["Ignore"] = "Yes"
    elif decision in ("customer", "partner", "affiliate"):
        fields["Ignore"] = "No"
        if decision == "customer":
            target["section"] = "customer"
        elif decision == "partner":
            target["section"] = "partner"
        # "affiliate" alone leaves the entry's own current section
        # untouched -- affiliate-ness comes from `Affiliate of` being
        # non-blank, not from which section it's filed under.
    else:
        return {"error": f"unknown decision {decision!r} -- expected customer/partner/affiliate/ignore"}

    if affiliate_of:
        fields["Affiliate of"] = affiliate_of
    if aliases:
        existing = fields.get("Aliases", "").strip()
        fields["Aliases"] = f"{existing}, {aliases}".strip(", ") if existing else aliases

    entities_path.write_text(render_entities(entries), encoding="utf-8")

    return {
        "matched": True,
        "name": fields.get("Company Name") or target["heading"],
        "domain": fields.get("Domain", ""),
        "section": target["section"],
        "ignore": fields["Ignore"],
        "affiliate_of": fields.get("Affiliate of", ""),
        "aliases": fields.get("Aliases", ""),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault-path", required=True)
    parser.add_argument("--entities-name", default="Entities.md")
    parser.add_argument("--company", required=True)
    parser.add_argument("--decision", required=True, choices=["customer", "partner", "affiliate", "ignore"])
    parser.add_argument("--affiliate-of", default=None)
    parser.add_argument("--aliases", default=None)
    args = parser.parse_args()

    vault_path = Path(args.vault_path)
    entities_path = vault_path / "Work" / args.entities_name
    if not entities_path.exists():
        print(json.dumps({"error": f"{entities_path} does not exist"}))
        return 1

    result = apply_entity_decision(
        vault_path, entities_path, args.company, args.decision, args.affiliate_of, args.aliases,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if "error" not in result else 1


if __name__ == "__main__":
    raise SystemExit(main())
