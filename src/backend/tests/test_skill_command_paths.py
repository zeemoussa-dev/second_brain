"""BUG-085 -- a Skill telling an agent to run a script that is not where it says.

Email capture's `SKILL.md` said `${HERMES_SKILL_DIR}\\scripts\\run_delta_capture.py`
while the deploy flattens a Skill's `scripts/` folder into the Skill's own
directory, so after a redeploy the documented command named a path that does not
exist. Nothing failed loudly: the job is agent-mediated, and a session that cannot
run its script still reported `ok`.

This pins every command a catalog Skill tells an agent to run against what the
deploy actually writes, so the two cannot drift apart again.
"""
import re

import pytest

from app.business.core.skills import skill_manager as skill_manager_module
from app.data_access import skills as skills_data

# `terminal(command="python \"${HERMES_SKILL_DIR}\some_script.py\" ...")`
SKILL_DIR_REFERENCE = re.compile(r"\$\{HERMES_SKILL_DIR\}\\\\?([^\"'\s]+?\.py)")

CATALOG = skill_manager_module.SkillManager()


def documented_scripts():
    """(skill id, script path as SKILL.md tells the agent to run it)."""
    for skill in CATALOG.get_all():
        skill_md = skills_data.read_skill_md(skill.id) or ""
        for match in SKILL_DIR_REFERENCE.finditer(skill_md):
            yield skill.id, match.group(1).replace("\\", "/")


def test_the_catalog_actually_documents_some_commands():
    """A regex that silently matches nothing would make the real check below
    pass forever."""
    assert len(list(documented_scripts())) >= 5


@pytest.mark.parametrize("skill_id, script_path", sorted(set(documented_scripts())))
def test_a_documented_command_names_a_script_the_deploy_writes(skill_id, script_path):
    deployed = {path.replace("\\", "/") for path in skills_data.list_scripts(skill_id)}

    assert script_path in deployed, (
        f"{skill_id}'s SKILL.md tells the agent to run {script_path!r}, which the deploy does not "
        f"write. It writes: {sorted(deployed)}"
    )


def test_the_deploy_writes_scripts_flat_which_is_what_the_commands_assume():
    """`list_scripts` keys are relative to the Skill's `scripts/` folder, and the
    deploy writes them at those keys -- so a deployed Skill has its scripts beside
    its SKILL.md, not under a `scripts/` folder. The commands must say the same."""
    scripts = skills_data.list_scripts("email-thread-capture")

    assert "run_delta_capture.py" in scripts
    assert not any(path.startswith("scripts") for path in scripts)
