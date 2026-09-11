"""Applies ONE structured extraction to the several places it belongs.

The design this serves (operator, 2026-09-10): reading a thread is the expensive
part of enrichment, so read it ONCE and emit everything worth knowing as JSON --
summary, the people it reveals, the actions it contains, the facts worth
remembering -- then fan that out mechanically. Four separate model passes would
cost four reads for the same content.

This script decides NOTHING. It applies a judgment already made, exactly as
`apply_thread_review.py` does; every value it writes comes from the extraction.

It writes ONLY onto the Thread -- its Summary and Actions -- and saves the read.
Everything else the read fans out to belongs to the pipeline that owns that
note (operator, 2026-09-11): company tags to Tagging; each company's History
and Captures, and the People fields, to the Company pipeline. Both work from the
extraction persisted here, so neither needs the model again.

    python apply_thread_extract.py --vault-path P --input-file F

F is the extraction JSON:

    {
      "schema_version": 1,
      "thread_id":      str,              # the conversation id the batch gives;
                                          # the Thread is found from it in code
      "thread_path":    str,              # accepted instead of thread_id; the
                                          # saved read always carries it
      "summary":        str,
      "companies":      [str],            # names, matched against real hubs
      "people":         [{"email", "name", "department", "job_title",
                          "company_name", "phone", "linkedin"}],
      "actions":        [{"text", "owner", "due"}],
      "history_line":   str,              # optional: one line for each company's History
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
import time
from contextlib import contextmanager
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


def _company_hubs(vault_path: Path) -> list[tuple[str, Path, list[str]]]:
    """(company tag, hub note, lowercased names) for every real hub -- its name
    and aliases, Affiliates included.

    Read from the HUBS, not from Entities.md: a hub is what actually exists in
    the vault, and Entities.md carries rows deliberately marked Ignore or
    Deleted that must not count as known -- otherwise a company the operator
    chose to ignore would be silently re-proposed forever.

    Only notes whose `type` is Customer or Partner. An Opportunity nested under
    a Customer has the same own-folder shape, and must never be mistaken for a
    company -- tagged as one, or given a History entry."""
    hubs: list[tuple[str, Path, list[str]]] = []
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
            aliases = frontmatter.get("aliases") or []
            if isinstance(aliases, str):
                aliases = [aliases]
            names = [str(n).strip().lower() for n in [frontmatter.get("name") or hub_dir.name, *aliases]]
            hubs.append((f"{kind}/{_tag_slug(hub_dir.name)}", hub_md, [n for n in names if n]))
    return hubs


def _company_index(vault_path: Path) -> dict[str, str]:
    """Every real hub's name and aliases, lowercased -> that hub's company tag."""
    index: dict[str, str] = {}
    for tag, _hub, names in _company_hubs(vault_path):
        for name in names:
            index.setdefault(name, tag)
    return index


def _company_hub_notes(vault_path: Path) -> dict[str, Path]:
    """Every real hub's name and aliases, lowercased -> the hub note itself."""
    notes: dict[str, Path] = {}
    for _tag, hub_md, names in _company_hubs(vault_path):
        for name in names:
            notes.setdefault(name, hub_md)
    return notes


def _known_company_names(vault_path: Path) -> set[str]:
    return set(_company_index(vault_path))


# ── Customer Logs: a dated line in each named company's History ─────────────
#
# One of the four places the operator's design fans a single read out to
# (2026-09-10: "{Summary, People Data, Thread Actions, Important Info} ... fill
# more than just the Thread: People, Customer Logs, Important Captures"). The
# applier this replaced wrote them; this one did not until 2026-09-11, and not
# one company History in the vault had a single entry.

_HISTORY_ENTRY = re.compile(r"^- (\d{4}-\d{2}-\d{2}): (.+)$")
_SENTENCE_END = re.compile(r"(?<=[.!?])\s")
_WHITESPACE = re.compile(r"\s+")
_HISTORY_LINE_MAX = 160


def _history_line(extraction: dict) -> str:
    """The one line a company's History gets for this Thread: the reader's own
    `history_line` when it wrote one, otherwise the first sentence of its
    summary -- which is all an extraction saved before the field existed has."""
    line = _WHITESPACE.sub(" ", str(extraction.get("history_line") or "")).strip()
    if not line:
        summary = _WHITESPACE.sub(" ", str(extraction.get("summary") or "")).strip()
        line = _SENTENCE_END.split(summary, 1)[0] if summary else ""
    line = line.rstrip(". ")
    if len(line) > _HISTORY_LINE_MAX:
        line = line[:_HISTORY_LINE_MAX].rsplit(" ", 1)[0].rstrip(",;: ") + "…"
    return line


def _history_update(hub_md: Path, date: str, line: str, thread_link: str):
    """(history note, frontmatter, new body) -- or None when nothing changes.

    ONE entry per Thread: an entry already pointing at this Thread is replaced,
    not joined by a second. A Thread enriched again after it grew gets its
    latest line at its latest date, instead of the company's History reading
    like a changelog of one conversation. Newest first; the note's header and
    frontmatter are kept."""
    history = hub_md.parent / f"{hub_md.stem}-history.md"
    if os.path.isfile(vm.long_path(history)):
        frontmatter, body = vm.read_note(history)
    else:
        frontmatter = {"type": "History", "name": f"{hub_md.stem} History",
                       "parent": f"[[{hub_md.stem}]]", "tags": ["kind/history"]}
        body = f"\n# {hub_md.stem}\n"
    lines = body.splitlines()
    kept = [line_ for line_ in lines if not _HISTORY_ENTRY.match(line_)]
    entries = [m.groups() for line_ in lines if (m := _HISTORY_ENTRY.match(line_))]
    suffix = f" -- {thread_link}"
    updated = [(d, t) for d, t in entries if not t.endswith(suffix)]
    updated.append((date, f"{line}{suffix}"))
    if set(updated) == set(entries):
        return None
    updated.sort(key=lambda entry: entry[0], reverse=True)
    while kept and not kept[-1].strip():
        kept.pop()
    new_body = "\n".join(kept) + "\n\n" + "\n".join(f"- {d}: {t}" for d, t in updated) + "\n"
    return history, frontmatter, new_body


def write_history(vault_path: Path, thread_path: Path, thread_frontmatter: dict,
                  extraction: dict, *, hubs: dict[str, Path] | None = None,
                  dry_run: bool = False) -> list[str]:
    """A dated entry, linking back to this Thread, in the History of every
    company the reader named that has a hub. Returns the hubs whose History
    gained or changed an entry. Dated by the Thread's own last message -- when
    it happened, not when it was read."""
    companies = [c for c in (extraction.get("companies") or []) if c and str(c).strip()]
    line = _history_line(extraction)
    if not companies or not line:
        return []
    hubs = _company_hub_notes(vault_path) if hubs is None else hubs
    date = (str(thread_frontmatter.get("last_message_at") or "")[:10]
            or datetime.now(timezone.utc).date().isoformat())
    link = f"[[{thread_path.stem}]]"
    written: list[str] = []
    seen: set[Path] = set()
    for name in companies:
        hub_md = hubs.get(str(name).strip().lower())
        if hub_md is None or hub_md in seen:
            continue
        seen.add(hub_md)
        update = _history_update(hub_md, date, line, link)
        if update is None:
            continue
        if not dry_run:
            vm.write_note(*update)
        written.append(hub_md.stem)
    return written


def resolve_thread(vault_path: Path, extraction: dict, thread_id: str) -> Path | None:
    """The Thread a saved extraction belongs to: its recorded path or, when the
    Thread has been renamed since it was read, the note carrying its id."""
    thread = Path(extraction.get("thread_path") or "")
    if not thread.is_absolute():
        thread = vault_path / thread
    if os.path.isfile(vm.long_path(thread)):
        return thread
    return vm.find_by_id(vault_path, thread_id, note_name="Threads")


@contextmanager
def _exclusive(path: Path, *, timeout: float = 60.0, stale_after: float = 300.0):
    """One writer at a time for a file every Enrichment job read-modify-writes.

    Enrichment runs as parallel jobs (2026-09-11). Two of them updating
    UnknownCompanies.json at once would each read it, each add their names,
    and the later rename would silently drop the other's. A lock file created
    with O_EXCL is atomic on every platform; one left behind by a crashed job
    is broken after `stale_after` seconds rather than blocking every job
    forever."""
    lock = path.with_suffix(path.suffix + ".lock")
    deadline = time.monotonic() + timeout
    while True:
        try:
            os.close(os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
            break
        except FileExistsError:
            try:
                if time.time() - lock.stat().st_mtime > stale_after:
                    lock.unlink()
                    continue
            except OSError:
                pass
            if time.monotonic() > deadline:
                raise TimeoutError(f"{lock} has been held for over {timeout:.0f}s")
            time.sleep(0.2)
    try:
        yield
    finally:
        try:
            lock.unlink()
        except OSError:
            pass


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
    with _exclusive(path):
        try:
            store = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            store = {}
        for name in unknown_names:
            entry = store.setdefault(name.strip(), {"seen": 0, "threads": []})
            entry["seen"] += 1
            # Capped: the point is to show the operator what it is, not to build
            # a full index -- that is what the thread's own company tags are for.
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

    given_id = str(extraction.get("thread_id") or "").strip()
    if given_id:
        # Found in code, not typed (2026-09-11): an agent building a path from
        # a Thread's title got it wrong -- a `|` Windows never allows, a name
        # cut at 80 characters, an invisible character the prompt stripped --
        # and those Threads failed on every run.
        thread_path = vm.find_by_id(vault_path, given_id, note_name="Threads")
        if thread_path is None:
            raise SystemExit(f"no Thread with id {given_id!r}")
        # The saved read keeps a path as well: Tagging and Company resolve it.
        try:
            saved_path = thread_path.relative_to(vault_path).as_posix()
        except ValueError:
            saved_path = str(thread_path)
        extraction = {**extraction, "thread_path": saved_path}
    else:
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

    # People fields are NOT written here. They belong to the Company pipeline,
    # which reads the extraction saved above (operator, 2026-09-11: "The
    # Company pipeline should pull the people as well").
    result["people_deferred"] = len(extraction.get("people") or [])
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
