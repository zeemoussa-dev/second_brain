"""The supported way for a Skill's tests to find the framework (`BUG-069`).

A Skill that lives in an agent repository (`sb-pss-agent`, `sb-cbo-agent`) imports
what it imports when deployed: the shared engines (`vault_manager.py`), its own
repository's engines, and Master Templates. None of those sit beside it, so its
tests have to be told where they are. Each agent repository used to answer that
itself -- by counting parent folders, which is true only inside the framework's own
tree, or by borrowing the copies deployed to Hermes, which tests yesterday's
deployment instead of today's source and skips everything on a machine without one.

This module is the one answer. An agent repository's Skill `conftest.py` finds the
framework checkout -- `SECOND_BRAIN_FRAMEWORK`, else a `second_brain` checkout in a
folder above the Skill -- loads this file by path, and calls `configure(__file__)`.
See `Documentation/Framework/Building-a-Skill.md`, "Testing a Skill outside the
framework".

Standard library only, and it imports nothing from `app`: it must load in an agent
repository's test run without the framework's dependencies.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

FRAMEWORK_ROOT = Path(__file__).resolve().parents[2]
_SHARED_MANAGERS = Path("src/backend/app/business/core/skills/managers")
_SKILL_CATALOG = Path("src/backend/app/business/core/skills/catalog")
_MASTER_TEMPLATES = Path("src/backend/app/business/core/templates/masters")
_MARKETPLACE = Path("src/marketplace")
_VERSION = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


class SkillTestPaths:
    """Where one Skill's tests find what a deployed Skill would import."""

    def __init__(self, scripts_dir: Path, repository: Path | None, framework: Path):
        self.scripts_dir = scripts_dir
        self.repository = repository
        self.framework = framework

    @property
    def engine_roots(self) -> list[Path]:
        """Folders holding shared engines, the repository's own first: an agent
        repository may ship engines the framework does not (`company_index.py`)."""
        roots = []
        if self.repository is not None:
            roots.append(self.repository / "data" / "managers")
        roots.append(self.framework / _SHARED_MANAGERS)
        return [root for root in roots if root.is_dir()]

    def shared_engine(self, name: str) -> Path:
        for root in self.engine_roots:
            if (root / name).is_file():
                return root / name
        raise FileNotFoundError(
            f"no shared engine {name!r} in {', '.join(str(root) for root in self.engine_roots)}")

    def framework_skill(self, skill_id: str) -> Path | None:
        """A Skill the framework ships, from its catalog source -- what a deployment
        would copy. An agent Skill that calls one (a pass running
        `summarize-and-tag-files`) otherwise finds it only on a machine where it is
        deployed. Its `scripts/` folder when it has one, as in a repository."""
        for skill in sorted((self.framework / _SKILL_CATALOG).glob(f"*/{skill_id}")):
            if skill.is_dir():
                return skill / "scripts" if (skill / "scripts").is_dir() else skill
        return None

    def template_roots(self) -> list[Path]:
        """Where a Master Template may live, in the order a Template is looked up:
        the repository's own `data/Templates/` (an install may ship its own copy),
        the framework's masters, then each Marketplace plugin's newest package --
        business Templates such as `customer` moved there with the Entities plugin."""
        roots = []
        if self.repository is not None:
            roots.append(self.repository / "data" / "Templates")
        roots.append(self.framework / _MASTER_TEMPLATES)
        marketplace = self.framework / _MARKETPLACE
        if marketplace.is_dir():
            for plugin in sorted(path for path in marketplace.iterdir() if path.is_dir()):
                versions = [path for path in plugin.iterdir() if path.is_dir() and _VERSION.match(path.name)]
                if versions:
                    newest = max(versions, key=lambda path: tuple(int(part) for part in path.name.split(".")))
                    roots.append(newest / "templates")
        return [root for root in roots if root.is_dir()]

    def master_template(self, template_id: str) -> Path:
        for root in self.template_roots():
            candidate = root / template_id / "Template.json"
            if candidate.is_file():
                return candidate
        raise FileNotFoundError(
            f"no Master Template {template_id!r} in {', '.join(str(root) for root in self.template_roots())}")


def _repository_of(scripts_dir: Path) -> Path | None:
    """The agent repository holding this Skill: the nearest folder above it with a
    `.git`. Found by looking, not by counting folders, so a Skill can move."""
    for folder in (scripts_dir, *scripts_dir.parents):
        if (folder / ".git").exists():
            return folder
    return None


def configure(conftest_file: str | Path, *, framework: Path | None = None) -> SkillTestPaths:
    """Puts a Skill's own scripts, its repository's engines and the framework's
    shared engines on `sys.path`, in that order, and returns where everything is.

    The Skill's own folder comes first so its `conftest` and modules are never
    shadowed by a same-named file among the engines."""
    scripts_dir = Path(conftest_file).resolve().parent
    paths = SkillTestPaths(scripts_dir, _repository_of(scripts_dir), framework or FRAMEWORK_ROOT)
    for folder in reversed([scripts_dir, *paths.engine_roots]):
        text = str(folder)
        if text in sys.path:
            sys.path.remove(text)
        sys.path.insert(0, text)
    return paths
