"""The soul as one verbatim document, and config as two labelled layers
(`REQ-SB-99-US-01-T04`, `ADR-043`).

Three raw reads the profile debug view needs and no surface serves today:

- `read_soul_document()` -- the full `SOUL.md` exactly as written. Everything
  downstream of `read_soul()` is lossy: `_split_soul_sections()` parses
  `## Scope` down to folders/tags and `_soul_excerpt()` cuts the first
  paragraph to 280 characters, so a document reassembled from either is not
  evidence of what the agent was actually given.
- `read_config_layers()` -- the profile's own `config.yaml` and the install
  root's, as two layers that are never merged. There is no inheritance model
  in this codebase to reproduce and Hermes' own precedence is not readable
  from this repository, so an "effective" value would be a guess at which
  file won.
- `install_is_readable()` -- "the install cannot be read at all" told apart
  from "this profile has no such file".

Honest absence is the point of the last two thirds of this file: a missing
file, an unreadable file and an empty file are four-way distinct here
(`absent` / `unreadable` / `read` with nothing in it / `read`), because a view
that collapses them says a profile holds nothing when the truth is that it
could not be read -- `BUG-085` (a job reporting `ok` while capture was dead)
and `BUG-088` (a refused plugin rendering as a broken page) are the two
measured precedents for that class of lie.

Cost is pinned by equality, not by a bound: each reader's exact list of file
reads is asserted (`BUG-086` is the measured precedent for an unwatched read
path -- 4.4 of the Agents Map's 6 seconds).

No test here touches the operator's real install. Every fixture is a real
Hermes home built under `tmp_path` -- real files, no mocks of the code under
test -- `subprocess.run`/`Popen` are refused for the whole file, and the last
two tests assert conftest's sandbox and prove every single path these readers
touched lies under `tmp_path`.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from app.config import settings
from app.hermes.config import HermesConfig
from app.hermes.profiles import (
    CONFIG_LAYER_INSTALL_ROOT,
    CONFIG_LAYER_PROFILE,
    FILE_IS_ABSENT,
    FILE_IS_UNREADABLE,
    FILE_WAS_READ,
    HermesProfiles,
    _soul_excerpt,
)
from app.hermes.skills import HermesSkills

# Captured before any test can patch it -- the recorder below wraps the real
# read rather than replacing it, so the fixtures stay real files on disk.
_REAL_READ_TEXT = Path.read_text

PROFILE = "adnoc-expert"

# The `default` profile IS <HERMES_HOME>, and with no profile.yaml of its own
# its `description` is `_soul_excerpt`'s 280-character cut of this first
# paragraph -- the live Agents Map surface this task must leave untouched.
ROOT_SOUL = """You are the primary identity of this install. You answer for the operator across every channel, you keep the vault's own conventions, and you never write into a profile you were not asked about. When a request is ambiguous you ask one question rather than guessing, because a wrong write costs far more than a slow answer.

## Guardrails

- Never send anything outside the operator's own domain without asking.
"""

# Pinned literals, not recomputations: if `_soul_excerpt` or `_first_sentence`
# ever changes, these fail, which is exactly what `AC-01`'s third clause asks
# the suite to notice.
ROOT_DESCRIPTION = (
    "You are the primary identity of this install. You answer for the operator across every "
    "channel, you keep the vault's own conventions, and you never write into a profile you were "
    "not asked about. When a request is ambiguous you ask one question rather than guessing, "
    "because a…"
)
ROOT_SHORT_DESCRIPTION = "You are the primary identity of this install."

# A soul with the shape `AC-01` is about: a `## Scope` section whose body is
# prose (the part `_split_soul_sections()` throws away, keeping only
# folders/tags) and a further section after it (so section ORDER is
# observable, not just section presence).
PROFILE_SOUL = """# ADNOC Expert

You act for the operator on everything ADNOC. You know the account's history, its people and
its open commitments, and you answer from the vault rather than from memory.

## Guardrails

- Never quote a commercial figure that is not in the vault.
- Never write into another customer's folder.

## Scope

Your scope is the ADNOC account and nothing else. That means the Customer note, every Project
note beneath it, the meetings and the threads that evidence them -- and, deliberately, not the
operator's personal notes, even when they mention ADNOC in passing.

folders:
  - Customers/ADNOC
tags:
  - adnoc

## Escalation

When a commitment is at risk, say so in the first line of the answer rather than at the end.
"""


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


@pytest.fixture(autouse=True)
def no_real_process_escapes_this_file(monkeypatch):
    """These are file reads and nothing else. Refusing both spawn entry points
    for the whole file turns "this reader must not shell out" from a claim in
    a docstring into something the suite enforces."""

    def refuse(*args, **kwargs):
        raise AssertionError(f"a raw-read test spawned a real process: {args!r}")

    monkeypatch.setattr(subprocess, "run", refuse)
    monkeypatch.setattr(subprocess, "Popen", refuse)


@pytest.fixture()
def home(tmp_path) -> Path:
    """A real Hermes home: the `default` profile at the root, one named
    profile beneath `profiles/`, and the two config.yaml files that make the
    layering observable -- the root sets only `provider`, the profile only
    `default`, so a merge would be visible as a layer carrying both."""
    _write(tmp_path / "SOUL.md", ROOT_SOUL)
    _write(tmp_path / "config.yaml", "model:\n  provider: custom\n")
    profile_dir = tmp_path / "profiles" / PROFILE
    _write(profile_dir / "SOUL.md", PROFILE_SOUL)
    _write(profile_dir / "config.yaml", "model:\n  default: gpt-5\n")
    _write(profile_dir / "profile.yaml", f"description: The {PROFILE} profile.\n")
    return tmp_path


@pytest.fixture()
def profiles(home) -> HermesProfiles:
    config = HermesConfig(base_url="http://127.0.0.1:9119", home_path=home)
    return HermesProfiles(config, HermesSkills(config))


class RecordedTextReads:
    """Wraps the real `Path.read_text` -- the files stay real, the reads get
    counted. Used to pin cost by equality rather than by an upper bound."""

    def __init__(self) -> None:
        self.paths: list[Path] = []

    def __call__(self, path: Path, *args, **kwargs) -> str:
        self.paths.append(Path(path))
        return _REAL_READ_TEXT(path, *args, **kwargs)


@pytest.fixture()
def recorded_reads(monkeypatch) -> RecordedTextReads:
    recorder = RecordedTextReads()

    # A plain function, not the recorder itself: only a function is a
    # descriptor, so only a function gets handed the Path it was called on.
    def record_then_really_read(path: Path, *args, **kwargs) -> str:
        return recorder(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", record_then_really_read)
    return recorder


# [REQ-SB-99-US-01-AC-01]
def test_the_soul_comes_back_byte_for_byte_with_the_file_it_came_from(profiles, home):
    """Verbatim means verbatim: the same characters, the same section order,
    and the `## Scope` body that `_split_soul_sections()` parses away."""
    soul_path = home / "profiles" / PROFILE / "SOUL.md"

    document = profiles.read_soul_document(PROFILE)

    assert document.text == soul_path.read_text(encoding="utf-8")
    assert document.path == str(soul_path), "the view must be able to name the file on screen"
    assert (document.status, document.error) == (FILE_WAS_READ, "")
    assert "Your scope is the ADNOC account and nothing else." in document.text, (
        "the `## Scope` BODY is the genuine loss -- the Registry keeps only folders/tags"
    )
    assert document.text.index("## Guardrails") < document.text.index("## Scope") < document.text.index("## Escalation"), (
        "section order survives; a soul reassembled from prompt/guardrails/scope cannot keep it"
    )


# [REQ-SB-99-US-01-AC-01]
def test_the_full_soul_is_not_the_280_character_excerpt(profiles, home):
    profile_dir = home / "profiles" / PROFILE

    text = profiles.read_soul_document(PROFILE).text

    assert len(text) > 280
    assert text != _soul_excerpt(profile_dir)
    assert not text.endswith("…"), "an excerpt is never presented as the full soul"


# [REQ-SB-99-US-01-AC-01]
def test_the_live_short_description_surface_is_untouched(profiles, home):
    """`_soul_excerpt`'s 280 characters is the `default` profile's
    `description` across the Agents Map. These are the values that fixture
    produced before this task; the new reader must not have moved them."""
    primary = profiles.find_by_id("default")

    assert primary.description == ROOT_DESCRIPTION
    assert primary.short_description == ROOT_SHORT_DESCRIPTION
    assert primary.description == _soul_excerpt(home)
    assert profiles.read_soul("default") == ROOT_SOUL, "read_soul() still returns the same bytes"
    assert profiles.read_soul_document("default").text == ROOT_SOUL
    assert len(primary.description) < len(ROOT_SOUL), "the excerpt is still an excerpt"


# [REQ-SB-99-US-01-AC-03]
def test_a_named_profile_reads_as_two_labelled_layers_and_nothing_merged(profiles, home):
    own, install_root = profiles.read_config_layers(PROFILE)

    assert (own.scope, own.path) == (CONFIG_LAYER_PROFILE, str(home / "profiles" / PROFILE / "config.yaml"))
    assert (install_root.scope, install_root.path) == (CONFIG_LAYER_INSTALL_ROOT, str(home / "config.yaml"))
    assert own.values == {"model": {"default": "gpt-5"}}
    assert install_root.values == {"model": {"provider": "custom"}}
    assert "provider" not in own.values["model"], "the root's key must not leak into the profile layer"
    assert "default" not in install_root.values["model"], "and the profile's must not leak into the root's"


# [REQ-SB-99-US-01-AC-03]
def test_no_merged_effective_value_is_returned_anywhere(profiles):
    """Hermes' own precedence is not readable from this repository, so a layer
    carrying both keys would be a guess at which file won (`ADR-043`)."""
    layers = profiles.read_config_layers(PROFILE)

    assert len(layers) == 2, "two layers and nothing else -- no third, merged one"
    assert not any(set(layer.values["model"]) == {"default", "provider"} for layer in layers)
    assert [sorted(layer.values["model"]) for layer in layers] == [["default"], ["provider"]]


# [REQ-SB-99-US-01-AC-03]
def test_the_default_profile_has_one_layer_because_it_is_the_install_root(profiles, home):
    """`<HERMES_HOME>/config.yaml` is the `default` profile's OWN config;
    listing it twice would invent a second source for the same file."""
    layers = profiles.read_config_layers("default")

    assert len(layers) == 1
    assert layers[0].path == str(home / "config.yaml")
    assert layers[0].values == {"model": {"provider": "custom"}}


# [REQ-SB-99-US-01-AC-06]
def test_a_missing_soul_names_the_file_it_looked_for_and_says_it_is_absent(profiles, home):
    soul_path = home / "profiles" / PROFILE / "SOUL.md"
    soul_path.unlink()

    document = profiles.read_soul_document(PROFILE)

    assert document.text is None, "nothing is fabricated to fill the gap"
    assert document.path == str(soul_path)
    assert document.status == FILE_IS_ABSENT
    assert str(soul_path) in document.error
    assert not soul_path.exists(), "looking must not create the file it looked for"


# [REQ-SB-99-US-01-AC-06]
def test_an_unreadable_soul_is_a_different_answer_from_an_absent_one(profiles, home):
    """The distinction the screen needs: `BUG-085`'s class of lie is reporting
    "there is nothing here" when the truth is "this could not be read"."""
    soul_path = home / "profiles" / PROFILE / "SOUL.md"
    soul_path.write_bytes(b"\xff\xfe not utf-8 at all \x00")

    document = profiles.read_soul_document(PROFILE)

    assert document.status == FILE_IS_UNREADABLE
    assert document.status != FILE_IS_ABSENT
    assert document.text is None
    assert document.error, "an unreadable file carries the real reason, not an empty string"
    assert document.path == str(soul_path)


# [REQ-SB-99-US-01-AC-06]
def test_an_empty_soul_is_read_successfully_and_is_not_absent(profiles, home):
    """A file that exists and says nothing is a fourth answer again -- the
    operator who emptied a SOUL.md needs to see that it is empty, not that it
    is missing."""
    _write(home / "profiles" / PROFILE / "SOUL.md", "")

    document = profiles.read_soul_document(PROFILE)

    assert (document.status, document.text, document.error) == (FILE_WAS_READ, "", "")


# [REQ-SB-99-US-01-AC-06]
def test_one_unreadable_config_layer_never_hides_the_other(profiles, home):
    _write(home / "profiles" / PROFILE / "config.yaml", "model:\n  default: [unclosed\n")

    own, install_root = profiles.read_config_layers(PROFILE)

    assert own.status == FILE_IS_UNREADABLE
    assert own.values is None, "a layer that did not parse must not report an empty mapping"
    assert str(home / "profiles" / PROFILE / "config.yaml") in own.error
    assert install_root.status == FILE_WAS_READ
    assert install_root.values == {"model": {"provider": "custom"}}, (
        "every region that COULD be read is still shown (`US-01` Scenario 6)"
    )


# [REQ-SB-99-US-01-AC-06]
def test_an_absent_config_layer_is_told_apart_from_an_empty_one(profiles, home):
    """`_read_yaml_file()` reports both as `{}` to its own callers, which is
    why `_read_agent()` cannot tell an unset key from an absent file. These
    layers can."""
    (home / "profiles" / PROFILE / "config.yaml").unlink()
    _write(home / "config.yaml", "")

    own, install_root = profiles.read_config_layers(PROFILE)

    assert (own.status, own.values) == (FILE_IS_ABSENT, None)
    assert str(home / "profiles" / PROFILE / "config.yaml") in own.error
    assert (install_root.status, install_root.values, install_root.error) == (FILE_WAS_READ, {}, "")


# [REQ-SB-99-US-01-AC-07]
def test_install_is_readable_separates_no_install_from_no_such_file(home, tmp_path):
    """The first of `ADR-043`'s three failures. A profile read on an absent
    install must not render as "this profile has no soul"."""
    absent_home = tmp_path / "no-hermes-install-here"
    unreachable = HermesProfiles(
        HermesConfig(base_url="", home_path=absent_home),
        HermesSkills(HermesConfig(base_url="", home_path=absent_home)),
    )
    readable = HermesProfiles(
        HermesConfig(base_url="", home_path=home),
        HermesSkills(HermesConfig(base_url="", home_path=home)),
    )

    assert unreachable.install_is_readable() is False
    assert readable.install_is_readable() is True
    assert not absent_home.exists(), "asking must not create the install it asked about"


# [REQ-SB-99-US-01-AC-07]
def test_a_file_on_an_absent_install_still_answers_honestly_rather_than_raising(tmp_path):
    absent_home = tmp_path / "no-hermes-install-here"
    config = HermesConfig(base_url="", home_path=absent_home)
    profiles = HermesProfiles(config, HermesSkills(config))

    document = profiles.read_soul_document(PROFILE)
    layers = profiles.read_config_layers(PROFILE)

    assert document.status == FILE_IS_ABSENT
    assert [layer.status for layer in layers] == [FILE_IS_ABSENT, FILE_IS_ABSENT]
    assert not absent_home.exists()


# [constraint: cost]
def test_each_reader_costs_exactly_the_files_it_names(profiles, home, recorded_reads):
    """Pinned by equality, not by a bound: `BUG-086` was a listing path whose
    per-profile reads nobody had counted until it cost 4.4 of 6 seconds."""
    profiles.read_soul_document(PROFILE)
    assert recorded_reads.paths == [home / "profiles" / PROFILE / "SOUL.md"]

    recorded_reads.paths.clear()
    profiles.read_config_layers(PROFILE)
    assert recorded_reads.paths == [
        home / "profiles" / PROFILE / "config.yaml",
        home / "config.yaml",
    ]

    recorded_reads.paths.clear()
    profiles.read_config_layers("default")
    assert recorded_reads.paths == [home / "config.yaml"], "`default` reads one file, not the same one twice"

    recorded_reads.paths.clear()
    assert profiles.install_is_readable() is True
    assert recorded_reads.paths == [], "asking whether the install exists reads no file at all"


# [constraint: cost]
def test_a_failed_read_is_reported_once_and_never_retried(profiles, home, recorded_reads):
    (home / "profiles" / PROFILE / "SOUL.md").unlink()
    (home / "profiles" / PROFILE / "config.yaml").unlink()

    profiles.read_soul_document(PROFILE)
    profiles.read_config_layers(PROFILE)

    assert recorded_reads.paths == [
        home / "profiles" / PROFILE / "SOUL.md",
        home / "profiles" / PROFILE / "config.yaml",
        home / "config.yaml",
    ], "a file that is not there is asked for exactly once"


# [REQ-SB-99-US-01-AC-05]
def test_reading_a_profile_writes_nothing(profiles, home):
    """`US-01` Scenario 5 by construction: these readers have no write in
    them, including for the profile that does not exist at all."""
    before = sorted(str(p.relative_to(home)) for p in home.rglob("*"))

    profiles.read_soul_document(PROFILE)
    profiles.read_config_layers(PROFILE)
    profiles.read_soul_document("no-such-profile")
    profiles.read_config_layers("no-such-profile")
    profiles.install_is_readable()

    assert sorted(str(p.relative_to(home)) for p in home.rglob("*")) == before
    assert not (home / "profiles" / "no-such-profile").exists()


def test_no_test_here_can_see_the_operators_real_install(profiles, home, tmp_path, recorded_reads):
    """Stated rather than assumed. conftest's first seam points
    `settings.hermes_home_path` at a directory that does not exist, and these
    readers derive every path from the `HermesConfig.home_path` they were
    handed -- so the proof is that every file any of them touched is under
    this test's own `tmp_path`."""
    assert not settings.hermes_home_path.exists(), "conftest's sandboxed home must not exist"
    assert home.is_relative_to(tmp_path)

    profiles.read_soul_document(PROFILE)
    profiles.read_soul_document("default")
    profiles.read_config_layers(PROFILE)
    profiles.read_config_layers("default")
    profiles.install_is_readable()

    assert recorded_reads.paths, "the recorder must actually have seen the reads it is vouching for"
    assert all(path.is_relative_to(tmp_path) for path in recorded_reads.paths), recorded_reads.paths
    assert not any(path.is_relative_to(settings.hermes_home_path.parent) for path in recorded_reads.paths)
