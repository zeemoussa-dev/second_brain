"""What has already been decided about who an owner is.

`Settings/Action-Owners.md` in the App Database Folder, one row per decision.
The install's Hermes Skills write it too, and read it before asking a model, so
a decision made here is what the agents work from next time (operator,
2026-09-24: the things in doubt are "the source of relearning of the agents").

A correction made on this screen is marked `operator`, which outranks a model's
own reading and is never overwritten by one.

The file is Markdown because the operator reads and edits it himself. This
module is the plugin's own reader and writer for it, reached through the Plugin
API's data files -- the same format the Skill writes, kept by the tests on both
sides.
"""
from __future__ import annotations

import re
from datetime import date

BOOK = "Settings/Action-Owners.md"

HEADER = """# Action owners

Who an owner named in an action really is, and where to write to them. The
Action Center's own edits and the owner job both record here; the jobs read it
before asking a model, so a decision made once is not asked again.

| Seen as | Is | Address | Decided | By |
|---|---|---|---|---|
"""

_ROW = re.compile(r"^\|(?P<seen>[^|]*)\|(?P<is>[^|]*)\|(?P<address>[^|]*)\|"
                  r"(?P<decided>[^|]*)\|(?P<by>[^|]*)\|\s*$")


def read(api) -> dict[str, dict]:
    """`{name as seen (lowercased): {...}}`. A missing or hand-mangled file is an
    empty book, never an error: the screen still works, it just knows nothing."""
    try:
        text = api.data.read_text(BOOK) or ""
    except Exception:
        return {}
    decided = {}
    for line in text.splitlines():
        match = _ROW.match(line.strip())
        if not match:
            continue
        seen = match.group("seen").strip()
        if not seen or seen.lower() in ("seen as", "---", ":---"):
            continue
        decided[seen.lower()] = {
            "seen": seen,
            "name": match.group("is").strip(),
            "email": match.group("address").strip().strip("<>"),
            "decided": match.group("decided").strip(),
            "by": match.group("by").strip() or "agent",
        }
    return decided


def record(api, seen: str, name: str, email: str, *, by: str = "operator") -> dict:
    """One decision, replacing any earlier one for the same name."""
    seen, name, email = seen.strip(), name.strip(), email.strip()
    if not seen:
        raise ValueError("a decision needs the name as it was seen")
    decided = read(api)
    decided[seen.lower()] = {"seen": seen, "name": name or seen, "email": email,
                             "decided": date.today().isoformat(), "by": by}
    rows = [f"| {d['seen']} | {d['name']} | {d['email']} | {d['decided']} | {d['by']} |"
            for _, d in sorted(decided.items())]
    api.data.write_text(BOOK, HEADER + "\n".join(rows) + "\n")
    return decided[seen.lower()]
