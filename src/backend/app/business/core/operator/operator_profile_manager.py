"""OperatorProfileManager -- the sole gateway onto the Operator Profile
(the same "one real gateway" rule Section/Agent/Pipeline/Index/Action
Managers already follow), and deliberately the smallest of them.

**A singleton, not a catalogue** (ADR-032). Its whole public surface is
`get()` and `save()`: no `get_all`, no `create`, no `delete`, no id
parameter anywhere. There is one record, so there is nothing to list,
nothing to tell apart, and no half of the app that could be looking at
a different one.

Three rules this file owns, and one it refuses to own:

- **It owns the shape.** `save()` reads ONLY the four fields the Profile
  owns out of whatever payload it is given and drops everything else on
  the floor. That is what makes "a team entry is an email and a role and
  nothing else" (ADR-032's membership-not-copies) a property of the
  store rather than of each caller's good behaviour -- and it is what
  makes the mirrored own address unpersistable no matter what a payload
  asks for.
- **It owns "unconfigured".** An install that has never saved reads back
  as `is_configured=False` with empty fields, never as an invented empty
  record that looks configured. The agent-context block has to be able
  to say "no Operator Profile is configured" rather than confidently
  name nobody (`US-01` Scenario 5), and that honesty has to come from
  here -- `data_access/operator_profile.py` reports an absent file and
  nothing more.
- **It owns the mirror, and only as a READ** (ADR-038). `get()` returns
  the operator's own address from the live `SELF_EMAIL` setting, flagged
  read-only and naming the surface that edits it. Nothing in this module
  writes that value: it is not in the saved record, `save()` cannot be
  made to put it there, and nothing here calls
  `setup_wizard.sync_settings_to_hermes(...)`. Changing the setting on
  Settings > System changes what the next `get()` returns, with no save
  in between.
- **It does not own the publication.** Pushing these facts into every
  agent's SOUL.md is `REQ-SB-95-US-01-T02`'s, beside the marker blocks
  AgentManager already owns, and the routes are `T03`'s.

Raw I/O lives entirely in `data_access/operator_profile.py` -- this file
holds zero path building and zero JSON calls, only entity shaping.
"""
from __future__ import annotations

from typing import Any, Mapping

from app.business.core.operator.operator_profile import (
    MirroredOwnAddress,
    OperatorProfile,
    TeamMember,
)
from app.config import settings
from app.data_access import operator_profile as operator_profile_data


class OperatorProfileManager:

    def get(self) -> OperatorProfile:
        """The one record, with the mirrored own address composed on
        top. Both halves are read fresh every time: the setting is not
        copied into the record, so the only way they can be shown as one
        coherent profile is to read both at the moment of asking."""
        stored = self._stored_record()
        record = stored or {}
        return OperatorProfile(
            name=self._text(record.get("name")),
            other_email_addresses=self._addresses(record.get("other_email_addresses")),
            timezone=self._text(record.get("timezone")),
            team=self._team(record.get("team")),
            own_address=self._mirrored_own_address(),
            is_configured=stored is not None,
        )

    def save(self, payload: Mapping[str, Any] | None = None) -> OperatorProfile:
        """Replaces the one record and returns it as `get()` would.

        A payload is read for the four owned fields and for nothing
        else, so a caller that sends the operator's own address, an id,
        a colleague's name or anything else simply does not have it
        stored. Refusing those instead would make the Profile's own
        guarantee depend on every caller being validated separately;
        dropping them makes it true of the file.
        """
        operator_profile_data.write_profile_json(self._owned_record(payload or {}))
        return self.get()

    @staticmethod
    def _text(value: Any) -> str:
        return str(value) if value is not None else ""

    @classmethod
    def _addresses(cls, value: Any) -> list[str]:
        """Order is preserved exactly as given: the operator's list is a
        list they wrote, not a set the app may reorder."""
        return [address for address in (cls._text(entry).strip() for entry in (value or [])) if address]

    @classmethod
    def _team(cls, value: Any) -> list[TeamMember]:
        """An entry with no email is dropped rather than stored empty --
        the email IS the join key onto the real Person note, so an entry
        without one is membership in nothing and could never resolve."""
        members = []
        for entry in (value or []):
            fields = entry if isinstance(entry, Mapping) else {}
            email = cls._text(fields.get("email")).strip()
            if not email:
                continue
            members.append(TeamMember(email=email, role=cls._text(fields.get("role")).strip()))
        return members

    @staticmethod
    def _stored_record() -> dict | None:
        """None means this install has never saved a Profile -- the one
        signal `is_configured` is built from. A record that exists but
        cannot be read back is reported the same way on purpose: naming
        a team from a file nobody could parse is the invention this
        whole flag exists to prevent."""
        if not operator_profile_data.profile_exists():
            return None
        try:
            return operator_profile_data.read_profile_json()
        except (OSError, ValueError):
            return None

    @classmethod
    def _owned_record(cls, payload: Mapping[str, Any]) -> dict:
        """Exactly what goes to disk. Every key here is a field the
        Profile owns; the operator's own address is absent because the
        setting owns it (ADR-038), and a team entry is reduced to its
        two membership fields because the vault's Person note owns the
        rest (ADR-032)."""
        return {
            "name": cls._text(payload.get("name")),
            "other_email_addresses": cls._addresses(payload.get("other_email_addresses")),
            "timezone": cls._text(payload.get("timezone")),
            "team": [{"email": member.email, "role": member.role} for member in cls._team(payload.get("team"))],
        }

    @staticmethod
    def _mirrored_own_address() -> MirroredOwnAddress:
        """Read from the live setting at the moment of asking, never
        held and never persisted (ADR-038)."""
        return MirroredOwnAddress(email=settings.self_email or "")
