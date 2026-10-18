"""Task notes projected down to the follow-up list the Action Center shows.

A Task is one ask: who it was asked of, when, where it came from, and whether
anything since then shows it was done. This module decides nothing about
completion -- whatever writes the note does -- it reads, filters, groups and
orders.

Every Task is the same note whether a cron pass read it out of sent mail
(`source: email`), an agent was told to create it (`source: agent`), or someone
typed it (`source: manual`). That is what lets one list hold all three and a
filter tell them apart.
"""
from __future__ import annotations

import re

from datetime import date, datetime
from pathlib import Path

from . import owner_book
from .parties import naming_words as _naming_words, parties as _parties

TASKS_KIND = "Tasks"
OPEN = "Open"
COMPLETED = "Completed"
DROPPED = "Dropped"

# What a Task can be grouped by, and where each value comes from on the note.
GROUPABLE = {
    "owner": lambda task: task["owner"] or "(unassigned)",
    "addressable": lambda task: "Can be messaged" if task["owner_email"] else "No address",
    "owner_kind": lambda task: ("A person" if task["owner_is_person"]
                                else "A team or company -- nobody named yet"),
    "customer": lambda task: task["customer"] or "(no customer)",
    "entity": lambda task: task["entity"] or "(not linked to a company)",
    "status": lambda task: task["status"],
    "source": lambda task: task["source"] or "(unknown)",
    "scope": lambda task: SCOPE_LABELS.get(task["scope"], task["scope"] or "(unknown)"),
    "due": lambda task: _due_bucket(task),
    "completed": lambda task: _completed_bucket(task),
}

_DUE_ORDER = ["Overdue", "Today", "This week", "Later", "No due date"]
_CLOSED_ORDER = ["Today", "This week", "This month", "Earlier", "No date recorded"]

# Both halves of the follow-up list, named as they read on a screen. What he is
# waiting on and what he owes are different work, and a list that mixes them
# reads as one long backlog (operator, 2026-09-20: "both his asks and his own").
MINE, WAITING = "mine", "waiting"
SCOPE_LABELS = {WAITING: "Waiting on others", MINE: "Mine"}


def _text(value) -> str:
    return str(value or "").strip()


def _as_date(value) -> date | None:
    """A due date written by a model is not a format. Accept the ISO date it
    usually is, an ISO timestamp, and the day-first form Outlook hands over;
    anything else is simply undated rather than an error the operator sees."""
    text = _text(value)
    if not text:
        return None
    candidate = text.replace("/", "-").split(" ")[0]
    for pattern in ("%Y-%m-%d", "%d-%m-%Y", "%m-%d-%Y"):
        try:
            return datetime.strptime(candidate, pattern).date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _due_bucket(task: dict) -> str:
    if not task["due"]:
        return "No due date"
    due = _as_date(task["due"])
    if due is None:
        return "No due date"
    today = date.today()
    if due < today:
        return "Overdue"
    if due == today:
        return "Today"
    return "This week" if (due - today).days <= 7 else "Later"


def _completed_bucket(task: dict) -> str:
    """When this was closed, in the sizes a reader thinks in. A completed list
    is read backwards -- what happened lately, then everything before it."""
    closed = _as_date(task["completed_at"])
    if closed is None:
        return "No date recorded"
    today = date.today()
    if closed >= today:
        return "Today"
    if (today - closed).days <= 7:
        return "This week"
    if (closed.year, closed.month) == (today.year, today.month):
        return "This month"
    return "Earlier"


class ActionView:
    def __init__(self, api) -> None:
        self._api = api
        self._people_index: dict[str, str] | None = None

    @property
    def api(self):
        """The Plugin API this view was built with -- the routes need it to ask
        Hermes for a chase, which is not a read of the vault."""
        return self._api

    def _tasks(self) -> list[dict]:
        tasks = []
        for path in self._api.vault.notes_in_kind(TASKS_KIND):
            frontmatter, _ = self._api.vault.read_note(path)
            if _text(frontmatter.get("type")) != "Task":
                continue
            due = _as_date(frontmatter.get("due"))
            status = _text(frontmatter.get("status")) or OPEN
            tasks.append({
                "subject": _text(frontmatter.get("subject")) or _text(frontmatter.get("title")),
                "owner": _text(frontmatter.get("owner")),
                "owner_email": _text(frontmatter.get("owner_email")),
                "asked_by": _text(frontmatter.get("asked_by")),
                "source": _text(frontmatter.get("source")),
                "scope": _text(frontmatter.get("scope")) or WAITING,
                "status": status,
                "priority": _text(frontmatter.get("priority")) or "Normal",
                "due": due.isoformat() if due else None,
                "overdue": bool(due and status == OPEN and due < date.today()),
                "asked_at": _text(frontmatter.get("asked_at")) or None,
                "source_thread": _text(frontmatter.get("source_thread")) or None,
                "customer": _text(frontmatter.get("customer")) or None,
                "completed_at": _text(frontmatter.get("completed_at")) or None,
                "evidence": _text(frontmatter.get("evidence")) or None,
                "evidence_source": _text(frontmatter.get("evidence_source")) or None,
                "keep_open_until": _text(frontmatter.get("keep_open_until")) or None,
                # Who this action's chases go to, as the operator settled it on
                # the screen. Empty means everyone the action names.
                "chase_to": _text(frontmatter.get("chase_to")),
                # What the action is ABOUT: the company its thread is tagged
                # with, written by the install's scan pass. `entity_tag` is the
                # stable half -- a company can be renamed, its tag rarely is --
                # and is what another screen matches on.
                "entity": _text(frontmatter.get("entity")),
                "entity_tag": _text(frontmatter.get("entity_tag")),
                # Filled in below: the vault decides, and it needs the whole row.
                "owner_is_person": None,
                "stem": getattr(path, "stem", _text(path)),
            })
        for task in tasks:
            task["owner_is_person"] = self.owner_is_a_person(task)
        return tasks

    def _filtered(self, filters: dict) -> list[dict]:
        tasks = self._tasks()
        for field in ("status", "owner", "customer", "source", "priority", "scope",
                      "entity", "entity_tag"):
            wanted = _text(filters.get(field))
            if wanted:
                tasks = [t for t in tasks if _text(t.get(field)).lower() == wanted.lower()]
        if filters.get("overdue"):
            tasks = [t for t in tasks if t["overdue"]]
        # An action is chased by messaging its owner (operator, 2026-09-24), so
        # one with no address cannot be chased at all -- that is worth filtering
        # for, not just worth showing.
        if filters.get("unaddressed"):
            tasks = [t for t in tasks if not t["owner_email"]]
        # "Core42 Commercial" is an honest answer to who was asked and a
        # misleading one to who will act (operator, 2026-09-26). Worth finding.
        if filters.get("not_a_person"):
            tasks = [t for t in tasks if not t["owner_is_person"]]
        # Evidence with no link back to where it came from: the quote is there,
        # the thing that proves it is not. Worth finding, not just counting
        # (operator, 2026-09-25) -- a number nobody can act on is the complaint
        # this screen already answered once.
        if filters.get("no_source"):
            tasks = [t for t in tasks if not _text(t.get("evidence_source"))]
        if _text(filters.get("due_before")):
            tasks = [t for t in tasks if t["due"] and t["due"] <= _text(filters["due_before"])]
        if _text(filters.get("due_after")):
            tasks = [t for t in tasks if t["due"] and t["due"] >= _text(filters["due_after"])]
        query = _text(filters.get("q")).lower()
        if query:
            tasks = [t for t in tasks
                     if query in t["subject"].lower()
                     or query in t["owner"].lower()
                     or query in _text(t["customer"]).lower()]
        # Overdue first, then what is due soonest, then the undated -- the order
        # someone chasing people actually works in.
        if _text(filters.get("status")).lower() == COMPLETED.lower():
            # Nothing completed is overdue and few carry a due date; what a
            # reader wants is the most recently closed first.
            tasks.sort(key=lambda t: (t["completed_at"] or "", t["subject"].lower()), reverse=True)
        else:
            tasks.sort(key=lambda t: (not t["overdue"], t["due"] is None, t["due"] or "",
                                      t["owner"].lower(), t["subject"].lower()))
        return tasks

    def list_actions(self, **filters) -> list[dict]:
        return self._filtered(filters)

    def grouped(self, group_by: str = "owner", **filters) -> list[dict]:
        """The same filtered list, cut into groups. An unknown `group_by` is
        refused by the caller, never silently answered as one big group."""
        key_of = GROUPABLE[group_by]
        groups: dict[str, dict] = {}
        for task in self._filtered(filters):
            key = key_of(task)
            group = groups.setdefault(key, {"key": key, "count": 0, "overdue": 0, "items": []})
            group["count"] += 1
            group["overdue"] += 1 if task["overdue"] else 0
            group["items"].append(task)
        ordered = list(groups.values())
        if group_by == "due":
            ordered.sort(key=lambda g: _DUE_ORDER.index(g["key"]) if g["key"] in _DUE_ORDER else 99)
        elif group_by == "completed":
            ordered.sort(key=lambda g: _CLOSED_ORDER.index(g["key"]) if g["key"] in _CLOSED_ORDER else 99)
        else:
            ordered.sort(key=lambda g: (-g["overdue"], -g["count"], g["key"].lower()))
        return ordered

    def facets(self, status: str = OPEN) -> dict:
        """Every value the filter bar can offer, with how many tasks OF THE
        STATUS BEING LOOKED AT carry it -- so a filter never offers a choice
        that selects nothing.

        The Completed screen has the same filters as the open one (operator,
        2026-09-25), and counted over the open tasks they would be wrong there:
        somebody whose every action is finished would not appear in the list of
        people at all. An empty `status` counts everything."""
        wanted = _text(status)
        open_tasks = [t for t in self._tasks()
                      if not wanted or t["status"].lower() == wanted.lower()]

        def counted(field: str, *, by_name: bool = False) -> list[dict]:
            """The values a filter can offer, with how many of the actions in
            view carry each. Names are listed ALPHABETICALLY (operator, 2026-09-24): a list
            of a hundred people ordered by how much they owe cannot be searched
            by eye, which is the only way a dropdown is used."""
            counts: dict[str, int] = {}
            for task in open_tasks:
                value = _text(task.get(field))
                if value:
                    counts[value] = counts.get(value, 0) + 1
            order = ((lambda kv: kv[0].lower()) if by_name
                     else (lambda kv: (-kv[1], kv[0].lower())))
            return [{"value": v, "count": c} for v, c in sorted(counts.items(), key=order)]

        return {
            "owners": counted("owner", by_name=True),
            "entities": counted("entity", by_name=True),
            "customers": counted("customer", by_name=True),
            "sources": counted("source"),
            "priorities": counted("priority"),
            "scopes": [{"value": s, "label": SCOPE_LABELS[s],
                        "count": sum(1 for t in open_tasks if t["scope"] == s)}
                       for s in (WAITING, MINE)],
            "statuses": [{"value": s, "count": sum(1 for t in self._tasks() if t["status"] == s)}
                         for s in (OPEN, COMPLETED, DROPPED)],
            # Grouping by when something was closed says nothing about work
            # that is still open, so it is offered only where it means
            # something.
            "group_by": sorted(k for k in GROUPABLE
                               if k != "completed" or wanted.lower() == COMPLETED.lower()),
        }

    def summary(self) -> dict:
        tasks = self._tasks()
        open_tasks = [t for t in tasks if t["status"] == OPEN]
        return {
            "total": len(tasks),
            "open": len(open_tasks),
            "not_a_person": sum(1 for t in open_tasks if not t["owner_is_person"]),
            "completed": sum(1 for t in tasks if t["status"] == COMPLETED),
            "dropped": sum(1 for t in tasks if t["status"] == DROPPED),
            "overdue": sum(1 for t in open_tasks if t["overdue"]),
            "unowned": sum(1 for t in open_tasks if not t["owner"]),
            "unaddressed": sum(1 for t in open_tasks if not t["owner_email"]),
            "waiting_on_others": sum(1 for t in open_tasks if t["scope"] == WAITING),
            "mine": sum(1 for t in open_tasks if t["scope"] == MINE),
            "owners": len({t["owner"] for t in open_tasks if t["owner"]}),
            "by_source": {s: sum(1 for t in open_tasks if t["source"] == s)
                          for s in sorted({t["source"] for t in open_tasks if t["source"]})},
        }

    # -- what nobody could settle ---------------------------------------------

    def doubts(self, *, limit: int = 6) -> dict:
        """What the agents could not settle, for the operator to settle instead.

        This is the top of the screen on purpose: every one of these is an
        action that cannot be chased, and what he decides here is written to
        `Settings/Action-Owners.md`, which the agents read before asking a model
        again (operator, 2026-09-24: "the source of relearning of the agents").
        """
        open_tasks = [t for t in self._tasks() if t["status"] == OPEN]
        decided = owner_book.read(self._api)

        several = [t for t in open_tasks if len(_parties(t["owner"])) > 1]

        # Grouped by OWNER, not by action: one address settles every action that
        # owner holds, so asking once is the whole job. Each comes with the
        # people on its own threads -- he wrote the ask TO whoever has to act
        # (operator, 2026-09-24), so the address is usually one click away.
        unaddressed: dict[str, dict] = {}
        for task in open_tasks:
            if task["owner_email"] or len(_parties(task["owner"])) > 1:
                continue
            name = task["owner"] or "(unassigned)"
            row = unaddressed.setdefault(name, {"owner": name, "actions": 0, "asks": [],
                                                "stems": [], "threads": []})
            row["actions"] += 1
            if len(row["asks"]) < 2:
                row["asks"].append(task["subject"])
            if len(row["stems"]) < 3:
                row["stems"].append(task["stem"])
            if task["source_thread"] and task["source_thread"] not in row["threads"]:
                row["threads"].append(task["source_thread"])
        mine = self._self_email()
        for row in unaddressed.values():
            row["candidates"] = self._people_on(row.pop("threads")[:2], mine)[:6]

        # Names that could be the same person. Offered as a question, never
        # merged: "CEO Office" and "COO Office" are different desks, so a shared
        # word that names nothing is not a resemblance.
        names = sorted({t["owner"] for t in open_tasks
                        if t["owner"] and len(_parties(t["owner"])) == 1})
        addresses = {t["owner"]: t["owner_email"] for t in open_tasks if t["owner_email"]}
        counts: dict[str, int] = {}
        for task in open_tasks:
            counts[task["owner"]] = counts.get(task["owner"], 0) + 1
        lookalikes = []
        for index, name in enumerate(names):
            mine = _naming_words(name)
            for other in names[index + 1:]:
                if mine and mine & _naming_words(other):
                    lookalikes.append({
                        "names": [
                            {"owner": name, "address": addresses.get(name),
                             "actions": counts.get(name, 0)},
                            {"owner": other, "address": addresses.get(other),
                             "actions": counts.get(other, 0)},
                        ],
                        "settled": name.lower() in decided and other.lower() in decided,
                    })

        ordered = sorted(unaddressed.values(), key=lambda r: (-r["actions"], r["owner"]))
        return {
            "asked_of_several": {
                "count": len(several),
                "items": [_doubt_row(t) for t in several[:limit]],
            },
            "no_address": {
                "count": sum(r["actions"] for r in unaddressed.values()),
                "owners": len(unaddressed),
                "items": ordered[:limit],
            },
            "possible_duplicate_owners": {
                "count": sum(1 for pair in lookalikes if not pair["settled"]),
                "items": [pair["names"] for pair in lookalikes if not pair["settled"]][:limit],
            },
            "decided": {
                "count": len(decided),
                "by_the_operator": sum(1 for d in decided.values() if d["by"] == "operator"),
                # The agents' own calls, newest first: these are the ones worth
                # a second look, and overruling one is a click.
                "items": sorted(decided.values(), key=lambda d: (d["by"] != "agent", d["seen"])),
            },
        }

    def same_ask(self, action: dict) -> list[dict]:
        """The other OPEN actions that are this same ask given to somebody else.

        The split pass writes one action per person, because each of them owes
        their own thing and each closes on its own -- but "Each team VP to book
        an intro call" is one ask, and chasing it four times is not how anybody
        chases (operator, 2026-09-26). Same subject, same thread, different
        owner."""
        subject = _text(action.get("subject")).lower()
        thread = _text(action.get("source_thread")).lower()
        if not subject:
            return []
        return [task for task in self._tasks()
                if task["stem"] != action["stem"]
                and task["status"] == OPEN
                and task["scope"] != MINE
                and _text(task["subject"]).lower() == subject
                and _text(task["source_thread"]).lower() == thread]

    def _people_notes(self) -> tuple[set[str], list[set[str]]]:
        """Everyone the vault has a Person note for: the names and addresses
        exactly as written, and what each name is ABOUT, for the spellings that
        do not match exactly. Read once per call, because it is asked of every
        action."""
        if self._people_index is None:
            exact: set[str] = set()
            about: list[set[str]] = []
            for entry in self._api.vault.entries():
                frontmatter = entry.get("frontmatter") or {}
                if _text(frontmatter.get("type")) != "Person":
                    continue
                address = _text(frontmatter.get("email")) or _text(entry.get("stem"))
                name = _text(frontmatter.get("name")) or _text(entry.get("stem"))
                if address:
                    exact.add(address.lower())
                if name:
                    exact.add(name.lower())
                    words = _naming_words(name)
                    if words:
                        about.append(words)
            self._people_index = (exact, about)
        return self._people_index

    def owner_is_a_person(self, task: dict) -> bool:
        """Whether the vault can say this owner is a PERSON.

        "Core42 Commercial", "CEO Office", "Group Finance" are real answers to
        "who was this asked of" and they are kept as written -- but showing them
        in a list of people is misleading (operator, 2026-09-26), because there
        is nobody there to do anything. A person is one the vault knows: an
        address on the action, or a Person note under that name.

        This asks what is on record; it never decides WHO a team means. That is
        the operator's call, on the "Needs your input" screen."""
        if _text(task.get("owner_email")):
            return True
        name = _text(task.get("owner"))
        if not name:
            return False
        exact, about = self._people_notes()
        if name.lower() in exact:
            return True
        # A person written a little differently is still a person: "Sherif
        # Tawfik (Core42)" and "Talal Al Kaissi" are both in this vault under
        # other spellings, and calling them teams is the same misleading label
        # the other way round. Every word that NAMES something has to be in one
        # person's name -- "Core42 Commercial" keeps only "commercial", which
        # nobody is called.
        words = _naming_words(name)
        return bool(words) and any(words <= person for person in about)

    def people_on(self, action: dict) -> list[dict]:
        """Everyone on the thread this action came from -- the addresses the ask
        was actually sent to, which is where a name the owner book does not know
        is usually found."""
        thread = _text(action.get("source_thread"))
        return self._people_on([thread], self._self_email()) if thread else []

    def _people_on(self, threads: list[str], mine: str = "") -> list[dict]:
        """Everyone on those threads, the CBO excluded -- the addresses he sent
        the ask to. Read from each Thread note's own `messages/` folder."""
        index = self._api.vault.index()
        found: list[dict] = []
        for link in threads:
            stem = _text(link).strip("[]")
            entry = index.get(stem)
            if not entry or not entry.get("path"):
                continue
            messages = Path(entry["path"]).parent / "messages"
            if not messages.is_dir():
                continue
            for message in sorted(messages.glob("*.md")):
                try:
                    frontmatter, _ = self._api.vault.read_note(message)
                except OSError:
                    continue
                sent_by_him = _text(frontmatter.get("direction")) == "sent" or (
                    _text(frontmatter.get("sender_email")).lower() == mine)
                # Who the ask was addressed TO, on a message HE sent, is the
                # person expected to act -- "90% he will be in the to"
                # (operator, 2026-09-26). Everyone else on the thread is a
                # weaker guess, and an outsider weaker still.
                pairs = [(_text(frontmatter.get("sender")),
                          _text(frontmatter.get("sender_email")), 2)]
                for address in (frontmatter.get("to_recipients") or []):
                    pairs.append(("", _text(address), 0 if sent_by_him else 1))
                for address in (frontmatter.get("cc_recipients") or []):
                    pairs.append(("", _text(address), 3))
                for name, email, rank in pairs:
                    email = email.lower()
                    if not email or email == mine:
                        continue
                    already = next((p for p in found if p["email"] == email), None)
                    if already:
                        already["rank"] = min(already["rank"], rank)
                        already["seen"] = already.get("seen", 1) + 1
                        continue
                    found.append({"name": name or email.split("@")[0].replace(".", " ").title(),
                                  "email": email, "rank": rank, "seen": 1})
        inside = self._own_domain()
        # Addressed first, then colleagues, then whoever appears most.
        found.sort(key=lambda p: (p["rank"],
                                  not (inside and p["email"].endswith("@" + inside)),
                                  -p.get("seen", 1), p["name"].lower()))
        # `rank` and `seen` are how the order was decided, not something a
        # screen should show. What it can honestly say is that he wrote TO this
        # person, which is the whole reason they are first.
        return [{"name": person["name"], "email": person["email"],
                 "written_to": person["rank"] == 0} for person in found]

    def _own_domain(self) -> str:
        """The company's own mail domain, from his address."""
        return self._self_email().partition("@")[2]

    def self_email(self) -> str:
        """Whose brain this is, for anything outside this class that needs it."""
        return self._self_email()

    def _self_email(self) -> str:
        """Whose brain this is -- never offered back as somebody to chase.

        Read from the Tasks themselves: an action he owns carries his address,
        which the install's capture puts there. The Plugin API has no setting for
        it, and an env var the backend does not happen to carry would silently
        put him in his own list of people to message."""
        counts: dict[str, int] = {}
        for task in self._tasks():
            if task["scope"] == MINE and task["owner_email"]:
                counts[task["owner_email"]] = counts.get(task["owner_email"], 0) + 1
        if not counts:
            import os
            return os.environ.get("SECOND_BRAIN_SELF_EMAIL", "").strip().lower()
        return max(counts.items(), key=lambda pair: pair[1])[0].lower()

    # -- one action, opened ---------------------------------------------------

    def detail(self, stem: str) -> dict | None:
        """One action with its sections, and links to where it came from and to
        what closed it -- each opening the Cockpit for that thread or meeting, so
        the operator can pick the conversation up from there."""
        row = next((t for t in self._tasks() if t["stem"] == stem), None)
        if row is None:
            return None
        path = next(p for p in self._api.vault.notes_in_kind(TASKS_KIND)
                    if getattr(p, "stem", None) == stem)
        _, body = self._api.vault.read_note(path)
        index = self._api.vault.index()
        return {
            **row,
            "ask": _section(body, "Ask"),
            "history": _lines(_section(body, "Evidence")),
            "chases": _lines(_section(body, "Chases")),
            "notes": _lines(_section(body, "Notes")),
            "source_link": _linked(row["source_thread"], index),
            "evidence_link": _linked(row["evidence_source"], index),
        }


def _section(body: str, name: str) -> str:
    lines = str(body or "").splitlines()
    try:
        start = next(i for i, text in enumerate(lines) if text.strip() == f"## {name}")
    except StopIteration:
        return ""
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    return "\n".join(lines[start + 1:end]).strip()


def _lines(text: str) -> list[str]:
    return [line[2:].strip() if line.startswith("- ") else line.strip()
            for line in text.splitlines() if line.strip()]


# The Cockpit a linked note opens in, by the note's own type. Anything else opens
# as a plain note.
_COCKPITS = {"Thread": "/inbox-cockpit/", "Meeting": "/meeting-cockpit/"}


def _linked(link: str | None, index: dict) -> dict | None:
    stem = _text(link).strip("[]")
    if not stem:
        return None
    entry = index.get(stem)
    kind = _text((entry or {}).get("frontmatter", {}).get("type")) if entry else ""
    return {
        "stem": stem,
        "kind": kind or None,
        "found": entry is not None,
        "cockpit": _COCKPITS[kind] + stem if kind in _COCKPITS else None,
        "note": "/browse/" + stem,
    }

def _doubt_row(task: dict) -> dict:
    return {"stem": task["stem"], "subject": task["subject"], "owner": task["owner"],
            "customer": task["customer"], "due": task["due"], "overdue": task["overdue"]}
