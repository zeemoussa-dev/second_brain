"""check_plugin_imports.py -- the `ADR-022` boundary, checked mechanically.

    --plugin <plugin_dir>   a plugin may import from the framework ONLY
                            `app.plugin_api`, and never another plugin's package
    --core <app_dir>        the framework may never import a plugin package
    --ui <ui_dir> --id <id> a plugin's screens may import only their own files,
                            the host contract in src/pluginHost/, and the
                            libraries the host provides

The rules themselves live in `app/business/core/plugins/import_rules.py`, so
publishing, installing from a repository and the framework's own tests all check
the same thing. They are loaded by file path rather than imported as a package:
this script must run without booting the application.

Exit code 1 on any violation, printing `file:line` and the offending import.
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

_RULES_FILE = Path(__file__).resolve().parents[1] / "app" / "business" / "core" / "plugins" / "import_rules.py"
_spec = importlib.util.spec_from_file_location("plugin_import_rules", _RULES_FILE)
import_rules = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(import_rules)

check_plugin = import_rules.check_plugin
check_core = import_rules.check_core
check_plugin_ui = import_rules.check_plugin_ui
FACADE_MODULE = import_rules.FACADE_MODULE
PLUGIN_PACKAGE_PREFIX = import_rules.PLUGIN_PACKAGE_PREFIX


def main() -> int:
    parser = argparse.ArgumentParser(description="Check the ADR-022 plugin import boundary.")
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--plugin", type=Path, help="a plugin's directory")
    target.add_argument("--core", type=Path, help="the framework's app/ directory")
    target.add_argument("--ui", type=Path, help="a plugin's ui/ directory (needs --id)")
    parser.add_argument("--id", help="the plugin id, for --ui")
    args = parser.parse_args()

    if args.ui and not args.id:
        parser.error("--ui needs --id, because imports are judged from src/plugins/<id>/")
    if args.plugin:
        violations = check_plugin(args.plugin)
    elif args.ui:
        violations = check_plugin_ui(args.ui, args.id)
    else:
        violations = check_core(args.core)
    for violation in violations:
        print(violation)
    print(f"{len(violations)} violation(s)")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
