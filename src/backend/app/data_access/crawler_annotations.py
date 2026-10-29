"""Raw data access for what the operator calls a crawler and how they
group it -- `<SECOND_BRAIN_DATA_PATH>/crawler-annotations.json`, in the
config folder beside `entry-points.json` and `routing-conditions.json`.

**An annotation, never the job.** Hermes owns the cron job: its name,
its schedule, when it next runs. This file holds only what Hermes has
nowhere to put -- a friendly name and tags -- keyed by the job id. The
job is still the job if this file is deleted; every reader falls back
to Hermes' own name, which is why losing this costs a label and not a
crawler.

Keyed by job id rather than by Hermes' name because a name can be
edited in Hermes and an id cannot: keying on the name would silently
orphan the annotation the first time somebody renamed a job there.

Zero interpretation: no tag vocabulary, no name validation, nothing
reconciled against the live job list. `business/hermes/crawlers.py`
owns all of that.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.config import settings

_FILENAME = "crawler-annotations.json"


def crawler_annotations_path() -> Path:
    return settings.second_brain_data_path / _FILENAME


def read_all() -> dict[str, dict]:
    """An absent file is an install that has labelled nothing, which is
    a normal state and not an error -- every crawler still shows, under
    Hermes' own name. A file that does not parse IS an error and is
    raised rather than read as "no annotations": silently showing every
    job unlabelled would invite the operator to type them all in again
    over the top of a file that still exists."""
    path = crawler_annotations_path()
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def write_all(annotations: dict[str, dict]) -> None:
    path = crawler_annotations_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(annotations, ensure_ascii=False, indent=2), encoding="utf-8",
    )
