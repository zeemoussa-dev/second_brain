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
- **It owns the publication TRIGGER, not the published text**
  (`REQ-SB-95-US-01-T02`, `ADR-036`). `save()` fires
  `publish_operator_profile_in_background()`, the same shape
  `ActionManager`/`WorkflowManager` use for their own catalogues, so no
  route, script or future caller has to remember a second step --
  editing the Profile IS the whole operation. What the block SAYS, and
  the one-pass/one-reload walk that writes it, are `AgentManager`'s,
  beside the marker blocks it already owns. The routes are `T03`'s.

Raw I/O lives entirely in `data_access/operator_profile.py` -- this file
holds zero path building and zero JSON calls, only entity shaping.
"""
from __future__ import annotations

import logging
import threading
from typing import Any, Mapping

from app.business.core.operator.operator_profile import (
    MirroredOwnAddress,
    OperatorProfile,
    TeamMember,
)
from app.config import settings
from app.data_access import operator_profile as operator_profile_data

_logger = logging.getLogger(__name__)


def publish_operator_profile() -> list[str]:
    """Pushes the operator's facts into every agent's own context,
    blocking, and names the agents whose SOUL.md really changed.

    The one trigger seam, the same shape `ActionManager` and
    `WorkflowManager` use for their catalogues (`ADR-036`). A
    publication that cannot run must not fail the save that triggered
    it: the Profile is already written, nothing is enforced against this
    text, and the next save republishes it -- so the honest failure mode
    is one install's agents describing the operator as they were
    described before, said loudly in the log.

    `AgentManager` is imported inside the function on purpose -- it
    imports this module back to read the Profile it publishes.
    """
    from app.business.core.agents.agent_manager import AgentManager

    try:
        return AgentManager().publish_operator_profile()
    except Exception:
        _logger.warning(
            "the Operator Profile was saved but could not be republished into agent context; "
            "every agent's block is now stale until the next save",
            exc_info=True,
        )
        return []


_background_publications: list[threading.Thread] = []
_background_publications_lock = threading.Lock()


def _publish_into(install: object) -> list[str]:
    """One publication pass, run only if this process is still pointed at
    the install the pass was started for.

    Both halves of "the install" are checked, because this pass spans
    both: it reads the Profile from `second_brain_data_path` and writes
    it into the profiles under `hermes_home_path`. Either can be
    reconfigured while the app runs (`REQ-SB-89`'s setup wizard) and
    nothing waits for a publication pass, so a pass in flight across a
    reconfiguration would otherwise write one operator's name and team
    into another install's agents.
    """
    if (settings.hermes_home_path, settings.second_brain_data_path) != install:
        _logger.warning(
            "an Operator Profile publication was started for the install at %r and this process "
            "is now pointed at %r; it was abandoned rather than published into the second one",
            tuple(str(part) for part in install),
            (str(settings.hermes_home_path), str(settings.second_brain_data_path)),
        )
        return []
    return publish_operator_profile()


def publish_operator_profile_in_background() -> threading.Thread:
    """Starts a republication pass and returns at once, naming the thread
    it started.

    **Saving the Profile must not block on republication** -- the same
    measurement that produced the operator's 2026-10-18 decision for the
    Action catalogue applies unchanged: a roster-wide pass rewrites
    every agent's SOUL.md, which one `PUT /operator/profile` must not
    hold a screen open for. The accepted consequence is that for a few
    seconds after a save an agent's block may still name the old team;
    an agent reads its SOUL.md once per session, not per second.

    Started threads are remembered so a caller that needs the roster to
    have settled can wait (`join_background_publications()`); finished
    ones are dropped on every call, so the list cannot grow with the
    Profile's edit history.
    """
    publication = threading.Thread(
        target=_publish_into,
        args=((settings.hermes_home_path, settings.second_brain_data_path),),
        name="publish-operator-profile",
        daemon=True,
    )
    with _background_publications_lock:
        _background_publications[:] = [t for t in _background_publications if t.is_alive()]
        _background_publications.append(publication)
        # Started while holding the lock so a concurrent joiner can never
        # see a tracked-but-not-yet-started thread, which it would skip as
        # "not alive" and then wrongly report as finished.
        publication.start()
    return publication


def join_background_publications(timeout: float = 30.0) -> bool:
    """Waits for every publication pass already in flight; True when they
    all finished inside `timeout`.

    Nothing on the request path calls this -- the whole point of the
    trigger above is that nothing waits. It is for a caller that needs
    the roster to have settled before looking at it: a test asserting
    what a save really published, rather than what it had published so
    far.
    """
    with _background_publications_lock:
        in_flight = [t for t in _background_publications if t.is_alive()]
    for publication in in_flight:
        publication.join(timeout)
    return not any(t.is_alive() for t in in_flight)


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

        Publication into every agent's context is fired here and nowhere
        else (`REQ-SB-95-US-01-T02`): editing the Profile is the only
        action a human takes, and no route or script has a second step
        to remember. It is fired AFTER the write, so the pass reads the
        record that was just saved, and it is not waited for.
        """
        operator_profile_data.write_profile_json(self._owned_record(payload or {}))
        publish_operator_profile_in_background()
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
