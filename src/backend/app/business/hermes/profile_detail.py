"""One composed, strictly read-only answer to "what is this Hermes profile
actually made of" -- the soul as written, every skill with its verdict, both
config layers, the cron jobs bound to it and the toolsets it has enabled
(`REQ-SB-99-US-01`, `ADR-043`).

Composes and never re-derives. Every region here already has exactly one
reader elsewhere, and this module calls it:

    soul      -> HermesProfiles.read_soul_document()
    config    -> HermesProfiles.read_config_layers()
    skills    -> SkillManager.compare_profile_skills()
    cron jobs -> business/hermes/cron_status.list_cron_jobs()
    toolsets  -> HermesCLI.read_tools()

A second answer to a question the codebase already answers is the failure
this story exists to avoid (`ESC-066`): nothing below parses a SKILL.md,
splits the soul into marker blocks, re-runs `_soul_excerpt`, merges the two
config layers or calls `cli.list_tools` (which cannot tell a failed read from
an empty one). `deployed_to` is not consulted on this path at all, so the view
cannot inherit the untrustworthiness `REQ-SB-96` exists to fix.

**Honest absence is the whole point.** Three failures are three different
answers (`ADR-043`): the install cannot be read at all (every region is
explicitly unread, none fabricated), one file is missing or unreadable (that
region only, naming the file, every other region still real), and the toolsets
subprocess failed (`read: false` with the real reason, never an empty mapping
presented as "nothing enabled"). Every region carries its own `read` flag and
its own `error`, and an unread region's payload is `None` -- never `[]`, `{}`
or `""`, which are the answers a successfully-read empty region gives.

**Cost is pinned deliberately** (`BUG-086` is the measured precedent -- 4.4 of
the Agents Map's 6 seconds spent parsing every SKILL.md of every profile).
One request costs exactly one `hermes tools list` subprocess, one skills
comparison, one profile listing, and the handful of file reads the readers
above each pin by equality in their own tests. Nothing here is reachable from
`GET /agents`, `GET /hermes/agents` or the Agents Map's mount-time fetches.

Layering (`ADR-003`): this is the `agents_map_adapter.py` shape -- a composing
module inside `business/hermes` that reaches Managers and `get_client()`, and
never `data_access` or `app.hermes` directly. The three-way file statuses and
the two config layer names are passed through exactly as their reader produced
them rather than restated here, so this file holds no copy of them to drift.
"""
from __future__ import annotations

from app.business.core.skills.skill_manager import SkillManager
from app.business.hermes import cron_status
from app.business.hermes.client import get_client

# A region that was never attempted, because the install itself could not be
# read. Distinct from every per-file status a reader can return: those mean a
# read happened and failed, this means no read was tried (`ADR-043`'s first
# failure vs its second).
REGION_WAS_NOT_READ = "not_read"

# How a config key relates to the two layers. The two "set here"/"inherited
# from the install root" answers are the layers' own `scope` names, passed
# through from the reader; only the three answers below are this view's own.
KEY_IS_NOT_SET = "not_set"
KEY_SOURCE_IS_UNKNOWN = "unknown"
KEY_IS_SET_IN_MORE_THAN_ONE_LAYER = "set_in_more_than_one_layer"

# Reported even when no layer sets them, so "not set" is visible as an answer
# rather than as a missing row. These three are what `_read_agent()` surfaces
# as an agent's model/provider/reasoning effort, which is what an operator
# comes to this view to check against the Agents Map.
KEYS_ALWAYS_REPORTED = ("agent.reasoning_effort", "model.default", "model.provider")


def _flatten_config_values(values: dict, prefix: str = "") -> dict:
    """`{"model": {"default": "x"}}` -> `{"model.default": "x"}`.

    An empty mapping is a leaf: `model: {}` is a key the file really sets, and
    dropping it would under-report what is written in the file.
    """
    flattened: dict = {}
    for key, value in values.items():
        dotted_key = f"{prefix}{key}"
        if isinstance(value, dict) and value:
            flattened.update(_flatten_config_values(value, f"{dotted_key}."))
        else:
            flattened[dotted_key] = value
    return flattened


def _config_key_rows(layers: list) -> list[dict]:
    """One row per key, naming the file each value came from.

    No merged or effective value is produced: when two layers both set a key
    this reports both occurrences and refuses to pick, because Hermes' own
    precedence between the files is not readable from this repository and
    guessing which one won is a fabrication (`ADR-043`).

    A key absent from every readable layer is `not_set` -- unless some layer
    could not be read at all, in which case it is `unknown`, because a file we
    failed to read may well set it.
    """
    flattened_by_layer = [(layer, _flatten_config_values(layer.values or {})) for layer in layers]
    some_layer_could_not_be_read = any(layer.values is None for layer in layers)

    every_key = set(KEYS_ALWAYS_REPORTED)
    for _layer, flattened in flattened_by_layer:
        every_key.update(flattened)

    rows = []
    for key in sorted(every_key):
        occurrences = [
            {"source": layer.scope, "path": layer.path, "value": flattened[key]}
            for layer, flattened in flattened_by_layer
            if key in flattened
        ]
        if len(occurrences) == 1:
            only = occurrences[0]
            source, value, path = only["source"], only["value"], only["path"]
        elif occurrences:
            source, value, path = KEY_IS_SET_IN_MORE_THAN_ONE_LAYER, None, None
        elif some_layer_could_not_be_read:
            source, value, path = KEY_SOURCE_IS_UNKNOWN, None, None
        else:
            source, value, path = KEY_IS_NOT_SET, None, None
        rows.append({
            "key": key, "value": value, "source": source, "path": path,
            "occurrences": occurrences,
        })
    return rows


def _region_that_failed(error: str, **unread_payload) -> dict:
    return {"read": False, "error": error, **unread_payload}


def _guarded(produce, unread_payload: dict) -> dict:
    """Runs one region's production, turning any failure into that region's
    own honest "unread" answer.

    Broad on purpose: a locked constraint of this view is that one region's
    failure never aborts another's, and an unforeseen exception from a reader
    must cost the operator that one region rather than the whole page -- which
    is the only thing a debugging view is for (`ADR-043`, `US-01` Scenario 6).
    """
    try:
        return produce()
    except Exception as failure:  # noqa: BLE001 -- see the docstring above
        return _region_that_failed(f"{type(failure).__name__}: {failure}", **unread_payload)


_SOUL_WHEN_UNREAD = {"path": None, "status": REGION_WAS_NOT_READ, "text": None}
_SKILLS_WHEN_UNREAD = {"items": None}
_CONFIG_WHEN_UNREAD = {"layers": None, "keys": None}
_CRON_WHEN_UNREAD = {"items": None, "install_level": None, "install_level_is_this_profile": None}
_TOOLSETS_WHEN_UNREAD = {"items": None}


def _soul_region(client, profile_id: str) -> dict:
    document = client.profiles.read_soul_document(profile_id)
    return {
        # `text is None` is exactly the reader's own failure condition: it
        # returns text only for a successful read, so this never restates the
        # status values it already produced.
        "read": document.text is not None,
        "path": document.path,
        "status": document.status,
        "text": document.text,
        "error": document.error,
    }


def _skills_region(profile_id: str) -> dict:
    return {"read": True, "items": SkillManager().compare_profile_skills(profile_id), "error": ""}


def _config_region(client, profile_id: str) -> dict:
    layers = client.profiles.read_config_layers(profile_id)
    return {
        "read": True,
        "layers": [
            {
                "source": layer.scope, "path": layer.path, "status": layer.status,
                "values": layer.values, "error": layer.error,
            }
            for layer in layers
        ],
        "keys": _config_key_rows(layers),
        "error": "",
    }


def _cron_region(profile_id: str, *, profile_is_the_install_root: bool) -> dict:
    """The profile's own jobs, and the install-level ones kept separate.

    Merging them would attribute a job to a profile that does not own it: a
    job's binding is the directory its `jobs.json` lives in, not a field
    (`ADR-043`). The install-level list exists so a job that runs with no `-p`
    is visible somewhere rather than nowhere.
    """
    own_jobs = cron_status.list_cron_jobs(profile_id)
    return {
        "read": True,
        "items": own_jobs,
        # The primary profile IS <HERMES_HOME>, so its own cron directory and
        # the install's are the same directory -- listing it again would show
        # the same jobs twice as if they were two different things.
        "install_level": [] if profile_is_the_install_root else cron_status.list_cron_jobs(),
        "install_level_is_this_profile": profile_is_the_install_root,
        "error": "",
    }


def _toolsets_region(client, profile_id: str) -> dict:
    """`read_tools`, never `list_tools`: the latter returns `{}` both for "a
    profile with nothing enabled" and for "the subprocess failed", and a screen
    that renders the second as the first tells the operator something it does
    not know (`ADR-043`'s third failure)."""
    succeeded, toolsets, message = client.cli.read_tools(profile_id)
    return {
        "read": succeeded,
        "items": toolsets if succeeded else None,
        "error": "" if succeeded else message,
    }


def _install_cannot_be_read(profile_id: str, home_path) -> dict:
    """Every region explicitly unread, because none was attempted. No empty
    list, mapping or string anywhere: an unreadable install must not render as
    a profile that happens to hold nothing (`US-01` Scenario 7)."""
    error = f"The Hermes install at {home_path} is not a readable directory"
    return {
        "profile_id": profile_id,
        "install": {"readable": False, "path": str(home_path), "error": error},
        "soul": _region_that_failed(error, **_SOUL_WHEN_UNREAD),
        "skills": _region_that_failed(error, **_SKILLS_WHEN_UNREAD),
        "config": _region_that_failed(error, **_CONFIG_WHEN_UNREAD),
        "cron_jobs": _region_that_failed(error, **_CRON_WHEN_UNREAD),
        "toolsets": _region_that_failed(error, **_TOOLSETS_WHEN_UNREAD),
    }


def read_profile_detail(profile_id: str) -> dict | None:
    """Everything one Hermes profile really is, in one read-only response.

    `None` means the profile directory genuinely does not exist on an install
    that IS readable -- the caller's 404. An install that cannot be read is
    never a 404: it comes back as a full envelope whose `install.readable` is
    false and whose every region says it was not read.

    Nothing here writes, caches, persists or reconciles anything (`ADR-003`).
    """
    client = get_client()
    if not client.profiles.install_is_readable():
        return _install_cannot_be_read(profile_id, client.config.home_path)

    # Cheapest honest existence check: two small YAML reads per profile and
    # NOT a single SKILL.md (`include_skills=False`, `BUG-086`). `find_by_id`
    # would read this profile's skills a second time, on top of the one
    # listing the comparison below already pays for.
    profile = next(
        (agent for agent in client.profiles.get_all(include_skills=False) if agent.id == profile_id),
        None,
    )
    if profile is None:
        return None

    return {
        "profile_id": profile_id,
        "install": {"readable": True, "path": str(client.config.home_path), "error": ""},
        "soul": _guarded(lambda: _soul_region(client, profile_id), _SOUL_WHEN_UNREAD),
        "skills": _guarded(lambda: _skills_region(profile_id), _SKILLS_WHEN_UNREAD),
        "config": _guarded(lambda: _config_region(client, profile_id), _CONFIG_WHEN_UNREAD),
        "cron_jobs": _guarded(
            lambda: _cron_region(profile_id, profile_is_the_install_root=profile.is_primary),
            _CRON_WHEN_UNREAD,
        ),
        "toolsets": _guarded(lambda: _toolsets_region(client, profile_id), _TOOLSETS_WHEN_UNREAD),
    }
