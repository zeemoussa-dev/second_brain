"""Which seed/blank-data files an artifact export carries, and an import
creates (Entities plan Phase 2).

A seed file is a data-path-relative file a Skill needs to exist before its
first run. Export records it empty; import creates it empty when a deployed
Skill references it and the file does not exist yet -- never over an existing
file, which holds the operator's data (`BUG-067`). A Skill "references" a
seed file when its content mentions the file's name.

Plugins register their seed files (`api.register_seed_data_file`), so export
and import compile in no business store: an older archive's
`Settings/Entities.md` is created only when the Entities plugin is installed.
"""
from __future__ import annotations

from pathlib import PurePosixPath

from app.business.core.plugins.plugin_manager import PluginManager


def seed_data_files() -> dict[str, str]:
    """{data-path-relative file: the name a Skill's content must mention for it to be needed}."""
    paths = dict.fromkeys(PluginManager().get_seed_data_files())
    return {path: PurePosixPath(path).name for path in paths}
