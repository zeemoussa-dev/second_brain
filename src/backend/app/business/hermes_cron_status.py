"""Shapes hermes_cron.py's real CronJob/CronExecution dataclasses into
plain JSON-able dicts for the API layer (same split as hermes_status.py --
ADR-005 point 5's "router never reaches into data_access/ directly").
Pure file/db reads underneath, so unlike hermes_status.py there is no
"unreachable" branch to guard here -- a missing jobs.json/executions.db
just means [] (hermes_cron.py's own contract), never an exception."""
from __future__ import annotations

from dataclasses import asdict

from app.data_access import hermes_cron


def list_cron_jobs() -> list[dict]:
    return [asdict(job) for job in hermes_cron.list_cron_jobs()]


def list_cron_executions(job_id: str, limit: int = 20) -> list[dict] | None:
    if hermes_cron.get_cron_job(job_id) is None:
        return None
    return [asdict(execution) for execution in hermes_cron.list_cron_executions(job_id, limit=limit)]


def get_execution_detail(job_id: str, execution_id: str) -> dict | None:
    for execution in hermes_cron.list_cron_executions(job_id, limit=200):
        if execution.id == execution_id:
            return hermes_cron.get_execution_detail(job_id, execution)
    return None
