from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Index:
    id: str
    name: str
    # Which top-level Work/ folders to include -- empty means every real
    # folder (matching the original build_vault_index.py's own default
    # behavior before this system existed).
    folders: list[str] = field(default_factory=list)
    # Which tags a note must carry to be included -- empty means no tag
    # filter (folder scope alone decides membership).
    tags: list[str] = field(default_factory=list)
    # Folder-recursion depth limit under each included top-level folder;
    # None means unlimited (the original script's own plain `rglob`).
    depth: int | None = None
    # Real absolute path this Index's own built output gets written to.
    storage_path: str = ""
    # Cron schedule string, same syntax `hermes cron create` itself
    # accepts ('30m', 'every 2h', '0 9 * * *').
    schedule: str = ""
    created_at: str = ""
    updated_at: str | None = None
    # The real Hermes cron job behind this Index -- cron_job_id is the
    # job's own real, opaque id (e.g. "dd45b9fd3a60"), NOT a stable name
    # the way Pipeline's own cron_job_id is; every job here was created
    # BY this backend (IndexManager.create), so the real id is always
    # known directly from that call, never guessed via name-matching.
    cron_profile_id: str | None = None
    cron_job_id: str | None = None
    # Composed live from the real Hermes cron job at read time (None
    # when cron_job_id is unset, or the referenced job can't be found) --
    # never persisted, same "always current, never a stale local copy"
    # principle Pipeline's own cron composition already established.
    cron_enabled: bool | None = None
    cron_schedule_display: str | None = None
    cron_last_run_at: str | None = None
    cron_next_run_at: str | None = None
    cron_last_status: str | None = None
