"""Raw data access for Index definitions (ADR-003's own api -> business
-> data_access layering) -- second_brain_data_path/data/Indexes/<id>/
Index.json -- AND the real deployment of an Index's own build script
into whichever Hermes profile owns its cron job. Zero business
interpretation here (no cron composition, no folder/tag/depth defaults)
-- that's IndexManager's own job.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from app.config import settings
from app.data_access import skills as skills_data

_INDEXES_SUBPATH = ("data", "Indexes")

# The real, checked-in source for the shared, standalone index-build
# engine, the vault_manager.py read_note() it reuses, and the per-Index
# runner template -- copied (never hand-duplicated) into a profile's own
# scripts/ dir on deploy, same "prepare here, apply where it's needed"
# convention vault_manager.py itself already established. Resolved
# relative to this file's own package layout, not settings -- this is
# bundled source, not user data.
#
# BACKEND-OWNED (operator, 2026-09-06). This used to resolve into
# Hermes-Provisioning/skills/vault-rebuild/vault-index/scripts/ -- an
# Index reaching into a Skill's own private scripts folder for its
# engine. That folder is normally held OUTSIDE the checkout, so
# deploy_index_builder() raised FileNotFoundError on every install
# without it. An Index is an artifact in its own right; it ships its
# own code.
_INDEX_PAYLOAD_DIR = Path(__file__).resolve().parents[1] / "business" / "core" / "index" / "scripts"
_RUNNER_TEMPLATE_NAME = "index_runner.py.template"


def _indexes_root() -> Path:
    return settings.second_brain_data_path.joinpath(*_INDEXES_SUBPATH)


def _index_file(index_id: str) -> Path:
    return _indexes_root() / index_id / "Index.json"


def list_index_ids() -> list[str]:
    root = _indexes_root()
    if not root.exists():
        return []
    return sorted(p.name for p in root.iterdir() if p.is_dir() and (p / "Index.json").is_file())


def read_index_json(index_id: str) -> dict:
    """Raises FileNotFoundError if the id doesn't exist, json.JSONDecodeError
    if the file doesn't parse -- never swallows either."""
    path = _index_file(index_id)
    if not path.is_file():
        raise FileNotFoundError(f"No Index.json for {index_id!r}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_index_json(index_id: str, data: dict) -> None:
    path = _index_file(index_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def delete_index_definition(index_id: str) -> None:
    """Removes this Index's own definition folder (just Index.json and
    its parent dir) -- NOT the built output at the Index's own
    storage_path, a separate real location IndexManager deletes via
    delete_output_path below."""
    index_dir = _indexes_root() / index_id
    if index_dir.is_dir():
        shutil.rmtree(index_dir, ignore_errors=True)


def delete_output_path(storage_path: str) -> None:
    """Removes the real built index output at an Index's own
    storage_path -- a file or a directory, whichever it turns out to be;
    tolerant of it already being gone."""
    if not storage_path:
        return
    path = Path(storage_path)
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
    elif path.is_file():
        path.unlink(missing_ok=True)


def scripts_dir(profile_id: str | None) -> Path:
    """Where a `--script` cron job's own referenced file must live --
    the real, live-confirmed `~/.hermes/scripts/` for the default
    profile (2026-08-28: `hermes cron create --script <name>` resolves
    against exactly this directory), `profiles/<id>/scripts/` for a
    named one -- mirrors HermesCron's own `_profile_dir` convention
    (app/hermes/cron.py), NOT independently verified live for a named
    profile specifically (disclosed gap, same as this session's own
    create_profile/delete_profile precedent)."""
    home = settings.hermes_home_path
    base = home if profile_id is None else home / "profiles" / profile_id
    return base / "scripts"


def deploy_index_builder(profile_id: str | None) -> None:
    """Copies the real, checked-in shared build engine (index_builder_lib.py)
    and the vault_manager.py it sibling-imports into this profile's own
    scripts/ dir -- always overwrites with the current checked-in source,
    so every real Index's own stub script stays on the same, current
    engine rather than an install-time snapshot. Raises FileNotFoundError
    if the payload is missing, rather than deploying a half-set.

    vault_manager.py comes from the ONE canonical copy under
    business/core/skills/managers/, not from a private copy beside the
    index engine (2026-09-06). That private copy was the 16th in the repo,
    across 5 versions -- the same drift that left this engine calling
    rglob for weeks after the MAX_PATH fix landed elsewhere."""
    target_dir = scripts_dir(profile_id)
    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(_INDEX_PAYLOAD_DIR / "index_builder_lib.py", target_dir / "index_builder_lib.py")
    shutil.copyfile(skills_data.managers_root() / "vault_manager.py", target_dir / "vault_manager.py")


def read_index_runner_template() -> str:
    """The raw per-Index runner text, placeholders unsubstituted --
    IndexManager bakes its own literals in (deciding WHAT the deployed
    script says is business logic; reading and writing the file is not).
    Deliberately a `.template`, not a `.py`: it is payload for a Hermes
    cron worker, and a real .py here would be import-collected by the
    backend's own test run."""
    return (_INDEX_PAYLOAD_DIR / _RUNNER_TEMPLATE_NAME).read_text(encoding="utf-8")


def _index_script_path(index_id: str, profile_id: str | None) -> Path:
    return scripts_dir(profile_id) / f"index_{index_id}.py"


def write_index_script(index_id: str, profile_id: str | None, content: str) -> None:
    path = _index_script_path(index_id, profile_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def delete_index_script(index_id: str, profile_id: str | None) -> None:
    _index_script_path(index_id, profile_id).unlink(missing_ok=True)
