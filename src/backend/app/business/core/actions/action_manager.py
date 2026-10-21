"""ActionManager -- the sole gateway onto Action data (same "one real
gateway" rule Section/Agent/Pipeline/Index Managers already follow). An
Action is ADR-032's sixth artifact kind: one invocable operation with an
id, a description, typed inputs carrying required flags, the agent ids
allowed to call it, whether it needs confirmation, and exactly ONE
implementation -- a deployed Skill, a route on this app, or an in-app
feature.

Two rules this file deliberately does and does not own:

- **It owns cardinality.** Zero implementations, or two, is refused here
  with a message naming the rule -- never coerced into a save. The
  refuse-rather-than-ship stance is SkillManager.deploy()'s, which
  refuses on validate_declared_writes problems rather than shipping
  something that only fails when it runs.
- **It owns resolution too, at SAVE time** (ADR-032, added by
  REQ-SB-95-US-02-T02). create() and update() resolve the one named
  implementation against the real source for its kind -- a DEPLOYED
  Skill, a route on this app's live route table, a registered front-end
  feature key -- and refuse naming what did not resolve, before
  anything reaches disk. Resolving at the call instead would let a
  broken Action sit in the catalogue waiting to fail in front of the
  operator, which is the thing ADR-032 exists to prevent. (The call
  gate re-checks as well -- REQ-SB-95-US-03 -- but that is a second
  line, not this one.)
- **It owns the publication trigger, not the published text.**
  `publish_action_catalogue()` below is that trigger (REQ-SB-95-US-03-T01,
  ADR-033); the block itself is AgentManager's, beside the two
  auto-generated ones it already owns. create(), update() and delete()
  each fire it IN THE BACKGROUND and return at once (operator,
  2026-10-18) -- see `publish_action_catalogue_in_background()` for why
  a save must not wait on a roster-wide republication.
- **It owns nothing about Workflows, and asks them one question.**
  `delete()` refuses an Action a Workflow step names, reporting which
  Workflows before anything is removed (REQ-SB-95-US-04-T02, ADR-034).
  The edge is one-directional: no back-reference is stored here, the
  answer is computed by the Workflow side on every delete, and an
  Action.json is byte-identical before and after a Workflow starts
  referencing it.
- **It does not cache the read side.** resolution_report() recomputes
  every Action's status from those same live sources on every call:
  what an Action points at is undeployed, unmounted or unregistered by
  events this module never sees, so a cached answer would be the
  silent-staleness failure ADR-032's consequences already name.

`get_all()` returns this install's STORED Actions with the loaded
plugins' contributed ones composed on top at read time (T05, ADR-022).
A plugin's Action is never written into the store, which is also why
every write path here refuses one: there is nothing of it on disk to
update or delete.

`seed_shipped_starters()` is the third way an Action reaches the
catalogue and the only one that WRITES without the operator asking
(REQ-SB-95-US-03-T05, ADR-032's shipped starters). It installs a
framework-shipped definition this install does not have, never
overwrites one it does, and from then on the result is an ordinary
stored Action -- mirroring `TemplateManager.seed_shipped_masters()`
exactly, including that it is meant to run on every boot.

Raw I/O lives entirely in `data_access/actions.py` -- this file holds
zero raw file calls, only entity shaping and the cardinality rule.
"""
from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from app.business.core.actions import shipped_starters
from app.business.core.actions.action import (
    IMPLEMENTATION_KINDS,
    UI_FEATURE_KEYS,
    Action,
    ActionImplementation,
    ActionInput,
)
from app.business.core.skills.skill_manager import SkillManager
from app.data_access import actions as actions_data

_logger = logging.getLogger(__name__)


@dataclass
class PluginContributedAction(Action):
    """One Action a loaded plugin registered through `app.plugin_api`
    (`ADR-022`), carrying the id of the plugin that contributed it.

    It lives here rather than beside `Action` because it is a property of
    the read-time composition, not of the stored kind: nothing writes one,
    nothing imports or exports one, and a stored Action must keep reading
    back exactly as it did before plugins could contribute at all -- which
    is why a stored one carries no `plugin_id` attribute whatsoever, rather
    than an empty one.
    """
    plugin_id: str = ""


class ActionImplementationCardinalityError(Exception):
    """The payload named no implementation, or more than one."""
    pass


class PluginContributedActionIsReadOnlyError(Exception):
    """A write path named an Action that belongs to a plugin. There is
    nothing stored to change: it is composed while that plugin is loaded
    and gone when it is uninstalled."""
    pass


class ActionImplementationUnresolvedError(Exception):
    """The one named implementation does not resolve on this install."""
    pass


class ActionReferencedByWorkflowError(Exception):
    """A Workflow step names this Action, so deleting it would leave
    that step pointing at nothing (`ADR-034`, `REQ-SB-95-US-04`)."""
    pass


def workflow_ids_referencing_action(action_id: str) -> list[str]:
    """The Workflow side's answer to "who names this Action?", asked
    only at delete time.

    The import is inside the function on purpose. The edge runs ONE
    direction -- `WorkflowManager` imports this module at module scope
    to validate its steps against the catalogue -- so importing it back
    at module scope here would close a cycle. Deferring it is the same
    shape `AgentManager._action_catalogue()` already uses against this
    very module, for the same reason, and it keeps the guard a property
    of `delete()` rather than of whoever remembered to inject a lookup.

    Nothing is stored on either side: an Action still knows nothing
    about Workflows between one delete and the next.
    """
    from app.business.core.workflows.workflow_manager import WorkflowManager

    return WorkflowManager().workflow_ids_referencing_action(action_id)


def deployed_skill_ids() -> set[str]:
    """Skills that are DEPLOYED, not merely catalogued. A catalogued
    Skill with an empty `deployed_to` exists in this repo and in no
    Hermes profile, so an Action pointing at it would resolve on paper
    and fail the moment the runner looked for it."""
    return {skill.id for skill in SkillManager().get_all() if skill.deployed_to}


def _collect_routes(routes: Any, prefix: str, table: set[tuple[str, str]]) -> None:
    """Walks DOWN into included routers and mounted sub-applications.

    This installed FastAPI keeps an included router in `app.routes` as a
    lazy placeholder -- the original router plus the prefix it was
    mounted under -- instead of flattening its endpoints onto the app.
    Reading `app.routes`' own `path` attributes therefore sees the four
    /docs routes and NOTHING else (measured: 4 paths, no /vault-index/
    refresh), so a flat read would refuse every real http implementation
    there is. Prefixes compose on the way down, which is what makes a
    plugin's `/plugins/<plugin_id>/...` route appear at its real path.
    """
    for route in routes or []:
        included = getattr(route, "original_router", None)
        if included is not None:
            context = getattr(route, "include_context", None)
            _collect_routes(
                getattr(included, "routes", None),
                prefix + (getattr(context, "prefix", "") or ""),
                table,
            )
            continue
        path = getattr(route, "path", "")
        if not path:
            continue
        mounted = getattr(route, "routes", None)
        if mounted:
            _collect_routes(mounted, prefix + path, table)
            continue
        for method in getattr(route, "methods", None) or {"GET"}:
            table.add((method.upper(), prefix + path))


def app_route_table() -> set[tuple[str, str]]:
    """(METHOD, path) for every route the RUNNING app exposes, read off
    the live FastAPI app rather than a hand-maintained list -- which is
    also the only way a plugin's routes, mounted under
    `/plugins/<plugin_id>/` during startup, are visible here at all.

    Imported inside the function on purpose: app.main imports the API
    layer, which imports this module, so a module-level import would be
    a cycle and would invert ADR-003's api -> business direction.
    """
    from app.main import app

    table: set[tuple[str, str]] = set()
    _collect_routes(app.routes, "", table)
    return table


def publish_action_catalogue() -> list[str]:
    """Pushes the catalogue into every agent's own context, and names
    the agents whose published block really changed.

    The one trigger seam -- the same shape `SkillManager` uses when it
    calls `publish_section_access_map()` on every deploy and undeploy
    (`ADR-033`). Synchronous and blocking: create/update/delete reach
    it through `publish_action_catalogue_in_background()` below, while
    a caller that genuinely needs the roster republished before it
    continues calls this one directly.

    A publication that cannot run must not fail the save that triggers
    it: the Action is already written, the gate validates against the
    live catalogue and never against the published text, so a block
    left stale here misleads an agent but can never let a call through.
    Logged loudly rather than swallowed.

    `AgentManager` is imported inside the function on purpose -- it
    imports this module back to read the catalogue it publishes.
    """
    from app.business.core.agents.agent_manager import AgentManager

    try:
        return AgentManager().publish_action_catalogue()
    except Exception:
        _logger.warning(
            "the Action catalogue changed but could not be republished into agent context; "
            "every agent's block is now stale until the next catalogue change",
            exc_info=True,
        )
        return []


_background_publications: list[threading.Thread] = []
_background_publications_lock = threading.Lock()


def publish_action_catalogue_in_background() -> threading.Thread:
    """Starts a republication pass and returns at once, naming the
    thread it started.

    **Operator decision, 2026-10-18: saving an Action must not block on
    republication.** Publication goes through `AgentManager.update()`,
    which reloads the Registry per agent -- measured at ~2.7s each, so
    one `allowed_callers: ["*"]` Action would otherwise hold a save open
    for ~110s across a 41-profile install. The accepted consequence is
    that for a few seconds after a save an agent's SOUL.md may still
    name the old catalogue; an agent reads it once per conversation, not
    per second, and `ADR-033`'s gate reads the live catalogue and never
    this text, so the window can mislead but can never let a call
    through.

    Same shape as the vault index rebuild this app already fires and
    never waits for (`main.py`'s `asyncio.to_thread(rebuild_index)`):
    the blocking, I/O-heavy pass runs on a worker thread and nothing
    joins it. A plain thread rather than that call's
    `asyncio.create_task` wrapper because this is reached from
    synchronous code -- a `def` route handler already running in
    Starlette's own threadpool has no event loop of its own to schedule
    onto.

    Started threads are remembered so a process that is about to be
    reconfigured can wait for the passes already in flight
    (`join_background_publications()`); finished ones are dropped on
    every call, so the list cannot grow with the catalogue's history.
    """
    publication = threading.Thread(
        target=publish_action_catalogue,
        name="publish-action-catalogue",
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
    """Waits for every publication pass already in flight; True when
    they all finished inside `timeout`.

    Nothing on the request path calls this -- the whole point of the
    decision above is that nothing waits. It exists for the callers for
    which an in-flight pass is a hazard rather than a nicety: the test
    suite, whose Hermes sandbox is torn down per test, so a pass
    outliving it would come back to life pointed at the operator's real
    install.
    """
    with _background_publications_lock:
        in_flight = [t for t in _background_publications if t.is_alive()]
    for publication in in_flight:
        publication.join(timeout)
    return not any(t.is_alive() for t in in_flight)


class _ResolutionSources:
    """The live sources, gathered ONCE per save or per report. Reading
    them per Action would re-list every Skill and re-walk the route
    table for each catalogue entry -- the same O(n x sources) shape
    SkillManager.check_deployment_drift() already caches per profile to
    avoid. Short-lived by construction: a new instance per call, never
    held, so nothing here is a cache across calls."""

    def __init__(self) -> None:
        self.deployed_skill_ids = deployed_skill_ids()
        self.app_route_table = app_route_table()
        self.ui_feature_keys = set(UI_FEATURE_KEYS)

    def unresolved_reason(self, kind: str, spec: Mapping[str, Any] | None) -> str | None:
        """None when it resolves; otherwise a sentence naming exactly
        what did not -- the operator has to be able to act on the
        refusal without opening the catalogue file."""
        spec = spec or {}
        if kind == "skill":
            skill_id = spec.get("skill_id", "")
            if skill_id not in self.deployed_skill_ids:
                return f"skill {skill_id!r} is not deployed on this install"
            return None
        if kind == "http":
            # An http implementation that omits its method is a GET, the
            # same default the route table itself falls back to.
            method = (spec.get("method") or "GET").upper()
            path = spec.get("path", "")
            if (method, path) not in self.app_route_table:
                return f"http route {method} {path!r} is not on this app's route table"
            return None
        feature_key = spec.get("feature_key", "")
        if feature_key not in self.ui_feature_keys:
            return f"ui feature key {feature_key!r} is not registered in this app's front end"
        return None


class ActionManager:
    @staticmethod
    def is_callable_by(action: Action, agent_id: str) -> bool:
        """Whether one agent id may call one Action. Lives here because
        `allowed_callers` is Action data: publication filters a whole
        catalogue down to one agent with it, and the call gate asks the
        same question of one call, so the two can never drift into
        disagreeing about what `["*"]` means (`ADR-033`: the wildcard is
        every agent, an empty list is nobody, and the id IS the Hermes
        profile id)."""
        return "*" in action.allowed_callers or agent_id in action.allowed_callers

    @staticmethod
    def _require_exactly_one_implementation(implementation: Mapping[str, Any] | None) -> str:
        """The stored `implementation` object is keyed BY kind, so "exactly
        one" is a property of the saved file itself rather than of the
        route that wrote it -- which is what lets create(), update() and
        import_action() share one rule and one message."""
        named = [kind for kind in IMPLEMENTATION_KINDS if (implementation or {}).get(kind) is not None]
        if len(named) != 1:
            named_description = ", ".join(named) if named else "none"
            raise ActionImplementationCardinalityError(
                "an Action has exactly one implementation -- one of skill, http or ui, "
                f"never zero and never two; this one names {named_description}"
            )
        return named[0]

    @staticmethod
    def _require_resolvable_implementation(implementation: Mapping[str, Any] | None) -> str:
        """Cardinality first, then resolution -- a payload naming two
        implementations has no single thing to resolve, so asking "does
        it resolve?" of it would produce a misleading answer to the
        wrong question.

        Raises before the caller writes anything, which is what makes
        AC-02's "no Action.json is created or changed on disk" a
        property of this method rather than of each write path.
        """
        kind = ActionManager._require_exactly_one_implementation(implementation)
        reason = _ResolutionSources().unresolved_reason(kind, (implementation or {}).get(kind))
        if reason is not None:
            raise ActionImplementationUnresolvedError(
                f"this Action's {kind} implementation does not resolve on this install: {reason}"
            )
        return kind

    def resolution_report(self) -> list[dict]:
        """Which catalogued Actions still resolve, and what no longer
        does for the ones that do not -- a flat list of dicts, one per
        Action, the same shape SkillManager.check_deployment_drift()
        returns.

        Computed fresh on every call, never cached and never written
        into Action.json: an Action breaks when something ELSE changes
        (a Skill is undeployed, a route is removed, a plugin is
        uninstalled), so a stored status would be wrong from the moment
        it was stored. Nothing here calls an Action to find out.
        """
        sources = _ResolutionSources()
        report: list[dict] = []
        for action in self.get_all():
            implementation = action.implementation
            if implementation is None:
                kind, reason = None, "this Action names no implementation"
            else:
                kind = implementation.kind
                reason = sources.unresolved_reason(kind, {
                    "skill_id": implementation.skill_id,
                    "method": implementation.method,
                    "path": implementation.path,
                    "feature_key": implementation.feature_key,
                })
            report.append({
                "action_id": action.id,
                "implementation_kind": kind,
                "status": "resolves" if reason is None else "broken",
                "reason": reason,
            })
        return report

    @staticmethod
    def _to_implementation(stored: Mapping[str, Any] | None) -> ActionImplementation | None:
        """Read-side only, and deliberately forgiving: a definition that
        somehow holds no implementation reads back as None rather than
        raising, so one bad entry can never make the whole catalogue
        unreadable. The save path is what guarantees it cannot happen."""
        for kind in IMPLEMENTATION_KINDS:
            spec = (stored or {}).get(kind)
            if spec is None:
                continue
            return ActionImplementation(
                kind=kind,
                skill_id=spec.get("skill_id", ""),
                method=spec.get("method", ""),
                path=spec.get("path", ""),
                feature_key=spec.get("feature_key", ""),
            )
        return None

    @staticmethod
    def _to_inputs(stored: list | None) -> list[ActionInput]:
        return [
            ActionInput(
                name=entry["name"],
                type=entry.get("type") or "string",
                required=bool(entry.get("required", False)),
                description=entry.get("description", ""),
            )
            for entry in (stored or [])
        ]

    def _to_action(self, action_id: str, data: Mapping[str, Any]) -> Action:
        return Action(
            id=action_id,
            description=data.get("description", ""),
            inputs=self._to_inputs(data.get("inputs")),
            allowed_callers=list(data.get("allowed_callers") or []),
            needs_confirmation=bool(data.get("needs_confirmation", False)),
            is_blocked=bool(data.get("is_blocked", False)),
            blocked_reason=str(data.get("blocked_reason", "") or ""),
            implementation=self._to_implementation(data.get("implementation")),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at"),
        )

    @staticmethod
    def _stored_inputs(inputs: list[Mapping[str, Any]] | None) -> list[dict]:
        """Every declared input is stored in full, including a `required`
        that happens to be False -- an absent flag and an explicitly
        optional one must not read back as the same thing to the call
        gate that later asks "was this one required?"."""
        return [
            {
                "name": entry["name"],
                "type": entry.get("type") or "string",
                "required": bool(entry.get("required", False)),
                "description": entry.get("description", ""),
            }
            for entry in (inputs or [])
        ]

    def _plugin_contributed(self) -> list[PluginContributedAction]:
        """What the loaded plugins registered, shaped into Actions and
        attributed to them (T05, ADR-022). Composed on every read and
        written nowhere, which is what makes "uninstalling a plugin removes
        its Actions" true by construction rather than by a cleanup step.

        The install's own stored ids win a collision, and the first plugin
        to register an id wins against a later one: a plugin may add to the
        catalogue, never replace an entry the operator saved or another
        plugin already contributed. A dropped one is logged, because two
        plugins silently disagreeing about an id is exactly the kind of
        thing nobody would otherwise discover.
        """
        # Imported here, not at module scope: the plugin manager imports
        # `app.plugin_api`, which reaches into business/ -- the same cycle
        # `plugin_api.get_service` avoids in the other direction.
        from app.business.core.plugins.plugin_manager import PluginManager

        taken = set(actions_data.list_action_ids())
        composed: list[PluginContributedAction] = []
        for definition in PluginManager().get_actions():
            action_id = str(definition.get("id") or "")
            plugin_id = str(definition.get("plugin_id") or "")
            if not action_id or action_id in taken:
                _logger.warning(
                    "plugin %r contributes action %r, which this install already has; the plugin's is ignored",
                    plugin_id, action_id,
                )
                continue
            taken.add(action_id)
            # Parsed by the very reader a stored definition goes through,
            # so a plugin's Action can never reach the catalogue in a shape
            # the catalogue cannot show.
            as_stored = self._to_action(action_id, definition)
            composed.append(PluginContributedAction(**vars(as_stored), plugin_id=plugin_id))
        return composed

    def _refuse_if_plugin_contributed(self, action_id: str) -> None:
        """Guards every write path. Checked against the composed list and
        not against the store, so an id the install really has stored is
        never refused -- a stored id is not a plugin-contributed one."""
        for action in self._plugin_contributed():
            if action.id == action_id:
                raise PluginContributedActionIsReadOnlyError(
                    f"action {action_id!r} belongs to the {action.plugin_id!r} plugin and cannot be "
                    "changed here -- it is contributed while that plugin is loaded and nothing about "
                    "it is stored on this install"
                )

    @staticmethod
    def _refuse_if_referenced_by_a_workflow(action_id: str) -> None:
        """Guards deletion only. Creating or editing an Action cannot
        orphan a step -- a step names an id, so only the id going away
        breaks one.

        The sentence names every referencing Workflow rather than the
        first: the operator has to clear all of them to delete the
        Action, and being told them one refusal at a time is the same
        drip-feed a half-validated save would be.
        """
        referencing = workflow_ids_referencing_action(action_id)
        if not referencing:
            return
        named = ", ".join(repr(workflow_id) for workflow_id in referencing)
        kind_word = "workflow" if len(referencing) == 1 else "workflows"
        raise ActionReferencedByWorkflowError(
            f"action {action_id!r} was not deleted: it is a step of {kind_word} {named}. Remove "
            "the step from each first, so no documented handling is left pointing at nothing"
        )

    def get_all(self) -> list[Action]:
        """This install's stored Actions, plus whatever the loaded plugins
        contributed -- one catalogue, with each plugin entry carrying the
        plugin id that registered it (AC-06)."""
        actions = []
        for action_id in actions_data.list_action_ids():
            try:
                data = actions_data.read_action_json(action_id)
            except (OSError, ValueError):
                continue
            actions.append(self._to_action(action_id, data))
        actions.extend(self._plugin_contributed())
        return actions

    def get_by_id(self, action_id: str) -> Action | None:
        """A stored Action, or a plugin-contributed one -- the catalogue is
        one catalogue on the read side too. Stored first: the store is the
        only thing a write path can act on."""
        try:
            data = actions_data.read_action_json(action_id)
        except (OSError, ValueError):
            return next((action for action in self._plugin_contributed() if action.id == action_id), None)
        return self._to_action(action_id, data)

    def seed_shipped_starters(self) -> dict:
        """Installs every shipped starter Action this install does not
        already have (`ADR-032`). Returns {"seeded": [...], "kept": [...]},
        the same answer `TemplateManager.seed_shipped_masters()` gives.

        **Never overwrites.** An id already in the store is left exactly
        as it is, whatever it now holds: the operator's own edit to a
        starter outranks the shipped copy, and a seed that runs on every
        boot would otherwise silently revert their change on every
        restart.

        **Seeded, not composed on read.** A starter becomes an ordinary
        stored Action the operator can edit, export and delete -- which a
        read-time composition (the shape a plugin's Action uses) could
        not offer, since there would be no file of its own to change.

        Shape is validated the way `import_action` validates an incoming
        definition -- cardinality plus a round-trip through the read-side
        parser -- but resolution deliberately is NOT: a starter must not
        fail to install because of what this install has deployed today.
        `resolution_report()` is where a starter that points at something
        missing shows up, and the call gate refuses it by name.

        Publication is fired only when something really was seeded, and
        in the background, for the reason create/update/delete already
        do: a roster-wide republication must not hold up whatever
        triggered it.
        """
        existing = set(actions_data.list_action_ids())
        seeded: list[str] = []
        kept: list[str] = []
        for action_id in shipped_starters.list_shipped_starter_ids():
            if action_id in existing:
                kept.append(action_id)
                continue
            definition = {
                **shipped_starters.read_shipped_starter_json(action_id),
                "id": action_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": None,
            }
            self._require_exactly_one_implementation(definition.get("implementation"))
            self._to_action(action_id, definition)
            actions_data.write_action_json(action_id, definition)
            seeded.append(action_id)
        if seeded:
            publish_action_catalogue_in_background()
        return {"seeded": seeded, "kept": kept}

    def create(
        self, action_id: str, *, description: str = "",
        inputs: list[Mapping[str, Any]] | None = None,
        allowed_callers: list[str] | None = None,
        needs_confirmation: bool = False,
        implementation: Mapping[str, Any] | None = None,
    ) -> Action:
        """Raises ActionImplementationCardinalityError or
        ActionImplementationUnresolvedError BEFORE anything is written,
        so a refused save leaves no half-catalogued Action.

        Republication is fired only once the write has really happened,
        so a refused save never pushes a catalogue the operator does not
        have into any agent's SOUL.md."""
        self._require_resolvable_implementation(implementation)
        definition = {
            "id": action_id,
            "description": description,
            "inputs": self._stored_inputs(inputs),
            "allowed_callers": list(allowed_callers or []),
            "needs_confirmation": bool(needs_confirmation),
            "is_blocked": False,
            "blocked_reason": "",
            "implementation": dict(implementation),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": None,
        }
        actions_data.write_action_json(action_id, definition)
        publish_action_catalogue_in_background()
        return self.get_by_id(action_id)

    def update(
        self, action_id: str, *, description: str | None = None,
        inputs: list[Mapping[str, Any]] | None = None,
        allowed_callers: list[str] | None = None,
        needs_confirmation: bool | None = None,
        is_blocked: bool | None = None,
        blocked_reason: str | None = None,
        implementation: Mapping[str, Any] | None = None,
    ) -> Action | None:
        """`None` (omitted) = leave unchanged for every field, the same
        convention every other Manager's own update() uses. An omitted
        implementation keeps the stored one and is NOT re-resolved here:
        an edit to a description must not be refused because something
        else on the install broke in the meantime -- that is what
        resolution_report() is for. A supplied one is held to both rules
        afresh. A plugin's Action is refused outright -- there is no file
        of its own to edit, and editing the plugin's registration is the
        plugin's business."""
        self._refuse_if_plugin_contributed(action_id)
        try:
            data = actions_data.read_action_json(action_id)
        except (OSError, ValueError):
            return None

        if implementation is not None:
            self._require_resolvable_implementation(implementation)
            data["implementation"] = dict(implementation)
        if description is not None:
            data["description"] = description
        if inputs is not None:
            data["inputs"] = self._stored_inputs(inputs)
        if allowed_callers is not None:
            data["allowed_callers"] = list(allowed_callers)
        if needs_confirmation is not None:
            data["needs_confirmation"] = bool(needs_confirmation)
        if is_blocked is not None:
            data["is_blocked"] = bool(is_blocked)
        if blocked_reason is not None:
            data["blocked_reason"] = str(blocked_reason)

        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        actions_data.write_action_json(action_id, data)
        publish_action_catalogue_in_background()
        return self.get_by_id(action_id)

    def import_action(self, action_id: str, data: Mapping[str, Any]) -> Action:
        """Real, narrowly-scoped write path for import provisioning
        (ADR-015), mirroring PipelineManager.import_pipeline and
        IndexManager.import_index. Validates by holding the incoming
        definition to the SAME cardinality rule and round-tripping it
        through the existing read-side parser, so a malformed shape
        raises before anything reaches disk."""
        definition = {**data, "id": action_id}
        self._require_exactly_one_implementation(definition.get("implementation"))
        self._to_action(action_id, definition)
        actions_data.write_action_json(action_id, definition)
        return self.get_by_id(action_id)

    def delete(self, action_id: str) -> dict:
        """Never raises for an already-deleted/unknown id --
        {"deleted": False} instead (ADR-014's own result-dict
        convention). A plugin's Action is the one case that does raise:
        reporting it deleted would be a lie the operator acts on, and
        reporting it absent would deny a row they are looking at.

        A Workflow step naming this Action is the second case that
        raises (`ADR-034`, `US-04` Scenario 6): the operator is told
        which Workflows reference it and NOTHING is removed, because the
        alternative is a documented handling that silently points at a
        capability this install no longer has. The question is asked of
        the Workflow side every time and answered from nothing stored
        here.

        Asked only once the id is known to exist: an id this install
        never had deletes nothing, so scanning every Workflow for it
        would be a cost paid to refuse nothing.
        """
        self._refuse_if_plugin_contributed(action_id)
        if self.get_by_id(action_id) is None:
            return {"deleted": False}
        self._refuse_if_referenced_by_a_workflow(action_id)
        actions_data.delete_action_definition(action_id)
        # Only on a real deletion: a {"deleted": False} for an id this
        # install never had changed no catalogue, so republishing on it
        # would rewrite every agent's SOUL.md for nothing.
        publish_action_catalogue_in_background()
        return {"deleted": True}
