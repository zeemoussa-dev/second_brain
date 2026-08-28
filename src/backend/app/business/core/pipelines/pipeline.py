from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PipelineStep:
    id: str
    name: str
    description: str
    depends_on: list[str] = field(default_factory=list)
    type: str = "worker"  # "worker" | "producer"


@dataclass
class Pipeline:
    id: str
    name: str
    description: str
    section_id: str
    # The real Hermes cron job this Pipeline describes -- cron_job_id is
    # the job's own stable `name` (e.g. "meeting-capture-recurring"),
    # never Hermes' own opaque per-job hash id, which is only meaningful
    # to Hermes itself. cron_profile_id is None for a job on the shared
    # default/root profile, else the real profile folder name that owns
    # it (confirmed live: not every job lives on default -- e.g.
    # meeting-capture-recurring lives on meeting-prep-agent's own cron).
    cron_profile_id: str | None = None
    cron_job_id: str | None = None
    # Composed live from the real Hermes cron job at read time (None when
    # cron_job_id is unset, or the referenced job can't be found) --
    # never persisted, same "always current, never a stale local copy"
    # principle as HermesCron itself.
    cron_enabled: bool | None = None
    cron_schedule: str | None = None
    cron_last_run_at: str | None = None
    cron_next_run_at: str | None = None
    cron_last_status: str | None = None
    steps: list[PipelineStep] = field(default_factory=list)
