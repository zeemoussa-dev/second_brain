"""publish_plugin.py -- validates a plugin repository and publishes one version of
it into the framework's Marketplace (`ADR-022`, `REQ-SB-91` Phase 4b).

    python publish_plugin.py <plugin-repo> [--dry-run]

One script for every plugin repository, so the rules a package must meet cannot
drift between repositories. Every check runs before anything is written, and a
plugin that fails any of them is not published:

  1. plugin.json   a valid id, an x.y.z version, and the framework API this
                   framework provides
  2. layout        backend/__init__.py and/or ui/index.tsx
  3. boundary      the backend imports only `app.plugin_api`; the screens import
                   only their own files, src/pluginHost/ and the host's libraries
  4. tests         the plugin's own tests pass, when it has a tests/ folder
  5. screens       the screens type-check and build inside this framework
  6. version       new: a published version is never overwritten

Exit code 1, listing every problem found, when publishing is refused.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
_BACKEND_ROOT = _SCRIPTS_DIR.parent
_SRC_ROOT = _BACKEND_ROOT.parent
_FRONTEND_ROOT = _SRC_ROOT / "frontend"
_PLUGIN_API_FILE = _BACKEND_ROOT / "app" / "plugin_api.py"
MARKETPLACE_ROOT = _SRC_ROOT / "marketplace"

sys.path.insert(0, str(_SCRIPTS_DIR))
import check_plugin_imports  # noqa: E402

# The plugin host's own id rule -- a package the host would refuse must never publish.
_VALID_PLUGIN_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
_VERSION = re.compile(r"^\d+\.\d+\.\d+$")
# A plugin's tests are for publishing, not for installing.
_NEVER_PACKAGED = shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache", "node_modules", "tests")
_PYTEST_NO_TESTS_COLLECTED = 5


class PublishRefused(Exception):
    def __init__(self, problems: list[str]) -> None:
        self.problems = list(problems)
        super().__init__("\n".join(self.problems))


def host_framework_api() -> int:
    """Read out of plugin_api.py rather than imported: importing the app loads
    settings and the vault stack, which publishing has no business touching."""
    tree = ast.parse(_PLUGIN_API_FILE.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "FRAMEWORK_API" for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise PublishRefused(["FRAMEWORK_API is not defined in app/plugin_api.py"])


def read_manifest(repo: Path) -> dict:
    path = repo / "plugin.json"
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise PublishRefused([f"{path} does not exist"]) from None
    except ValueError as exc:
        raise PublishRefused([f"{path} is not valid JSON: {exc}"]) from None
    if not isinstance(manifest, dict):
        raise PublishRefused([f"{path} must hold a JSON object"])
    return manifest


def manifest_problems(manifest: dict, host_api: int) -> list[str]:
    problems = []
    if not _VALID_PLUGIN_ID.match(str(manifest.get("id") or "")):
        problems.append(f"id {manifest.get('id')!r} is not a valid plugin id (lowercase letters, digits, hyphens)")
    if not _VERSION.match(str(manifest.get("version") or "")):
        problems.append(f"version {manifest.get('version')!r} is not x.y.z")
    if manifest.get("framework_api") != host_api:
        problems.append(
            f"built for framework API {manifest.get('framework_api')!r}; this framework provides API {host_api}"
        )
    return problems


def layout_problems(repo: Path) -> list[str]:
    has_backend = (repo / "backend").is_dir()
    has_ui = (repo / "ui").is_dir()
    problems = []
    if not has_backend and not has_ui:
        problems.append("the plugin has neither backend/ nor ui/")
    if has_backend and not (repo / "backend" / "__init__.py").is_file():
        problems.append("backend/ has no __init__.py defining register(api)")
    if has_ui and not (repo / "ui" / "index.tsx").is_file():
        problems.append("ui/ has no index.tsx default-exporting the plugin's screens")
    return problems


def boundary_problems(repo: Path, plugin_id: str) -> list[str]:
    problems = []
    if (repo / "backend").is_dir():
        problems.extend(check_plugin_imports.check_plugin(repo / "backend"))
    if (repo / "ui").is_dir():
        problems.extend(check_plugin_imports.check_plugin_ui(repo / "ui", plugin_id))
    return problems


def run_plugin_tests(repo: Path) -> str | None:
    tests = repo / "tests"
    if not tests.is_dir():
        return None
    environment = dict(os.environ)
    # So a plugin's tests can import `app.plugin_api` exactly as the host provides it.
    environment["PYTHONPATH"] = os.pathsep.join(
        part for part in (str(_BACKEND_ROOT), environment.get("PYTHONPATH", "")) if part
    )
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "tests", "-q", "-p", "no:cacheprovider"],
        cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace", env=environment,
    )
    if completed.returncode in (0, _PYTEST_NO_TESTS_COLLECTED):
        return None
    tail = "\n".join((completed.stdout + completed.stderr).strip().splitlines()[-25:])
    return f"the plugin's own tests fail:\n{tail}"


def build_screens_in_framework(repo: Path, plugin_id: str) -> str | None:
    """Copies the screens beside the installed plugins under a folder name the
    host never mounts (it is not a valid plugin id), builds the whole frontend,
    and always removes the copy. The copy sits at an installed plugin's depth,
    so `../../pluginHost/...` resolves exactly as it will once installed.

    The build output left in `dist/` includes the copy until the next build;
    the dev server never serves `dist/`."""
    if not (repo / "ui").is_dir():
        return None
    npm = shutil.which("npm") or shutil.which("npm.cmd")
    if npm is None:
        return "npm was not found on PATH, so the screens could not be built"
    check_dir = _FRONTEND_ROOT / "src" / "plugins" / f"__publish-check-{plugin_id}"
    shutil.rmtree(check_dir, ignore_errors=True)
    shutil.copytree(repo / "ui", check_dir, ignore=shutil.ignore_patterns("node_modules"))
    try:
        completed = subprocess.run(
            [npm, "run", "build"], cwd=_FRONTEND_ROOT,
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
    finally:
        shutil.rmtree(check_dir, ignore_errors=True)
    if completed.returncode == 0:
        return None
    tail = "\n".join((completed.stdout + completed.stderr).strip().splitlines()[-25:])
    return f"the screens do not build inside this framework:\n{tail}"


def publish(
    repo: Path,
    *,
    dry_run: bool = False,
    marketplace_root: Path = MARKETPLACE_ROOT,
    test_runner: Callable[[Path], str | None] = run_plugin_tests,
    screen_builder: Callable[[Path, str], str | None] = build_screens_in_framework,
) -> dict:
    """Raises PublishRefused carrying every problem found. The cheap checks all
    run first and report together; the slow ones (tests, then the build) run
    only when those pass, and each stops publishing on its own."""
    repo = repo.resolve()
    manifest = read_manifest(repo)
    problems = manifest_problems(manifest, host_framework_api())
    if problems:
        raise PublishRefused(problems)

    plugin_id, version = manifest["id"], manifest["version"]
    target = marketplace_root / plugin_id / version
    problems = layout_problems(repo)
    if target.exists():
        problems.append(f"{plugin_id} {version} is already published -- a published version is never overwritten; bump the version")
    problems.extend(boundary_problems(repo, plugin_id))
    if problems:
        raise PublishRefused(problems)

    for slow_check in (lambda: test_runner(repo), lambda: screen_builder(repo, plugin_id)):
        problem = slow_check()
        if problem:
            raise PublishRefused([problem])

    if dry_run:
        return {"published": False, "dry_run": True, "plugin_id": plugin_id, "version": version}

    target.mkdir(parents=True)
    shutil.copy2(repo / "plugin.json", target / "plugin.json")
    for part in ("backend", "ui"):
        if (repo / part).is_dir():
            shutil.copytree(repo / part, target / part, ignore=_NEVER_PACKAGED)
    return {"published": True, "plugin_id": plugin_id, "version": version, "path": str(target)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a plugin repository and publish it to the Marketplace.")
    parser.add_argument("repo", type=Path, help="the plugin repository")
    parser.add_argument("--dry-run", action="store_true", help="run every check, publish nothing")
    args = parser.parse_args()
    try:
        result = publish(args.repo, dry_run=args.dry_run)
    except PublishRefused as refused:
        print("REFUSED -- nothing was published:")
        for problem in refused.problems:
            print(f"  - {problem}")
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
