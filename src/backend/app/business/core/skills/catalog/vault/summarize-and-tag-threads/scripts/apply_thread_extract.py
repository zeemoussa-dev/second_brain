"""Applies ONE structured extraction to the several places it belongs.

The design this serves (operator, 2026-09-10): reading a thread is the expensive
part of enrichment, so read it ONCE and emit everything worth knowing as JSON --
summary, the people it reveals, the actions it contains, the facts worth
remembering -- then fan that out mechanically. Four separate model passes would
cost four reads for the same content.

This script decides NOTHING. It applies a judgment already made, exactly as
`apply_thread_review.py` does; every value it writes comes from the extraction.

    python apply_thread_extract.py --vault-path P --input-file F

F is the extraction JSON:

    {
      "schema_version": 1,
      "thread_path":    str,
      "summary":        str,
      "companies":      [str],            # names, matched against real hubs
      "people":         [{"email", "name", "department", "job_title",
                          "company_name", "phone", "linkedin"}],
      "actions":        [{"text", "owner", "due"}],
      "important_info": [{"text", "company"}]
    }

`schema_version` is required and checked. This JSON is a contract between one
model pass and four independent appliers; when a fifth field is added the
appliers have to know which shape they are reading.

**The extraction is PERSISTED before anything is applied**, under
`<data>/data/ThreadExtracts/<thread-id>.json`. If an applier turns out to have a
bug, the fix re-applies from disk instead of re-reading several thousand threads
through a model -- the difference between a cheap correction and a full re-run.

**Person fields are filled, never overwritten.** This rule is inherited
deliberately: the regex signature parser this replaces was written conservatively
because "a false positive writes a wrong job title onto a real Person note, which
is worse than leaving it blank". A model extracting from the same signatures
carries the same risk, and fan-out makes it worse -- a hallucinated title lands
permanently on a note other threads then reference. So the model proposes and
this applier only fills blanks.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import vault_manager as vm

_SCHEMA_VERSION = 1
_VM_CALLER = "apply_thread_extract"
_THREAD_TEMPLATE_ID = "thread"

# Filled only when blank. `name` and `email` are excluded on purpose -- they are
# the note's identity, set at capture from the real message headers, and a model
# must never restate them.
_PERSON_FILLABLE = ("department", "role", "phone", "linkedin", "company")

# The extraction uses the vocabulary a reader would; the Person note uses its own
# field names. Mapped explicitly rather than hoping they line up.
_PERSON_FIELD_MAP = {
    "department": "department",
    "job_title": "role",
    "phone": "phone",
    "linkedin": "linkedin",
    "company_name": "company",
}


def _extracts_dir() -> Path:
    data_root = (os.environ.get("SECOND_BRAIN_DATA_PATH") or "").strip()
    if not data_root:
        raise SystemExit(
            "SECOND_BRAIN_DATA_PATH is not set -- there is nowhere to persist the "
            "extraction, and persisting it is what makes a re-apply possible."
        )
    return Path(data_root) / "data" / "ThreadExtracts"


def persist(extraction: dict, thread_id: str) -> Path:
    path = _extracts_dir() / f"{thread_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    scratch = path.with_suffix(".writing")
    scratch.write_text(json.dumps(extraction, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(scratch, path)
    return path


def _person_note(vault_path: Path, email: str) -> Path | None:
    """Person notes are named by address. Never CREATED here -- capture owns
    that, and a person this applier has never seen in a real message header
    should not be conjured from a model's reading of a signature."""
    if not email:
        return None
    name = f"{email.strip().lower()}.md"
    # Flat first -- where capture writes -- then filed under a company. The
    # People pipeline moves each person into their hub's People/ folder, and a
    # lookup of the flat folder alone would report every filed person as "not
    # in the vault" and silently stop filling their fields (2026-09-11).
    candidate = vault_path / "Work" / "People" / name
    if os.path.isfile(vm.long_path(candidate)):
        return candidate
    for root in ("Customers", "Partners"):
        base = vault_path / "Work" / root
        for pattern in (f"*/People/{name}", f"*/Affiliates/*/People/{name}"):
            for found in base.glob(pattern):
                return found
    return None


def fill_people(vault_path: Path, people: list[dict]) -> dict:
    filled, skipped_missing, left_alone = 0, 0, 0
    for person in people or []:
        note = _person_note(vault_path, person.get("email") or "")
        if note is None:
            skipped_missing += 1
            continue
        frontmatter, _ = vm.read_note(note)
        updates = {}
        for source_key, note_key in _PERSON_FIELD_MAP.items():
            value = (person.get(source_key) or "").strip()
            if not value:
                continue
            if (frontmatter.get(note_key) or "").strip():
                left_alone += 1      # a real value is already there; never overwrite
                continue
            updates[note_key] = value
        if updates:
            vm.update(vault_path, note, frontmatter=updates)
            filled += 1
    return {"people_filled": filled, "people_not_in_vault": skipped_missing,
            "fields_left_alone": left_alone}


def _render_actions(actions: list[dict]) -> str:
    lines = []
    for action in actions or []:
        text = (action.get("text") or "").strip()
        if not text:
            continue
        owner = (action.get("owner") or "").strip()
        due = (action.get("due") or "").strip()
        suffix = " — ".join(part for part in (owner, due) if part)
        lines.append(f"- [ ] {text}" + (f" ({suffix})" if suffix else ""))
    return "\n".join(lines)


def _tag_slug(text: str) -> str:
    # The same slug create-companies-partners gives a hub's own tag, so a
    # Thread tagged here from its content and one tagged by participant domain
    # carry the SAME tag rather than two spellings of one company.
    slug = re.sub(r"[^a-z0-9/]+", "-", text.lower()).strip("-")
    return slug or "untitled"


def _company_index(vault_path: Path) -> dict[str, str]:
    """Every real hub's name and aliases, lowercased -> that hub's company tag.

    Read from the HUBS, not from Entities.md: a hub is what actually exists in
    the vault, and Entities.md carries rows deliberately marked Ignore or
    Deleted that must not count as known -- otherwise a company the operator
    chose to ignore would be silently re-proposed forever.

    Only notes whose `type` is Customer or Partner. An Opportunity nested under
    a Customer has the same own-folder shape, and must never be mistaken for a
    company and tagged as one."""
    index: dict[str, str] = {}
    for root_name, kind in (("Customers", "customer"), ("Partners", "partner")):
        base = vault_path / "Work" / root_name
        if not base.is_dir():
            continue
        for hub_dir in list(base.glob("*")) + list(base.glob("*/Affiliates/*")):
            hub_md = hub_dir / f"{hub_dir.name}.md"
            if not hub_md.is_file():
                continue
            frontmatter, _ = vm.read_note(hub_md)
            if frontmatter.get("type") not in ("Customer", "Partner"):
                continue
            tag = f"{kind}/{_tag_slug(hub_dir.name)}"
            aliases = frontmatter.get("aliases") or []
            if isinstance(aliases, str):
                aliases = [aliases]
            for name in [frontmatter.get("name") or hub_dir.name, *aliases]:
                key = str(name).strip().lower()
                if key:
                    index.setdefault(key, tag)
    return index


def _known_company_names(vault_path: Path) -> set[str]:
    return set(_company_index(vault_path))


def record_unknown_companies(vault_path: Path, companies: list[str],
                             thread_id: str, thread_name: str) -> list[str]:
    """Files any company the model named that has no hub, for the operator to
    review (operator, 2026-09-11: "When Enrichement Start Check Entities in the
    new threads").

    Domain-based discovery only ever finds a company someone EMAILED. A company
    discussed in the body -- an account named in an internal forecast thread, a
    competitor, a partner mentioned by a third party -- has no domain to be
    found by, and enrichment is the only pass that reads prose. So this is the
    one place those can surface at all.

    Accumulates rather than deciding: never writes Entities.md, never creates a
    hub. A model naming a company is a suggestion, and the classification that
    follows (Customer vs Partner, and the real company name behind a
    half-remembered one) is the operator's own call."""
    if not companies:
        return []
    # Built ONCE, not per name: the comprehension form rebuilt the whole hub
    # index for every company in the list.
    known = _known_company_names(vault_path)
    unknown_names = [c for c in companies if c and c.strip().lower() not in known]
    if not unknown_names:
        return []
    path = _extracts_dir().parent / "UnknownCompanies.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        store = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        store = {}
    for name in unknown_names:
        entry = store.setdefault(name.strip(), {"seen": 0, "threads": []})
        entry["seen"] += 1
        # Capped: the point is to show the operator what it is, not to build a
        # full index -- that is what the thread's own company tags are for.
        if thread_id not in [t["id"] for t in entry["threads"]] and len(entry["threads"]) < 5:
            entry["threads"].append({"id": thread_id, "name": thread_name})
    scratch = path.with_suffix(".writing")
    scratch.write_text(json.dumps(store, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(scratch, path)
    return unknown_names


def apply_extract(vault_path: Path, extraction: dict) -> dict:
    version = extraction.get("schema_version")
    if version != _SCHEMA_VERSION:
        raise SystemExit(
            f"extraction schema_version {version!r}, this applier understands "
            f"{_SCHEMA_VERSION}. Refusing rather than writing a shape it may "
            "only partly understand."
        )

    thread_path = Path(extraction["thread_path"])
    if not thread_path.is_absolute():
        thread_path = vault_path / thread_path
    if not thread_path.is_file():
        raise SystemExit(f"no Thread note at {thread_path}")

    template = vm.load_template(vault_path, _THREAD_TEMPLATE_ID)
    frontmatter, _ = vm.read_note(thread_path)
    thread_id = frontmatter.get("id") or ""
    if not thread_id:
        raise SystemExit(
            f"{thread_path.name} carries no `id`. The extraction is keyed on it "
            "and section writes resolve through it -- refusing rather than "
            "minting one silently."
        )

    stored_at = persist(extraction, thread_id)

    result = {"thread_id": thread_id, "extraction_saved_to": str(stored_at)}

    summary = (extraction.get("summary") or "").strip()
    if summary:
        vm.modify_section(vault_path, template, section="Summary", content=summary,
                          mode="replace", note_id=thread_id, caller=_VM_CALLER)
        result["summary_written"] = True

    actions = _render_actions(extraction.get("actions") or [])
    if actions:
        vm.modify_section(vault_path, template, section="Actions", content=actions,
                          mode="replace", note_id=thread_id, caller=_VM_CALLER)
        result["actions_written"] = len(extraction.get("actions") or [])

    result.update(fill_people(vault_path, extraction.get("people") or []))
    # `important_info` deliberately NOT applied here: it belongs on a Customer or
    # Partner hub's own captures note, and those hubs are owned by
    # create-companies-partners. Applying it from this side would put two
    # scripts in charge of one note. Carried in the persisted extraction so the
    # hub-side applier can consume it without re-reading the thread.
    result["important_info_deferred"] = len(extraction.get("important_info") or [])

    # Company TAGS are not applied here. Tagging is its own pipeline, and it
    # reads the extraction persisted above (operator, 2026-09-11: "Enrich is
    # different from Tagging, 2 Pipelines now").
    unknown = record_unknown_companies(
        vault_path, extraction.get("companies") or [], thread_id,
        frontmatter.get("thread_name") or thread_path.stem)
    if unknown:
        result["unknown_companies"] = unknown

    # Freshness, stamped LAST so a crash mid-apply leaves the thread looking
    # unenriched and it is simply picked up again.
    #
    # The count matters as much as the timestamp. `last_summarized_at >=
    # last_message_at` is the rule inherited from apply_thread_review, and it
    # only catches a thread that grew at the NEWEST end. A history backfill adds
    # messages at the OLDEST end without moving last_message_at at all, so a
    # conversation whose earlier half arrives later would stay marked fresh
    # against a summary that never saw it.
    message_count = len(list((thread_path.parent / "messages").glob("*.md")))
    vm.update(vault_path, thread_path, frontmatter={
        "last_summarized_at": datetime.now(timezone.utc).isoformat(),
        "summarized_message_count": str(message_count),
    })
    result["summarized_message_count"] = message_count
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault-path", default=os.environ.get("SECOND_BRAIN_VAULT_PATH", ""))
    parser.add_argument("--input-file", required=True)
    args = parser.parse_args()
    if not (args.vault_path or "").strip():
        print("SECOND_BRAIN_VAULT_PATH is not set and --vault-path was not given")
        return 2
    extraction = json.loads(Path(args.input_file).read_text(encoding="utf-8"))
    print(json.dumps(apply_extract(Path(args.vault_path), extraction), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
