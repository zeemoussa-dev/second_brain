"""Rules evaluated at the moment an Action is called, against the
inputs it was called with (`REQ-SB-102`; operator: "a rule, not a
switch" -- "never mail anyone outside the company", "never write to
this folder").

**A rule is about the call, not about the Action.** The kill switch
turns an Action off for everyone; a rule lets the same Action through a
hundred times and stops the hundred-and-first because of what it was
asked to do. That is why it lives here and is evaluated per call with
the real inputs in hand, rather than being a flag on the catalogue.

**The asymmetry that makes "never" mean never.** Two shapes of rule
fail in opposite directions when the input a rule names is simply not
there:

  `refuse_unless` -- "only ever mail @core42.ai". If the call carries no
      `to` at all, we cannot show it is inside the company, so the rule
      REFUSES. A deny-unless rule that waved through the one call it
      could not inspect would not be a "never".

  `refuse_if` -- "never write to C:/Windows". If the call carries no
      `path`, there is nothing matching the forbidden thing, so the rule
      does NOT fire. A deny-if rule that refused everything it could not
      inspect would block the whole catalogue the day someone wrote a
      rule about an input most Actions do not have.

Both are correct and they are opposites, which is exactly why each rule
says which it is rather than the engine guessing from the operator's
wording.

**A broken rule refuses and says so.** A pattern that will not compile
is not skipped: a rule the operator wrote to stop something, which
silently stops nothing, is worse than an error. It refuses the call and
names itself, so the first call after a typo reports the typo.

**Rules never grant.** The worst outcome of a bug here is an Action
refused that should have run -- recoverable, visible, and the operator
is told which rule did it. They cannot permit anything `allowed_callers`
or a block already refused.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Mapping

MATCH_IF = "refuse_if"
MATCH_UNLESS = "refuse_unless"
EFFECTS = ("refuse", "needs_confirmation")


@dataclass(frozen=True)
class Rule:
    id: str
    name: str
    action_id: str = "*"
    caller_agent_id: str = "*"
    input_name: str = ""
    kind: str = MATCH_IF
    pattern: str = ""
    effect: str = "refuse"
    reason: str = ""
    enabled: bool = True

    @staticmethod
    def from_dict(data: Mapping[str, Any]) -> "Rule":
        return Rule(
            id=str(data.get("id") or ""),
            name=str(data.get("name") or ""),
            action_id=str(data.get("action_id") or "*"),
            caller_agent_id=str(data.get("caller_agent_id") or "*"),
            input_name=str(data.get("input_name") or ""),
            kind=str(data.get("kind") or MATCH_IF),
            pattern=str(data.get("pattern") or ""),
            effect=str(data.get("effect") or "refuse"),
            reason=str(data.get("reason") or ""),
            enabled=bool(data.get("enabled", True)),
        )


@dataclass
class Verdict:
    """What the rules together say about one call. `refused_by` and
    `confirmation_required_by` name the RULE, not just the outcome, so
    an operator reading a refusal knows which of their own rules to go
    and look at."""

    refused_by: Rule | None = None
    confirmation_required_by: Rule | None = None
    sentence: str = ""
    evaluated: list[str] = field(default_factory=list)
    broken: list[str] = field(default_factory=list)


def _applies_to(rule: Rule, action_id: str, caller_agent_id: str) -> bool:
    if rule.action_id not in ("*", action_id):
        return False
    return rule.caller_agent_id in ("*", caller_agent_id)


def _matches(rule: Rule, value: Any) -> bool:
    """Whether the value matches this rule's pattern. Raises
    `re.error` on a pattern that will not compile -- the caller turns
    that into a refusal rather than a skip."""
    return re.search(rule.pattern, str(value), re.IGNORECASE) is not None


def evaluate(
    rules: list[Rule], action_id: str, caller_agent_id: str, inputs: Mapping[str, Any],
) -> Verdict:
    """The first rule to refuse wins, and evaluation stops there -- a
    call refused twice is still refused once, and reporting the first
    reason keeps the message about one thing the operator wrote.

    A `needs_confirmation` rule does NOT stop evaluation: a later rule
    might refuse outright, and "this needed your say-so" would be the
    wrong thing to tell someone about a call that was never going to be
    allowed.
    """
    verdict = Verdict()
    for rule in rules:
        if not rule.enabled or not _applies_to(rule, action_id, caller_agent_id):
            continue
        verdict.evaluated.append(rule.id)

        present = rule.input_name in inputs
        value = inputs.get(rule.input_name)
        try:
            if rule.kind == MATCH_UNLESS:
                # Absent cannot be shown to be allowed, so it fails.
                fires = not present or not _matches(rule, value)
            else:
                fires = present and _matches(rule, value)
        except re.error as exc:
            verdict.broken.append(rule.id)
            verdict.refused_by = rule
            verdict.sentence = (
                f"rule {rule.name!r} could not be applied -- its pattern is not valid "
                f"({exc}). The call was refused rather than let through, because a rule "
                "that silently stops nothing is worse than one that errors."
            )
            return verdict

        if not fires:
            continue

        if rule.effect == "needs_confirmation":
            if verdict.confirmation_required_by is None:
                verdict.confirmation_required_by = rule
            continue

        verdict.refused_by = rule
        verdict.sentence = _refusal_sentence(rule, action_id, present)
        return verdict

    return verdict


def _refusal_sentence(rule: Rule, action_id: str, input_was_present: bool) -> str:
    """Names the rule, the input and why -- and says plainly when the
    reason is that the input was MISSING, which is otherwise the most
    confusing refusal a deny-unless rule can produce."""
    reason = (rule.reason or "").strip()
    if rule.kind == MATCH_UNLESS and not input_was_present:
        return (
            f"action {action_id!r} was not run: the rule {rule.name!r} only allows it when "
            f"{rule.input_name!r} matches {rule.pattern!r}, and this call supplied no "
            f"{rule.input_name!r} at all"
            + (f". {reason}" if reason else "")
        )
    return (
        f"action {action_id!r} was not run: it is stopped by the rule {rule.name!r} "
        f"({rule.input_name!r} "
        + ("must match" if rule.kind == MATCH_UNLESS else "must not match")
        + f" {rule.pattern!r})"
        + (f". {reason}" if reason else "")
    )
