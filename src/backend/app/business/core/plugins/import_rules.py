"""The `ADR-022` plugin import boundary, checked mechanically.

Three directions:

- **a plugin's backend** may import from the framework ONLY `app.plugin_api`,
  and never another plugin's package;
- **the framework** may never import a plugin package;
- **a plugin's screens** may import only their own files, the host contract in
  `src/pluginHost/`, and the libraries the host provides.

A plugin that reaches past the facade breaks on the next framework change even
when its `framework_api` matches -- the drift the version gate exists to stop.
So this runs wherever a plugin enters an install: publishing
(`scripts/check_plugin_imports.py`), installing from a repository
(`MarketplaceManager`), and the framework's own tests.

Deliberately **stdlib only, and importing nothing from `app`**: the publish
script loads it by file path without booting the application.
"""
from __future__ import annotations

import ast
import posixpath
import re
from pathlib import Path

FACADE_MODULE = "app.plugin_api"
PLUGIN_PACKAGE_PREFIX = "sb_plugins_"


def _python_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)


def _absolute_imports(tree: ast.AST):
    """Yields `(line, module, imported_names)` for every absolute import.
    Relative imports (`from . import x`) are skipped: they cannot leave the
    package they are written in."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield node.lineno, alias.name, []
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            yield node.lineno, node.module, [alias.name for alias in node.names]


def _parse(path: Path) -> tuple[ast.AST | None, str | None]:
    try:
        return ast.parse(path.read_text(encoding="utf-8")), None
    except SyntaxError as exc:
        return None, f"{path}:{exc.lineno}: cannot be parsed, so its imports cannot be checked"


def _is_facade(module: str, names: list[str]) -> bool:
    if module == FACADE_MODULE or module.startswith(FACADE_MODULE + "."):
        return True
    # `from app import plugin_api` names the facade without spelling its module.
    return module == "app" and bool(names) and all(name == "plugin_api" for name in names)


def check_plugin(plugin_dir: Path) -> list[str]:
    violations: list[str] = []
    for path in _python_files(Path(plugin_dir)):
        tree, parse_error = _parse(path)
        if parse_error:
            violations.append(parse_error)
            continue
        for line, module, names in _absolute_imports(tree):
            top_level = module.split(".")[0]
            if top_level == "app" and not _is_facade(module, names):
                violations.append(
                    f"{path}:{line}: imports framework internal `{module}` -- a plugin may import only `{FACADE_MODULE}`"
                )
            elif top_level.startswith(PLUGIN_PACKAGE_PREFIX):
                violations.append(
                    f"{path}:{line}: imports another plugin's package `{module}` -- plugins meet only through the Plugin API"
                )
    return violations


def check_core(app_dir: Path) -> list[str]:
    violations: list[str] = []
    for path in _python_files(Path(app_dir)):
        tree, parse_error = _parse(path)
        if parse_error:
            violations.append(parse_error)
            continue
        for line, module, _ in _absolute_imports(tree):
            if module.split(".")[0].startswith(PLUGIN_PACKAGE_PREFIX):
                violations.append(
                    f"{path}:{line}: framework code imports plugin package `{module}` -- core must never depend on a plugin"
                )
    return violations


# A plugin's screens are installed at `src/plugins/<plugin-id>/` in the frontend,
# so every relative import is judged as if the file already sat there. Beyond its
# own files a screen may reach only the host contract in `src/pluginHost/` and the
# libraries the host provides. Any other framework module -- or a library the
# framework merely happens to depend on -- is an internal that changes under it.
_ALLOWED_UI_PACKAGES = {"react", "react/jsx-runtime", "react-router"}
_UI_SOURCE_SUFFIXES = {".ts", ".tsx", ".js", ".jsx"}
_UI_IMPORT_PATTERNS = (
    # import x from '...' / import { a,\n b } from '...' / export { x } from '...'
    re.compile(r"""\b(?:import|export)\s[^'"`;]*?\bfrom\s*['"]([^'"]+)['"]"""),
    # import './side-effect.css'
    re.compile(r"""\bimport\s*['"]([^'"]+)['"]"""),
    # import('./lazy')
    re.compile(r"""\bimport\(\s*['"]([^'"]+)['"]\s*\)"""),
)


def _ui_import_specifiers(source: str):
    """Yields `(line, specifier)` once for every static, side-effect and dynamic import."""
    seen: set[tuple[int, str]] = set()
    for pattern in _UI_IMPORT_PATTERNS:
        for match in pattern.finditer(source):
            found = (source.count("\n", 0, match.start()) + 1, match.group(1))
            if found not in seen:
                seen.add(found)
                yield found


def check_plugin_ui(ui_dir: Path, plugin_id: str) -> list[str]:
    violations: list[str] = []
    ui_dir = Path(ui_dir)
    installed_root = f"plugins/{plugin_id}"
    sources = sorted(
        path for path in ui_dir.rglob("*")
        if path.suffix in _UI_SOURCE_SUFFIXES and "node_modules" not in path.parts
    )
    for path in sources:
        placed_dir = posixpath.dirname(f"{installed_root}/{path.relative_to(ui_dir).as_posix()}")
        for line, specifier in _ui_import_specifiers(path.read_text(encoding="utf-8")):
            if specifier.startswith("."):
                resolved = posixpath.normpath(posixpath.join(placed_dir, specifier))
                inside_plugin = resolved == installed_root or resolved.startswith(installed_root + "/")
                host_contract = resolved == "pluginHost" or resolved.startswith("pluginHost/")
                if not (inside_plugin or host_contract):
                    violations.append(
                        f"{path}:{line}: imports `{specifier}` -- outside the plugin and the host contract (src/pluginHost/)"
                    )
            elif specifier not in _ALLOWED_UI_PACKAGES:
                violations.append(
                    f"{path}:{line}: imports package `{specifier}` -- screens may use only "
                    f"{', '.join(sorted(_ALLOWED_UI_PACKAGES))} and src/pluginHost/"
                )
    return violations
