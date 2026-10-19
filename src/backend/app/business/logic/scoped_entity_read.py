"""What is known about one resolved entity, read from that entity's own scope
(`REQ-SB-95-US-05-T04`, `ADR-037`, `ADR-032`).

Hub synthesis FIRST, then that entity's tagged evidence newest first -- and
nothing else, from nowhere else. "Give me the updates about X" used to be a
whole-vault search because searching was the only verb available; a search
returns thirty mails ranked by term frequency and buries the one note that
says what is actually going on. The order here is the requirement, not a
presentation preference: a read that hands back thirty correct Threads ahead
of the one hub note has failed even though every item is right.

**Why this is a module of its own rather than another function in
`tag_resolution.py`.** That module's whole claim is that it reads no note and
touches no index -- its own test file arms `VaultManager.search`,
`hybrid_search.search` AND `get_entries_for_tag` to fail every test in it, so
"a registry lookup, never a fuzzy search over note titles" is enforced by
construction. Putting a note reader inside it would delete that tripwire and
with it the only mechanical proof of the property. Two modules keep both
claims checkable: resolution answers *which tag*, this answers *what the tag
holds*. `business/logic/` is where cross-entity composition belongs
(`CLAUDE.md`'s module layout), and this composes the resolver, the tag-keyed
projection and the note reader.

**The vault is reached ONLY through the tag-keyed projection.**
`VaultManager.get_entries_for_tag(tag)` is the single door; no search entry
point is called on any path, including the path where the entity turns out to
have no evidence at all. Widening to the whole vault is the exact failure this
story exists to remove, so it is not a fallback and not an empty-result
consolation: an entity with no hub, or with no evidence, is told so.

**Every note is addressed by its own `path`, never by its stem.** The by-stem
map holds one note per name (`BUG-076`), so a stem lookup can hand back a
*different* note that happens to share a filename -- which, in a module whose
contract is "nothing outside the tag scope is read", would be the one way to
break it without ever calling a search. Bodies are read with the same
`vault_writer.read_note` primitive `get_note_detail` uses, pointed straight at
the projection entry's own path.

**The recency fields are the real ones, and none is invented.**
`business/logic/capture_freshness.py` already fixes this vault's convention and
is the single source of it: a `Meeting` is dated by `start`, a `RawMessage` by
`received`, and a `Thread` carries `last_message_at` kept current by the
email-capture pipeline. Its `_parsed` is imported rather than copied, because
two parsers for "what a stamp in this vault looks like" is how one of them
ends up not understanding the space-separated form capture really writes
(`2026-10-09 17:11:47.410000+00:00`). It is private and this task may not
rename it -- `capture_freshness.py` is not in this task's `## Files to
Modify`, and a second copy would be worse than a documented private import.

One deliberate difference from that module: a **future** stamp is kept here.
`capture_freshness` drops it because its question is "when did something last
land", and next week's meeting would mask a capture that stopped. The question
here is "what is known about this entity", and next week's meeting is
legitimately the newest thing known.

**The fallback rule for a note this cannot date, stated once and enforced in
one place -- `evidence_sort_key`:**

> A note whose recency field is missing, empty or unparseable -- or whose note
> type has no known recency field at all -- is **undated**, and every undated
> note sorts **after every dated note**, however old the dated one is. Undated
> notes are ordered among themselves by stem and then path, case-insensitively,
> so the order is a rule rather than whatever order the vault walk happened to
> produce.

Last, never first, and never silently "treat as newest": the read's one
promise is *newest first*, and a note that cannot be dated cannot be claimed
to be the newest without making that promise false exactly where a reader
checks it. Sorting it to the bottom makes a missing stamp visible as a
degradation instead of letting it impersonate today's news. It stays inside
the scope and is still returned -- being undated is not a reason to drop a
note that carries the entity's tag.

**The hub is found INSIDE the tag scope.** The registered hub is matched
against the notes carrying the entity's tag, not fetched from the vault by
name. That is what makes "every note in the result carries that entity's tag"
true by construction rather than by assertion. The consequence is deliberate:
a hub note that does not carry its own entity tag is reported as not found,
because reading it would mean reading outside the scope, and an untagged hub
is a real vault defect this read should surface rather than paper over.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from app.business.core.vault import note_text
from app.business.core.vault.vault_manager import VaultManager
from app.business.logic import tag_resolution
# Private on purpose at its own module, imported on purpose here: see the
# module docstring -- one parser for this vault's two real stamp formats.
from app.business.logic.capture_freshness import _parsed as parse_vault_timestamp
from app.config import settings
from app.data_access import vault_writer

_logger = logging.getLogger(__name__)

_vault_manager = VaultManager()

SYNTHESIS = "synthesis"
EVIDENCE = "evidence"

DATED = "dated"
UNDATED = "undated"

HUB_FOUND = "found"
HUB_NOT_REGISTERED = "none_registered"
HUB_NOT_FOUND_IN_SCOPE = "not_found_in_scope"

#: The documented fallback, in one sentence, where a reader looking at the
#: result will find it. The rule itself is implemented once, in
#: `evidence_sort_key`, and nowhere else.
UNDATED_EVIDENCE_RULE = (
    "a note whose recency field is missing, empty or unparseable -- or whose type has no known "
    "recency field -- is undated and sorts after every dated note, ordered by stem then path"
)

#: Each note kind's OWN real recency field. Not a guess and not extensible by
#: convention: a kind absent from this map is undated by the rule above rather
#: than dated by a field invented for it.
RECENCY_FIELD_BY_NOTE_TYPE = {
    "Thread": "last_message_at",
    "Meeting": "start",
    "RawMessage": "received",
}

#: How many evidence notes one read returns. An entity with ten thousand
#: message notes is the normal case on this install, and a read that
#: materialised every body would be unusable; what makes a cap honest rather
#: than a quiet lie is that `evidence_total` always reports how many tagged
#: notes there really are and `evidence_truncated` says the list was cut.
DEFAULT_EVIDENCE_LIMIT = 20

_NOTE_SUFFIX = ".md"
_WIKILINK_OPEN = "[["
_WIKILINK_CLOSE = "]]"
_PATH_SEPARATOR = "/"
_WINDOWS_PATH_SEPARATOR = "\\"


@dataclass
class ScopedNote:
    """One note inside the entity's tag scope, as the read hands it back.

    `recency` is `dated` or `undated` and `undated_because` says which it was
    and why, so a reader can tell "this is genuinely the oldest" from "nobody
    could date this" without re-reading the note.
    """
    role: str
    stem: str
    path: str
    title: str
    note_type: object
    tags: list[str]
    recency_field: str | None
    recency_at: str | None
    recency_epoch: float | None
    recency: str
    undated_because: str | None
    body: str = ""
    body_unreadable: str | None = None

    @property
    def carries(self) -> list[str]:
        return list(self.tags)


@dataclass
class ScopedEntityRead:
    """One entity's own answer: its synthesis, then its evidence, then the
    honest account of anything that was not there.

    `performed` is the one field a caller must branch on, for the reason
    `TagResolution.resolved` and `ActionCallVerdict.accepted` are separate from
    their outcomes: a read that was never performed and a read that found
    nothing are different facts, and a caller that had to infer the difference
    from an empty list would report "nothing is known about X" for a name that
    simply did not resolve.
    """
    name_as_asked: str
    performed: bool
    message: str
    kind: object = None
    tag: str | None = None
    hub_as_registered: str | None = None
    hub_status: str = HUB_NOT_REGISTERED
    synthesis: ScopedNote | None = None
    evidence: list[ScopedNote] = field(default_factory=list)
    evidence_total: int = 0
    evidence_truncated: bool = False
    hub_matched_more_than_one: list[str] = field(default_factory=list)
    scope_failure: str | None = None
    resolution: tag_resolution.TagResolution | None = None

    @property
    def notes(self) -> list[ScopedNote]:
        """The whole result in its required order: the hub's synthesis first
        when there is one, then the evidence newest first."""
        return ([self.synthesis] if self.synthesis is not None else []) + list(self.evidence)

    @property
    def found_anything(self) -> bool:
        return self.synthesis is not None or bool(self.evidence)


def evidence_sort_key(note: ScopedNote) -> tuple:
    """Newest first, undated last -- the one implementation of the documented
    fallback rule (`UNDATED_EVIDENCE_RULE`).

    The first element of the key is what enforces it: every dated note scores
    0 and every undated note scores 1, so no dated note, however old, can ever
    sort below an undated one. Stem and path break the remaining ties so two
    runs over the same vault order the result identically regardless of the
    order the walk produced.
    """
    if note.recency == DATED and note.recency_epoch is not None:
        return (0, -note.recency_epoch, note.stem.casefold(), note.path.casefold())
    return (1, 0.0, note.stem.casefold(), note.path.casefold())


def read_scoped_entity(
    resolution: tag_resolution.TagResolution,
    evidence_limit: int = DEFAULT_EVIDENCE_LIMIT,
) -> ScopedEntityRead:
    """Everything known about one resolved entity, from that entity's scope
    alone: its hub synthesis, then its tagged evidence newest first.

    A resolution that did not resolve performs no read at all -- it does not
    fall back to a search, and it does not return someone else's notes under
    this entity's name.
    """
    name_as_asked = getattr(resolution, "name_as_asked", "") or ""
    if not getattr(resolution, "resolved", False) or not getattr(resolution, "tag", None):
        return ScopedEntityRead(
            name_as_asked=name_as_asked,
            performed=False,
            message=(
                f"no scoped read was performed for \"{name_as_asked}\": it did not resolve to an "
                f"entity, and nothing was searched for in its place -- "
                f"{getattr(resolution, 'message', 'no resolution was supplied')}"
            ),
            resolution=resolution if isinstance(resolution, tag_resolution.TagResolution) else None,
        )

    tag = resolution.tag
    try:
        tagged_entries = list(_vault_manager.get_entries_for_tag(tag))
    except Exception as exc:  # noqa: BLE001 -- any projection failure is still not a reason to widen
        failure = f"{type(exc).__name__}: {exc}"
        _logger.warning(
            "the tag-keyed index could not be read for %r, so nothing is being reported about it "
            "and nothing is being searched for instead: %s", tag, failure,
        )
        return ScopedEntityRead(
            name_as_asked=name_as_asked,
            performed=False,
            message=(
                f'"{name_as_asked}" resolves to {tag}, but the tag-keyed index could not be read, '
                f"so nothing is being reported about it: {failure}"
            ),
            kind=resolution.kind,
            tag=tag,
            hub_as_registered=resolution.hub,
            scope_failure=failure,
            resolution=resolution,
        )

    hub_position, hub_matches = _match_hub(tagged_entries, resolution.hub)

    synthesis = None
    if hub_position is not None:
        synthesis = _scoped_note(tagged_entries[hub_position], SYNTHESIS)
        _read_body_into(synthesis)

    evidence = sorted(
        (_scoped_note(entry, EVIDENCE)
         for position, entry in enumerate(tagged_entries) if position != hub_position),
        key=evidence_sort_key,
    )
    evidence_total = len(evidence)
    limit = evidence_total if evidence_limit is None or evidence_limit < 0 else evidence_limit
    returned_evidence = evidence[:limit]
    for note in returned_evidence:
        _read_body_into(note)

    hub_status = _hub_status(resolution.hub, hub_position)
    return ScopedEntityRead(
        name_as_asked=name_as_asked,
        performed=True,
        message=_message(name_as_asked, tag, resolution.hub, hub_status,
                         evidence_total, len(returned_evidence)),
        kind=resolution.kind,
        tag=tag,
        hub_as_registered=resolution.hub,
        hub_status=hub_status,
        synthesis=synthesis,
        evidence=returned_evidence,
        evidence_total=evidence_total,
        evidence_truncated=len(returned_evidence) < evidence_total,
        hub_matched_more_than_one=hub_matches if len(hub_matches) > 1 else [],
        resolution=resolution,
    )


def read_entity_named(
    name: str,
    evidence_limit: int = DEFAULT_EVIDENCE_LIMIT,
) -> ScopedEntityRead:
    """The whole question in one call: resolve the name, then read that
    entity's scope -- and perform no read at all if it did not resolve.

    The guard lives here rather than in every caller because "did not resolve"
    must never become "searched the vault instead", and a rule each caller has
    to remember is a rule one of them will not.
    """
    return read_scoped_entity(tag_resolution.resolve(name), evidence_limit=evidence_limit)


def _hub_status(hub_as_registered: object, hub_position: int | None) -> str:
    if not isinstance(hub_as_registered, str) or not hub_as_registered.strip():
        return HUB_NOT_REGISTERED
    return HUB_FOUND if hub_position is not None else HUB_NOT_FOUND_IN_SCOPE


def _message(name_as_asked: str, tag: str, hub_as_registered: object, hub_status: str,
             evidence_total: int, evidence_returned: int) -> str:
    if hub_status == HUB_FOUND:
        hub_sentence = "its hub synthesis comes first"
    elif hub_status == HUB_NOT_REGISTERED:
        hub_sentence = "it registers no hub note, so there is no synthesis to lead with"
    else:
        hub_sentence = (
            f"its registered hub ({hub_as_registered}) is not among the notes carrying {tag}, "
            f"so there is no synthesis to lead with and none was read from outside the tag"
        )
    if evidence_total == 0:
        evidence_sentence = f"no note in the vault carries {tag}, and nothing else was searched"
    elif evidence_returned < evidence_total:
        evidence_sentence = (
            f"{evidence_returned} of {evidence_total} tagged evidence note(s), newest first"
        )
    else:
        evidence_sentence = f"{evidence_total} tagged evidence note(s), newest first"
    return f'"{name_as_asked}" read from {tag} alone: {hub_sentence}; {evidence_sentence}'


def _scoped_note(entry: dict, role: str) -> ScopedNote:
    """One projection entry as a returned note, dated by its own kind's real
    field or honestly marked undated. No body yet -- bodies are read only for
    the notes that are actually returned."""
    frontmatter = entry.get("frontmatter") or {}
    note_type = frontmatter.get("type")
    recency_field = (
        RECENCY_FIELD_BY_NOTE_TYPE.get(note_type) if isinstance(note_type, str) else None
    )
    stamp = frontmatter.get(recency_field) if recency_field else None
    parsed = parse_vault_timestamp(stamp) if recency_field else None

    if recency_field is None:
        undated_because = (
            f"no recency field is known for a note of type {note_type!r}, and this read invents "
            f"none"
        )
    elif not str(stamp or "").strip():
        undated_because = f"its {recency_field} is missing"
    elif parsed is None:
        undated_because = f"its {recency_field} ({stamp!r}) could not be read as a timestamp"
    else:
        undated_because = None

    tags = entry.get("tags")
    return ScopedNote(
        role=role,
        stem=entry.get("stem", ""),
        path=str(entry.get("path", "")),
        # The same title rule the vault browser already uses: a captured note's
        # own subject when it has one, otherwise its filename stem.
        title=frontmatter.get("subject") or entry.get("stem", ""),
        note_type=note_type,
        tags=list(tags) if isinstance(tags, list) else [],
        recency_field=recency_field,
        recency_at=parsed.isoformat() if parsed is not None else None,
        recency_epoch=parsed.timestamp() if parsed is not None else None,
        recency=DATED if parsed is not None else UNDATED,
        undated_because=undated_because,
    )


def _read_body_into(note: ScopedNote) -> None:
    """The note's readable body, from its own path.

    By path and never by stem: a stem lookup can return a different note that
    shares the filename (`BUG-076`), which is the one way a scoped read could
    serve a note from outside its scope without ever calling a search. A note
    that cannot be read says so and keeps its place -- one unreadable note must
    not take down the answer about the whole entity.
    """
    try:
        frontmatter, body = vault_writer.read_note(Path(note.path))
    except Exception as exc:  # noqa: BLE001 -- a bad note is a fact about that note, not an outage
        note.body_unreadable = f"{type(exc).__name__}: {exc}"
        _logger.warning("a note inside the scope could not be read and is reported empty: %s (%s)",
                        note.path, note.body_unreadable)
        return
    # A captured email's body is the original HTML on disk and is converted on
    # the way out, exactly as `get_note_detail` does it (`BUG-081`).
    note.body = note_text.readable_body(frontmatter, body)


def _match_hub(entries: list[dict], hub_as_registered: object) -> tuple[int | None, list[str]]:
    """Which of the tagged notes is the registered hub, if any.

    Matched inside the scope on purpose (see the module docstring). A spelling
    that names a path wins over one that only matches a filename stem, because
    two tagged notes may legitimately share a stem; when only the stem
    fallback matched and it matched more than one, every match is reported so
    the pick is disclosed rather than silent.
    """
    if not isinstance(hub_as_registered, str) or not hub_as_registered.strip():
        return None, []
    asked = _normalized_note_name(hub_as_registered)
    if not asked:
        return None, []

    matched_by_path: list[int] = []
    matched_by_stem: list[int] = []
    for position, entry in enumerate(entries):
        path_spellings, stem_spelling = _note_spellings(entry)
        if asked in path_spellings:
            matched_by_path.append(position)
        elif asked == stem_spelling:
            matched_by_stem.append(position)

    matched = matched_by_path or matched_by_stem
    if not matched:
        return None, []
    return matched[0], [str(entries[position].get("path", "")) for position in matched]


def _note_spellings(entry: dict) -> tuple[set[str], str]:
    """Every way the registered hub might name this note: its full path, its
    vault-relative path, each with and without the `.md` suffix -- and,
    separately, its bare filename stem."""
    path = Path(str(entry.get("path", "")))
    spellings = {str(path), str(path.with_suffix(""))}
    vault_root = settings.vault_path
    if vault_root is not None:
        try:
            relative = path.relative_to(Path(vault_root))
        except ValueError:
            relative = None
        if relative is not None:
            spellings.update({str(relative), str(relative.with_suffix(""))})
    return (
        {_normalized_note_name(spelling) for spelling in spellings},
        _normalized_note_name(str(entry.get("stem", ""))),
    )


def _normalized_note_name(text: str) -> str:
    """One spelling of a note's name, comparable with another.

    A registered hub is written by hand, so it arrives as a wikilink, a
    Windows path, a POSIX path, with or without `.md`, in whatever case the
    author used. None of those differences is a different note.
    """
    name = text.strip()
    if name.startswith(_WIKILINK_OPEN) and name.endswith(_WIKILINK_CLOSE):
        name = name[len(_WIKILINK_OPEN):-len(_WIKILINK_CLOSE)].strip()
    name = name.replace(_WINDOWS_PATH_SEPARATOR, _PATH_SEPARATOR)
    if name.casefold().endswith(_NOTE_SUFFIX):
        name = name[: -len(_NOTE_SUFFIX)]
    return name.strip(_PATH_SEPARATOR).casefold()
