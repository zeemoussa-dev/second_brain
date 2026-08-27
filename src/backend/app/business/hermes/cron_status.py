"""Shapes the Hermes library's CronJob/CronExecution dataclasses into
plain JSON-able dicts for the API layer. Pure file/db reads underneath,
so unlike status.py there is no "unreachable" branch to guard here -- a
missing jobs.json/executions.db just means [] (the library's own
contract), never an exception."""
from __future__ import annotations

from dataclasses import asdict

from app.business.hermes.client import get_client


def list_cron_jobs() -> list[dict]:
    return [asdict(job) for job in get_client().cron.list_cron_jobs()]


def list_cron_executions(job_id: str, limit: int = 20) -> list[dict] | None:
    if get_client().cron.get_cron_job(job_id) is None:
        return None
    return [asdict(execution) for execution in get_client().cron.list_cron_executions(job_id, limit=limit)]


def get_execution_detail(job_id: str, execution_id: str) -> dict | None:
    for execution in get_client().cron.list_cron_executions(job_id, limit=200):
        if execution.id == execution_id:
            return get_client().cron.get_execution_detail(job_id, execution)
    return None
