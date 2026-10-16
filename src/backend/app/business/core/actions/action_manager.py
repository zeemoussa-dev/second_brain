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
- **It does not cache the read side.** resolution_report() recomputes
  every Action's status from those same live sources on every call:
  what an Action points at is undeployed, unmounted or unregistered by
  events this module never sees, so a cached answer would be the
  silent-staleness failure ADR-032's consequences already name.

`get_all()` returns this install's STORED Actions. Plugin-contributed
Actions are composed on top at read time (T05, ADR-022) and are never
written into the store.

Raw I/O lives entirely in `data_access/actions.py` -- this file holds
zero raw file calls, only entity shaping and the cardinality rule.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from app.business.core.actions.action import (
    IMPLEMENTATION_KINDS,
    UI_FEATURE_KEYS,
    Action,
    ActionImplementation,
    ActionInput,
)
from app.business.core.skills.skill_manager import SkillManager
from app.data_access import actions as actions_data


class ActionImplementationCardinalityError(Exception):
    """The payload named no implementation, or more than one."""
    pass


class ActionImplementationUnresolvedError(Exception):
    """The one named implementation does not resolve on this install."""
    pass


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

    def get_all(self) -> list[Action]:
        actions = []
        for action_id in actions_data.list_action_ids():
            try:
                data = actions_data.read_action_json(action_id)
            except (OSError, ValueError):
                continue
            actions.append(self._to_action(action_id, data))
        return actions

    def get_by_id(self, action_id: str) -> Action | None:
        try:
            data = actions_data.read_action_json(action_id)
        except (OSError, ValueError):
            return None
        return self._to_action(action_id, data)

    def create(
        self, action_id: str, *, description: str = "",
        inputs: list[Mapping[str, Any]] | None = None,
        allowed_callers: list[str] | None = None,
        needs_confirmation: bool = False,
        implementation: Mapping[str, Any] | None = None,
    ) -> Action:
        """Raises ActionImplementationCardinalityError or
        ActionImplementationUnresolvedError BEFORE anything is written,
        so a refused save leaves no half-catalogued Action."""
        self._require_resolvable_implementation(implementation)
        definition = {
            "id": action_id,
            "description": description,
            "inputs": self._stored_inputs(inputs),
            "allowed_callers": list(allowed_callers or []),
            "needs_confirmation": bool(needs_confirmation),
            "implementation": dict(implementation),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": None,
        }
        actions_data.write_action_json(action_id, definition)
        return self.get_by_id(action_id)

    def update(
        self, action_id: str, *, description: str | None = None,
        inputs: list[Mapping[str, Any]] | None = None,
        allowed_callers: list[str] | None = None,
        needs_confirmation: bool | None = None,
        implementation: Mapping[str, Any] | None = None,
    ) -> Action | None:
        """`None` (omitted) = leave unchanged for every field, the same
        convention every other Manager's own update() uses. An omitted
        implementation keeps the stored one and is NOT re-resolved here:
        an edit to a description must not be refused because something
        else on the install broke in the meantime -- that is what
        resolution_report() is for. A supplied one is held to both rules
        afresh."""
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

        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        actions_data.write_action_json(action_id, data)
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
        convention)."""
        if self.get_by_id(action_id) is None:
            return {"deleted": False}
        actions_data.delete_action_definition(action_id)
        return {"deleted": True}
