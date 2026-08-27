"""Reads Hermes' own real cron job definitions, schedules, and run
history directly from its local install. Deliberately read-only and
display-only, same convention as definitions.py -- no local persistence,
every call re-reads the real files/db, so this can never drift from what
Hermes itself actually has scheduled/run.

Real layout:
    <home>/cron/jobs.json          -- every job's own definition +
                                       schedule + last/next run + status.
    <home>/cron/executions.db      -- one SQLite `executions` table, one
                                       row per real run.
    <home>/cron/output/<job_id>/<YYYY-MM-DD_HH-MM-SS>.md
                                    -- one real per-run report, filename
                                       timestamp matches that run's own
                                       `finished_at`.
    <home>/logs/agent.log          -- raw interleaved log lines, each
                                       run's own lines tagged
                                       `[cron_<job_id>_<started_at as
                                       YYYYMMDD_HHMMSS>]`.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from app.hermes.config import HermesConfig

# Real per-run log lines are tagged with this many trailing characters of
# `agent.log` scanned from the end -- generous enough to cover a job
# whose run spans several minutes of interleaved output from other
# concurrent jobs, without reading the whole (multi-MB) file every time.
_LOG_TAIL_BYTES = 4_000_000


@dataclass
class CronJob:
    id: str
    name: str
    prompt: str
    skill: str
    schedule_kind: str  # "once" | "interval"
    schedule_display: str
    enabled: bool
    state: str  # "scheduled" | "completed" | "paused" | ...
    created_at: str
    next_run_at: str | None
    last_run_at: str | None
    last_status: str | None
    last_error: str | None
    failure_streak: int
    deliver: str
    repeat_times: int | None
    repeat_completed: int


@dataclass
class CronExecution:
    id: str
    job_id: str
    status: str
    claimed_at: str
    started_at: str | None
    finished_at: str | None
    error: str | None


def _job_from_raw(raw: dict) -> CronJob:
    schedule = raw.get("schedule") or {}
    repeat = raw.get("repeat") or {}
    return CronJob(
        id=str(raw.get("id") or ""),
        name=str(raw.get("name") or ""),
        prompt=str(raw.get("prompt") or ""),
        skill=str(raw.get("skill") or ""),
        schedule_kind=str(schedule.get("kind") or ""),
        schedule_display=str(raw.get("schedule_display") or schedule.get("display") or ""),
        enabled=bool(raw.get("enabled")),
        state=str(raw.get("state") or ""),
        created_at=str(raw.get("created_at") or ""),
        next_run_at=raw.get("next_run_at"),
        last_run_at=raw.get("last_run_at"),
        last_status=raw.get("last_status"),
        last_error=raw.get("last_error"),
        failure_streak=int(raw.get("failure_streak") or 0),
        deliver=str(raw.get("deliver") or ""),
        repeat_times=repeat.get("times"),
        repeat_completed=int(repeat.get("completed") or 0),
    )


class HermesCron:
    def __init__(self, config: HermesConfig) -> None:
        self._config = config

    def _jobs_json_path(self) -> Path:
        return self._config.home_path / "cron" / "jobs.json"

    def _executions_db_path(self) -> Path:
        return self._config.home_path / "cron" / "executions.db"

    def list_cron_jobs(self) -> list[CronJob]:
        """Every real cron job Hermes has defined, [] (never raises) if
        jobs.json doesn't exist yet."""
        path = self._jobs_json_path()
        if not path.is_file():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        return [_job_from_raw(raw) for raw in data.get("jobs", [])]

    def get_cron_job(self, job_id: str) -> CronJob | None:
        for job in self.list_cron_jobs():
            if job.id == job_id:
                return job
        return None

    def list_cron_executions(self, job_id: str, limit: int = 20) -> list[CronExecution]:
        """Real run history for one job, most recent first. [] (never
        raises) if executions.db doesn't exist yet."""
        path = self._executions_db_path()
        if not path.is_file():
            return []
        try:
            con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        except sqlite3.OperationalError:
            return []
        try:
            cur = con.execute(
                "SELECT id, job_id, status, claimed_at, started_at, finished_at, error "
                "FROM executions WHERE job_id = ? ORDER BY claimed_at DESC LIMIT ?",
                (job_id, limit),
            )
            return [
                CronExecution(id=row[0], job_id=row[1], status=row[2], claimed_at=row[3], started_at=row[4], finished_at=row[5], error=row[6])
                for row in cur.fetchall()
            ]
        finally:
            con.close()

    def _output_report_path(self, job_id: str, execution: CronExecution) -> Path | None:
        """The one real per-run markdown report for this execution -- filed
        under its `finished_at` timestamp. None if the run never finished
        or the file isn't there."""
        if not execution.finished_at:
            return None
        try:
            finished = datetime.fromisoformat(execution.finished_at)
        except ValueError:
            return None
        candidate = self._config.home_path / "cron" / "output" / job_id / f"{finished.strftime('%Y-%m-%d_%H-%M-%S')}.md"
        return candidate if candidate.is_file() else None

    def _log_session_tag(self, job_id: str, execution: CronExecution) -> str | None:
        if not execution.started_at:
            return None
        try:
            started = datetime.fromisoformat(execution.started_at)
        except ValueError:
            return None
        return f"cron_{job_id}_{started.strftime('%Y%m%d_%H%M%S')}"

    def get_execution_detail(self, job_id: str, execution: CronExecution) -> dict:
        """The real per-run report (if the run finished and wrote one)
        plus a matching excerpt of raw agent.log lines carrying this
        run's own session tag -- both keyed off the SAME real execution
        row, so nothing here is guessed or approximated."""
        report_path = self._output_report_path(job_id, execution)
        report_markdown = None
        if report_path is not None:
            try:
                report_markdown = report_path.read_text(encoding="utf-8")
            except OSError:
                report_markdown = None

        tag = self._log_session_tag(job_id, execution)
        log_lines: list[str] = []
        if tag is not None:
            log_path = self._config.home_path / "logs" / "agent.log"
            try:
                with log_path.open("rb") as f:
                    f.seek(0, 2)
                    size = f.tell()
                    f.seek(max(0, size - _LOG_TAIL_BYTES))
                    tail = f.read().decode("utf-8", errors="replace")
                log_lines = [line for line in tail.splitlines() if f"[{tag}]" in line]
            except OSError:
                log_lines = []

        return {
            "report_markdown": report_markdown,
            "log_lines": log_lines,
        }
