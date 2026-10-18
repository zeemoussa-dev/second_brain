"""REQ-SB-95-US-05-T01 -- the one tag-keyed index, as a projection (`ADR-037`).

Entity scoping is ONE index keyed by tag, not one `Index` artifact per entity:
a brand-new entity is served the moment a note carrying its tag is indexed, with
no provisioning step, no cron job and no second refresh trigger. The projection
is rebound inside `VaultManager.rebuild_index()`, in the same assignment block as
`_vault_entries`, so it cannot be newer or older than the notes it groups --
`BUG-082` is why that matters: a stored copy whose own refresh trigger was never
wired is how the backend served a three-day-stale vault with 250 notes invisible.

Everything below runs over a synthetic tmp vault through the REAL walk
(`vault_writer.list_all_note_paths()`, not a monkeypatched list), so the fixture
also proves the one thing a shorter fixture would hide: a note whose full path
passes Windows' 260-character limit is grouped like any other. `os.path.isfile()`
answers False rather than raising on such a path, so a walk that skipped it would
skip it silently.
"""
import ast
import os
from pathlib import Path

import pytest

from app.business.core.vault import vault_manager as module
from app.business.core.vault.vault_manager import VaultManager
from app.config import settings
from app.data_access import indexes as indexes_data
from app.hermes.cli import HermesCLI
from app.obsidian.notes import long_path

GLYPH = "glyph/lumen-cartography"
WARD = "ward/tessellate-works"
DEEPER_TAG = "glyph/lumen-cartography/northern-reach"

HUB = "Work/Hubs/Lumen Cartography.md"
THREAD = "Work/Threads/A quiet handover/A quiet handover.md"
MEETING = "Work/Meetings/A short standup/A short standup.md"
OTHER_HUB = "Work/Hubs/Tessellate Works.md"
UNNAMESPACED = "Work/Notes/Loose ends.md"
DEEPER = "Work/Notes/Regional split.md"

# Long enough that `<folder>/<same name>.md` under pytest's own tmp root passes
# 260 characters, which is the shape the real vault produces for itself.
LONG_NAME = ("a deliberately long synthetic note name standing in for the sort of "
             "subject line a captured thread really carries")
LONG_NOTE = f"Work/Threads/{LONG_NAME}/{LONG_NAME}.md"

NOTES = {
    HUB: [GLYPH, "kind/hub"],
    THREAD: [GLYPH, "kind/thread"],
    MEETING: [GLYPH, "kind/meeting"],
    OTHER_HUB: [WARD, "kind/hub"],
    UNNAMESPACED: ["urgent"],
    DEEPER: [DEEPER_TAG],
    LONG_NOTE: [GLYPH, "kind/thread"],
}

MODULE_SOURCE = Path(module.__file__).read_text(encoding="utf-8")
MODULE_TREE = ast.parse(MODULE_SOURCE)
PROJECTION = "_vault_tag_index"


def write_note(vault_root, relative, tags):
    """Every write goes through `long_path`: pytest's own tmp root plus a real
    subject line is already past the limit, so a plain `open()` would raise
    FileNotFoundError on a file this test is in the middle of creating."""
    path = Path(vault_root) / relative
    os.makedirs(long_path(path.parent), exist_ok=True)
    tag_list = ", ".join(f'"{tag}"' for tag in tags)
    with open(long_path(path), "w", encoding="utf-8") as handle:
        handle.write(f'---\ntype: "Note"\ntags: [{tag_list}]\n---\n\nbody\n')
    return path


@pytest.fixture()
def vault(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "vault_path", tmp_path)
    for relative, tags in NOTES.items():
        write_note(tmp_path, relative, tags)
    assert len(str(tmp_path / LONG_NOTE)) > 260, "the fixture must actually pass the limit"
    return tmp_path


@pytest.fixture(autouse=True)
def nothing_is_provisioned(monkeypatch):
    """No per-entity setup step of ANY kind, in every test in this file: an
    `Index` artifact written to disk or a Hermes cron job created would both be
    the second refresh trigger `ADR-037` exists to refuse."""
    monkeypatch.setattr(indexes_data, "write_index_json",
                        lambda *a, **k: pytest.fail("no Index artifact may be written"))
    monkeypatch.setattr(HermesCLI, "create_cron_job",
                        lambda *a, **k: pytest.fail("no cron job may be created"))


def paths_under(manager, tag):
    return sorted(entry["path"] for entry in manager.get_entries_for_tag(tag))


# -- AC-04: one index, one rebind, no provisioning ----------------------------------


def test_every_note_is_grouped_under_each_of_its_tags(vault):
    """[REQ-SB-95-US-05-AC-04] One rebuild, no per-entity setup anywhere: every
    `<namespace>/<slug>` tag the vault holds already groups its own notes."""
    manager = VaultManager()
    manager.rebuild_index()

    assert paths_under(manager, GLYPH) == sorted(
        str(vault / relative) for relative in (HUB, THREAD, MEETING, LONG_NOTE)
    )
    assert paths_under(manager, WARD) == [str(vault / OTHER_HUB)]
    assert paths_under(manager, "kind/hub") == sorted(
        str(vault / relative) for relative in (HUB, OTHER_HUB)
    )
    assert paths_under(manager, "kind/meeting") == [str(vault / MEETING)]
    # A note carrying three tags is under all of them, not filed once.
    assert str(vault / THREAD) in paths_under(manager, "kind/thread")


def test_a_brand_new_tag_is_a_key_immediately_after_the_next_rebuild(vault):
    """[REQ-SB-95-US-05-AC-04] A new entity needs no `Index` artifact and no cron
    job -- both are spied on for every test here and fail the test if called."""
    manager = VaultManager()
    manager.rebuild_index()
    assert "glyph/first-mention" not in manager.get_tag_index_keys()

    write_note(vault, "Work/Threads/A first mention.md", ["glyph/first-mention", "kind/thread"])
    manager.rebuild_index()

    assert "glyph/first-mention" in manager.get_tag_index_keys()
    assert paths_under(manager, "glyph/first-mention") == [
        str(vault / "Work/Threads/A first mention.md")
    ]


def test_the_projection_describes_the_same_notes_as_the_entries_after_one_rebuild(vault):
    """[REQ-SB-95-US-05-AC-04] Mutate the vault, rebuild ONCE, assert immediately:
    no other refresh is invoked, and there is no intermediate state in which one
    of the two is newer. The entries in the projection are the very objects
    `get_entries()` hands back, which is what "same pass" means."""
    manager = VaultManager()
    manager.rebuild_index()

    os.remove(long_path(vault / MEETING))
    write_note(vault, "Work/Threads/A later arrival.md", ["glyph/later", "kind/thread"])

    manager.rebuild_index()

    entries = manager.get_entries()
    grouped = [entry for key in manager.get_tag_index_keys()
               for entry in manager.get_entries_for_tag(key)]
    assert all(any(entry is candidate for candidate in entries) for entry in grouped)

    paths_with_a_namespaced_tag = {
        entry["path"] for entry in entries
        if any("/" in tag and not tag.startswith("/") and not tag.endswith("/")
               for tag in entry["tags"])
    }
    assert {entry["path"] for entry in grouped} == paths_with_a_namespaced_tag
    assert str(vault / "Work/Threads/A later arrival.md") in paths_with_a_namespaced_tag
    assert str(vault / MEETING) not in {entry["path"] for entry in entries}
    assert "kind/meeting" not in manager.get_tag_index_keys()


def test_the_projection_is_assigned_in_exactly_one_place(vault):
    """[REQ-SB-95-US-05-AC-04] Exactly one refresh path, read off the module's own
    source: one declaration, one rebind, and the rebind sits in `rebuild_index`
    immediately beside `_vault_entries`. A second assignment site anywhere would
    be a second way for the projection to drift from the notes (`BUG-082`)."""
    assignments = [node for node in ast.walk(MODULE_TREE) if _assigns(node, PROJECTION)]
    assert len(assignments) == 2, "expected one declaration and one rebind"

    module_level = [node for node in MODULE_TREE.body if _assigns(node, PROJECTION)]
    assert len(module_level) == 1

    rebuild = _function_named("rebuild_index")
    rebinds = [node for node in ast.walk(rebuild) if _assigns(node, PROJECTION)]
    assert len(rebinds) == 1

    for function in _every_function():
        if function is rebuild:
            continue
        assert not [node for node in ast.walk(function) if _assigns(node, PROJECTION)], (
            f"{function.name} also assigns the projection"
        )

    body = rebuild.body
    entries_at = next(i for i, node in enumerate(body) if _assigns(node, "_vault_entries"))
    assert _assigns(body[entries_at + 1], PROJECTION), "not rebound in the same block"


# -- AC-07: every tag in the vault, no namespace list -------------------------------


def test_every_namespace_present_is_a_key_with_nothing_registered(vault):
    """[REQ-SB-95-US-05-AC-07] Zero namespaces registered -- nothing in this file
    registers one, and T02's registration seam does not exist yet. Every
    `<namespace>/<slug>` tag in the vault is still a key, including `kind/thread`,
    which no plugin would ever claim as an entity namespace."""
    manager = VaultManager()
    manager.rebuild_index()

    keys = manager.get_tag_index_keys()
    assert keys == sorted({
        GLYPH, WARD, DEEPER_TAG, "kind/hub", "kind/thread", "kind/meeting",
    })
    assert "kind/thread" in keys
    assert sorted({key.split("/")[0] for key in keys}) == ["glyph", "kind", "ward"]


def test_an_invented_namespace_is_a_key_on_the_same_terms(vault):
    """[REQ-SB-95-US-05-AC-07] The behavioural half of "no namespace prefix is
    filtered in or out by a list written into the framework": a namespace nothing
    in this repository has ever heard of is keyed exactly like the others."""
    manager = VaultManager()
    for namespace in ("quarl", "zz9", "a", "Mixed-Case"):
        write_note(vault, f"Work/Notes/{namespace} note.md", [f"{namespace}/some-slug"])
    manager.rebuild_index()

    for namespace in ("quarl", "zz9", "a", "Mixed-Case"):
        assert paths_under(manager, f"{namespace}/some-slug") == [
            str(vault / f"Work/Notes/{namespace} note.md")
        ]


def test_the_builder_carries_no_namespace_literal_at_all(vault):
    """[REQ-SB-95-US-05-AC-07] The structural half: the function that builds the
    index holds no string literal containing a separator, so there is no allow-
    list or deny-list for it to consult. Asserted over the real source rather
    than over a hand-kept list of forbidden prefixes, which would date itself."""
    builder = _function_named("_build_tag_index")
    literals = [node.value for node in ast.walk(builder)
                if isinstance(node, ast.Constant) and isinstance(node.value, str)]
    literals.remove(ast.get_docstring(builder, clean=False))

    assert all("/" not in literal for literal in literals), literals


def test_a_tag_no_namespace_claims_is_retained_and_nameable(vault):
    """[REQ-SB-95-US-05-AC-07] Nothing is registered, so EVERY key here is a key
    with no registered entry -- and all of them are retained and reportable by
    name. Dropping the unclaimed ones is how an index stops being able to say
    which entity it has notes about but no registration for."""
    manager = VaultManager()
    manager.rebuild_index()

    unknown = manager.get_tag_index_keys()

    assert WARD in unknown
    assert manager.get_entries_for_tag(WARD), "the notes behind an unknown key are kept too"
    assert DEEPER_TAG in unknown


# -- the one stated tag-shape rule, and the walk that must not skip quietly ---------


def test_the_one_tag_shape_rule_holds_at_both_edges(vault):
    """A tag with a namespace is always a key, keyed by its own full name -- so a
    deeper tag is kept rather than dropped. A tag with no namespace is not an
    entity tag and is not a key; `list_tags()` is what counts those."""
    manager = VaultManager()
    write_note(vault, "Work/Notes/Edges.md", ["", "/leading", "trailing/", "plain"])
    manager.rebuild_index()

    keys = manager.get_tag_index_keys()
    assert DEEPER_TAG in keys
    assert "glyph/lumen-cartography" in keys and DEEPER_TAG != GLYPH
    assert [key for key in keys if "urgent" in key or "plain" in key] == []
    assert [key for key in keys if key.startswith("/") or key.endswith("/")] == []
    assert {"urgent", "plain"} <= {tag["tag"] for tag in manager.list_tags()["tags"]}


def test_a_note_past_the_windows_path_limit_is_grouped_by_its_tag(vault):
    """The walk is the real one, and the deepest note in the fixture is past 260
    characters. `os.path.isfile()` returns False instead of raising on such a
    path, so a walk that lost it would lose it with no error anywhere -- the only
    honest check is that its tag group actually contains it."""
    manager = VaultManager()
    manager.rebuild_index()

    long_note = str(vault / LONG_NOTE)
    assert len(long_note) > 260
    assert long_note in paths_under(manager, GLYPH)
    assert long_note in paths_under(manager, "kind/thread")
    assert long_note in {entry["path"] for entry in manager.get_entries()}


# -- source-reading helpers ---------------------------------------------------------


def _assigns(node, name) -> bool:
    if isinstance(node, ast.Assign):
        return any(isinstance(target, ast.Name) and target.id == name for target in node.targets)
    if isinstance(node, ast.AnnAssign):
        return isinstance(node.target, ast.Name) and node.target.id == name
    return False


def _every_function():
    return [node for node in ast.walk(MODULE_TREE)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]


def _function_named(name):
    [found] = [node for node in _every_function() if node.name == name]
    return found
