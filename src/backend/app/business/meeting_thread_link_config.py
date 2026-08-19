"""`Link-to-Thread` Job fallback-strategy threshold config
(REQ-SB-56-US-01-T02) — the attendee-overlap floor, the 1:1 carve-out
toggle, and the date-proximity window, backed by a new sibling
`.second-brain/meeting_thread_link_config.json` store. Composed alongside
`app/business/meeting_classification.py`, never inside it — mirrors
`agent_prompts.py`/`working_mode_registry.py`'s own "compose alongside,
don't bake into the consuming module" precedent, applying ADR-011 point 2's
"agent identity/type/actions stay hardcoded" reasoning a further time over
to keep threshold VALUES out of the linking-logic module too. Explicit
operator instruction, 2026-08-17: these three numbers must be real,
accessible config values, never Python constants inside
meeting_classification.py.

Self-healing to the operator-confirmed defaults on first read, mirroring
working_mode_registry._load_state()'s own seeded-default shape — this is a
single flat record, not a per-id store, so seeding folds directly into
_load_state() rather than a separate per-key default lookup.

No HTTP endpoint or Settings UI surface wires these set_* functions yet —
deliberate, out of this task's own scope (see T02's own `## Out of Scope`);
they exist as real, programmatically-settable config today so a future
story can wire them in without another code change here.
"""
from app.data_access import vault_writer

_DEFAULT_CONFIG = {
    "attendee_overlap_floor": 2,
    "one_on_one_carve_out_enabled": True,
    "date_proximity_days": 7,
}


def _load_state() -> dict:
    """Never returns a record missing any of the three keys — an
    already-saved config file created before a future key was added would
    otherwise silently miss it; each missing key is seeded to its own
    operator-confirmed default and persisted back, mirroring
    working_mode_registry._load_state()'s own per-agent self-healing loop
    applied here to per-key self-healing instead."""
    config = vault_writer.load_meeting_thread_link_config()
    if config is None:
        config = dict(_DEFAULT_CONFIG)
        vault_writer.save_meeting_thread_link_config(config)
        return config
    changed = False
    for key, default_value in _DEFAULT_CONFIG.items():
        if key not in config:
            config[key] = default_value
            changed = True
    if changed:
        vault_writer.save_meeting_thread_link_config(config)
    return config


def get_attendee_overlap_floor() -> int:
    return _load_state()["attendee_overlap_floor"]


def set_attendee_overlap_floor(value: int) -> None:
    config = _load_state()
    config["attendee_overlap_floor"] = value
    vault_writer.save_meeting_thread_link_config(config)


def get_one_on_one_carve_out_enabled() -> bool:
    return _load_state()["one_on_one_carve_out_enabled"]


def set_one_on_one_carve_out_enabled(value: bool) -> None:
    config = _load_state()
    config["one_on_one_carve_out_enabled"] = value
    vault_writer.save_meeting_thread_link_config(config)


def get_date_proximity_days() -> int:
    return _load_state()["date_proximity_days"]


def set_date_proximity_days(value: int) -> None:
    config = _load_state()
    config["date_proximity_days"] = value
    vault_writer.save_meeting_thread_link_config(config)
