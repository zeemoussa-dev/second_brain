"""The generic tag resolver (REQ-SB-95-US-05-T03; AC-01, AC-03, AC-05, AC-07).

A name, an alias or an email domain becomes `(kind, tag, hub)` by asking the
registered namespaces at that moment -- or it becomes an honest non-answer.
The namespaces are registered by REAL plugins written into a temporary App
Database Folder and loaded by the real `PluginManager`, the technique
tests/test_plugin_host.py and tests/test_tag_namespace_registration.py already
use, so every resolution below goes through the same seam a shipped plugin
would use. Each fake plugin reads its own entries from a file beside its
backend and records every call, which makes "it was asked now, not at load"
an assertion about observed behaviour.

The vocabulary is synthetic throughout (`glyph`, `ward`, `quarl`) for the
reason the resolver itself has none: the framework names no plugin and
enumerates no kind (`ADR-022`, `ADR-035`, `ADR-037`).

Two whole-file tripwires carry assertions the ACs make in words:

- **no search and no scoped read, ever** -- both vault search entry points and
  the per-tag read are replaced with failures for every test here, so "it is a
  registry lookup, never a fuzzy search over note titles" is enforced rather
  than inspected;
- **nothing this file loads outlives it** -- the plugin host's and the vault
  index's module-level state are both restored, so a plugin installed in a
  temporary folder can never be seen by a later test.
"""
import json
import os
import textwrap
from pathlib import Path

import pytest

from app import plugin_api
from app.business.core.plugins import plugin_manager as plugin_manager_module
from app.business.core.plugins.plugin_manager import PluginManager
from app.business.core.vault import vault_manager as vault_manager_module
from app.business.core.vault.vault_manager import VaultManager
from app.business.logic import hybrid_search
from app.business.logic import tag_resolution
from app.config import settings
from app.obsidian.notes import long_path

GLYPH = "glyph"
WARD = "ward"
QUARL = "quarl"

GLYPH_TAG = "glyph/lumen-cartography"
WARD_TAG = "ward/tessellate-works"

A_NAME = "Lumen Cartography"
AN_ALIAS = "LC"
A_DOMAIN = "lumen.example.invalid"
A_HUB = "Work/Hubs/Lumen Cartography.md"

# Carries a separator, punctuation and a non-ASCII letter on purpose: anything
# that split, trimmed, cased, validated or mapped `kind` would change a byte.
AN_OPAQUE_KIND = "Counterparty :: 42/x — née"

AN_ENTRY = {
    "slug": "lumen-cartography",
    "name": A_NAME,
    "aliases": [AN_ALIAS, "Lumen"],
    "domains": [A_DOMAIN],
    "hub": A_HUB,
    "kind": AN_OPAQUE_KIND,
}
ANOTHER_ENTRY = {
    "slug": "tessellate-works",
    "name": "Tessellate Works",
    "aliases": [],
    "domains": ["tessellate.example.invalid"],
    "hub": "Work/Hubs/Tessellate Works.md",
    "kind": "Ward",
}


def registry_backend(namespace: str) -> str:
    """A plugin whose entries come from a file it rereads every time it is
    asked -- an operator editing a registry while the app runs."""
    return f'''
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CALLS = HERE / "calls.json"
ENTRIES = HERE / "entries.json"


def register(api):
    def entries():
        asked = json.loads(CALLS.read_text(encoding="utf-8")) if CALLS.is_file() else []
        asked.append("asked")
        CALLS.write_text(json.dumps(asked), encoding="utf-8")
        return json.loads(ENTRIES.read_text(encoding="utf-8"))

    api.register_tag_namespace("{namespace}", entries)
'''


def raising_backend(namespace: str, message: str) -> str:
    return f'''
def register(api):
    def entries():
        raise RuntimeError("{message}")

    api.register_tag_namespace("{namespace}", entries)
'''


@pytest.fixture(autouse=True)
def data_path(tmp_path, monkeypatch) -> Path:
    """This file's own App Database Folder. tests/conftest.py sandboxes the
    Hermes install and nothing else, so without this the loader would read the
    operator's real installed plugins -- and their namespaces, not these,
    would be what the resolver answered from."""
    monkeypatch.setattr(settings, "second_brain_data_path", tmp_path / "data")
    (tmp_path / "data").mkdir()
    return tmp_path / "data"


@pytest.fixture(autouse=True)
def nothing_loaded_here_outlives_this_test(monkeypatch):
    monkeypatch.setattr(plugin_manager_module, "_plugin_tag_namespaces",
                        dict(plugin_manager_module._plugin_tag_namespaces))
    monkeypatch.setattr(plugin_manager_module, "_load_report", list(plugin_manager_module._load_report))
    monkeypatch.setattr(vault_manager_module, "_vault_index", dict(vault_manager_module._vault_index))
    monkeypatch.setattr(vault_manager_module, "_vault_entries", list(vault_manager_module._vault_entries))
    monkeypatch.setattr(vault_manager_module, "_vault_tag_index", dict(vault_manager_module._vault_tag_index))


@pytest.fixture(autouse=True)
def no_search_and_no_scoped_read(monkeypatch):
    """Resolution is a registry lookup. A fuzzy search over note titles is the
    failure this story exists to remove, and a scoped read is T04's work, so
    both are armed to fail every test in this file rather than being checked
    in one."""
    monkeypatch.setattr(VaultManager, "search",
                        lambda *a, **k: pytest.fail("resolution must never search the vault"))
    monkeypatch.setattr(hybrid_search, "search",
                        lambda *a, **k: pytest.fail("resolution must never search the vault"))
    monkeypatch.setattr(VaultManager, "get_entries_for_tag",
                        lambda *a, **k: pytest.fail("resolution must never perform a scoped read"))


def install(data_path: Path, plugin_id: str, backend: str) -> Path:
    folder = data_path / "plugins" / plugin_id
    (folder / "backend").mkdir(parents=True)
    (folder / "plugin.json").write_text(json.dumps({
        "id": plugin_id, "name": plugin_id.title(), "version": "0.1.0",
        "framework_api": plugin_api.FRAMEWORK_API, "requires": [],
    }), encoding="utf-8")
    (folder / "backend" / "__init__.py").write_text(textwrap.dedent(backend), encoding="utf-8")

    record_path = data_path / "plugins" / "installed.json"
    record = json.loads(record_path.read_text(encoding="utf-8")) if record_path.is_file() else {"plugins": []}
    record["plugins"].append({"id": plugin_id, "version": "0.1.0"})
    record_path.write_text(json.dumps(record), encoding="utf-8")
    return folder


def set_entries(data_path: Path, plugin_id: str, entries: list[dict]) -> None:
    """What that plugin's registry holds at this moment."""
    path = data_path / "plugins" / plugin_id / "backend" / "entries.json"
    path.write_text(json.dumps(entries), encoding="utf-8")


def times_asked(data_path: Path, plugin_id: str) -> int:
    path = data_path / "plugins" / plugin_id / "backend" / "calls.json"
    return len(json.loads(path.read_text(encoding="utf-8"))) if path.is_file() else 0


def register_namespace(data_path: Path, namespace: str, entries: list[dict],
                       plugin_id: str | None = None) -> str:
    plugin_id = plugin_id or f"{namespace}-owner"
    install(data_path, plugin_id, registry_backend(namespace))
    set_entries(data_path, plugin_id, entries)
    PluginManager().load_all()
    return plugin_id


def write_note(vault_root: Path, relative: str, tags: list[str]) -> Path:
    """Every write goes through `long_path`: pytest's own tmp root plus a real
    subject line is already past Windows' 260 characters, where a plain
    `open()` raises and `os.path.isfile()` answers False without raising."""
    path = Path(vault_root) / relative
    os.makedirs(long_path(path.parent), exist_ok=True)
    tag_list = ", ".join(f'"{tag}"' for tag in tags)
    with open(long_path(path), "w", encoding="utf-8") as handle:
        handle.write(f'---\ntype: "Note"\ntags: [{tag_list}]\n---\n\nbody\n')
    return path


# -- AC-01: a name resolves to a kind, a tag and a hub -------------------------------


def test_a_registered_name_resolves_to_its_kind_its_tag_and_its_hub(data_path):
    """[REQ-SB-95-US-05-AC-01]"""
    register_namespace(data_path, GLYPH, [AN_ENTRY])

    resolution = tag_resolution.resolve(A_NAME)

    assert resolution.resolved is True
    assert resolution.outcome == tag_resolution.RESOLVED
    assert resolution.kind == AN_OPAQUE_KIND
    assert resolution.tag == GLYPH_TAG
    assert resolution.hub == A_HUB
    assert resolution.namespace == GLYPH
    assert resolution.plugin_id == "glyph-owner"
    assert resolution.every_namespace_answered is True


def test_the_callable_is_asked_during_the_resolve_and_the_next_answer_follows_the_registry(data_path):
    """[REQ-SB-95-US-05-AC-01] Asked at that moment, never read from a list
    captured when the namespace was registered: the registry is rewritten
    between two resolves with no re-registration, and the answer changes."""
    plugin_id = register_namespace(data_path, GLYPH, [AN_ENTRY])
    assert times_asked(data_path, plugin_id) == 0

    first = tag_resolution.resolve(A_NAME)
    assert times_asked(data_path, plugin_id) == 1
    assert first.resolved is True
    assert first.hub == A_HUB

    moved = {**AN_ENTRY, "slug": "lumen-cartography-nw", "hub": "Work/Hubs/Lumen Cartography NW.md"}
    set_entries(data_path, plugin_id, [moved])

    second = tag_resolution.resolve(A_NAME)

    assert times_asked(data_path, plugin_id) == 2
    assert second.tag == "glyph/lumen-cartography-nw"
    assert second.hub == "Work/Hubs/Lumen Cartography NW.md"
    assert PluginManager().get_tag_namespaces()[0]["plugin_id"] == plugin_id


def test_a_name_that_is_a_real_note_title_but_no_registered_entry_does_not_resolve(data_path, tmp_path, monkeypatch):
    """[REQ-SB-95-US-05-AC-01] The vault really holds a note of that name --
    indexed through the real walk -- and it still does not resolve. The search
    entry points are armed to fail for every test in this file, so zero calls
    is enforced, not inspected."""
    vault = tmp_path / "vault"
    write_note(vault, "Work/Hubs/Tessellate Works.md", [WARD_TAG])
    monkeypatch.setattr(settings, "vault_path", vault)
    VaultManager().rebuild_index()
    assert "Tessellate Works" in VaultManager().get_index(), "the fixture must really hold that note"

    register_namespace(data_path, GLYPH, [AN_ENTRY])

    resolution = tag_resolution.resolve("Tessellate Works")

    assert resolution.resolved is False
    assert resolution.outcome == tag_resolution.DID_NOT_RESOLVE
    assert resolution.tag is None


def test_a_kind_the_framework_has_never_seen_comes_back_byte_identically(data_path):
    """[REQ-SB-95-US-05-AC-01] `kind` is opaque: no validation against any
    list, no normalisation, no mapping onto a framework concept."""
    never_seen = "Counterparty"
    register_namespace(data_path, GLYPH, [{**AN_ENTRY, "kind": never_seen}])

    resolution = tag_resolution.resolve(A_NAME)

    assert resolution.kind == never_seen
    assert resolution.kind.encode("utf-8") == never_seen.encode("utf-8")

    stranger = {**AN_ENTRY, "kind": AN_OPAQUE_KIND}
    set_entries(data_path, "glyph-owner", [stranger])
    assert tag_resolution.resolve(A_NAME).kind.encode("utf-8") == AN_OPAQUE_KIND.encode("utf-8")


def test_the_resolution_hands_over_synthesis_and_a_scope_but_never_notes(data_path):
    """[REQ-SB-95-US-05-AC-01] Synthesis before evidence, carried in the
    shape: the hub is a field of its own and no note list exists here at all,
    so nothing downstream can serve tagged evidence without having first been
    told where the synthesis is. An entry registering no hub says so rather
    than leaving a reader to lead with evidence."""
    register_namespace(data_path, GLYPH, [AN_ENTRY, {**ANOTHER_ENTRY, "slug": "no-hub",
                                                     "name": "No Hub Here", "hub": ""}])

    with_hub = tag_resolution.resolve(A_NAME)
    without_hub = tag_resolution.resolve("No Hub Here")

    assert with_hub.hub == A_HUB
    assert not hasattr(with_hub, "notes") and not hasattr(with_hub, "entries")
    assert without_hub.resolved is True
    assert without_hub.hub is None
    assert "no hub note" in without_hub.message


def test_the_resolver_names_no_plugin_and_enumerates_no_kind(data_path):
    """[REQ-SB-95-US-05-AC-01] Read off the module's own source: a framework
    that knew one plugin's vocabulary would have failed `ADR-022`'s test --
    a second brain built for someone tracking nothing but books gets the same
    resolver."""
    source = Path(tag_resolution.__file__).read_text(encoding="utf-8").casefold()

    for plugin_word in ("customer", "partner", "entities", "opportunity"):
        assert plugin_word not in source, f"the resolver must not know the word {plugin_word!r}"


# -- AC-03: an alias, a domain, and ambiguity ----------------------------------------


def test_an_alias_a_bare_domain_and_an_address_at_it_all_resolve_the_same(data_path):
    """[REQ-SB-95-US-05-AC-03] Each asked in mixed letter case."""
    register_namespace(data_path, GLYPH, [AN_ENTRY])

    by_name = tag_resolution.resolve("lUmEn CaRtOgRaPhY")
    by_alias = tag_resolution.resolve("  Lc  ")
    by_domain = tag_resolution.resolve("Lumen.Example.INVALID")
    by_address = tag_resolution.resolve("Someone.Else@Lumen.Example.Invalid")

    for resolution in (by_name, by_alias, by_domain, by_address):
        assert resolution.resolved is True, resolution.message
        assert (resolution.kind, resolution.tag, resolution.hub) == (AN_OPAQUE_KIND, GLYPH_TAG, A_HUB)


def test_two_entries_matching_one_name_are_reported_ambiguous_naming_both(data_path):
    """[REQ-SB-95-US-05-AC-03] Never silently resolved to one of them."""
    register_namespace(data_path, GLYPH, [AN_ENTRY])
    register_namespace(data_path, WARD, [{**ANOTHER_ENTRY, "name": A_NAME}], plugin_id="ward-owner")

    resolution = tag_resolution.resolve(A_NAME)

    assert resolution.resolved is False
    assert resolution.outcome == tag_resolution.AMBIGUOUS
    assert resolution.tag is None and resolution.kind is None and resolution.hub is None
    assert sorted(candidate.tag for candidate in resolution.candidates) == [GLYPH_TAG, WARD_TAG]
    assert GLYPH_TAG in resolution.message and WARD_TAG in resolution.message


def test_two_entries_sharing_a_domain_are_reported_ambiguous_naming_both(data_path):
    """[REQ-SB-95-US-05-AC-03]"""
    shared = "shared.example.invalid"
    register_namespace(data_path, GLYPH, [
        {**AN_ENTRY, "domains": [shared]},
        {**ANOTHER_ENTRY, "slug": "second-claimant", "domains": [f"info@{shared}"]},
    ])

    by_domain = tag_resolution.resolve(shared.upper())
    by_address = tag_resolution.resolve(f"Anyone@{shared}")

    for resolution in (by_domain, by_address):
        assert resolution.outcome == tag_resolution.AMBIGUOUS
        assert resolution.resolved is False
        assert sorted(candidate.tag for candidate in resolution.candidates) == [
            GLYPH_TAG, "glyph/second-claimant",
        ]
        assert all(candidate.tag in resolution.message for candidate in resolution.candidates)


def test_one_entry_matched_by_two_of_its_own_spellings_is_not_ambiguous(data_path):
    """[REQ-SB-95-US-05-AC-03] Ambiguity means two entries, not two ways of
    naming one -- otherwise an entry listing its own name as an alias could
    never be resolved at all."""
    register_namespace(data_path, GLYPH, [{**AN_ENTRY, "aliases": [A_NAME, A_NAME.upper()]}, AN_ENTRY])

    resolution = tag_resolution.resolve(A_NAME)

    assert resolution.resolved is True
    assert resolution.tag == GLYPH_TAG
    assert len(resolution.candidates) == 1


# -- AC-05: the honest non-answers ----------------------------------------------------


def test_a_name_no_namespace_knows_does_not_resolve_and_repeats_it_exactly(data_path):
    """[REQ-SB-95-US-05-AC-05] No scoped read and no search is performed --
    both are armed to fail this test if touched."""
    register_namespace(data_path, GLYPH, [AN_ENTRY])
    asked = "  A Name Nobody Registered  "

    resolution = tag_resolution.resolve(asked)

    assert resolution.resolved is False
    assert resolution.outcome == tag_resolution.DID_NOT_RESOLVE
    assert resolution.name_as_asked == asked
    assert asked in resolution.message
    assert "did not resolve" in resolution.message
    assert resolution.tag is None and resolution.kind is None and resolution.hub is None
    assert resolution.candidates == []
    assert resolution.every_namespace_answered is True


def test_with_zero_namespaces_registered_nothing_resolves_honestly(data_path):
    """[REQ-SB-95-US-05-AC-05] `ADR-035`'s degrade-to-nothing, literal: no
    plugin is installed at all."""
    PluginManager().load_all()
    assert PluginManager().get_tag_namespaces() == []

    resolution = tag_resolution.resolve(A_NAME)

    assert resolution.resolved is False
    assert resolution.outcome == tag_resolution.DID_NOT_RESOLVE
    assert resolution.name_as_asked == A_NAME
    assert A_NAME in resolution.message


def test_a_raising_namespace_is_skipped_and_logged_while_the_rest_still_answer(data_path, caplog):
    """[REQ-SB-95-US-05-AC-05] The broken one is skipped and logged, the other
    still resolves its own names, and a name only the broken one knew returns
    "did not resolve" rather than anything else."""
    install(data_path, "quarl-owner", raising_backend(QUARL, "the registry behind this is unreadable"))
    install(data_path, "glyph-owner", registry_backend(GLYPH))
    set_entries(data_path, "glyph-owner", [AN_ENTRY])
    PluginManager().load_all()
    assert len(PluginManager().get_tag_namespaces()) == 2, "both namespaces must really be registered"

    with caplog.at_level("WARNING", logger=tag_resolution.__name__):
        still_answered = tag_resolution.resolve(A_NAME)
        only_the_broken_one_knew = tag_resolution.resolve("Something Only Quarl Knew")

    assert still_answered.resolved is True
    assert still_answered.tag == GLYPH_TAG
    assert only_the_broken_one_knew.resolved is False
    assert only_the_broken_one_knew.outcome == tag_resolution.DID_NOT_RESOLVE
    assert only_the_broken_one_knew.tag is None

    logged = [record.getMessage() for record in caplog.records if record.levelname == "WARNING"]
    assert any(QUARL in message and "unreadable" in message for message in logged), logged


def test_an_answer_reached_without_every_namespace_is_not_dressed_as_a_final_one(data_path):
    """[REQ-SB-95-US-05-AC-05] "nothing knows that name" and "something could
    not be asked" are two different answers, and the second may never borrow
    the look of the first (`SPRINT-091` retro)."""
    install(data_path, "quarl-owner", raising_backend(QUARL, "the registry behind this is unreadable"))
    PluginManager().load_all()

    resolution = tag_resolution.resolve(A_NAME)

    assert resolution.outcome == tag_resolution.DID_NOT_RESOLVE
    assert resolution.every_namespace_answered is False
    [could_not_answer] = resolution.namespaces_that_could_not_answer
    assert could_not_answer.namespace == QUARL
    assert could_not_answer.plugin_id == "quarl-owner"
    assert "unreadable" in could_not_answer.failure
    assert "incomplete rather than final" in resolution.message


# -- AC-07: every tag key in the vault is named, never dropped -----------------------


@pytest.fixture()
def vault_with_unregistered_tags(tmp_path, monkeypatch) -> Path:
    """A vault carrying tags from namespaces nobody registered, including one
    note whose path passes 260 characters -- the limit `os.path.isfile()`
    answers False at, silently, which is how a tag key would go missing."""
    vault = tmp_path / "vault"
    long_name = ("a deliberately long synthetic note name standing in for the sort of subject "
                 "line a captured thread really carries")
    long_note = f"Work/Threads/{long_name}/{long_name}.md"
    notes = {
        "Work/Hubs/Lumen Cartography.md": [GLYPH_TAG, "kind/hub"],
        "Work/Hubs/Tessellate Works.md": [WARD_TAG, "kind/hub"],
        "Work/Threads/A quiet handover.md": [GLYPH_TAG, "kind/thread"],
        long_note: ["zz9/plural-z-alpha", "kind/thread"],
        "Work/Notes/Loose ends.md": ["urgent"],
    }
    for relative, tags in notes.items():
        write_note(vault, relative, tags)
    assert len(str(vault / long_note)) > 260, "the fixture must actually pass the limit"
    monkeypatch.setattr(settings, "vault_path", vault)
    VaultManager().rebuild_index()
    return vault


def test_every_tag_key_with_no_registered_entry_is_named_and_none_is_dropped(
        data_path, vault_with_unregistered_tags):
    """[REQ-SB-95-US-05-AC-07] One namespace is registered; everything else in
    the vault is unknown and is reported BY NAME rather than dropped."""
    register_namespace(data_path, GLYPH, [AN_ENTRY])

    report = tag_resolution.report_unknown_tags()

    assert report.index_was_read is True
    assert report.is_complete is True
    assert report.known_tags == [GLYPH_TAG]
    assert report.unknown_tags == ["kind/hub", "kind/thread", WARD_TAG, "zz9/plural-z-alpha"]
    assert sorted(report.known_tags + report.unknown_tags) == VaultManager().get_tag_index_keys()
    assert report.tags_whose_namespace_could_not_answer == []
    assert "zz9/plural-z-alpha" in report.message or "4" in report.message


def test_a_registered_tag_no_note_carries_is_its_own_answer_not_an_unknown_tag(
        data_path, vault_with_unregistered_tags):
    """[REQ-SB-95-US-05-AC-07] "no such tag" and "the tag exists and no note
    carries it" are two different answers."""
    register_namespace(data_path, GLYPH, [AN_ENTRY, {**AN_ENTRY, "slug": "nothing-written-yet",
                                                     "name": "Nothing Written Yet"}])

    report = tag_resolution.report_unknown_tags()

    assert report.registered_tags_with_no_notes == ["glyph/nothing-written-yet"]
    assert "glyph/nothing-written-yet" not in report.unknown_tags
    assert "glyph/nothing-written-yet" not in VaultManager().get_tag_index_keys()
    assert tag_resolution.resolve("Nothing Written Yet").tag == "glyph/nothing-written-yet"


def test_a_tag_whose_namespace_could_not_answer_is_never_counted_as_unknown(
        data_path, vault_with_unregistered_tags):
    """[REQ-SB-95-US-05-AC-07] A failed read is not a finding: the `glyph`
    namespace is registered and broken, so its tag is neither known nor
    unknown -- it is unclassified, and the report says which namespace could
    not be asked."""
    install(data_path, "glyph-owner", raising_backend(GLYPH, "the registry behind this is unreadable"))
    PluginManager().load_all()

    report = tag_resolution.report_unknown_tags()

    assert report.index_was_read is True
    assert report.is_complete is False
    assert report.tags_whose_namespace_could_not_answer == [GLYPH_TAG]
    assert GLYPH_TAG not in report.unknown_tags
    assert report.known_tags == []
    assert [failure.namespace for failure in report.namespaces_that_could_not_answer] == [GLYPH]
    assert "could not be asked" in report.message


def test_an_unreadable_index_reports_nothing_rather_than_nothing_unknown(data_path, monkeypatch):
    """[REQ-SB-95-US-05-AC-07] "we read it and there were none" is an empty
    list; "we could not read it" is `None`. A caller cannot collapse the two
    by being careless (`SPRINT-091` retro)."""
    register_namespace(data_path, GLYPH, [AN_ENTRY])

    def the_index_cannot_be_read(self):
        raise RuntimeError("the vault index is unavailable")

    monkeypatch.setattr(VaultManager, "get_tag_index_keys", the_index_cannot_be_read)

    report = tag_resolution.report_unknown_tags()

    assert report.index_was_read is False
    assert report.is_complete is False
    assert report.unknown_tags is None
    assert report.known_tags is None
    assert report.registered_tags_with_no_notes is None
    assert report.tags_whose_namespace_could_not_answer is None
    assert "the vault index is unavailable" in report.index_failure
    assert "could not be read" in report.message
