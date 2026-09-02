"""CLI entry point: cheap, mechanical (no LLM) first pass at company/
partner discovery -- Step 1 of a 4-step sequence (2026-08-21):

  1. THIS script -- group every Thread's real participants by email
     domain, write one flat report (.second-brain/Settings/Entities.md) for the operator
     to review by hand.
  2. [Manual] Operator edits Entities.md directly -- merges any
     duplicate entries, moves real partners into its ## Partners
     section.
  3. [Separate, later, one-time pipeline] Reads the curated Entities.md,
     creates the real Customer/Partner OKF hub notes from it.
  4. [Separate, later, one-time pipeline] Summarizes every Thread (real
     LLM/agent work) -- with the curated company list already in hand,
     wiki-tags recognized company names directly into each summary
     instead of needing to discover them from scratch.

This script is ONLY step 1. It never writes to Threads, never calls an
LLM, never creates a Customer/Partner note -- pure read of already-
captured vault data, grouped by domain. Grouping by domain (not
free-text company name) is what keeps two spellings of the same real
company (e.g. "DGE" vs "Digital Government Entity", both
@dge.gov.ae) from ever becoming two separate entries in the first
place -- they share one domain, so they're the same group by
construction.

Usage:
    python build_entities_report.py --vault-path P [--output-name NAME]

Prints {"report_path": str, "companies_found": int, "threads_scanned": int}.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

_FRONTMATTER_LINE = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*):\s?(.*)$")
_LIST_ITEM_PATTERN = re.compile(r'"((?:[^"\\]|\\.)*)"')
_WIKILINK_PATTERN = re.compile(r"\[\[([^\]]+)\]\]")

# Same denylist as Second Brain's own app/business/people_extraction.py
# (_PERSONAL_EMAIL_DOMAINS) -- kept in sync by hand, not imported, since
# this Skill has zero dependency on Second Brain's own backend.
_PERSONAL_EMAIL_DOMAINS = frozenset({
    "gmail.com", "googlemail.com", "outlook.com", "hotmail.com", "live.com",
    "msn.com", "yahoo.com", "ymail.com", "icloud.com", "me.com", "aol.com",
    "protonmail.com", "proton.me", "gmx.com", "mail.com", "yandex.com",
    "zoho.com",
})

# The operator's own organization -- every subdomain excluded too (e.g.
# a notification sender on a subdomain is still "us", not a Customer or
# Partner candidate). Both TLDs (2026-08-21, operator: "core42.ae and
# core42.ai are the same thing") -- a real "Core42" Partner-Affiliate-of-
# G42 entity got created from the .ae domain before this fix, archived
# to Work/_archive/Partners-Affiliates/Core42 by hand once caught.
_OWN_DOMAIN_SUFFIXES = ("core42.ai", "core42.ae")


def _parse_frontmatter_value(raw: str):
    raw = raw.strip()
    if raw.startswith('"') and raw.endswith('"'):
        return raw[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1]
        return [
            match.group(1).replace('\\"', '"').replace("\\\\", "\\")
            for match in _LIST_ITEM_PATTERN.finditer(inner)
        ]
    return raw


def read_note(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    frontmatter_block = text[4:end]
    body = text[end + 5:]
    frontmatter: dict = {}
    for line in frontmatter_block.splitlines():
        match = _FRONTMATTER_LINE.match(line)
        if match:
            frontmatter[match.group(1)] = _parse_frontmatter_value(match.group(2))
    return frontmatter, body


def _domain_of(email: str) -> str | None:
    email = email.strip().lower()
    if "@" not in email:
        return None
    return email.rsplit("@", 1)[1]


def _is_excluded_domain(domain: str) -> bool:
    if domain in _PERSONAL_EMAIL_DOMAINS:
        return True
    return any(domain == own or domain.endswith("." + own) for own in _OWN_DOMAIN_SUFFIXES)


def _display_name(domain: str) -> str:
    """Mirrors Second Brain's own derive_company_from_email display-name
    convention exactly (domain's first label, capitalized) -- so a
    company name derived here matches what Step 3's later hub-note
    creation would independently derive from the same domain."""
    label = domain.split(".", 1)[0]
    return label[0].upper() + label[1:] if label else domain


def list_thread_notes(vault_path: Path) -> list[Path]:
    threads_root = vault_path / "Work" / "Threads"
    if not threads_root.exists():
        return []
    return sorted(
        path for path in threads_root.glob("*/*.md")
        if path.parent.name == path.stem and path.is_file()
    )


def build_report(vault_path: Path) -> dict:
    threads_scanned = 0
    # domain -> {"threads": {thread_stem: wikilink}}
    domains: dict[str, dict] = {}

    for concept_path in list_thread_notes(vault_path):
        threads_scanned += 1
        thread_wikilink = f"[[{concept_path.stem}]]"
        messages_dir = concept_path.parent / "messages"
        if not messages_dir.exists():
            continue
        for message_path in sorted(messages_dir.glob("*.md")):
            if not message_path.is_file():
                continue
            frontmatter, _ = read_note(message_path)

            candidate_emails: list[str] = []
            sender_email = frontmatter.get("sender_email")
            if sender_email:
                candidate_emails.append(sender_email)
            for link in frontmatter.get("participant_links") or []:
                match = _WIKILINK_PATTERN.match(link)
                target = match.group(1) if match else link
                if "@" in target:
                    candidate_emails.append(target)

            for email in candidate_emails:
                domain = _domain_of(email)
                if not domain or _is_excluded_domain(domain):
                    continue
                entry = domains.setdefault(domain, {"threads": {}})
                entry["threads"].setdefault(concept_path.stem, thread_wikilink)

    return {"threads_scanned": threads_scanned, "domains": domains}


def render_report(domains: dict[str, dict]) -> str:
    """Compact, key:value-per-line schema (2026-08-21, operator: "the file
    is very long", "Don't include the Threads/People") -- just the
    tracker fields Job 3 (a later, separate one-time pipeline) will
    actually read to decide what to create -- `Company Name`/`Aliases`/
    `Affiliate of`/`Created`/`Ignore` -- plus `Domain` for identification.
    A blank line between every field (not just between entries) is
    deliberate: plain markdown collapses adjacent lines with no blank
    line between them into one rendered paragraph, so without it the
    fields don't actually render as separate lines (operator: "New Lines
    are still not Created"). `Aliases` starts blank -- domain-based
    grouping already prevents most same-company duplicates by
    construction; the operator fills this in only for the rarer case of
    one real company spanning two different domains, merging the second
    entry's domain in here and deleting that second entry."""
    lines = [
        "# Entities",
        "",
        "Step 1 of the company/partner discovery sequence -- mechanical,",
        "domain-based grouping only, no LLM, no judgment about which of",
        "these are real Customers vs. Partners vs. noise.",
        "",
        "**Edit this file by hand.** `Created`/`Ignore` are Yes/No flags a",
        "later pipeline reads -- set `Ignore: Yes` instead of deleting an",
        "entry (a notification sender, a one-off vendor -- not a real",
        "business relationship); leave `Created: No` until that later,",
        "separate pipeline has actually made the hub note for it. Use",
        "`Aliases` to merge a duplicate that slipped through under a",
        "different domain (rare -- domain grouping already prevents most",
        "of this). Move real partners into `## Partners` below.",
        "",
        "## Companies",
        "",
    ]

    ordered = sorted(domains.items(), key=lambda kv: len(kv[1]["threads"]), reverse=True)
    for domain, entry in ordered:
        name = _display_name(domain)
        # Plain markdown collapses adjacent lines with no blank line
        # between them into one rendered paragraph (a single "\n" is a
        # soft wrap, not a line break) -- a blank line between every
        # field is what makes each one actually render on its own visible
        # line (2026-08-21, operator: "New Lines are still not Created").
        # A leading tab on each field line (operator: "add a tab before
        # the internals ... so I can visually understand it") renders the
        # whole field block as an indented code block -- visually
        # subordinate to the ### heading above it, not a new top-level
        # paragraph.
        lines.append(f"### {name}")
        lines.append("")
        lines.append(f"\tCompany Name: {name}")
        lines.append("")
        lines.append("\tAliases: ")
        lines.append("")
        lines.append("\tAffiliate of: ")
        lines.append("")
        lines.append("\tCreated: No")
        lines.append("")
        lines.append("\tIgnore: No")
        lines.append("")
        lines.append(f"\tDomain: {domain}")
        lines.append("")
        # Deleted -- soft-delete field (2026-08-27), schema-consistent
        # with find_new_entities.py/create_companies_partners.py's own
        # _render_entry even though this one-time Step-1 script never
        # reads it back itself.
        lines.append("\tDeleted: No")
        lines.append("")
        lines.append("")

    lines.append("## Partners")
    lines.append("")
    lines.append("<!-- Move entries here from ## Companies as you review them. -->")
    lines.append("")

    return "\n".join(lines)


_ENTRY_HEADING_RE = re.compile(r"^### ", re.M)


def _existing_entry_count(path: Path) -> int:
    """Cheap non-emptiness check, not a real parse -- this script only
    ever needs to know "is there already real curation here", never the
    entries themselves. Any real `### <name>` heading counts, in either
    section; a not-yet-created file or a bare, entry-less template (the
    genuine first-seed case) both count as zero."""
    if not path.exists():
        return 0
    return len(_ENTRY_HEADING_RE.findall(path.read_text(encoding="utf-8-sig")))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault-path", required=True)
    parser.add_argument("--output-name", default="Entities.md")
    parser.add_argument(
        "--force", action="store_true",
        help="Overwrite an already-curated Entities.md. Without this flag, "
             "the script refuses (real curation -- Ignore flags, Affiliate "
             "of, merged Aliases -- would be silently destroyed by this "
             "script's own full-rewrite design otherwise; found live "
             "2026-09-02, see MEMORY.md).",
    )
    args = parser.parse_args()

    vault_path = Path(args.vault_path)
    # Settings/Entities.md under .second-brain -- see find_new_entities.py's
    # own comment for the full 2026-08-27 relocation reasoning.
    output_path = vault_path / ".second-brain" / "Settings" / args.output_name

    existing_count = _existing_entry_count(output_path)
    if existing_count and not args.force:
        print(json.dumps({
            "error": "refused: Entities.md already has real curated entries",
            "report_path": str(output_path),
            "existing_entries": existing_count,
            "hint": "This is Step 1, a ONE-TIME first seed for a genuinely "
                    "new vault -- it always does a full rewrite, which would "
                    "destroy real curation (Ignore flags, Affiliate of, "
                    "merged Aliases) already in this file. Pass --force only "
                    "if you genuinely want to discard everything currently "
                    "in it and start over.",
        }))
        return 1

    result = build_report(vault_path)
    report_text = render_report(result["domains"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report_text, encoding="utf-8")

    print(json.dumps({
        "report_path": str(output_path),
        "companies_found": len(result["domains"]),
        "threads_scanned": result["threads_scanned"],
        "overwrote_existing_entries": existing_count,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
