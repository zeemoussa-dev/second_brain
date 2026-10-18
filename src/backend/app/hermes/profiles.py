"""CRUD for Hermes' real Agent (profile) definitions -- profile.yaml/
config.yaml/SOUL.md, read directly off the local install. Every real
call re-reads the actual files, so this can never drift from what
Hermes itself has configured (no local persistence/caching here).

Real layout:
    <home>/                          -- the "default" profile IS the
        SOUL.md                         home dir itself, no profile.yaml
        config.yaml                     of its own
        skills/**/SKILL.md
    <home>/profiles/<name>/          -- every OTHER profile
        SOUL.md
        config.yaml
        profile.yaml                    -- has `description`; absent on
        skills/**/SKILL.md                 "default"

Profile CREATE/DELETE are NOT here -- `hermes profile create --clone`
does real work a plain mkdir can't replicate (copying config.yaml/.env/
SOUL.md/skills from the source profile), so those go through
HermesCLI/HermesClient instead. UPDATE (SOUL.md content, config.yaml
fields) has no CLI equivalent and is genuinely just a file write, so it
lives here.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from app.hermes.config import HermesConfig
from app.hermes.skills import HermesSkill, HermesSkills

_PRIMARY_PROFILE_ID = "default"
_SENTENCE_END = re.compile(r"^(.*?[.!?])(\s|$)", re.DOTALL)

# The three different answers one file read can give (`ADR-043`'s second
# failure). A caller that collapses the last two tells the operator a profile
# holds nothing when the truth is that it could not be read -- BUG-085's class
# of dishonesty. An EMPTY file is none of the three: it is FILE_WAS_READ with
# empty content, which is a fourth, equally honest answer.
FILE_WAS_READ = "read"
FILE_IS_ABSENT = "absent"
FILE_IS_UNREADABLE = "unreadable"

# Which config.yaml a layer was read from. Never a merged third value --
# Hermes' own precedence between the two is not readable from this repository.
CONFIG_LAYER_PROFILE = "profile"
CONFIG_LAYER_INSTALL_ROOT = "install_root"


@dataclass(frozen=True)
class SoulDocument:
    """One profile's SOUL.md as a document rather than as parts: `text` is the
    file verbatim, or None with `status`/`error` saying which failure happened.
    `path` is always the file it came from or would have come from."""
    path: str
    status: str
    text: str | None
    error: str


@dataclass(frozen=True)
class ConfigLayer:
    """One config.yaml exactly as written -- `scope` names which file it is,
    `values` is its own parsed mapping (None when there is nothing to parse)
    and `error` names the file when it could not be read. Two of these are
    never combined into one."""
    scope: str
    path: str
    status: str
    values: dict | None
    error: str


@dataclass
class HermesAgent:
    id: str  # profile folder name, "default" for the primary identity
    name: str
    description: str  # full text -- the profile's own real description/SOUL.md excerpt
    short_description: str  # a genuinely SHORT excerpt of `description`, never fabricated
    model: str
    provider: str
    reasoning_effort: str
    is_primary: bool
    skills: list[HermesSkill] = field(default_factory=list)
    icon: str = "smart_toy"
    source: str = "hermes"


def _read_yaml_file(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        parsed = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _file_error_text(failure: Exception, path: Path) -> str:
    """The OS's own reason, with the file named -- so a caller can report
    which file it was without holding the path itself."""
    reason = getattr(failure, "strerror", None) or str(failure)
    return f"{reason}: {path}"


def _read_file_as_written(path: Path) -> tuple[str, str | None, str]:
    """(status, text, error) for one file read verbatim -- no strip, no
    normalisation, no truncation.

    Absence is decided by the read itself rather than by a preceding
    `is_file()`: on this Windows host a path over 260 characters makes
    `is_file()` answer False (`MEMORY.md`), which would report an unreachable
    file as a file that does not exist. Here the OS's own error is reported
    instead, which is the honest per-file failure `ADR-043` asks for.

    A file whose bytes are not UTF-8 is unreadable, not absent, and not a
    crash -- one such file must not take the whole view down with it.
    """
    try:
        return FILE_WAS_READ, path.read_text(encoding="utf-8"), ""
    except FileNotFoundError as no_such_file:
        return FILE_IS_ABSENT, None, _file_error_text(no_such_file, path)
    except (OSError, UnicodeDecodeError) as unreadable:
        return FILE_IS_UNREADABLE, None, _file_error_text(unreadable, path)


def _first_sentence(text: str, max_len: int = 140) -> str:
    """The real first sentence of `text` -- never fabricated, just a
    genuine excerpt. Falls back to a length-capped prefix if no
    sentence-ending punctuation is found."""
    text = text.strip()
    if not text:
        return ""
    match = _SENTENCE_END.match(text)
    sentence = match.group(1).strip() if match else text
    if len(sentence) > max_len:
        sentence = sentence[:max_len].rsplit(" ", 1)[0].rstrip(".,;:") + "…"
    return sentence


def _soul_excerpt(profile_dir: Path, max_len: int = 280) -> str:
    """First real paragraph of SOUL.md, for profiles with no profile.yaml
    (only "default" today) -- never fabricated, empty if absent."""
    soul_path = profile_dir / "SOUL.md"
    try:
        text = soul_path.read_text(encoding="utf-8").strip()
    except OSError:
        return ""
    first_paragraph = text.split("\n\n", 1)[0].strip()
    if len(first_paragraph) > max_len:
        first_paragraph = first_paragraph[:max_len].rsplit(" ", 1)[0] + "…"
    return first_paragraph


def _deep_merge(base: dict, patch: dict) -> dict:
    merged = dict(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _read_config_layer(scope: str, path: Path) -> ConfigLayer:
    """One config.yaml as written. An empty file is a successful read of a
    file that sets nothing (`{}`), which is a different answer from an absent
    one (None) -- and YAML that does not parse, or parses to something that is
    not a mapping, is a read failure naming the file rather than a silent
    `{}` the way `_read_yaml_file()` has to report it to its own callers."""
    status, text, error = _read_file_as_written(path)
    if text is None:
        return ConfigLayer(scope=scope, path=str(path), status=status, values=None, error=error)
    try:
        parsed = yaml.safe_load(text)
    except yaml.YAMLError as broken_yaml:
        return ConfigLayer(
            scope=scope,
            path=str(path),
            status=FILE_IS_UNREADABLE,
            values=None,
            error=f"{path} is not valid YAML: {broken_yaml}",
        )
    if parsed is None:
        return ConfigLayer(scope=scope, path=str(path), status=FILE_WAS_READ, values={}, error="")
    if not isinstance(parsed, dict):
        return ConfigLayer(
            scope=scope,
            path=str(path),
            status=FILE_IS_UNREADABLE,
            values=None,
            error=f"{path} does not hold a mapping of settings (it parsed as {type(parsed).__name__})",
        )
    return ConfigLayer(scope=scope, path=str(path), status=FILE_WAS_READ, values=parsed, error="")


def is_real_profile(path) -> bool:
    """A profile directory, not one of Hermes' own bookkeeping folders.

    `hermes profile delete` does not erase a profile, it TOMBSTONES it: the
    directory is moved under `profiles/.deleted/<name>`. Taking every
    directory made `.deleted` itself an Agent, id and name both `.deleted`,
    appearing in the Agents list and on the Agents Map after the first
    deletion an install ever performs (BUG-053).

    Excluded by the leading dot rather than by name: `.deleted` is the one
    that bit us, but a dot-prefixed directory under `profiles/` is Hermes'
    own bookkeeping by convention, and a real profile id never starts with
    one -- `hermes profile create` slugs its input.
    """
    return path.is_dir() and not path.name.startswith(".")


class HermesProfiles:
    def __init__(self, config: HermesConfig, skills: HermesSkills) -> None:
        self._config = config
        self._skills = skills

    def _profile_dir(self, agent_id: str) -> Path:
        home = self._config.home_path
        return home if agent_id == _PRIMARY_PROFILE_ID else home / "profiles" / agent_id

    def _read_agent(self, profile_id: str, profile_dir: Path, *, include_skills: bool = True) -> HermesAgent:
        is_primary = profile_id == _PRIMARY_PROFILE_ID
        profile_meta = _read_yaml_file(profile_dir / "profile.yaml")
        description = str(profile_meta.get("description") or "").strip()
        if not description:
            description = _soul_excerpt(profile_dir) if is_primary else ""

        config = _read_yaml_file(profile_dir / "config.yaml")
        model_section = config.get("model") or {}
        model = str(model_section.get("default") or "")
        provider = str(model_section.get("provider") or "")
        reasoning_effort = str((config.get("agent") or {}).get("reasoning_effort") or "medium")

        return HermesAgent(
            id=profile_id,
            name="Primary" if is_primary else profile_id,
            description=description,
            short_description=_first_sentence(description),
            model=model,
            provider=provider,
            reasoning_effort=reasoning_effort,
            is_primary=is_primary,
            # Reading one profile's skills means parsing every SKILL.md it has;
            # across an install's profiles that is thousands of files, and a
            # listing throws every one of them away (`BUG-086`).
            skills=self._skills.get_all(profile_id) if include_skills else [],
            icon="hub" if is_primary else "smart_toy",
        )

    def get_all(self, *, include_skills: bool = True) -> list[HermesAgent]:
        """Every real profile found on disk -- "default" plus every
        profiles/<name> directory. Returns [] (never raises) if home_path
        doesn't exist, e.g. running somewhere without a local Hermes
        install.

        `include_skills=False` leaves every agent's `skills` empty and makes the
        call a cheap read of two small YAML files per profile. Loading them means
        parsing every SKILL.md of every profile -- 2,788 files on the reporting
        install, 4.4 of the Agents Map's 6 seconds, every one of them discarded by
        a caller that only wanted names (`BUG-086`). Ask for a single agent's
        skills with `find_by_id`, which still reads them."""
        home = self._config.home_path
        if not home.is_dir():
            return []
        agents = [self._read_agent(_PRIMARY_PROFILE_ID, home, include_skills=include_skills)]
        profiles_root = home / "profiles"
        if profiles_root.is_dir():
            for profile_dir in sorted(p for p in profiles_root.iterdir() if is_real_profile(p)):
                agents.append(self._read_agent(profile_dir.name, profile_dir, include_skills=include_skills))
        return agents

    def find_by_id(self, agent_id: str) -> HermesAgent | None:
        home = self._config.home_path
        if not home.is_dir():
            return None
        profile_dir = self._profile_dir(agent_id)
        if not profile_dir.is_dir():
            return None
        return self._read_agent(agent_id, profile_dir)

    def read_soul(self, agent_id: str) -> str | None:
        """The real, full SOUL.md content -- distinct from find_by_id's
        `description`, which is a short excerpt derived from it (or from
        profile.yaml, when present)."""
        soul_path = self._profile_dir(agent_id) / "SOUL.md"
        try:
            return soul_path.read_text(encoding="utf-8")
        except OSError:
            return None

    def read_soul_document(self, agent_id: str) -> SoulDocument:
        """The profile's SOUL.md verbatim -- the text exactly as it is on
        disk, section order and `## Scope` body intact -- with the path it
        came from and, when there is no text, which failure happened.

        Distinct from `read_soul()`, which returns the same text but reports
        both "no such file" and "could not be read" as None, and from
        everything downstream of it: `_split_soul_sections()` parses
        `## Scope` down to folders/tags lists and `_soul_excerpt()` cuts the
        first paragraph to 280 characters, so a soul rebuilt from either is
        not evidence of what the agent was actually given (`ADR-043`).
        Nothing here excerpts, splits or reassembles.

        Exactly one file read. Read-only: a missing profile directory is
        reported, never created.
        """
        soul_path = self._profile_dir(agent_id) / "SOUL.md"
        status, text, error = _read_file_as_written(soul_path)
        return SoulDocument(path=str(soul_path), status=status, text=text, error=error)

    def read_config_layers(self, agent_id: str) -> list[ConfigLayer]:
        """The profile's own config.yaml as written and -- for any profile
        other than `default` -- the install root's config.yaml as written, as
        two separate layers in that order.

        Never merged, and no "effective" value: there is no inheritance model
        in this codebase to reproduce (`_deep_merge` is `update()`'s write
        patch, not a parent overlay) and Hermes' own precedence between the
        two files is not readable from this repository, so a single merged
        answer would be a guess at which file won (`ADR-043`). The caller
        labels a key present only in the root layer as inherited, and a key in
        neither as not set, from the two layers themselves.

        `default` gets ONE layer because the `default` profile IS
        <HERMES_HOME> -- its own config.yaml and the install root's are the
        same file, and listing it twice would invent a second source.

        One file read per layer, and one unreadable layer never hides the
        other. `_read_agent()` still reads the profile's own config only.
        """
        layers = [_read_config_layer(CONFIG_LAYER_PROFILE, self._profile_dir(agent_id) / "config.yaml")]
        if agent_id != _PRIMARY_PROFILE_ID:
            layers.append(_read_config_layer(CONFIG_LAYER_INSTALL_ROOT, self._config.home_path / "config.yaml"))
        return layers

    def install_is_readable(self) -> bool:
        """Whether <HERMES_HOME> is a directory at all -- `ADR-043`'s first
        failure, which is a different answer from "this profile has no such
        file" and must not be rendered as one (`US-01` Scenario 7). Exposed
        here so the business layer can ask without reaching for a path of its
        own. One stat, no file read, nothing created."""
        return self._config.home_path.is_dir()

    def write_soul(self, agent_id: str, content: str) -> None:
        """No CLI equivalent exists for this -- SOUL.md is genuinely
        just a file Hermes reads at session-creation time (MEMORY.md's
        own documented "injected once, never re-read mid-conversation"
        constraint)."""
        profile_dir = self._profile_dir(agent_id)
        profile_dir.mkdir(parents=True, exist_ok=True)
        (profile_dir / "SOUL.md").write_text(content, encoding="utf-8")

    def update(self, agent_id: str, config_patch: dict) -> HermesAgent | None:
        """Deep-merges `config_patch` into the profile's own config.yaml
        (e.g. {"model": {"default": "..."}, "agent": {"reasoning_effort":
        "..."}}) and writes it back. For the one config.yaml-independent
        field with a real CLI command (`description`), use
        HermesClient.describe_profile instead -- that one's real
        auxiliary-LLM `--auto` mode has no file-only equivalent."""
        profile_dir = self._profile_dir(agent_id)
        if not profile_dir.is_dir():
            return None
        config_path = profile_dir / "config.yaml"
        current = _read_yaml_file(config_path)
        merged = _deep_merge(current, config_patch)
        config_path.write_text(yaml.safe_dump(merged, sort_keys=False), encoding="utf-8")
        return self.find_by_id(agent_id)
