"""The Tagging pass's wiring: every step's script is found, in the right order.

A step whose script cannot be found fails every night on the machine that runs
it -- the nightly pass's discovery step did exactly that when it named a path
that existed only in a repo checkout.
"""
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

_SCRIPTS = Path(__file__).resolve().parent.parent
# tests -> scripts -> create-companies-partners -> vault -> catalog -> skills
_MANAGERS = Path(__file__).resolve().parents[5] / "managers"


def test_every_step_script_is_found():
    import run_tagging_pass as t
    for label, _argv, cwd, script in t.plan_steps("V"):
        assert cwd is not None, f"{label}: its Skill folder was not found"
        assert (cwd / script).is_file(), f"{label}: {cwd / script} does not exist"


def test_domain_first_and_engagement_last():
    """Engagement is derived from company tags, so it must see both sources."""
    import run_tagging_pass as t
    labels = [label for label, *_ in t.plan_steps("V")]
    assert labels == ["domain", "content-threads", "content-files", "engagement"]


def test_the_creator_accepts_the_split_flags():
    assert (_MANAGERS / "vault_manager.py").is_file(), f"no shared engine at {_MANAGERS}"
    env = dict(os.environ, PYTHONPATH=str(_MANAGERS))
    proc = subprocess.run([sys.executable, "create_companies_partners.py", "--help"],
                          cwd=_SCRIPTS, env=env, capture_output=True, text=True)
    # The exit code first: an import failure prints nothing to stdout, and
    # asserting on stdout alone reported that as a missing flag.
    assert proc.returncode == 0, proc.stderr[-800:]
    for flag in ("--hub-upkeep", "--domain-tags", "--engagement", "--retag-only"):
        assert flag in proc.stdout, flag


def test_inventory_counters_do_not_count_as_work():
    import run_tagging_pass as t
    quiet_night = [{"step": "content-threads", "ok": True,
                    "result": {"extractions_read": 179, "threads_tagged": 0, "tags_added": 0,
                               "names_still_unresolved": 63, "threads_not_found": 0}}]
    assert not t._did_something(quiet_night)
    busy_night = [{"step": "content-threads", "ok": True, "result": {"tags_added": 4}}]
    assert t._did_something(busy_night)
