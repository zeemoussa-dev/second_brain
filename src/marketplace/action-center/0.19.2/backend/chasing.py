"""Asking the install's own agent to chase somebody, from the screen.

The operator declined a scheduled chasing job and asked for a button instead
(2026-09-24: "add a button in the action center to Chase for now"). So nothing
is chased until he presses it, and what is pressed is recorded here for the
Hermes job that does the writing.

Two halves, because a plugin cannot write an email itself:

1. The ACTION is written to this plugin's own data file, the job's inbox tray --
   one action, one email (operator, 2026-09-24: "Each task is one email"), so a
   person owing three things is chased three times, each answerable on its own.
2. The Hermes job is fired through the Plugin API, which is the one way a plugin
   can start an agent. The job reads the tray, hands the agent that one ask and
   who owes it, and the AGENT writes the mail -- in its own words, never
   a template -- and SENDS it, from the agent's own address. The operator asked
   for that once he had read what the agent writes ("I will click on the button
   it should send an email"), so the screen confirms the press before making it.

A plugin cannot know whether the agent later wrote anything, so the screen says
what it actually did: the chase was asked for.

In bulk it is the same queue, longer (operator, 2026-09-24: "bulk send to person
and everyone ... Still it will go one by one but Just for a faster execution").
The job takes a few at a time and asks itself back for the rest, so twenty
chases are twenty separate emails written one at a time -- the speed is in not
having to press twenty times.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

REQUESTS = "data/ActionChase/requested.json"

# The Hermes job that does the writing. Its schedule is years out on purpose --
# it exists to be triggered, never to fire by itself.
JOB = "SB action chase"


def _read(api) -> list[str]:
    try:
        stored = json.loads(api.data.read_text(REQUESTS) or "{}")
    except Exception:
        return []
    return [str(s) for s in (stored.get("stems") or []) if str(s).strip()]


def _read_to(api) -> dict[str, list[str]]:
    try:
        stored = json.loads(api.data.read_text(REQUESTS) or "{}")
    except Exception:
        return {}
    return {str(stem): [str(a) for a in (addresses or [])]
            for stem, addresses in (stored.get("to") or {}).items()}


def request(api, stems: list[str], to: dict[str, list[str]] | None = None) -> dict:
    """Adds these actions to the tray and asks the job to run.

    Queued rather than replaced: pressing Chase on two actions before the job
    picks either up must chase both.

    `to` is who each action's mail goes to, where the operator chose. An action
    owed by several people is ONE email to all of them (2026-09-26), and the
    screen shows that list with everybody ticked -- so what arrives here is
    whoever he left ticked. Without an entry the job writes to everyone the
    action names."""
    wanted = [str(s).strip() for s in stems if str(s).strip()]
    if not wanted:
        raise ValueError("a chase needs an action to chase")
    queued = _read(api)
    for stem in wanted:
        if stem not in queued:
            queued.append(stem)
    addressed = _read_to(api)
    for stem, addresses in (to or {}).items():
        chosen = [str(a).strip() for a in (addresses or []) if str(a).strip()]
        if chosen:
            addressed[str(stem)] = chosen
    api.data.write_text(REQUESTS, json.dumps({
        "stems": queued,
        "to": {stem: addresses for stem, addresses in addressed.items() if stem in queued},
        "asked_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ"),
    }, indent=2))

    started = False
    problem = ""
    try:
        started = bool(api.hermes.run_cron_job(JOB))
    except Exception as exc:  # the agent host being down is not a screen error
        problem = str(exc)
    return {"status": "asked", "actions": wanted, "queued": len(queued),
            "agent_started": started,
            # Said plainly: the tray is kept either way, so the next run takes it.
            "note": ("The agent is writing the message and will send it from "
                     "cbo-agent01@core42.ai." if started else
                     "Queued. The agent could not be started just now"
                     + (f" ({problem})" if problem else "") + "; it will be picked up."),
            }
