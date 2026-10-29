"""The fields Hermes stores about a cron job but does not hand back --
read from its own `cron/jobs.json` (`ADR-043`'s precedent: the profile
debugger already reads Hermes' files directly for exactly this reason).

**Why this exists.** The Hermes client's `CronJob` dataclass carries 17
fields. The file carries 37. The 20 it drops include the ones that
answer "what does this crawler actually do":

    script              the .py a script job runs -- 5 of this
                        install's 12 jobs have one and NO prompt, so
                        without it they read as empty
    no_agent            whether it is a script job at all
    skills              the real list; the dataclass's singular `skill`
                        is empty on jobs that declare skills here
    last_delivery_error why a run that says `delivery_failed` failed,
                        which `last_error` does not hold
    origin              where the job came from, e.g. a WhatsApp ask

**This is a read of somebody else's storage and is treated as such.**
Everything here is best-effort: an unreadable or moved file, a shape
that changed, a job id that is not in it -- each answers "nothing extra
known" rather than raising. The job list itself still comes from the
client, so a failure here costs detail and never a crawler.

It is deliberately NOT a second source for anything the client already
returns. Where both have a field, the client wins; this only fills in
what it has no slot for.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from app.config import settings

_logger = logging.getLogger(__name__)

# Only the fields worth the coupling. A blanket merge of everything the
# file holds would quietly start surfacing whatever Hermes adds next,
# including things it considers private.
_FIELDS_WORTH_READING = (
    "script",
    "no_agent",
    "skills",
    "last_delivery_error",
    "origin",
    "model_snapshot",
    "provider_snapshot",
)


def _jobs_files() -> list[Path]:
    """`<HERMES_HOME>/cron/jobs.json` plus each named profile's own.

    The `default` profile IS `<HERMES_HOME>` and has no
    `profiles/default/` (`cron_status.py` states the same rule), so the
    root file is listed once and never twice.
    """
    home = settings.hermes_home_path
    if not home:
        return []
    root = Path(home)
    files = [root / "cron" / "jobs.json"]
    profiles = root / "profiles"
    if profiles.is_dir():
        files.extend(sorted(profiles.glob("*/cron/jobs.json")))
    return [path for path in files if path.is_file()]


def read_extra_fields_by_job_id() -> dict[str, dict]:
    """`{job_id: {field: value}}` for the fields above, across every
    jobs.json this install has. Missing, unreadable or unparseable
    files contribute nothing and are logged, never raised."""
    extras: dict[str, dict] = {}
    for path in _jobs_files():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            _logger.warning("could not read Hermes cron file %s", path, exc_info=True)
            continue
        jobs = data if isinstance(data, list) else data.get("jobs") or []
        if not isinstance(jobs, list):
            continue
        for job in jobs:
            if not isinstance(job, dict) or not job.get("id"):
                continue
            present = {
                field: job[field]
                for field in _FIELDS_WORTH_READING
                if field in job and job[field] not in (None, "", [], {})
            }
            if present:
                extras[str(job["id"])] = present
    return extras
