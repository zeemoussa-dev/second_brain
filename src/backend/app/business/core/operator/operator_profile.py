"""OperatorProfile entity -- the singleton record of who this install's
agents act for (ADR-032), plus the one address it MIRRORS rather than
owns (ADR-038). Instance data at data/Operator/Profile.json, never the
repository.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# Where the operator's own address really lives (ADR-038). Published
# with the mirrored value so every reader -- the Profile page, the
# agent-context block, a future API consumer -- can say where to edit it
# without hardcoding the answer a second time.
OWN_ADDRESS_SETTING_KEY = "SELF_EMAIL"
OWN_ADDRESS_EDITED_AT = "Settings > System"


@dataclass
class TeamMember:
    """One colleague, as MEMBERSHIP: the email that reaches their real
    Person note in the vault (notes are filenamed by email), and the
    role they hold. Deliberately no name, title, avatar or description
    -- the vault note is the one place a person is described, and a
    second copy here would only go stale."""
    email: str
    role: str = ""


@dataclass
class MirroredOwnAddress:
    """The operator's own mail address, READ from the `SELF_EMAIL`
    setting and owned by it (ADR-038).

    It carries its own read-only flag and the surface that edits it
    rather than leaving a caller to remember: this value looks exactly
    like the Profile's own fields when it reaches a page or an agent's
    context, and the one thing that must never be guessed about it is
    who may write it.
    """
    email: str = ""
    # Always True. A field rather than a constant because it travels
    # with the value into every reader, including ones that never see
    # this module.
    read_only: bool = True
    setting_key: str = OWN_ADDRESS_SETTING_KEY
    edited_at: str = OWN_ADDRESS_EDITED_AT


@dataclass
class OperatorProfile:
    """One record, read back as one object. A singleton: it carries no
    id, because there is never a second one to tell it apart from.

    `is_configured` is the honest answer to "has this install ever saved
    a Profile?", and it is the reason an unconfigured install does not
    read back as an invented empty record that looks configured.
    Everything downstream -- the agent-context block that must say "no
    Operator Profile is configured" rather than name nobody, the page
    that must offer to create rather than claim to show -- turns on this
    one flag.
    """
    # Everything the Profile OWNS.
    name: str = ""
    # The operator's OTHER addresses. Their own is the mirrored one
    # below and is never in this list.
    other_email_addresses: list[str] = field(default_factory=list)
    timezone: str = ""
    team: list[TeamMember] = field(default_factory=list)
    # Read from the setting on every get(), stored nowhere.
    own_address: MirroredOwnAddress = field(default_factory=MirroredOwnAddress)
    is_configured: bool = False
