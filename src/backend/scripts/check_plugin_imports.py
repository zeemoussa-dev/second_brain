"""check_plugin_imports.py -- the `ADR-022` boundary, checked mechanically.

Two directions:

    --plugin <plugin_dir>   a plugin may import from the framework ONLY
                            `app.plugin_api`, and never another plugin's package
    --core <app_dir>        the framework may never import a plugin package

A plugin that reaches past the facade breaks on the next framework change even
when its `framework_api` matches -- the drift the version gate exists to stop --
so this runs at publish time and in the framework's own tests. Relative imports
inside a plugin are always allowed; they stay within the plugin.

Exit code 1 on any violation, printing `file:line` and the offending import.
"""
from __future__ import annotations

import argparse
import ast
import sys
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
    for path in _python_files(plugin_dir):
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
    for path in _python_files(app_dir):
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Check the ADR-022 plugin import boundary.")
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--plugin", type=Path, help="a plugin's directory")
    target.add_argument("--core", type=Path, help="the framework's app/ directory")
    args = parser.parse_args()

    violations = check_plugin(args.plugin) if args.plugin else check_core(args.core)
    for violation in violations:
        print(violation)
    print(f"{len(violations)} violation(s)")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
