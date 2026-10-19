"""The scoped entity read (REQ-SB-95-US-05-T04; AC-02).

Hub synthesis first, then that entity's tagged evidence newest first, and
nothing from outside its tag -- answered from the tag-keyed projection alone,
with no whole-vault search on any path including the one where the entity has
no evidence at all.

The vault here is a real tmp vault walked by the real indexer, seeded the way
tests/test_capture_freshness.py seeds real-shaped frontmatter, and the
vocabulary is synthetic throughout (`glyph`, `ward`) for the reason the module
under test has none: the framework names no plugin and enumerates no kind
(`ADR-022`, `ADR-035`, `ADR-037`).

Three whole-file tripwires carry in code what the AC says in words:

- **no search, ever** -- all three vault search entry points are replaced with
  counters and every test in this file fails at teardown if any of them was
  called, so "the search entry point is never called" is enforced rather than
  checked once;
- **nothing outside the tag** -- a second entity, an untagged note and a note
  whose only tag has no namespace are present in every vault built here, so a
  read that widened would show it;
- **nothing this file loads outlives it** -- the vault index's and the plugin
  host's module-level state are both restored.
"""
import json
import os
import textwrap
from pathlib import Path

import pytest

from app import plugin_api
from app.business.core.plugins import plugin_manager as plugin_manager_module
from app.business.core.plugins.plugin_manager import PluginManager
from app.business.core.semantic.semantic_manager import SemanticManager
from app.business.core.vault import vault_manager as vault_manager_module
from app.business.core.vault.vault_manager import VaultManager
from app.business.logic import hybrid_search, scoped_entity_read, tag_resolution
from app.config import settings
from app.obsidian.notes import long_path

GLYPH = "glyph"
THE_TAG = "glyph/lumen-cartography"
ANOTHER_ENTITYS_TAG = "glyph/tessellate-works"
A_TAG_WITH_NO_NAMESPACE = "urgent"

THE_NAME = "Lumen Cartography"
THE_HUB = "Work/Hubs/Lumen Cartography.md"
AN_OPAQUE_KIND = "Counterparty :: 42/x — née"

# Both real stamp formats this vault carries, on both evidence kinds, with the
# dates deliberately interleaved so kind order and date order disagree.
A_MEETING_NEWEST = "2026-10-13 06:00:00.000000+00:00"
A_THREAD_SECOND = "2026-10-11T09:30:00+00:00"
A_MEETING_THIRD = "2026-10-09T17:11:47+00:00"
A_THREAD_OLDEST = "2026-10-07 08:00:00.000000+00:00"

# Folder names ordered so the vault walk's own order is NOT the answer's order.
THE_ENTITYS_EVIDENCE = [
    ("Work/Threads/a-oldest/a-oldest.md", "Thread", {"last_message_at": A_THREAD_OLDEST}),
    ("Work/Meetings/b-third/b-third.md", "Meeting", {"start": A_MEETING_THIRD}),
    ("Work/Threads/c-second/c-second.md", "Thread", {"last_message_at": A_THREAD_SECOND}),
    ("Work/Meetings/d-newest/d-newest.md", "Meeting", {"start": A_MEETING_NEWEST}),
]
NEWEST_FIRST = ["d-newest", "c-second", "b-third", "a-oldest"]

UNDATED_FIELD_MISSING = "Work/Threads/u-no-stamp/u-no-stamp.md"
UNDATED_FIELD_UNPARSEABLE = "Work/Threads/u-bad-stamp/u-bad-stamp.md"
UNDATED_TYPE_HAS_NO_FIELD = "Work/Notes/u-plain-note/u-plain-note.md"


# -- the vault ------------------------------------------------------------------------


def write_note(vault_root: Path, relative: str, note_type: str, tags: list[str],
               fields: dict | None = None, body: str = "body") -> Path:
    """Every write goes through `long_path`: pytest's own tmp root plus a real
    subject line is already past Windows' 260 characters, where a plain
    `open()` raises and `os.path.isfile()` answers False without raising."""
    path = Path(vault_root) / relative
    os.makedirs(long_path(path.parent), exist_ok=True)
    lines = ["---", f'type: "{note_type}"', "tags: [" + ", ".join(f'"{tag}"' for tag in tags) + "]"]
    for key, value in (fields or {}).items():
        lines.append(f'{key}: "{value}"')
    lines.append("---")
    with open(long_path(path), "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n\n" + body + "\n")
    return path


@pytest.fixture()
def vault(tmp_path, monkeypatch):
    """A vault holding the entity, a SECOND entity, an untagged note and a note
    whose only tag has no namespace -- so every test in this file would show a
    read that widened, not only the one that looks for it."""
    root = tmp_path / "vault"
    monkeypatch.setattr(settings, "vault_path", root)

    def build(notes: list[tuple], with_hub: bool = True, walk_order=None):
        if with_hub:
            write_note(root, THE_HUB, "Glyph", [THE_TAG],
                       body="## Synthesis\n\nwhat is actually going on with this entity")
        for relative, note_type, fields in notes:
            write_note(root, relative, note_type, [THE_TAG], fields)

        # Outside the scope, in three different ways.
        write_note(root, "Work/Hubs/Tessellate Works.md", "Glyph", [ANOTHER_ENTITYS_TAG],
                   body="another entity's synthesis")
        write_note(root, "Work/Threads/z-other/z-other.md", "Thread", [ANOTHER_ENTITYS_TAG],
                   {"last_message_at": A_MEETING_NEWEST})
        write_note(root, "Work/Threads/z-untagged/z-untagged.md", "Thread", [],
                   {"last_message_at": A_MEETING_NEWEST})
        write_note(root, "Work/Notes/z-no-namespace/z-no-namespace.md", "Note",
                   [A_TAG_WITH_NO_NAMESPACE])

        if walk_order is not None:
            real = list(vault_manager_module.vault_writer.list_all_note_paths())
            monkeypatch.setattr(vault_manager_module.vault_writer, "list_all_note_paths",
                                lambda: walk_order(real))
        VaultManager().rebuild_index()
        return root

    return build


def resolved(tag: str = THE_TAG, hub: str | None = THE_HUB,
             name: str = THE_NAME) -> tag_resolution.TagResolution:
    """A resolution exactly as `T03` hands one over -- the hub and the tag that
    scopes the evidence, and deliberately no notes."""
    return tag_resolution.TagResolution(
        name_as_asked=name, outcome=tag_resolution.RESOLVED, resolved=True,
        message=f'"{name}" resolves to {tag}', kind=AN_OPAQUE_KIND, tag=tag, hub=hub,
        namespace=tag.partition("/")[0], plugin_id=f"{tag.partition('/')[0]}-owner",
    )


# -- the tripwires --------------------------------------------------------------------


@pytest.fixture(autouse=True)
def searches(monkeypatch):
    """Every vault search entry point, counted rather than merely forbidden --
    `assert zero calls` is the AC's own wording, and a counter can be asserted
    on the empty path where a fallback would be tempting. The teardown makes
    the same assertion for every other test in the file."""
    counts = {"keyword": 0, "hybrid": 0, "semantic": 0}

    def counting(which):
        def spy(*args, **kwargs):
            counts[which] += 1
            return {"query": "", "results": []}
        return spy

    monkeypatch.setattr(VaultManager, "search", counting("keyword"))
    monkeypatch.setattr(hybrid_search, "search", counting("hybrid"))
    monkeypatch.setattr(SemanticManager, "search", counting("semantic"))
    yield counts
    assert counts == {"keyword": 0, "hybrid": 0, "semantic": 0}, (
        "a scoped read must never reach a search entry point"
    )


@pytest.fixture(autouse=True)
def nothing_loaded_here_outlives_this_test(monkeypatch):
    monkeypatch.setattr(vault_manager_module, "_vault_index", dict(vault_manager_module._vault_index))
    monkeypatch.setattr(vault_manager_module, "_vault_entries", list(vault_manager_module._vault_entries))
    monkeypatch.setattr(vault_manager_module, "_vault_tag_index", dict(vault_manager_module._vault_tag_index))
    monkeypatch.setattr(plugin_manager_module, "_plugin_tag_namespaces",
                        dict(plugin_manager_module._plugin_tag_namespaces))
    monkeypatch.setattr(plugin_manager_module, "_load_report", list(plugin_manager_module._load_report))


@pytest.fixture(autouse=True)
def data_path(tmp_path, monkeypatch) -> Path:
    """This file's own App Database Folder. tests/conftest.py sandboxes the
    Hermes install and nothing else, so without this the loader would read the
    operator's real installed plugins."""
    monkeypatch.setattr(settings, "second_brain_data_path", tmp_path / "data")
    (tmp_path / "data").mkdir()
    return tmp_path / "data"


# -- 1. synthesis first, then tagged evidence -----------------------------------------


def test_the_hubs_synthesis_comes_first_and_everything_after_it_is_tagged_evidence(vault):
    """[REQ-SB-95-US-05-AC-02] The order is the requirement: a read that put
    four correct Threads ahead of the one hub note would have failed the story
    with every item right."""
    vault(THE_ENTITYS_EVIDENCE)

    result = scoped_entity_read.read_scoped_entity(resolved())

    assert result.performed is True
    assert result.hub_status == scoped_entity_read.HUB_FOUND
    assert result.notes[0].role == scoped_entity_read.SYNTHESIS
    assert result.notes[0].stem == "Lumen Cartography"
    assert "what is actually going on" in result.notes[0].body
    assert [note.role for note in result.notes[1:]] == [scoped_entity_read.EVIDENCE] * 4
    assert [note.stem for note in result.evidence] == NEWEST_FIRST
    assert result.evidence_total == 4
    assert result.evidence_truncated is False


def test_an_entity_with_no_hub_note_says_so_instead_of_leading_with_evidence(vault):
    """[REQ-SB-95-US-05-AC-02] Two honest shapes, never one borrowed for the
    other: a hub nobody registered, and a registered hub that is not among the
    notes carrying the tag. Neither is read from outside the scope."""
    vault(THE_ENTITYS_EVIDENCE, with_hub=False)

    none_registered = scoped_entity_read.read_scoped_entity(resolved(hub=None))
    assert none_registered.performed is True
    assert none_registered.hub_status == scoped_entity_read.HUB_NOT_REGISTERED
    assert none_registered.synthesis is None
    assert "registers no hub note" in none_registered.message
    assert len(none_registered.evidence) == 4

    not_in_scope = scoped_entity_read.read_scoped_entity(resolved())
    assert not_in_scope.hub_status == scoped_entity_read.HUB_NOT_FOUND_IN_SCOPE
    assert not_in_scope.synthesis is None
    assert "not among the notes carrying" in not_in_scope.message
    assert "none was read from outside the tag" in not_in_scope.message


def test_a_hub_registered_as_a_bare_name_or_a_wikilink_is_the_same_hub(vault):
    """[REQ-SB-95-US-05-AC-02] A registered hub is written by hand. A wikilink,
    a Windows path and a bare stem are spellings, not different notes."""
    vault([])

    for spelling in (THE_HUB, "Work/Hubs/Lumen Cartography", r"Work\Hubs\Lumen Cartography.md",
                     "[[Lumen Cartography]]", "lumen cartography"):
        result = scoped_entity_read.read_scoped_entity(resolved(hub=spelling))
        assert result.hub_status == scoped_entity_read.HUB_FOUND, spelling
        assert result.synthesis.stem == "Lumen Cartography", spelling


# -- 2. newest first, by each kind's own real recency field ---------------------------


def test_the_evidence_is_strictly_newest_first_across_both_kinds_and_both_stamp_formats(vault):
    """[REQ-SB-95-US-05-AC-02] A Thread is dated by `last_message_at` and a
    Meeting by `start` -- the live convention `capture_freshness.py` records,
    not a field invented here. The dates interleave the two kinds, and both
    real stamp formats appear on both kinds, so a reader that understood only
    ISO would order this wrongly rather than fail visibly."""
    vault(THE_ENTITYS_EVIDENCE)

    evidence = scoped_entity_read.read_scoped_entity(resolved()).evidence

    assert [note.stem for note in evidence] == NEWEST_FIRST
    assert [note.note_type for note in evidence] == ["Meeting", "Thread", "Meeting", "Thread"]
    assert [note.recency_field for note in evidence] == [
        "start", "last_message_at", "start", "last_message_at",
    ]
    stamps = [note.recency_epoch for note in evidence]
    assert stamps == sorted(stamps, reverse=True)
    assert all(note.recency == scoped_entity_read.DATED for note in evidence)
    # The space-separated form capture really writes, parsed rather than dropped.
    assert evidence[0].recency_at.startswith("2026-10-13T06:00:00")
    assert evidence[3].recency_at.startswith("2026-10-07T08:00:00")


def test_a_meeting_scheduled_ahead_is_still_the_newest_thing_known(vault):
    """[REQ-SB-95-US-05-AC-02] A deliberate difference from
    `capture_freshness`, which drops future stamps because it asks when
    something last LANDED. This asks what is known, and next week's meeting is
    known."""
    vault(THE_ENTITYS_EVIDENCE + [
        ("Work/Meetings/e-future/e-future.md", "Meeting", {"start": "2099-01-01T09:00:00+00:00"}),
    ])

    evidence = scoped_entity_read.read_scoped_entity(resolved()).evidence

    assert [note.stem for note in evidence] == ["e-future"] + NEWEST_FIRST


# -- 3. everything inside the tag, nothing outside it ---------------------------------


def test_every_returned_item_carries_the_tag_and_no_other_entitys_note_appears(vault):
    """[REQ-SB-95-US-05-AC-02] The vault holds a second entity under the same
    namespace, an untagged Thread stamped newer than everything here, and a
    note whose only tag has no namespace at all."""
    vault(THE_ENTITYS_EVIDENCE)

    result = scoped_entity_read.read_scoped_entity(resolved())

    assert len(result.notes) == 5
    for note in result.notes:
        assert THE_TAG in note.tags, note.stem
        assert ANOTHER_ENTITYS_TAG not in note.tags
    returned_stems = {note.stem for note in result.notes}
    assert returned_stems.isdisjoint(
        {"Tessellate Works", "z-other", "z-untagged", "z-no-namespace"})
    # The index really does hold them -- the fixture is not quietly empty.
    assert {"Tessellate Works", "z-other", "z-untagged", "z-no-namespace"} <= set(
        VaultManager().get_index())


def test_the_read_reaches_the_vault_only_through_the_tag_keyed_projection(vault, monkeypatch):
    """[REQ-SB-95-US-05-AC-02] Both whole-vault surfaces are armed to fail
    AFTER the index is built: `get_entries()` is every note there is, and
    `get_index()` is the by-stem map that can hand back a different note
    sharing a filename (`BUG-076`) -- the one way a scoped read could serve
    something outside its scope without ever calling a search."""
    vault(THE_ENTITYS_EVIDENCE)
    for whole_vault_surface in ("get_entries", "get_index"):
        monkeypatch.setattr(
            VaultManager, whole_vault_surface,
            lambda *a, **k: pytest.fail("a scoped read must reach the vault only through its tag"))

    result = scoped_entity_read.read_scoped_entity(resolved())

    assert [note.stem for note in result.evidence] == NEWEST_FIRST
    assert result.synthesis is not None


def test_two_notes_sharing_a_filename_are_both_inside_the_scope(vault):
    """[REQ-SB-95-US-05-AC-02] The by-stem map holds one note per name, so a
    read built on it would silently drop the other (`BUG-076`). Both carry the
    tag; both are returned."""
    vault(THE_ENTITYS_EVIDENCE + [
        ("Work/Threads/twin/same-name.md", "Thread", {"last_message_at": A_THREAD_SECOND}),
        ("Work/Meetings/twin/same-name.md", "Meeting", {"start": A_MEETING_THIRD}),
    ])

    result = scoped_entity_read.read_scoped_entity(resolved())

    assert [note.stem for note in result.evidence].count("same-name") == 2
    assert len({note.path for note in result.evidence}) == 6


# -- 4. no whole-vault search on any path, including the empty one --------------------


def test_no_search_entry_point_is_called_including_for_an_entity_with_no_evidence(vault, searches):
    """[REQ-SB-95-US-05-AC-02] The empty case is the one that matters: an
    honest "nothing carries this tag" is exactly where falling back to a
    search would feel helpful, and it is the failure this story removes."""
    vault(THE_ENTITYS_EVIDENCE)

    populated = scoped_entity_read.read_scoped_entity(resolved())
    assert populated.found_anything is True
    assert searches == {"keyword": 0, "hybrid": 0, "semantic": 0}

    empty = scoped_entity_read.read_scoped_entity(
        resolved(tag="glyph/nobody-has-written-about-this", hub=None, name="Nobody"))

    assert searches == {"keyword": 0, "hybrid": 0, "semantic": 0}
    assert empty.performed is True
    assert empty.found_anything is False
    assert empty.evidence == []
    assert empty.evidence_total == 0
    assert empty.synthesis is None
    assert "no note in the vault carries glyph/nobody-has-written-about-this" in empty.message
    assert "nothing else was searched" in empty.message


def test_a_name_that_did_not_resolve_performs_no_read_at_all(vault, searches):
    """[REQ-SB-95-US-05-AC-02] `performed` is False, not an empty result: "it
    did not resolve" and "nothing is known about it" are different facts, and
    neither is answered with a search."""
    vault(THE_ENTITYS_EVIDENCE)
    unresolved = tag_resolution.resolve("a name nothing knows")
    assert unresolved.resolved is False

    result = scoped_entity_read.read_scoped_entity(unresolved)

    assert result.performed is False
    assert result.notes == []
    assert result.tag is None
    assert "no scoped read was performed" in result.message
    assert "nothing was searched for in its place" in result.message
    assert searches == {"keyword": 0, "hybrid": 0, "semantic": 0}


def test_an_unreadable_tag_keyed_index_reports_itself_and_does_not_widen(vault, searches, monkeypatch):
    """[REQ-SB-95-US-05-AC-02] A failed read may not borrow the look of an
    empty one, and may certainly not become a search."""
    vault(THE_ENTITYS_EVIDENCE)
    monkeypatch.setattr(
        VaultManager, "get_entries_for_tag",
        lambda *a, **k: (_ for _ in ()).throw(OSError("the projection is gone")))

    result = scoped_entity_read.read_scoped_entity(resolved())

    assert result.performed is False
    assert result.scope_failure == "OSError: the projection is gone"
    assert result.notes == []
    assert searches == {"keyword": 0, "hybrid": 0, "semantic": 0}


# -- 5. the documented fallback for a note that cannot be dated -----------------------


def test_a_note_that_cannot_be_dated_is_placed_by_the_documented_rule(vault):
    """[REQ-SB-95-US-05-AC-02] The rule, not the list: `evidence_sort_key` is
    asserted directly, so every undated note outranks-after every dated one by
    construction rather than by where this particular vault happened to put
    them. Three ways to be undated are present -- a missing field, a field that
    will not parse, and a type with no known recency field at all."""
    vault(THE_ENTITYS_EVIDENCE + [
        (UNDATED_FIELD_MISSING, "Thread", {}),
        (UNDATED_FIELD_UNPARSEABLE, "Thread", {"last_message_at": "last Tuesday"}),
        (UNDATED_TYPE_HAS_NO_FIELD, "Note", {"created": A_MEETING_NEWEST}),
    ])

    evidence = scoped_entity_read.read_scoped_entity(resolved()).evidence
    dated = [note for note in evidence if note.recency == scoped_entity_read.DATED]
    undated = [note for note in evidence if note.recency == scoped_entity_read.UNDATED]
    assert len(dated) == 4 and len(undated) == 3

    # The rule itself: no dated note, however old, sorts below an undated one.
    for undated_note in undated:
        for dated_note in dated:
            assert (scoped_entity_read.evidence_sort_key(undated_note)
                    > scoped_entity_read.evidence_sort_key(dated_note))

    assert [note.stem for note in evidence[:4]] == NEWEST_FIRST
    assert [note.stem for note in evidence[4:]] == ["u-bad-stamp", "u-no-stamp", "u-plain-note"]

    # Undated, and each says why -- never a silent "treat as newest".
    assert all(note.recency_at is None and note.recency_epoch is None for note in undated)
    reasons = {note.stem: note.undated_because for note in undated}
    assert reasons["u-no-stamp"] == "its last_message_at is missing"
    assert "could not be read as a timestamp" in reasons["u-bad-stamp"]
    assert "no recency field is known for a note of type 'Note'" in reasons["u-plain-note"]
    assert "invents none" in reasons["u-plain-note"]

    # Still inside the tag scope: undated is not a reason to drop a tagged note.
    assert all(THE_TAG in note.tags for note in undated)
    assert all(note.body.strip() == "body" for note in undated)


def test_the_order_is_the_rule_and_not_the_order_the_vault_was_walked_in(vault):
    """[REQ-SB-95-US-05-AC-02] The same vault indexed in the reverse walk order
    produces the identical answer -- including where the three undated notes
    sit, which is the half an accident of list order would get right once."""
    notes = THE_ENTITYS_EVIDENCE + [
        (UNDATED_FIELD_MISSING, "Thread", {}),
        (UNDATED_FIELD_UNPARSEABLE, "Thread", {"last_message_at": "last Tuesday"}),
        (UNDATED_TYPE_HAS_NO_FIELD, "Note", {"created": A_MEETING_NEWEST}),
    ]
    expected = NEWEST_FIRST + ["u-bad-stamp", "u-no-stamp", "u-plain-note"]

    vault(notes)
    forwards = [note.stem for note in scoped_entity_read.read_scoped_entity(resolved()).evidence]

    vault(notes, walk_order=lambda paths: list(reversed(paths)))
    backwards = [note.stem for note in scoped_entity_read.read_scoped_entity(resolved()).evidence]

    assert forwards == expected
    assert backwards == expected


def test_a_truncated_read_says_how_many_there_really_were(vault):
    """[REQ-SB-95-US-05-AC-02] A cap is honest only if the count it hid is
    reported; a silently short list reads as "that is all there is"."""
    vault(THE_ENTITYS_EVIDENCE)

    result = scoped_entity_read.read_scoped_entity(resolved(), evidence_limit=2)

    assert [note.stem for note in result.evidence] == NEWEST_FIRST[:2]
    assert result.evidence_total == 4
    assert result.evidence_truncated is True
    assert "2 of 4 tagged evidence note(s), newest first" in result.message


# -- the whole question, through a really registered namespace ------------------------


def registry_backend(namespace: str, entries: list[dict]) -> str:
    return f'''
def register(api):
    api.register_tag_namespace("{namespace}", lambda: {entries!r})
'''


def install(data_path: Path, plugin_id: str, backend: str) -> None:
    folder = data_path / "plugins" / plugin_id
    (folder / "backend").mkdir(parents=True)
    (folder / "plugin.json").write_text(json.dumps({
        "id": plugin_id, "name": plugin_id.title(), "version": "0.1.0",
        "framework_api": plugin_api.FRAMEWORK_API, "requires": [],
    }), encoding="utf-8")
    (folder / "backend" / "__init__.py").write_text(textwrap.dedent(backend), encoding="utf-8")
    record = data_path / "plugins" / "installed.json"
    record.write_text(json.dumps({"plugins": [{"id": plugin_id, "version": "0.1.0"}]}),
                      encoding="utf-8")


def test_a_name_registered_by_a_real_plugin_reads_its_own_scope_end_to_end(vault, data_path):
    """[REQ-SB-95-US-05-AC-02] The resolver and the read, joined the way the
    catalogued Action (`T05`) will join them: one name in, that entity's
    synthesis and its own evidence out, and still not one search."""
    vault(THE_ENTITYS_EVIDENCE)
    install(data_path, "glyph-owner", registry_backend(GLYPH, [{
        "slug": "lumen-cartography", "name": THE_NAME, "aliases": ["LC"],
        "domains": ["lumen.example.invalid"], "hub": THE_HUB, "kind": AN_OPAQUE_KIND,
    }]))
    PluginManager().load_all()

    by_alias = scoped_entity_read.read_entity_named("lc")

    assert by_alias.performed is True
    assert by_alias.tag == THE_TAG
    assert by_alias.kind == AN_OPAQUE_KIND
    assert by_alias.notes[0].role == scoped_entity_read.SYNTHESIS
    assert [note.stem for note in by_alias.evidence] == NEWEST_FIRST

    not_known = scoped_entity_read.read_entity_named("Tessellate Works")

    assert not_known.performed is False
    assert not_known.notes == []
