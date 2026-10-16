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
- **It does not yet own resolution.** ADR-032 resolves the named
  implementation when the Action is SAVED, not when it is called; that
  check, and the read-side broken-entry status, are REQ-SB-95-US-02-T02's
  own scope and attach to the same seam (`_require_exactly_one_implementation`
  is the only save-time gate here today).

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
    Action,
    ActionImplementation,
    ActionInput,
)
from app.data_access import actions as actions_data


class ActionImplementationCardinalityError(Exception):
    """The payload named no implementation, or more than one."""
    pass


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
        """Raises ActionImplementationCardinalityError BEFORE anything is
        written, so a refused save leaves no half-catalogued Action."""
        self._require_exactly_one_implementation(implementation)
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
        implementation keeps the stored one, which is already known to
        satisfy the rule; a supplied one is held to it afresh."""
        try:
            data = actions_data.read_action_json(action_id)
        except (OSError, ValueError):
            return None

        if implementation is not None:
            self._require_exactly_one_implementation(implementation)
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
