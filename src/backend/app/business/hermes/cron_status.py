"""Shapes the Hermes library's CronJob/CronExecution dataclasses into
plain JSON-able dicts for the API layer. Pure file/db reads underneath,
so unlike status.py there is no "unreachable" branch to guard here -- a
missing jobs.json/executions.db just means [] (the library's own
contract), never an exception."""
from __future__ import annotations

from dataclasses import asdict

from app.business.hermes.client import get_client


# The `default` profile IS `<HERMES_HOME>`, so it has no `profiles/default`
# directory -- `HermesCron._profile_dir("default")` would resolve a path that
# exists on no install. Same convention as `HermesSkills._profile_dir` and
# `cli._profile_args`' `-p` flag (`ADR-043`).
_IDS_MEANING_THE_INSTALL_ROOT = {None, "", "default"}


def _profile_dir_id(profile_id: str | None) -> str | None:
    return None if profile_id in _IDS_MEANING_THE_INSTALL_ROOT else profile_id


def list_cron_jobs(profile_id: str | None = None) -> list[dict]:
    """Every cron job held by one profile's own `cron/jobs.json`.

    A job's profile binding is structural, not a field: `CronJob` has no
    profile attribute, and a job belongs to whichever directory's jobs.json
    holds it (`ADR-043`). `scope` states which side of that split each job
    came from, so a view never has to re-derive it -- `install` for the
    root-level jobs (the ones that run with no `-p`), `profile` for a named
    profile's own.

    Omitting `profile_id` keeps the root-only behaviour every existing
    caller already gets.
    """
    resolved_profile_id = _profile_dir_id(profile_id)
    scope = "install" if resolved_profile_id is None else "profile"
    return [
        {**asdict(job), "scope": scope}
        for job in get_client().cron.list_cron_jobs(resolved_profile_id)
    ]


def list_cron_executions(job_id: str, limit: int = 20) -> list[dict] | None:
    if get_client().cron.get_cron_job(job_id) is None:
        return None
    return [asdict(execution) for execution in get_client().cron.list_cron_executions(job_id, limit=limit)]


def get_execution_detail(job_id: str, execution_id: str) -> dict | None:
    for execution in get_client().cron.list_cron_executions(job_id, limit=200):
        if execution.id == execution_id:
            return get_client().cron.get_execution_detail(job_id, execution)
    return None
