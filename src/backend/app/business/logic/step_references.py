"""Resolving what a step is called with, when it is not a fixed value
(`REQ-SB-103`).

A step input may hold a literal, as every Workflow step has until now,
or a reference to something only known once the run is under way:

    {{request.customer}}        what the ask was about
    {{steps.find-tasks.result}} what an earlier step came back with

**An unresolvable reference refuses the step. It is never passed
through.** A literal `{{steps.find-tasks.result}}` arriving in an email
body is the failure that actually sends -- and the one a test will not
catch, because the call succeeds. So resolution either produces a value
or produces a refusal naming the reference, and there is no third
outcome.

**A reference to a step that has not produced a result is NOT the same
as a reference to one that produced nothing.** A step still waiting,
refused, or failed cannot supply a value and the run must stop and say
which; a step that genuinely returned an empty answer supplied one, and
the run carries on. Collapsing those two is how a pipeline quietly mails
an empty list and reports success.

**Only whole-value substitution is supported, deliberately.** A
reference may be the entire input, not a fragment inside a longer
string. Interpolating a result into prose means deciding how to render
a dict as text, and that is a formatting judgement -- which this
requirement gives to an agent step, where it can be seen, rather than
burying it in a template engine nobody reads.
"""
from __future__ import annotations

import re
from typing import Any, Mapping

_REFERENCE = re.compile(r"^\s*\{\{\s*([a-zA-Z0-9_.\-]+)\s*\}\}\s*$")

# A step whose status is one of these has not supplied a value, and
# never will without something changing. Distinct from "produced an
# empty result", which IS a value.
_CANNOT_SUPPLY = {"not_reached", "running", "awaiting_confirmation", "refused", "failed"}


class ReferenceError(Exception):
    """Carries the sentence the step is refused with. Names the
    reference, because an operator reading "a value could not be
    resolved" has to go and find which one."""


def is_reference(value: Any) -> bool:
    return isinstance(value, str) and _REFERENCE.match(value) is not None


def _step_by_id(run: Mapping[str, Any], step_id: str) -> dict | None:
    for step in run.get("steps") or []:
        if step.get("step_id") == step_id:
            return step
    return None


def resolve_one(path: str, run: Mapping[str, Any]) -> Any:
    """`request.<name>` or `steps.<step_id>.result`. Anything else is a
    reference this build does not understand, which is refused rather
    than guessed at -- a typo that silently resolved to None would be
    indistinguishable from a value that really was None."""
    parts = path.split(".")

    if parts[0] == "request":
        if len(parts) != 2:
            raise ReferenceError(
                f"{{{{{path}}}}} is not a reference this app understands. A request "
                "reference names one value, like {{request.customer}}."
            )
        request = run.get("request") or {}
        if parts[1] not in request:
            known = ", ".join(sorted(request)) or "nothing"
            raise ReferenceError(
                f"this run was not started with {parts[1]!r}, so {{{{{path}}}}} cannot be "
                f"resolved. The run carries: {known}."
            )
        return request[parts[1]]

    if parts[0] == "steps":
        if len(parts) != 3 or parts[2] != "result":
            raise ReferenceError(
                f"{{{{{path}}}}} is not a reference this app understands. A step reference "
                "names a step's result, like {{steps.find-tasks.result}}."
            )
        step = _step_by_id(run, parts[1])
        if step is None:
            raise ReferenceError(
                f"{{{{{path}}}}} names the step {parts[1]!r}, which is not in this Workflow."
            )
        status = step.get("status")
        if status in _CANNOT_SUPPLY:
            raise ReferenceError(
                f"step {parts[1]!r} is {status!r}, so it has produced no result for "
                f"{{{{{path}}}}} to use. Nothing was run."
            )
        return step.get("result")

    raise ReferenceError(
        f"{{{{{path}}}}} is not a reference this app understands. References begin with "
        "`request.` or `steps.`."
    )


def resolve_inputs(inputs: Mapping[str, Any], run: Mapping[str, Any]) -> dict:
    """Every input, with references replaced by their values.

    Raises `ReferenceError` on the FIRST reference that cannot be
    resolved, and resolves nothing further: a step is dispatched with
    all of its inputs or none of them, and half-resolved inputs are how
    an Action gets called with a customer name and no body.
    """
    resolved: dict[str, Any] = {}
    for name, value in (inputs or {}).items():
        if is_reference(value):
            path = _REFERENCE.match(value).group(1)  # type: ignore[union-attr]
            try:
                resolved[name] = resolve_one(path, run)
            except ReferenceError as exc:
                raise ReferenceError(f"input {name!r}: {exc}") from exc
        else:
            resolved[name] = value
    return resolved


def references_in(inputs: Mapping[str, Any]) -> list[str]:
    """Every reference an input set names. For the authoring screens and
    for the flow map, which can then say that a step depends on another
    without running anything."""
    found = []
    for value in (inputs or {}).values():
        if is_reference(value):
            found.append(_REFERENCE.match(value).group(1))  # type: ignore[union-attr]
    return found
