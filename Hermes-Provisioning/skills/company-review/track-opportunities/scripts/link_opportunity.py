"""CLI entry point: links ONE existing Thread or Meeting note to ONE
existing Opportunity (2026-08-22, operator's own explicit choice:
"Manual only, you say so in chat" -- never a proactive/automatic guess,
since a Customer can have several open Opportunities at once and
guessing which one a Thread/Meeting belongs to is a real risk this
vault's own history already warns against, operator: "the company in
message is the company not the parent" / the earlier person-tagging
cascade bug -- same "never fabricate, never guess" discipline applied
here). The agent parses the operator's own real intent ("link this
thread to the ADNOC HPC Expansion opp") first; this script only ever
applies that decision.

Usage:
    python link_opportunity.py --vault-path P --note-path N --opportunity TITLE [--customer NAME]

N: the Thread's or Meeting's own concept .md path (vault-absolute or
relative -- whatever the agent's own read_file call used).
TITLE: the Opportunity's own title, matched against real Opportunity
notes' own `title`-derived stem or frontmatter `name` -- case-
insensitive, never fuzzy/partial (a wrong-but-plausible match is worse
than reporting "not found"). --customer optionally disambiguates if the
same title genuinely exists under more than one Customer.

Prints {"linked": bool, "note_path": str, "opportunity_path": str} or
{"error": str}.

`vault_manager.py`-based migration, `opportunities` frontmatter write
(2026-09-02, REQ-SB-88-US-02-T01): the target note's `opportunities`
frontmatter-list write goes through this Skill's own already-deployed
`vault_manager.py` copy (`vm.read_note`/`vm.update`) instead of this
file's own hand-rolled frontmatter-line rewrite -- the same shape
`apply_thread_review.py`'s own frontmatter stamping already uses.
`resolve_opportunity()`/`_iter_opportunity_notes()` (title/`--customer`
matching, ambiguity handling) are UNCHANGED, real Opportunity-specific
business logic, still using this file's own local `read_note`.

`## Related` write migration (2026-09-02, REQ-SB-88-US-02-T02): the
`## Related` write now goes through `vm.modify_section`
(`caller="link_opportunity"`), the same already-public, template-driven
entry point `apply_thread_review.py` already uses -- no reach into any
underscore-private helper. The target Template (`"thread"` or
`"meeting"`) is derived from the note's own real `Work/Threads/` vs
`Work/Meetings/` path prefix (`_template_id_for_note`). A real
pre-migration Thread/Meeting note carries no `id` frontmatter field yet
if no other migrated caller has touched it first -- the first migrated
`## Related` write mints one and backfills it via `vm.update`, same
id-mint-if-missing pattern this project's migrations already establish.
The real, deployed Thread `Template.json`'s `## Related` section gained
`link_opportunity` as a second, additive `allowed_callers` entry
alongside `link_person_to_thread` -- the Meeting template's own
`## Related` carries no `allowed_callers` key at all, so it needed no
edit. The now-fully-superseded local `_RELATED_CALLER`/
`_CALLER_ALLOW_LISTS` guard and the local `insert_body_section_if_missing`/
`read_body_section`/`replace_body_section`/`_format_frontmatter_value`
primitives are removed -- zero remaining callers. Access to `## Related`
for a Thread target is now enforced SOLELY by the Thread template's own
`allowed_callers` declaration, never local Python.
"""
from __future__ import annotations

import argparse
import os
import json
import re
import uuid
from pathlib import Path

import vault_manager as vm

_FRONTMATTER_LINE = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*):\s?(.*)$")
_LIST_ITEM_PATTERN = re.compile(r'"((?:[^"\\]|\\.)*)"')

# The Thread/Meeting templates' own declared caller identity for their
# machine_write sections this script writes -- REQ-SB-88-US-02-T02,
# mirrors apply_thread_review.py's own _VM_CALLER precedent
# (REQ-SB-87-US-04-T01).
_VM_CALLER = "link_opportunity"


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


def _template_id_for_note(vault_path: Path, note_path: Path) -> str:
    """Derives which template to load from the target note's own real
    location -- trivially derivable from its `Work/Threads/` vs
    `Work/Meetings/` prefix (architect finding, REQ-SB-88-US-02). Never
    guesses for a note outside either root -- refuses with a real error
    instead."""
    try:
        relative_parts = note_path.relative_to(vault_path).parts
    except ValueError:
        relative_parts = note_path.parts
    if len(relative_parts) >= 2 and relative_parts[0] == "Work" and relative_parts[1] == "Threads":
        return "thread"
    if len(relative_parts) >= 2 and relative_parts[0] == "Work" and relative_parts[1] == "Meetings":
        return "meeting"
    raise vm.VaultManagerError(
        f"cannot derive a template for {note_path} -- expected it under Work/Threads/ or Work/Meetings/"
    )


def _iter_opportunity_notes(vault_path: Path):
    customers_root = vault_path / "Work" / "Customers"
    if not customers_root.exists():
        return
    # Search recursively to support affiliate/subcompany nesting like
    # Work/Customers/<Parent>/Affiliates/<Affiliate>/Opportunities/<Title>/<Title>.md
    for md_path in customers_root.rglob("Opportunities/*/*.md"):
        if md_path.is_file() and md_path.parent.name == md_path.stem:
            yield md_path


def resolve_opportunity(vault_path: Path, title: str, customer_name: str | None) -> tuple[Path | None, list[Path]]:
    """Returns (single_match, all_matches) -- all_matches lets the caller
    report a genuine ambiguity (same title under >1 Customer) rather than
    silently picking one."""
    key = title.strip().lower()
    customer_key = customer_name.strip().lower() if customer_name else None
    matches: list[Path] = []
    for md_path in _iter_opportunity_notes(vault_path):
        frontmatter, _ = read_note(md_path)
        if md_path.stem.lower() != key:
            continue
        if customer_key:
            note_customer = (frontmatter.get("customer") or "").strip().lower()
            if note_customer != customer_key:
                continue
        matches.append(md_path)
    if len(matches) == 1:
        return matches[0], matches
    return None, matches


def _resolve_note_path(vault_path: Path, note_path_str: str) -> Path:
    p = Path(note_path_str)
    return p if p.is_absolute() else vault_path / p


def link_opportunity(vault_path: Path, note_path_str: str, opportunity_title: str, customer_name: str | None) -> dict:
    note_path = _resolve_note_path(vault_path, note_path_str)
    if not note_path.exists():
        return {"error": f"note not found: {note_path}"}

    opportunity_path, matches = resolve_opportunity(vault_path, opportunity_title, customer_name)
    if opportunity_path is None:
        if len(matches) > 1:
            return {
                "error": f"{opportunity_title!r} matches more than one Opportunity -- pass --customer to disambiguate",
                "candidates": [str(m) for m in matches],
            }
        return {"error": f"no Opportunity named {opportunity_title!r} exists -- create it first"}

    frontmatter, _ = vm.read_note(note_path)
    existing = list(frontmatter.get("opportunities") or [])
    wikilink = f"[[{opportunity_path.stem}]]"
    changed_frontmatter = False
    if wikilink not in existing:
        merged = existing + [wikilink]
        vm.update(vault_path, note_path, frontmatter={"opportunities": merged})
        changed_frontmatter = True

    existing_related = vm.get_section_content(note_path, "Related")
    changed_related = False
    if wikilink not in existing_related:
        lines = [line for line in existing_related.splitlines() if line.strip()]
        lines.append(f"- {wikilink}")
        template_id = _template_id_for_note(vault_path, note_path)
        template = vm.load_template(vault_path, template_id)
        note_frontmatter, _ = vm.read_note(note_path)
        note_id = note_frontmatter.get("id")
        if not note_id:
            # A real pre-migration Thread/Meeting note carries no `id`
            # field yet whenever no other migrated caller has touched it
            # first -- mint one now and persist it, same id-mint-if-
            # missing pattern REQ-SB-87-US-04-T01/REQ-SB-88-US-01-T01
            # already established.
            note_id = str(uuid.uuid4())
            vm.update(vault_path, note_path, frontmatter={"id": note_id})
        vm.modify_section(
            vault_path, template, section="Related", content="\n".join(lines), mode="replace",
            note_id=note_id, caller=_VM_CALLER,
        )
        changed_related = True

    return {
        "linked": changed_frontmatter or changed_related,
        "note_path": str(note_path),
        "opportunity_path": str(opportunity_path),
    }


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
    parser.add_argument("--note-path", required=True)
    parser.add_argument("--opportunity", required=True)
    parser.add_argument("--customer", default=None)
    args = parser.parse_args()
    if not (args.vault_path or "").strip():
        # An empty value would become Path("") -> the CWD, which is exactly the
        # silent-wrong-folder failure this whole change exists to remove.
        raise SystemExit(
            "No vault path. Set SECOND_BRAIN_VAULT_PATH in Hermes' own .env "
            "(Second Brain's setup wizard writes it) or pass --vault-path."
        )

    vault_path = Path(args.vault_path)
    result = link_opportunity(vault_path, args.note_path, args.opportunity, args.customer)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if "error" not in result else 1


if __name__ == "__main__":
    raise SystemExit(main())
