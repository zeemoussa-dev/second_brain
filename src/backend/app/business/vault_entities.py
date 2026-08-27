"""Vault > Entities (Settings, 2026-08-27) -- a real CRUD UI over the
Customer/Partner discovery registry the company-review Hermes Skill
suite reads/writes, replacing hand-editing raw markdown (operator: "I
will need to approve, delete, edit Aliases and domains for every one in
that list instead of working with the md file from settings").

Parses/renders the EXACT same format find_new_entities.py/
apply_entity_decision.py/create_companies_partners.py already use
(ported byte-for-byte, not reimplemented from scratch, so this backend
and those Hermes scripts stay round-trip compatible on the same file) --
see Hermes-Provisioning/skills/company-review/new-company-discovery/
scripts/find_new_entities.py's own parse_entities/render_entities for
the canonical source this mirrors. If that source ever changes its
format, re-mirror it here by hand.

File location (relocated 2026-08-27, operator: "it should be in the
Settings folder... lots of Agents are Accessing this file") --
settings.second_brain_data_path / "Settings" / "Entities.md", was
Work/Entities.md. "Approve" in this UI only marks an entry reviewed
(flips Ignore -> No); it does NOT create the Customer/Partner hub note
itself -- that still happens on its own via the existing
create-companies-partners Hermes cron pipeline, unchanged (operator:
"just mark it reviewed").
"""
from __future__ import annotations

from pathlib import Path

from app.config import settings

_KNOWN_FIELDS = {"Company Name", "Aliases", "Affiliate of", "Created", "Ignore", "Domain", "Deleted"}


class EntityNotFoundError(Exception):
    def __init__(self, name: str) -> None:
        super().__init__(f"No entity named {name!r}")
        self.name = name


class DuplicateEntityError(Exception):
    def __init__(self, name: str) -> None:
        super().__init__(f"An entity named {name!r} already exists")
        self.name = name


def _entities_path() -> Path:
    return settings.second_brain_data_path / "Settings" / "Entities.md"


def _parse_entities(content: str) -> list[dict]:
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
    # A real hard-delete removes the row's own Domain from the "already
    # tracked" set find_new_entities.py checks before appending a new
    # entry -- so a noise domain (SharePoint, Teams notification senders)
    # that gets deleted just gets rediscovered on the next scan (operator,
    # 2026-08-27: "sharepoint and Teams should be delete but they will
    # keep surfacing and I know they will never be a company"). Deleted:
    # Yes keeps the row (and its Domain) in the file instead -- delete_
    # entity() below sets this rather than removing the entry.
    lines.append(f"\tDeleted: {f.get('Deleted', 'No')}")
    lines.append("")
    lines.append("")


def _render_entities(entries: list[dict]) -> str:
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


def _load() -> list[dict]:
    path = _entities_path()
    if not path.exists():
        return []
    return _parse_entities(path.read_text(encoding="utf-8-sig"))


def _save(entries: list[dict]) -> None:
    path = _entities_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_render_entities(entries), encoding="utf-8")


def _to_public(entry: dict) -> dict:
    f = entry["fields"]
    return {
        "name": f.get("Company Name") or entry["heading"],
        "section": entry["section"],
        "aliases": f.get("Aliases", ""),
        "affiliate_of": f.get("Affiliate of", ""),
        "created": f.get("Created", "No") == "Yes",
        "ignore": f.get("Ignore", "No") == "Yes",
        "domain": f.get("Domain", ""),
    }


def _is_deleted(entry: dict) -> bool:
    return entry["fields"].get("Deleted", "No") == "Yes"


def list_entities() -> list[dict]:
    # Soft-deleted rows stay in the file (see delete_entity()) but must
    # never surface in the UI -- operator: "add a field called delete...
    # so it shouldn't be surfaced there."
    return [_to_public(entry) for entry in _load() if not _is_deleted(entry)]


def _find(entries: list[dict], name: str) -> dict | None:
    key = name.strip().lower()
    for entry in entries:
        entry_name = (entry["fields"].get("Company Name") or entry["heading"]).strip().lower()
        if entry_name == key:
            return entry
    return None


def update_entity(name: str, patch: dict) -> dict:
    entries = _load()
    target = _find(entries, name)
    if target is None:
        raise EntityNotFoundError(name)
    fields = target["fields"]

    if "name" in patch:
        new_name = patch["name"].strip()
        if new_name and new_name.lower() != (fields.get("Company Name") or target["heading"]).strip().lower():
            if _find(entries, new_name) is not None:
                raise DuplicateEntityError(new_name)
            target["heading"] = new_name
            fields["Company Name"] = new_name
    if "section" in patch and patch["section"] in ("customer", "partner"):
        target["section"] = patch["section"]
    if "aliases" in patch:
        fields["Aliases"] = patch["aliases"]
    if "affiliate_of" in patch:
        fields["Affiliate of"] = patch["affiliate_of"]
    if "domain" in patch:
        fields["Domain"] = patch["domain"]
    if "ignore" in patch:
        fields["Ignore"] = "Yes" if patch["ignore"] else "No"

    _save(entries)
    return _to_public(target)


def delete_entity(name: str) -> None:
    """Soft delete -- sets Deleted: Yes (and Ignore: Yes, belt-and-
    suspenders for any Hermes script instance that hasn't been redeployed
    with the Deleted field yet) rather than removing the row. A real
    removal would drop the entry's own Domain from
    find_new_entities.py's `_already_tracked_domains` check, so a noise
    domain (SharePoint, Teams notification senders) would just get
    rediscovered on the next scan -- confirmed live, operator: "sharepoint
    and Teams should be delete but they will keep surfacing and I know
    they will never be a company." list_entities() filters Deleted: Yes
    rows out, so this is invisible in the UI despite staying on disk."""
    entries = _load()
    target = _find(entries, name)
    if target is None:
        raise EntityNotFoundError(name)
    target["fields"]["Deleted"] = "Yes"
    target["fields"]["Ignore"] = "Yes"
    _save(entries)


def create_entity(
    name: str, section: str, domain: str = "", aliases: str = "", affiliate_of: str = "",
) -> dict:
    if section not in ("customer", "partner"):
        raise ValueError(f"section must be 'customer' or 'partner', got {section!r}")
    entries = _load()
    if _find(entries, name) is not None:
        raise DuplicateEntityError(name)
    entry = {
        "section": section,
        "heading": name.strip(),
        "fields": {
            "Company Name": name.strip(),
            "Aliases": aliases,
            "Affiliate of": affiliate_of,
            "Created": "No",
            "Ignore": "No",
            "Domain": domain,
        },
    }
    entries.append(entry)
    _save(entries)
    return _to_public(entry)
