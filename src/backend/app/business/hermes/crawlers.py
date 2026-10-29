"""A crawler, as the operator reads one (operator, 2026-10-24: "I need
to see what's inside, a quick visual of the steps, a friendly name, a
tag, and when they run and the next run").

Three sources, composed and kept distinguishable:

- **Hermes' own job** -- the schedule, the state, when it last ran and
  when it runs next. Hermes owns all of it and nothing here edits it.
- **The fields Hermes' client drops** (`hermes_cron_files`) -- chiefly
  `script`, which is the whole answer to "what's inside" for a job that
  has no prompt.
- **The operator's labels** -- a friendly name and tags, which Hermes
  has nowhere to put, stored beside the install's other annotations.

**What a job IS is derived, not assumed.** Five of this install's
twelve jobs run a script with an empty prompt; one has a prompt with
numbered steps; the rest have a prompt that is a sentence. A view that
expected any single shape would show nothing for most of them, so
`definition` says which shape this job has and the view renders that.
"""
from __future__ import annotations

import re

from app.business.hermes import cron_status
from app.data_access import crawler_annotations as annotations_data
from app.data_access import hermes_cron_files

# A numbered step at the start of a line: "1. Ask which Threads are due".
# Only the first line of each is the step; the indented lines under it
# are its detail, which the view shows on demand rather than in the
# chain.
_NUMBERED_STEP = re.compile(r"(?m)^[ \t]{0,3}(\d+)[.)][ \t]+(\S.*)$")

# Long enough to be a real instruction rather than a list item inside a
# sentence, short enough not to be a paragraph that happens to start
# with a number.
_SHORTEST_STEP = 4


def steps_in(prompt: str) -> list[dict]:
    """The numbered steps a prompt spells out, in order.

    **Empty is the common answer and is not a failure.** On this
    install exactly one job of twelve writes its work as a numbered
    list; the rest are a script or a single sentence. Returning `[]`
    lets the view say what the job actually is instead of drawing an
    empty chain and implying the job has no steps.

    The numbers are taken in the order they appear and are NOT trusted
    to be sequential: a prompt that jumps from 2 to 4 is shown as
    written, because renumbering it here would hide an edit someone
    made badly.
    """
    if not prompt:
        return []
    return [
        {"number": number, "says": says.strip()}
        for number, says in _NUMBERED_STEP.findall(prompt)
        if len(says.strip()) >= _SHORTEST_STEP
    ]


def definition_of(job: dict, extra: dict) -> dict:
    """What this crawler actually runs, named by kind so the view does
    not have to guess from empty fields.

    `script` beats `prompt`: a job with `no_agent` runs the script and
    its prompt, if any, is not what happens.
    """
    script = extra.get("script")
    prompt = (job.get("prompt") or "").strip()
    skills = extra.get("skills") or ([job["skill"]] if job.get("skill") else [])

    if script:
        return {
            "kind": "script",
            "runs": script,
            "says": prompt,
            "skills": skills,
            "steps": steps_in(prompt),
        }
    if prompt:
        steps = steps_in(prompt)
        return {
            "kind": "steps" if steps else "instruction",
            "runs": skills[0] if skills else "",
            "says": prompt,
            "skills": skills,
            "steps": steps,
        }
    return {
        "kind": "unknown",
        "runs": skills[0] if skills else "",
        "says": "",
        "skills": skills,
        # Said plainly rather than left as an empty card: a job that
        # runs successfully every hour while this app can see nothing
        # that defines it is a gap in what we read, not an empty job.
        "steps": [],
    }


def list_crawlers() -> list[dict]:
    """Every cron job, with what defines it and whatever the operator
    has called it.

    A failure to read the annotations is reported on the payload rather
    than raised: the crawlers are the point of the screen and they are
    still readable under Hermes' own names.
    """
    jobs = cron_status.list_cron_jobs()
    extras = hermes_cron_files.read_extra_fields_by_job_id()

    unreadable_annotations = None
    try:
        labels = annotations_data.read_all()
    except (OSError, ValueError) as exc:
        labels, unreadable_annotations = {}, str(exc)

    crawlers = []
    for job in jobs:
        extra = extras.get(str(job.get("id")), {})
        label = labels.get(str(job.get("id")), {}) if isinstance(labels, dict) else {}
        crawlers.append({
            **job,
            # Hermes' name is always kept and always shown somewhere: a
            # friendly name that replaced it entirely would make a job
            # unfindable by the name it has in Hermes' own logs.
            "friendly_name": (label.get("friendly_name") or "").strip(),
            "tags": [str(tag) for tag in (label.get("tags") or [])],
            "definition": definition_of(job, extra),
            "delivery_error": extra.get("last_delivery_error"),
            "origin": extra.get("origin"),
            "model": extra.get("model_snapshot"),
        })
    return {
        "crawlers": crawlers,
        "tags": sorted({tag for c in crawlers for tag in c["tags"]}),
        "annotations_unreadable": unreadable_annotations,
    }


def set_annotation(job_id: str, friendly_name: str, tags: list[str]) -> dict:
    """Name and tag one crawler. Writes only this install's annotation
    file; Hermes' own job is untouched, so a wrong label is never a
    wrong schedule.

    Tags are trimmed, de-duplicated and kept in the order given --
    there is no tag vocabulary and none is invented, because the
    operator's example ("indexes") is a grouping they decide, not one
    this app could have known.
    """
    everything = annotations_data.read_all()
    cleaned: list[str] = []
    for tag in tags:
        tag = str(tag).strip()
        if tag and tag not in cleaned:
            cleaned.append(tag)

    entry = {"friendly_name": friendly_name.strip(), "tags": cleaned}
    if not entry["friendly_name"] and not entry["tags"]:
        # Nothing left to say about this job: drop the row rather than
        # leave an empty one, so the file stays a list of things the
        # operator actually labelled.
        everything.pop(job_id, None)
    else:
        everything[job_id] = entry
    annotations_data.write_all(everything)
    return entry
