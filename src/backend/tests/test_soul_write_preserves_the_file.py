"""A write to an agent's SOUL.md changes what it was asked to change and
nothing else (`BUG-093`, `BUG-092`).

Every assertion here is byte-for-byte (`read_bytes()` before and after), never
semantic. That is the point: the defect these tests close was invisible to a
semantic comparison, because the file the app wrote back still parsed into the
same three fields it had read. What it no longer held was a human's prose
inside `## Scope`, the order the sections were in, and the final newline --
all of which a "the agent still has the same scope" assertion is happy with.

Measured on a disposable install before the fix: a prompt-only publish took
the profile below from 269 bytes to 187, deleted both lines of Scope prose and
moved `## How I like to be answered` above `## Guardrails`.

Nothing here can reach the operator's own install: `settings.hermes_home_path`
and `settings.second_brain_data_path` both point inside pytest's `tmp_path`,
on top of the suite-wide sandbox in `conftest.py`.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import app.business.hermes.client as hermes_client_module
from app.business.core.agents.agent_manager import AgentManager, _rewrite_soul
from app.config import settings
from app.data_access.registry import loader as registry_loader

AGENT_ID = "adnoc-expert"
SECTION_ID = "customers"

# A soul no composition of (prompt, guardrails, scope) can reproduce: prose in
# `## Scope` beside the one line this app understands, a section it does not
# recognise AFTER the ones it does, and a final newline.
HAND_WRITTEN_SOUL = (
    "You are the ADNOC Expert.\n"
    "\n"
    "## Guardrails\n"
    "\n"
    "Never invent a number.\n"
    "\n"
    "## Scope\n"
    "\n"
    "Everything ADNOC touches, including the downstream joint ventures.\n"
    "Ask before you widen this.\n"
    "\n"
    "Tags: customer/adnoc\n"
    "\n"
    "## How I like to be answered\n"
    "\n"
    "Short, with the number first.\n"
)


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def _write_exactly(path: Path, text: str) -> None:
    """The file holding exactly these bytes -- `newline=""` because the
    default would turn every `\\n` into `\\r\\n` on this host, and a test
    about which bytes a write leaves behind cannot have its own fixture
    rewritten on the way to disk. 21 of the reporting install's 40 profiles
    are LF, so LF is the shape to hold the app to."""
    path.write_text(text, encoding="utf-8", newline="")


@pytest.fixture
def soul_path(tmp_path, monkeypatch) -> Path:
    """One real profile on a disposable install, plus the Registry entry that
    makes `update()` take its full path (Hermes write + Registry mirror)."""
    home = tmp_path / "hermes-home"
    profile_dir = home / "profiles" / AGENT_ID
    profile_dir.mkdir(parents=True)
    _write_exactly(profile_dir / "SOUL.md", HAND_WRITTEN_SOUL)

    monkeypatch.setattr(settings, "hermes_home_path", home)
    monkeypatch.setattr(settings, "second_brain_data_path", tmp_path / "sb-data")
    monkeypatch.setattr(registry_loader, "_hermes_reachable", lambda: True)
    monkeypatch.setattr(hermes_client_module, "_client", None)
    registry_loader._registry = None
    registry_loader._last_seen_fingerprint = None

    data = tmp_path / "sb-data" / "data"
    _write_json(data / "Sections" / SECTION_ID / "Section.json", {"id": SECTION_ID, "name": "Customers"})
    agent_dir = data / "Sections" / SECTION_ID / "Agents" / AGENT_ID
    _write_json(agent_dir / "Agent.json", {
        "id": AGENT_ID, "name": "ADNOC Expert", "type": "expert", "icon": None, "color": None,
    })
    _write_exactly(agent_dir / "soul.md", HAND_WRITTEN_SOUL)
    return profile_dir / "SOUL.md"


def _registry_mirror() -> Path:
    return registry_loader.data_root() / "Sections" / SECTION_ID / "Agents" / AGENT_ID / "soul.md"


def test_a_prompt_only_write_changes_only_the_prompt(soul_path) -> None:
    """The invariant: append a block to the prompt, and the ONLY difference
    in the file is that block. Scope prose, guardrails, section order and the
    final newline are the same bytes they were."""
    before = soul_path.read_bytes()
    manager = AgentManager()
    agent = manager.get_by_id(AGENT_ID)

    appended = "\n\n<!-- BEGIN SOMETHING -->\nA block.\n<!-- END SOMETHING -->"
    manager.update(AGENT_ID, prompt=agent.prompt + appended)
    after = soul_path.read_bytes()

    assert after != before, "the prompt really was written"
    assert after.decode("utf-8").replace(appended, "", 1).encode("utf-8") == before, (
        "removing exactly what was appended gives back the original bytes"
    )
    assert after.endswith(b"\n"), "the final newline survives (BUG-092)"
    assert b"Everything ADNOC touches, including the downstream joint ventures." in after
    assert b"Ask before you widen this." in after
    assert after.index(b"## Guardrails") < after.index(b"## Scope") < after.index(b"## How I like")


def test_a_write_that_changes_nothing_writes_nothing(soul_path) -> None:
    """Sending back exactly what was read -- every field, as the Agent detail
    panel does on every save -- leaves the file untouched, mtime included."""
    before = soul_path.read_bytes()
    before_mtime = soul_path.stat().st_mtime_ns
    agent = AgentManager().get_by_id(AGENT_ID)

    AgentManager().update(
        AGENT_ID, prompt=agent.prompt, guardrails=agent.guardrails, scope=agent.scope,
    )

    assert soul_path.read_bytes() == before
    assert soul_path.stat().st_mtime_ns == before_mtime, "no write happened at all"


def test_a_prompt_edit_carrying_the_scope_it_read_does_not_touch_the_scope(soul_path) -> None:
    """The real shape of a UI save: the panel posts the whole entity, so a
    prompt edit arrives with the scope it was given. The parsed scope round
    trips to the same two values, so the section a human wrote prose into is
    left exactly as it is -- this is the path that was destroying it."""
    before = soul_path.read_bytes()
    agent = AgentManager().get_by_id(AGENT_ID)
    edited = agent.prompt.replace("You are the ADNOC Expert.", "You are the ADNOC Expert, and brief.")

    AgentManager().update(
        AGENT_ID, prompt=edited, guardrails=agent.guardrails, scope=agent.scope,
    )
    after = soul_path.read_bytes()

    assert after == before.replace(
        b"You are the ADNOC Expert.", b"You are the ADNOC Expert, and brief.",
    )


def test_changing_the_scope_changes_the_scope_line_and_nothing_else(soul_path) -> None:
    """The other half of the invariant: a write that DOES change scope edits
    the `Tags:` line it understands, and leaves the prose beside it, the
    other sections and the final newline byte-identical."""
    before = soul_path.read_bytes()

    AgentManager().update(AGENT_ID, scope={"folders": [], "tags": ["customer/adnoc", "energy"]})
    after = soul_path.read_bytes()

    assert after == before.replace(b"Tags: customer/adnoc", b"Tags: customer/adnoc, energy")


def test_adding_a_folder_to_a_scope_that_had_none_keeps_the_prose(soul_path) -> None:
    before = soul_path.read_bytes()

    AgentManager().update(AGENT_ID, scope={"folders": ["Customers/ADNOC"], "tags": ["customer/adnoc"]})
    after = soul_path.read_bytes()

    assert b"Everything ADNOC touches" in after
    assert after == before.replace(
        b"Tags: customer/adnoc", b"Tags: customer/adnoc\nFolders: Customers/ADNOC",
    )


def test_changing_the_guardrails_changes_only_that_section(soul_path) -> None:
    before = soul_path.read_bytes()

    AgentManager().update(AGENT_ID, guardrails="Never invent a number. Cite the note.")
    after = soul_path.read_bytes()

    assert after == before.replace(
        b"Never invent a number.", b"Never invent a number. Cite the note.",
    )


def test_a_registry_only_change_never_rewrites_the_soul(soul_path) -> None:
    """Renaming an agent is not an edit to its soul. It used to recompose and
    rewrite the file anyway, which is how a field nobody touched got lost."""
    before = soul_path.read_bytes()

    AgentManager().update(AGENT_ID, name="ADNOC Specialist")

    assert soul_path.read_bytes() == before


def test_the_registry_mirror_gets_the_same_text_as_the_profile(soul_path) -> None:
    """`data/.../soul.md` is a one-way mirror of the real SOUL.md, so it has
    to say the same thing -- it was getting the recomposed, lossy version
    even when the write was a rename that touched no soul field at all.

    Text rather than bytes: the mirror is written by the Registry writer, in
    this host's own line endings, and it is not the file Hermes reads."""
    AgentManager().update(AGENT_ID, prompt="You are the ADNOC Expert, briefly.")

    assert _registry_mirror().read_text(encoding="utf-8") == soul_path.read_text(encoding="utf-8")
    assert "Everything ADNOC touches" in _registry_mirror().read_text(encoding="utf-8")


def test_a_write_keeps_the_line_endings_the_file_already_had(soul_path) -> None:
    """Found by this file's own byte comparison, not reported: `read_soul()`
    reads in universal-newline mode and the write used to translate back to
    the platform's, so writing one section of an LF soul rewrote every line
    of it. 21 of the reporting install's 40 profiles are LF."""
    assert b"\r\n" not in soul_path.read_bytes(), "the fixture really is LF"

    AgentManager().update(AGENT_ID, prompt="You are the ADNOC Expert, briefly.")

    assert b"\r\n" not in soul_path.read_bytes()


def test_a_crlf_soul_stays_crlf(soul_path) -> None:
    """The other direction: the 8 profiles this app has already written are
    CRLF, and a write must not flip those to LF either."""
    _write_exactly(soul_path, HAND_WRITTEN_SOUL.replace("\n", "\r\n"))
    before = soul_path.read_bytes()
    agent = AgentManager().get_by_id(AGENT_ID)

    AgentManager().update(
        AGENT_ID,
        prompt=agent.prompt.replace("You are the ADNOC Expert.", "You are the ADNOC Expert, briefly."),
    )
    after = soul_path.read_bytes()

    assert b"\n" in after and after.count(b"\r\n") == after.count(b"\n")
    assert after == before.replace(b"You are the ADNOC Expert.", b"You are the ADNOC Expert, briefly.")


def test_a_soul_with_no_scope_section_does_not_grow_one(soul_path) -> None:
    """`azure-calculator`'s shape: a hand-written soul whose sections are all
    its own. A prompt edit must not append a `## Scope` it never had."""
    hand_written = (
        "You are the Azure Calculator.\n\n## What you don't do\n\nYou don't guess.\n"
    )
    _write_exactly(soul_path, hand_written)
    agent = AgentManager().get_by_id(AGENT_ID)

    AgentManager().update(AGENT_ID, prompt=agent.prompt + "\n\nAlways show the sum.", scope=agent.scope)

    assert soul_path.read_text(encoding="utf-8") == (
        "You are the Azure Calculator.\n\n## What you don't do\n\nYou don't guess."
        "\n\nAlways show the sum.\n"
    )


def test_a_scope_that_parses_to_nothing_still_exists_afterwards(soul_path) -> None:
    """The worst observed case: a `## Scope` holding only prose parses to no
    folders and no tags, so composition emitted no section at all and the
    whole thing vanished."""
    _write_exactly(
        soul_path,
        "You are the ADNOC Expert.\n\n## Scope\n\nAsk the operator before you widen this.\n",
    )
    agent = AgentManager().get_by_id(AGENT_ID)
    assert agent.scope == {"folders": [], "tags": []}

    AgentManager().update(AGENT_ID, prompt=agent.prompt + "\n\nBe brief.", scope=agent.scope)

    assert soul_path.read_text(encoding="utf-8") == (
        "You are the ADNOC Expert.\n\nBe brief.\n\n## Scope\n\n"
        "Ask the operator before you widen this.\n"
    )


# -- _rewrite_soul's own shapes, without an install around them ---------------

def test_rewrite_leaves_a_section_in_the_middle_of_the_prompt_in_place() -> None:
    """The core the UI edits is the file with the recognised sections cut
    out, so it can be discontiguous. Editing one end of it must not move the
    section sitting between the two halves."""
    original = (
        "You are X.\n\n## Scope\n\nTags: a\n\n## Notes\n\nSome notes.\n"
    )
    rewritten = _rewrite_soul(original, prompt="You are X.\n\n## Notes\n\nSome other notes.")

    assert rewritten == "You are X.\n\n## Scope\n\nTags: a\n\n## Notes\n\nSome other notes.\n"


def test_rewrite_of_a_prompt_that_straddles_a_section_still_keeps_the_section() -> None:
    """The one case with no single right answer: the prompt the UI edits is
    the file with `## Guardrails`/`## Scope` cut out, so replacing all of it
    at once is an edit on both sides of them. The new prompt lands in the
    first half, the second half goes, the separators stay -- and the sections
    themselves are never collateral, which is the part that matters."""
    original = (
        "You are X.\n\n## Scope\n\nAsk first.\nTags: a\n\n## Notes\n\nSome notes.\n"
    )
    assert _rewrite_soul(original, prompt="You are Y, and that is all.") == (
        "You are Y, and that is all.\n\n## Scope\n\nAsk first.\nTags: a\n\n\n"
    )


def test_rewrite_appends_a_scope_section_the_file_never_had() -> None:
    original = "You are X.\n"
    assert _rewrite_soul(original, scope={"folders": ["Customers"], "tags": ["a"]}) == (
        "You are X.\n\n## Scope\n\nFolders: Customers\nTags: a\n"
    )


def test_rewrite_appending_a_section_keeps_a_missing_final_newline_missing() -> None:
    assert _rewrite_soul("You are X.", guardrails="Be careful.") == (
        "You are X.\n\n## Guardrails\n\nBe careful."
    )


def test_rewrite_removes_a_scope_section_that_held_only_what_it_parsed() -> None:
    original = "You are X.\n\n## Scope\n\nTags: a\n"
    assert _rewrite_soul(original, scope={"folders": [], "tags": []}) == "You are X.\n\n"


def test_rewrite_clearing_the_scope_keeps_prose_that_was_beside_it() -> None:
    original = "You are X.\n\n## Scope\n\nAsk first.\nTags: a\n"
    assert _rewrite_soul(original, scope={"folders": [], "tags": []}) == (
        "You are X.\n\n## Scope\n\nAsk first.\n"
    )


def test_rewrite_of_an_unchanged_field_is_the_identical_string() -> None:
    assert _rewrite_soul(HAND_WRITTEN_SOUL, prompt=None, guardrails=None, scope=None) == HAND_WRITTEN_SOUL
    parsed_scope = {"folders": [], "tags": ["customer/adnoc"]}
    assert _rewrite_soul(
        HAND_WRITTEN_SOUL, guardrails="Never invent a number.", scope=parsed_scope,
    ) == HAND_WRITTEN_SOUL
