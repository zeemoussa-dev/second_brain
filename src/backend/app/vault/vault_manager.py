"""The vault engine — re-exported, not reimplemented.

**This file used to be a second, older copy of the engine, and it claimed to
be the canonical one.** Its own docstring said "editing the engine happens in
exactly ONE place (this file, then re-copy)" while it sat at 606 lines against
the 1,543 actually deployed to every Hermes profile. It was the v1 flat
Template reader, and it resolved Templates relative to the VAULT — a location
that has not held them since the 2026-09-03 config/vault split. So every
template-driven backend write failed:

    load_template(vault_path, "file")
        -> VaultManagerError: unknown template: 'file'

Fixing the path alone would not have fixed it: pointed at the right directory,
a v1 reader parses today's v2 Templates into zero sections and reports no
error — the same defect found in `TemplateManager` on 2026-09-06, in a second
engine.

There is now ONE engine, at
`app/business/core/skills/managers/vault_manager.py`. It is deliberately
standalone (stdlib only, no backend import) because a vault-writing Skill has
to keep working with the backend down, which is exactly why it cannot be an
ordinary package import — it is loaded here by path instead.

It resolves the App Database Folder from the environment via `data_root()`.
`app/config.py` exports `SECOND_BRAIN_DATA_PATH` on load so it behaves
identically in this process and inside a Hermes worker.

**Two signatures differ from the old fork.** Both are positional traps, so
call them by keyword:

    create(vault_path, template, title, note_name=..., ...)
        # the fork took (…, note_name, title, …) — reversed
    modify_section(vault_path, template, section, content, mode, note_id=..., ...)
        # the fork took (…, note_id, section, content, mode, …)
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_CANONICAL = (
    Path(__file__).resolve().parents[1]
    / "business" / "core" / "skills" / "managers" / "vault_manager.py"
)

_spec = importlib.util.spec_from_file_location("vault_manager", _CANONICAL)
_engine = importlib.util.module_from_spec(_spec)
# Registered under its own name so the engine's own sibling imports resolve
# the same way they do in a flat, deployed Skill folder.
sys.modules.setdefault("vault_manager", _engine)
_spec.loader.exec_module(_engine)

# Re-export the engine's public surface unchanged.
globals().update({name: value for name, value in vars(_engine).items() if not name.startswith("__")})

__all__ = [name for name in vars(_engine) if not name.startswith("_")]
