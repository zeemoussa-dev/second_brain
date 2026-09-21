"""Building a plugin's screens inside this framework -- the gate that proves the
screens compile against the host they will run in (`ADR-022`).

The screens are copied beside the installed plugins under a folder name the host
never mounts (it is not a valid plugin id), the whole frontend is built, and the
copy is always removed. The copy sits at an installed plugin's depth, so
`../../pluginHost/...` resolves exactly as it will once installed.

Deliberately **stdlib only, and importing nothing from `app`**: the publish
script loads it by file path without booting the application, and the
Marketplace calls it while installing from a repository.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def build_screens(frontend_root: Path, plugin_id: str, ui_dir: Path, *, purpose: str = "publish") -> str | None:
    """None when the screens build, otherwise why they do not.

    The build output left in `dist/` includes the copy until the next build; the
    dev server never serves `dist/`."""
    frontend_root, ui_dir = Path(frontend_root), Path(ui_dir)
    if not ui_dir.is_dir():
        return None
    npm = shutil.which("npm") or shutil.which("npm.cmd")
    if npm is None:
        return "npm was not found on PATH, so the screens could not be built"
    check_dir = frontend_root / "src" / "plugins" / f"__{purpose}-check-{plugin_id}"
    shutil.rmtree(check_dir, ignore_errors=True)
    shutil.copytree(ui_dir, check_dir, ignore=shutil.ignore_patterns("node_modules"))
    try:
        completed = subprocess.run(
            [npm, "run", "build"], cwd=frontend_root,
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
    finally:
        shutil.rmtree(check_dir, ignore_errors=True)
    if completed.returncode == 0:
        return None
    tail = "\n".join((completed.stdout + completed.stderr).strip().splitlines()[-25:])
    return f"the screens do not build inside this framework:\n{tail}"
