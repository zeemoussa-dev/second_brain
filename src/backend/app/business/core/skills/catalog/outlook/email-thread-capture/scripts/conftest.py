"""Import paths for this Skill's own tests.

A deployed Skill is flat: Hermes copies SKILL.md + scripts/ into a profile
and everything sibling-imports. In the repo the shared managers are NOT
carried per skill -- one canonical copy lives in ../managers/ and is
materialised at deploy time -- so the tests have to be told where it is.

That is an improvement on what it replaces: these tests now run against
the single canonical vault_manager.py rather than against whichever local
copy this skill happened to be carrying.
"""
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
_MANAGERS = _SCRIPTS.parents[3] / "managers"

for path in (_SCRIPTS, _MANAGERS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
