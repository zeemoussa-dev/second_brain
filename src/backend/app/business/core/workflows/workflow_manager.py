"""WorkflowManager -- the sole gateway onto Workflow data (the same "one
real gateway" rule Section/Agent/Pipeline/Index/Action Managers already
follow). A Workflow is `ADR-032`'s seventh artifact kind: one kind of
request, the ordered steps the operator documented for it -- each naming
a catalogued Action, carrying that step's inputs and its own
confirmation flag -- and what is reported back.

What this file owns, and what it deliberately does not:

- **It owns order.** Steps are a list, written in the order given and
  read back in the order stored, on every path. Nothing here sorts,
  de-duplicates or normalises them: the order IS the operator's
  documented handling, so re-ordering it would change what the Workflow
  means. `ADR-034` then makes "in order" and "no skipped step"
  properties of the run record rather than promises by a model, which
  only works if the stored order is exactly what was saved.
- **It owns stable step identity.** A step keeps the id it was given and
  is minted one when it has none, unique within the Workflow and never
  derived from position -- see `_identified_steps`.
- **It does not own referential integrity.** Whether a step's
  `action_id` is really in the catalogue is checked at save by
  `REQ-SB-95-US-04-T02`, which is where the refusal naming the step and
  the unknown id belongs. This task stores what it is given, in order.
- **It does not own runs.** Starting a run, handing back one step at a
  time and composing the report from recorded outcomes are `T05`'s, over
  their own `WorkflowRuns/` store (`ADR-034`). A Workflow is the
  definition; a run is what happened once.
- **It does not publish.** Telling agents which Workflows exist is
  `T06`'s. Unlike `ActionManager`, no write path here fires a
  republication -- adding one before the published block exists would be
  a trigger onto nothing.

**Nothing here is shared with `Pipeline`** (`ADR-032`, `US-04` Scenario
7). `PipelineManager` is the nearest step-based shape and was read as
reference only: no import, no shared store, no migration, no
re-labelling. A Workflow is intent-triggered; a Pipeline is
time-triggered and keeps its own cron, its own store and its own
Manager, untouched.

Raw I/O lives entirely in `data_access/workflows.py` -- this file holds
zero raw file calls, only entity shaping and step identity.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import uuid4

from app.business.core.workflows.workflow import (
    Workflow,
    WorkflowReport,
    WorkflowStep,
)
from app.data_access import workflows as workflows_data

_logger = logging.getLogger(__name__)


class WorkflowManager:
    @staticmethod
    def _mint_step_id() -> str:
        """Random, not positional: `step-2` would mean a different step
        after every reorder, and a run addressing steps by id would then
        record step 2's outcome against whatever had moved into second
        place."""
        return f"step-{uuid4().hex[:8]}"

    @classmethod
    def _identified_steps(cls, steps: list[Mapping[str, Any]] | None) -> list[dict]:
        """The steps as stored: same order, every one carrying an id that
        is unique within this Workflow.

        A supplied id is kept verbatim -- that is how a reorder save
        keeps pointing at the same steps, and how a run started before
        the save still names steps the Workflow holds. An absent one is
        minted. A *colliding* one is also minted rather than refused: two
        steps sharing an id is an already-ambiguous instruction, and
        failing the whole save over it would lose the other steps the
        operator authored, while keeping both would make one of them
        unaddressable at run time. Logged, because a silently re-keyed
        step is otherwise invisible.
        """
        identified: list[dict] = []
        taken: set[str] = set()
        for step in steps or []:
            step_id = str(step.get("id") or "")
            if not step_id or step_id in taken:
                if step_id:
                    _logger.warning(
                        "workflow step id %r is used by more than one step; this one was given a new id",
                        step_id,
                    )
                step_id = cls._mint_step_id()
            taken.add(step_id)
            identified.append({
                "id": step_id,
                "action_id": step.get("action_id", ""),
                "inputs": dict(step.get("inputs") or {}),
                "needs_confirmation": bool(step.get("needs_confirmation", False)),
                "description": step.get("description", ""),
            })
        return identified

    @staticmethod
    def _stored_report(report: Mapping[str, Any] | None) -> dict:
        """A report definition is always stored in full, including an
        empty `include_step_ids` -- "every step" and "a list that happens
        to be empty today" must not read back as different things to the
        run engine composing the report."""
        return {
            "description": (report or {}).get("description", ""),
            "include_step_ids": list((report or {}).get("include_step_ids") or []),
        }

    @staticmethod
    def _to_steps(stored: list | None) -> list[WorkflowStep]:
        """Read side, in stored order. A step that somehow carries no id
        reads back with a minted one rather than raising, so one hand-
        edited file can never make the whole Workflow unreadable -- the
        save paths are what guarantee it should not happen."""
        return [
            WorkflowStep(
                id=str(entry.get("id") or WorkflowManager._mint_step_id()),
                action_id=entry.get("action_id", ""),
                inputs=dict(entry.get("inputs") or {}),
                needs_confirmation=bool(entry.get("needs_confirmation", False)),
                description=entry.get("description", ""),
            )
            for entry in (stored or [])
        ]

    @staticmethod
    def _to_report(stored: Mapping[str, Any] | None) -> WorkflowReport:
        return WorkflowReport(
            description=(stored or {}).get("description", ""),
            include_step_ids=list((stored or {}).get("include_step_ids") or []),
        )

    def _to_workflow(self, workflow_id: str, data: Mapping[str, Any]) -> Workflow:
        return Workflow(
            id=workflow_id,
            request_kind=data.get("request_kind", ""),
            description=data.get("description", ""),
            steps=self._to_steps(data.get("steps")),
            report=self._to_report(data.get("report")),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at"),
        )

    def get_all(self) -> list[Workflow]:
        """Every Workflow this install has stored. An unreadable
        definition is skipped rather than fatal, the same way
        `ActionManager.get_all()` treats one: a single bad file must not
        hide the catalogue."""
        workflows: list[Workflow] = []
        for workflow_id in workflows_data.list_workflow_ids():
            try:
                data = workflows_data.read_workflow_json(workflow_id)
            except (OSError, ValueError):
                continue
            workflows.append(self._to_workflow(workflow_id, data))
        return workflows

    def get_by_id(self, workflow_id: str) -> Workflow | None:
        try:
            data = workflows_data.read_workflow_json(workflow_id)
        except (OSError, ValueError):
            return None
        return self._to_workflow(workflow_id, data)

    def create(
        self, workflow_id: str, *, request_kind: str = "", description: str = "",
        steps: list[Mapping[str, Any]] | None = None,
        report: Mapping[str, Any] | None = None,
    ) -> Workflow:
        definition = {
            "id": workflow_id,
            "request_kind": request_kind,
            "description": description,
            "steps": self._identified_steps(steps),
            "report": self._stored_report(report),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": None,
        }
        workflows_data.write_workflow_json(workflow_id, definition)
        return self.get_by_id(workflow_id)

    def update(
        self, workflow_id: str, *, request_kind: str | None = None,
        description: str | None = None,
        steps: list[Mapping[str, Any]] | None = None,
        report: Mapping[str, Any] | None = None,
    ) -> Workflow | None:
        """`None` (omitted) = leave unchanged for every field, the same
        convention every other Manager's own update() uses.

        A supplied `steps` REPLACES the stored list wholesale, in the
        order given -- that is what a reorder is. There is no merge by
        step id: merging would have to decide what an absent step meant,
        and "the operator deleted it" and "the caller only sent the ones
        it changed" are indistinguishable from here.
        """
        try:
            data = workflows_data.read_workflow_json(workflow_id)
        except (OSError, ValueError):
            return None

        if request_kind is not None:
            data["request_kind"] = request_kind
        if description is not None:
            data["description"] = description
        if steps is not None:
            data["steps"] = self._identified_steps(steps)
        if report is not None:
            data["report"] = self._stored_report(report)

        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        workflows_data.write_workflow_json(workflow_id, data)
        return self.get_by_id(workflow_id)

    def import_workflow(self, workflow_id: str, data: Mapping[str, Any]) -> Workflow:
        """Real, narrowly-scoped write path for import provisioning
        (`ADR-015`), mirroring `ActionManager.import_action` and
        `PipelineManager.import_pipeline`. Validates by round-tripping
        the incoming definition through the read-side parser, so a
        malformed shape raises before anything reaches disk, and
        re-identifies the steps so an imported Workflow can never arrive
        holding two steps with one id.

        Step order arrives as the exporting machine wrote it and is kept
        exactly: a bundle that reordered an operator's documented
        handling on the way in would be the same silent corruption as
        reordering it on save.
        """
        definition = {
            **data,
            "id": workflow_id,
            "steps": self._identified_steps(data.get("steps")),
            "report": self._stored_report(data.get("report")),
        }
        self._to_workflow(workflow_id, definition)
        workflows_data.write_workflow_json(workflow_id, definition)
        return self.get_by_id(workflow_id)

    def delete(self, workflow_id: str) -> dict:
        """Never raises for an already-deleted/unknown id --
        {"deleted": False} instead (`ADR-014`'s own result-dict
        convention). Deleting a Workflow removes its definition only: the
        Actions its steps named are the catalogue's and stay exactly as
        they are."""
        if self.get_by_id(workflow_id) is None:
            return {"deleted": False}
        workflows_data.delete_workflow_definition(workflow_id)
        return {"deleted": True}
