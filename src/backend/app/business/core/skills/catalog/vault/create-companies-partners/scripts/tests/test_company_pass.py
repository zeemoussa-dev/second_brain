"""The Company pass's wiring: every step's script is found, and a quiet hour
stays quiet.

A step whose script cannot be found fails on every run on the machine that
runs it -- the nightly pass's discovery step did exactly that when it named a
path that existed only in a repo checkout.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_every_step_script_is_found():
    import run_company_pass as c
    for label, _argv, cwd, script in c.plan_steps("V"):
        assert cwd is not None, f"{label}: its Skill folder was not found"
        assert (cwd / script).is_file(), f"{label}: {cwd / script} does not exist"


def test_the_steps():
    import run_company_pass as c
    assert [label for label, *_ in c.plan_steps("V")] == ["history", "captures", "people"]


def test_inventory_counters_do_not_count_as_work():
    """It runs every hour; counts of what it read are not news."""
    import run_company_pass as c
    quiet_hour = [
        {"step": "captures", "ok": True,
         "result": {"status": "complete", "extractions_read": 179, "captures_notes_written": 0,
                    "facts_filed": 0, "facts_unresolved": 12, "threads_not_found": 1}},
        {"step": "people", "ok": True,
         "result": {"status": "complete", "extractions_read": 179, "people_filled": 0,
                    "fields_filled": 0, "changes_logged": 0, "people_not_in_vault": 40}},
    ]
    assert not c._did_something(quiet_hour)
    assert c._did_something([{"step": "captures", "ok": True, "result": {"facts_filed": 3}}])
