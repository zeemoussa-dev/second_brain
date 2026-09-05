"""CLI entry point: recurring, INCREMENTAL sibling of entity-domain-
extraction's own one-time build_entities_report.py (2026-08-21).

That script does a full, destructive rewrite of .second-brain/Settings/
Entities.md every
run -- correct for a one-time Step 1, catastrophic for a recurring job,
since by now Entities.md is the operator's own hand-curated file (Ignore
flags, Affiliate of, merged multi-domain entries like Core42's own
"core42.ae, core42.ai" -- all real, hard-won curation that a rewrite
would silently destroy). This script instead:

  1. Parses the CURRENT Entities.md byte-faithfully (same parse_entities/
     render_entities round-trip create-companies-partners.py already
     uses) -- every existing entry, and every field on it, is preserved
     exactly.
  2. Scans Threads (participant_links) AND Meetings (attendees) for real
     email domains -- Meetings weren't a Step 1 evidence source (that
     Skill predates meeting-capture).
  3. APPENDS a new entry only for a domain that isn't already covered by
     any existing entry's own Domain field (comma-split, so "core42.ae,
     core42.ai" correctly counts as two covered domains) and isn't
     excluded (personal-email denylist, the operator's own org domains).
  4. New entries default to `Ignore: Yes` -- the safe, non-auto-creating
     default (create-companies-partners.py never creates a hub note for
     an Ignore: Yes entry) -- an operator WhatsApp approval (see
     apply_entity_decision.py, this Skill's own sibling script) is what
     flips it to Ignore: No, not this script.

Usage:
    python find_new_entities.py --vault-path P [--entities-name Entities.md]

Prints {"new_entities": [{"name","domain","thread_count",
"meeting_count"}, ...], "entities_path": str}. An empty `new_entities`
list means nothing new -- the file is left completely untouched (not
even re-rendered) in that case, so a byte-identical rerun never shows up
as a spurious git/Obsidian diff.
"""
from __future__ import annotations

import argparse
import os
import json
import re
from pathlib import Path


# Same resolution as vault_manager.data_root(), inlined because this Skill
# ships no vault_manager.py -- importing one that isn't there is how this
# script would fail at run time rather than here. Kept byte-for-byte in step
# with that function: SECOND_BRAIN_DATA_PATH first, the historical in-vault
# folder as the fallback.
def _data_root(vault_path: Path) -> Path:
    configured = os.environ.get("SECOND_BRAIN_DATA_PATH", "").strip()
    return Path(configured) if configured else vault_path / ".second-brain"



_FRONTMATTER_LINE = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*):\s?(.*)$")
_LIST_ITEM_PATTERN = re.compile(r'"((?:[^"\\]|\\.)*)"')
_WIKILINK_PATTERN = re.compile(r"\[\[([^\]]+)\]\]")

_KNOWN_FIELDS = {"Company Name", "Aliases", "Affiliate of", "Created", "Ignore", "Domain", "Deleted"}

# Same denylist entity-domain-extraction's own build_entities_report.py
# uses -- kept in sync by hand, not imported (per-Skill self-containment).
_PERSONAL_EMAIL_DOMAINS = frozenset({
    "gmail.com", "googlemail.com", "outlook.com", "hotmail.com", "live.com",
    "msn.com", "yahoo.com", "ymail.com", "icloud.com", "me.com", "aol.com",
    "protonmail.com", "proton.me", "gmx.com", "mail.com", "yandex.com",
    "zoho.com",
})
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
    email = (email or "").strip().lower()
    if "@" not in email:
        return None
    return email.rsplit("@", 1)[1]


def _is_excluded_domain(domain: str) -> bool:
    if domain in _PERSONAL_EMAIL_DOMAINS:
        return True
    return any(domain == own or domain.endswith("." + own) for own in _OWN_DOMAIN_SUFFIXES)


def _display_name(domain: str) -> str:
    label = domain.split(".", 1)[0]
    return label[0].upper() + label[1:] if label else domain


def _split_domains(domain_field: str) -> list[str]:
    return [d.strip().lower() for d in domain_field.split(",") if d.strip()]


# ── Entities.md parsing / re-rendering (byte-faithful round-trip,
# identical to create-companies-partners.py's own copy) ─────────────────

def parse_entities(content: str) -> list[dict]:
    section = None
    entries: list[dict] = []
    current: dict | None = None
    for line in content.splitlines():
        if line.startswith("## Companies"):
            section = "customer"
            continue
        if line.startswith("## Partners"):
            section = "partner"
            continue
        if line.startswith("### "):
            if current is not None:
                entries.append(current)
            current = {"section": section, "heading": line[4:].strip(), "fields": {}}
            continue
        stripped = line.strip()
        if current is not None and stripped and ":" in stripped:
            key, _, value = stripped.partition(":")
            key = key.strip()
            if key in _KNOWN_FIELDS:
                current["fields"][key] = value.strip()
    if current is not None:
        entries.append(current)
    return entries


def render_entities(entries: list[dict]) -> str:
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
    for entry in entries:
        if entry["section"] != "customer":
            continue
        _render_entry(lines, entry)
    lines.append("## Partners")
    lines.append("")
    for entry in entries:
        if entry["section"] != "partner":
            continue
        _render_entry(lines, entry)
    return "\n".join(lines)


def _render_entry(lines: list[str], entry: dict) -> None:
    f = entry["fields"]
    lines.append(f"### {entry['heading']}")
    lines.append("")
    lines.append(f"\tCompany Name: {f.get('Company Name', '')}")
    lines.append("")
    lines.append(f"\tAliases: {f.get('Aliases', '')}")
    lines.append("")
    lines.append(f"\tAffiliate of: {f.get('Affiliate of', '')}")
    lines.append("")
    lines.append(f"\tCreated: {f.get('Created', 'No')}")
    lines.append("")
    lines.append(f"\tIgnore: {f.get('Ignore', 'No')}")
    lines.append("")
    lines.append(f"\tDomain: {f.get('Domain', '')}")
    lines.append("")
    # 2026-08-27, operator: a real hard-DELETE of a row removed its Domain
    # from _already_tracked_domains, so a noise domain (SharePoint, Teams
    # notification senders) kept getting rediscovered every scan --
    # "they will keep surfacing and I know they will never be a company."
    # Deleted: Yes is a soft delete instead -- the row (and its Domain)
    # stays, so this check keeps it out of `tracked` forever; the app's
    # own Settings > Vault > Entities UI hides Deleted: Yes rows rather
    # than removing them.
    lines.append(f"\tDeleted: {f.get('Deleted', 'No')}")
    lines.append("")
    lines.append("")


# ── evidence scan: Threads + Meetings ───────────────────────────────────

def _list_thread_notes(vault_path: Path) -> list[Path]:
    threads_root = vault_path / "Work" / "Threads"
    if not threads_root.exists():
        return []
    return sorted(
        path for path in threads_root.glob("*/*.md")
        if path.parent.name == path.stem and path.is_file()
    )


def _list_meeting_notes(vault_path: Path) -> list[Path]:
    """One-time meeting files, series concept files, and every occurrence
    file -- concept-only entries carry no attendees of their own for a
    series (by meeting-capture's own design), so scanning occurrences too
    is what actually finds a series' real attendee domains."""
    meetings_root = vault_path / "Work" / "Meetings"
    if not meetings_root.exists():
        return []
    notes: list[Path] = []
    for concept_path in sorted(meetings_root.glob("*/*.md")):
        if not concept_path.is_file() or concept_path.parent.name != concept_path.stem:
            continue
        notes.append(concept_path)
        occurrences_dir = concept_path.parent / "occurrences"
        if occurrences_dir.exists():
            notes.extend(sorted(p for p in occurrences_dir.glob("*.md") if p.is_file()))
    return notes


def build_domain_evidence(vault_path: Path) -> dict[str, dict]:
    """domain -> {"threads": {thread_stem: True}, "meetings": {meeting_stem: True}}"""
    domains: dict[str, dict] = {}

    for concept_path in _list_thread_notes(vault_path):
        messages_dir = concept_path.parent / "messages"
        if not messages_dir.exists():
            continue
        for message_path in sorted(messages_dir.glob("*.md")):
            if not message_path.is_file():
                continue
            frontmatter, _ = read_note(message_path)
            candidate_emails: list[str] = []
            if frontmatter.get("sender_email"):
                candidate_emails.append(frontmatter["sender_email"])
            for link in frontmatter.get("participant_links") or []:
                match = _WIKILINK_PATTERN.match(link)
                target = match.group(1) if match else link
                if "@" in target:
                    candidate_emails.append(target)
            for email in candidate_emails:
                domain = _domain_of(email)
                if not domain or _is_excluded_domain(domain):
                    continue
                entry = domains.setdefault(domain, {"threads": {}, "meetings": {}})
                entry["threads"].setdefault(concept_path.stem, True)

    for meeting_path in _list_meeting_notes(vault_path):
        frontmatter, _ = read_note(meeting_path)
        for link in frontmatter.get("attendees") or []:
            match = _WIKILINK_PATTERN.match(link)
            target = match.group(1) if match else link
            if "@" not in target:
                continue
            domain = _domain_of(target)
            if not domain or _is_excluded_domain(domain):
                continue
            entry = domains.setdefault(domain, {"threads": {}, "meetings": {}})
            entry["meetings"].setdefault(meeting_path.stem, True)

    return domains


def _already_tracked_domains(entries: list[dict]) -> set[str]:
    tracked: set[str] = set()
    for entry in entries:
        tracked |= set(_split_domains(entry["fields"].get("Domain", "")))
    return tracked


def find_new_entities(vault_path: Path, entities_path: Path) -> dict:
    content = entities_path.read_text(encoding="utf-8-sig")
    entries = parse_entities(content)
    tracked = _already_tracked_domains(entries)
    evidence = build_domain_evidence(vault_path)

    new_entities: list[dict] = []
    for domain, ev in sorted(evidence.items()):
        if domain in tracked:
            continue
        name = _display_name(domain)
        entries.append({
            "section": "customer",
            "heading": name,
            "fields": {
                "Company Name": name, "Aliases": "", "Affiliate of": "",
                "Created": "No", "Ignore": "Yes", "Domain": domain,
            },
        })
        new_entities.append({
            "name": name, "domain": domain,
            "thread_count": len(ev["threads"]), "meeting_count": len(ev["meetings"]),
        })

    if new_entities:
        entities_path.write_text(render_entities(entries), encoding="utf-8")

    return {"new_entities": new_entities, "entities_path": str(entities_path)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--vault-path",
        # Defaults to what Second Brain's setup wizard writes into Hermes'
        # own .env, so a Skill never has to name a machine-specific
        # absolute path and a bundle never has to have one rewritten on
        # import. Pass it only to override.
        default=os.environ.get("SECOND_BRAIN_VAULT_PATH", ""),
    )
    parser.add_argument("--entities-name", default="Entities.md")
    args = parser.parse_args()
    if not (args.vault_path or "").strip():
        # An empty value would become Path("") -> the CWD, which is exactly the
        # silent-wrong-folder failure this whole change exists to remove.
        raise SystemExit(
            "No vault path. Set SECOND_BRAIN_VAULT_PATH in Hermes' own .env "
            "(Second Brain's setup wizard writes it) or pass --vault-path."
        )

    vault_path = Path(args.vault_path)
    # Settings/Entities.md, under the app's own .second-brain data folder
    # (relocated 2026-08-27, operator: "it should be in the Settings
    # folder... lots of Agents are Accessing this file") -- no longer
    # Work/Entities.md. Same vault-relative-literal convention
    # vault_manager.py's own Templates lookup already uses for this same
    # folder; if the operator ever relocates their App Database Folder off
    # the vault from Second Brain's own System settings page, this script
    # (and every other Entities.md consumer in this Skill) keeps looking
    # here -- a known, disclosed limitation, not a bug.
    entities_path = _data_root(vault_path) / "Settings" / args.entities_name
    if not entities_path.exists():
        print(json.dumps({"error": f"{entities_path} does not exist -- run entity-domain-extraction first"}))
        return 1

    result = find_new_entities(vault_path, entities_path)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
