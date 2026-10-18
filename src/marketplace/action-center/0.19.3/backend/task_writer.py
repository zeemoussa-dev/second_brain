"""The Action Center's own edits to its Task notes: add one, change one, close
it, reopen it, write a note on it.

The Tasks are this plugin's note type, so editing them is Action Center
behaviour, not a vault capability (operator, 2026-09-21). The Plugin API reads
notes; this module writes the same plain-text format the vault reads -- quoted
frontmatter values, `## ` sections -- with its own few lines rather than any
framework code.

It never writes a note it cannot find in the Tasks folder: every write names a
Task by its stem, and the stem is looked up, never joined into a path.

The semantics match the Hermes Skill that writes the same notes
(`task-capture` in the install's repository): evidence is required to close,
the reason for a reopen is kept beside the close it corrects, and a held action
(`keep_open_until`) is only completed when the closer says the condition is met.
"""
from __future__ import annotations

import re
import uuid
from datetime import date
from pathlib import Path

from . import owner_book
from .parties import parties as _parties

TASKS_KIND = "Tasks"
OPEN, COMPLETED, DROPPED = "Open", "Completed", "Dropped"
SCOPES = ("waiting", "mine")
PRIORITIES = ("Low", "Normal", "High")

# What the screen may change on an action. Status, evidence and completion move
# only through complete/reopen, which keep the record of why.
EDITABLE = ("subject", "owner", "owner_email", "due", "priority", "scope", "customer",
            "keep_open_until")

# A new Task's frontmatter, in the Template's order. Kept here because an
# installed plugin carries its backend, not its `templates/` folder; a test pins
# this to `templates/task/Template.json` so the two cannot drift.
DEFAULTS = {
    "type": "Task", "status": OPEN, "owner": "", "owner_email": "", "asked_by": "",
    "source": "agent", "scope": "waiting", "due": "", "asked_at": "", "source_thread": "",
    "customer": "", "priority": "Normal", "completed_at": "", "evidence": "",
    "evidence_source": "", "keep_open_until": "", "chased_at": "", "chase_to": "",
    "chase_conversation": "", "chases": 0,
    "tags": ["kind/tasks"],
}

_UNSAFE_FILENAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class TaskError(ValueError):
    """What the operator asked for cannot be done as asked; the message says why."""


class TaskNotFound(LookupError):
    pass


def _text(value) -> str:
    return str(value or "").strip()


def _today() -> str:
    return date.today().isoformat()


def _format_value(value) -> str:
    if isinstance(value, list):
        return "[" + ", ".join(_format_value(v) for v in value) + "]"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return str(value)


def _write(path: Path, frontmatter: dict, body: str) -> None:
    lines = ["---"] + [f"{key}: {_format_value(value)}" for key, value in frontmatter.items()]
    lines.append("---")
    path.write_text("\n".join(lines) + "\n" + body, encoding="utf-8")


def _one_line(value: str, field: str, *, required: bool = False) -> str:
    text = " ".join(_text(value).split())
    if required and not text:
        raise TaskError(f"{field} is required")
    return text


def _check_date(value: str, field: str) -> str:
    text = _text(value)
    if text and not _DATE.match(text):
        raise TaskError(f"{field} must be a date, YYYY-MM-DD")
    if text:
        try:
            date.fromisoformat(text)
        except ValueError as exc:
            raise TaskError(f"{field} is not a real date: {text}") from exc
    return text


def with_line_in_section(body: str, name: str, line: str) -> str:
    """`line` appended under `## <name>`, adding the section if the note lacks it."""
    heading = f"## {name}"
    lines = str(body or "").splitlines()
    try:
        start = next(i for i, text in enumerate(lines) if text.strip() == heading)
    except StopIteration:
        lines += ["", heading, ""]
        start = len(lines) - 2
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    while end > start + 1 and not lines[end - 1].strip():
        end -= 1
    lines[end:end] = [line]
    return "\n".join(lines) + "\n"


def _link(value: str) -> str:
    stem = _text(value).strip("[]")
    return f"[[{stem}]]" if stem else ""


class TaskWriter:
    def __init__(self, api) -> None:
        self._api = api

    # -- finding --------------------------------------------------------------

    def _paths(self) -> list[Path]:
        return [Path(p) for p in self._api.vault.notes_in_kind(TASKS_KIND)]

    def path_of(self, stem: str) -> Path:
        wanted = _text(stem)
        for path in self._paths():
            if path.stem == wanted:
                return path
        raise TaskNotFound(f"no action named {stem!r}")

    def _folder(self) -> Path:
        """Where Task notes live. Taken from an existing one; with none yet, from
        where any note under `Work/` lives -- the Tasks folder is its sibling."""
        paths = self._paths()
        if paths:
            return paths[0].parent
        # `entries()`, not `index()`: the index holds one note per name and is
        # for looking one up (`BUG-076`, framework v5). Walking the vault is a
        # different question, even when the answer is "any note will do".
        for entry in self._api.vault.entries():
            parts = Path(entry["path"]).parts
            if "Work" in parts:
                return Path(*parts[:parts.index("Work") + 1]) / TASKS_KIND
        raise TaskError("cannot tell where the vault keeps its notes")

    def _load(self, stem: str) -> tuple[Path, dict, str]:
        path = self.path_of(stem)
        frontmatter, body = self._api.vault.read_note(path)
        if _text(frontmatter.get("type")) != "Task":
            raise TaskNotFound(f"{stem!r} is not an action")
        return path, dict(frontmatter), body

    # -- writing --------------------------------------------------------------

    def create(self, fields: dict) -> dict:
        subject = _one_line(fields.get("subject"), "subject", required=True)
        scope = _text(fields.get("scope")) or "waiting"
        if scope not in SCOPES:
            raise TaskError(f"scope must be one of {', '.join(SCOPES)}")
        priority = _text(fields.get("priority")) or "Normal"
        if priority not in PRIORITIES:
            raise TaskError(f"priority must be one of {', '.join(PRIORITIES)}")

        frontmatter = {k: (list(v) if isinstance(v, list) else v) for k, v in DEFAULTS.items()}
        frontmatter.update({
            "status": OPEN, "source": "manual", "scope": scope, "priority": priority,
            "subject": subject, "title": subject,
            "owner": _one_line(fields.get("owner"), "owner"),
            "owner_email": _one_line(fields.get("owner_email"), "owner_email"),
            "due": _check_date(fields.get("due"), "due"),
            "customer": _one_line(fields.get("customer"), "customer"),
            "asked_at": _today(), "created": _today(), "id": str(uuid.uuid4()),
        })
        ask = _text(fields.get("note")) or "Added in the Action Center."
        body = f"\n## Ask\n\n{ask}\n\n## Evidence\n\n## Notes\n"

        folder = self._folder()
        folder.mkdir(parents=True, exist_ok=True)
        name = _UNSAFE_FILENAME.sub("-", subject)[:120].strip(" .") or "Action"
        path, counter = folder / f"{name}.md", 2
        while path.exists():
            path, counter = folder / f"{name} {counter}.md", counter + 1
        _write(path, frontmatter, body)
        return {"status": "created", "stem": path.stem}

    def set_chase_to(self, stem: str, addresses: list[str]) -> dict:
        """Who this action's chases go to, as the operator settled it.

        An ask owed by several people is one email to all of them, and the
        screen shows that list with everybody ticked; what he leaves ticked is
        written here. The press itself is consumed by the job, so without this
        the decision would last exactly one email -- and when chasing runs
        unattended there is nobody to ask again. Empty means what it has always
        meant: everyone the action names."""
        path, frontmatter, body = self._load(stem)
        chosen = []
        for address in addresses or []:
            one = _text(address).lower()
            if one and one not in chosen:
                chosen.append(one)
        settled = ", ".join(chosen)
        if _text(frontmatter.get("chase_to")) == settled:
            return {"status": "unchanged", "stem": stem, "chase_to": chosen}
        frontmatter["chase_to"] = settled
        _write(path, frontmatter, body)
        return {"status": "saved", "stem": stem, "chase_to": chosen}

    def update(self, stem: str, fields: dict) -> dict:
        path, frontmatter, body = self._load(stem)
        was_owner = _text(frontmatter.get("owner"))
        changed = []
        for field in EDITABLE:
            if field not in fields:
                continue
            value = fields[field]
            if field == "subject":
                value = _one_line(value, "subject", required=True)
                frontmatter["title"] = value
            elif field == "due":
                value = _check_date(value, "due")
            elif field == "scope":
                value = _text(value)
                if value not in SCOPES:
                    raise TaskError(f"scope must be one of {', '.join(SCOPES)}")
            elif field == "priority":
                value = _text(value)
                if value not in PRIORITIES:
                    raise TaskError(f"priority must be one of {', '.join(PRIORITIES)}")
            else:
                value = _one_line(value, field)
            if _text(frontmatter.get(field)) != value:
                frontmatter[field] = value
                changed.append(field)
        if changed:
            _write(path, frontmatter, body)
        # Naming an owner here settles who they are everywhere: the decision goes
        # to the book the install's agents read before asking a model again
        # (operator, 2026-09-24). Marked `operator`, so no model overrides it.
        if "owner" in changed or "owner_email" in changed:
            owner_book.record(self._api, was_owner, _text(frontmatter.get("owner")),
                              _text(frontmatter.get("owner_email")), by="operator")
        return {"status": "updated" if changed else "unchanged", "stem": stem, "changed": changed}

    def complete(self, stem: str, evidence: str, *, status: str = COMPLETED,
                 evidence_source: str = "", condition_met: bool = False) -> dict:
        evidence = _one_line(evidence, "evidence", required=True)
        if status not in (COMPLETED, DROPPED):
            raise TaskError(f"status must be {COMPLETED} or {DROPPED}")
        path, frontmatter, body = self._load(stem)
        if (_text(frontmatter.get("status")) or OPEN) != OPEN:
            return {"status": "unchanged", "stem": stem, "already": frontmatter.get("status")}
        hold = _text(frontmatter.get("keep_open_until"))
        if hold and status == COMPLETED and not condition_met:
            raise TaskError(f"this action stays open until {hold}; confirm that is what "
                            "the evidence shows, or drop it instead")
        today = _today()
        frontmatter.update({"status": status, "completed_at": today, "evidence": evidence,
                            "evidence_source": _link(evidence_source)})
        source = f" ({frontmatter['evidence_source']})" if frontmatter["evidence_source"] else ""
        body = with_line_in_section(body, "Evidence",
                                    f"- {today}: {evidence}{source} -- in the Action Center")
        _write(path, frontmatter, body)
        return {"status": status.lower(), "stem": stem}

    def reopen(self, stem: str, reason: str, *, keep_open_until: str = "") -> dict:
        reason = _one_line(reason, "reason", required=True)
        hold = _one_line(keep_open_until, "keep_open_until")
        path, frontmatter, body = self._load(stem)
        was = _text(frontmatter.get("status")) or OPEN
        if was == OPEN and not hold:
            return {"status": "unchanged", "stem": stem, "already": OPEN}
        frontmatter.update({"status": OPEN, "completed_at": "", "evidence": "",
                            "evidence_source": ""})
        if hold:
            frontmatter["keep_open_until"] = hold
        # Back in front of the completion agent on its next run, condition and all.
        frontmatter.pop("offered_at", None)
        frontmatter.pop("evidence_seen_through", None)
        line = f"- {_today()}: reopened (was {was}): {reason}"
        if hold:
            line += f" -- keep open until {hold}"
        _write(path, frontmatter, with_line_in_section(body, "Evidence", line))
        return {"status": "reopened", "stem": stem, "was": was}

    def set_owner(self, owner: str, *, name: str = "", email: str = "",
                  clear_address: bool = False) -> dict:
        """One name and one address on every OPEN action of one owner.

        Asked once, not once per action: an owner holds several actions and they
        are all chased the same way. The decision is recorded as the operator's,
        which no agent may overwrite -- including one it made itself and got
        wrong."""
        owner = _one_line(owner, "owner", required=True)
        name = _one_line(name, "name")
        email = _one_line(email, "email").lower()
        if not name and not email and not clear_address:
            raise TaskError("give a name, an address, or clear the address")
        if len(_parties(name or owner)) > 1:
            raise TaskError("that names several parties -- split the action first")

        wanted = owner.lower()
        changed = []
        for path in self._paths():
            frontmatter, body = self._api.vault.read_note(path)
            if _text(frontmatter.get("type")) != "Task":
                continue
            if (_text(frontmatter.get("status")) or OPEN) != OPEN:
                continue
            if _text(frontmatter.get("owner")).lower() != wanted:
                continue
            frontmatter = dict(frontmatter)
            frontmatter["owner"] = name or _text(frontmatter.get("owner"))
            frontmatter["owner_email"] = "" if clear_address else (
                email or _text(frontmatter.get("owner_email")))
            _write(Path(path), frontmatter, body)
            changed.append(Path(path).stem)
        owner_book.record(self._api, owner, name or owner,
                          "" if clear_address else email, by="operator")
        return {"status": "set", "owner": owner, "name": name or owner,
                "email": "" if clear_address else email or None,
                "actions_changed": len(changed), "changed": changed[:10]}

    def add_note(self, stem: str, text: str) -> dict:
        text = _one_line(text, "note", required=True)
        path, frontmatter, body = self._load(stem)
        _write(path, frontmatter, with_line_in_section(body, "Notes", f"- {_today()}: {text}"))
        return {"status": "noted", "stem": stem}
