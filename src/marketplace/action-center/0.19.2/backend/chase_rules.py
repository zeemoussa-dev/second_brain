"""What the chasing agent is allowed to do without being asked each time.

One rule so far, and it exists because chasing is on its way to running
unattended (operator, 2026-09-26: "for now only send to internal people ... we
can uncheck this later"). Pressing the button is a decision about one email; a
job that fires on a schedule is a standing permission, and the first thing worth
bounding is WHO an agent may write to with nobody watching.

**Internal** means the CBO's own mail domain -- taken from his address, never
typed in here, so an install for somebody else is internal to their own company
and not to Core42.

The rule is stored with the plugin's data and read by BOTH halves: this screen,
which greys out an address it would refuse, and the Skill the cron job runs,
which refuses it whoever asks. A rule only the screen honours is not a rule --
the autonomous path is exactly where it has to hold.
"""
from __future__ import annotations

import json

SETTINGS = "data/ActionChase/settings.json"


def _text(value) -> str:
    return str(value or "").strip()


def internal_domains(view) -> list[str]:
    """The domains that count as inside the company: the CBO's own.

    Taken from the view, which reads his address off the actions he owns --
    NOT from `SECOND_BRAIN_SELF_EMAIL`, which the backend does not happen to
    carry. Read from the environment this returned nothing, so every colleague
    counted as an outsider and the rule held back every chase there is."""
    domain = _text(view.self_email()).lower().partition("@")[2]
    return [domain] if domain else []


def read(view) -> dict:
    """`{"internal_only": bool, "domains": [...]}`. Unreadable settings mean the
    careful answer, not an error: internal only."""
    try:
        stored = json.loads(view.api.data.read_text(SETTINGS) or "{}")
    except Exception:
        stored = {}
    return {"internal_only": bool(stored.get("internal_only", True)),
            "domains": internal_domains(view)}


def save(view, internal_only: bool) -> dict:
    view.api.data.write_text(SETTINGS, json.dumps({"internal_only": bool(internal_only)}, indent=2))
    return read(view)


def is_internal(address: str, domains: list[str]) -> bool:
    at = _text(address).lower().partition("@")[2]
    return bool(at) and at in domains


def allowed(view, addresses: list[str]) -> tuple[list[str], list[str]]:
    """`(may be written to, held back)` under the rule as it stands."""
    rule = read(view)
    if not rule["internal_only"]:
        return list(addresses), []
    may, held = [], []
    for address in addresses:
        (may if is_internal(address, rule["domains"]) else held).append(address)
    return may, held
