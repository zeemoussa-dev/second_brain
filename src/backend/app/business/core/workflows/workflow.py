from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class WorkflowStep:
    """One documented step: the catalogued Action it runs, what that
    Action is called with, and whether the operator must confirm it.

    `id` is the step's own stable handle, NOT its position. A run
    addresses one step at a time by id and refuses an outcome for a step
    id the Workflow does not hold (`ADR-034`, `T05`), so an id derived
    from position would silently re-point at a different step the moment
    the operator reordered the list -- the exact failure "nothing
    dropped or duplicated" exists to rule out.

    `inputs` is stored verbatim and interpreted by nobody here: it holds
    either the literal values for that Action's declared inputs or a
    mapping describing where each value comes from. The call gate
    (`ADR-033`) is what validates values against the Action's declared
    inputs at the moment the step is dispatched; storing them is this
    kind's job, checking them is not.
    """
    id: str
    action_id: str
    inputs: dict[str, Any] = field(default_factory=dict)
    # Per step, not per Workflow: the operator marks the one step that
    # needs them in the loop (sending the mail), not the whole intent.
    # Honoured at run time by ADR-033's existing awaiting_confirmation
    # call record; this kind stores the flag and nothing more.
    needs_confirmation: bool = False
    description: str = ""


@dataclass
class WorkflowReport:
    """What is reported back when the run finishes.

    Deliberately a *definition*, never a report: `ADR-034` composes the
    real text from the run record's own recorded step outcomes, so a
    failed step can never be reported as done. All this holds is what
    the operator said should come back.

    An empty `include_step_ids` means every step, in documented order --
    the honest default for "tell me what happened", and the reason the
    common case needs no list to maintain alongside the steps.
    """
    description: str = ""
    include_step_ids: list[str] = field(default_factory=list)


@dataclass
class Workflow:
    """One kind of request and the ordered handling the operator
    documented for it (`ADR-032`'s seventh artifact kind). Instance data:
    it lives in the App Database Folder at data/Workflows/<id>/
    Workflow.json, never in the repository.

    `steps` is an ordered list and is the operator's documented order,
    not a set -- position carries meaning and is preserved exactly on
    round-trip. There is no branching, loop or condition: order is the
    only control flow this kind has (story Non-Goals).
    """
    id: str
    # The kind of request this handles -- what an agent recognises an
    # incoming intent as. A plain operator-authored string: nothing here
    # infers, suggests or derives it, which is the PRD's own
    # "documented by the operator, not inferred by the model".
    request_kind: str = ""
    description: str = ""
    steps: list[WorkflowStep] = field(default_factory=list)
    # Always present, never None: a Workflow always reports something,
    # and a default WorkflowReport() already means "every step's
    # recorded outcome, in order" -- so the run engine composing the
    # report never has to decide what a missing definition meant.
    report: WorkflowReport = field(default_factory=WorkflowReport)
    created_at: str = ""
    updated_at: str | None = None
