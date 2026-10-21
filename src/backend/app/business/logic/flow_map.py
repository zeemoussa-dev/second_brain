"""The flow: entry points, the agents behind them, where each routes,
and what each may do (`REQ-SB-102`).

**Every edge is read from a real record.** Agents and `depends_on` come
from the registry, the `when` on each edge from the operator's own
annotation, Actions and Workflows from their catalogues, and the doors
from real traffic. Nothing here infers intent from behaviour: a map
built by guessing what a model meant would be a diagram that cannot be
wrong, which is the same as one that cannot be useful.

**It is a map of what the install SAYS, not a guarantee of what the
agent DOES.** A routing condition is an instruction to a model, not an
enforced branch -- the agent can ignore it. That is stated here because
the map's whole value depends on the reader knowing it: the map says
what should happen, a session transcript says what did, and the gap
between the two is the most useful thing either can show.

**Gaps are output, not decoration.** The operator asked for this to see
gaps, so they are collected deliberately and named in words rather than
left to be spotted by looking hard at a diagram. A gap here is always a
fact about records -- a condition naming an agent that does not exist,
an Action nobody may call -- never a judgement about whether something
is a good idea.
"""
from __future__ import annotations

from typing import Any


def _gap(kind: str, subject: str, says: str) -> dict:
    return {"kind": kind, "subject": subject, "says": says}


def build(
    agents: list[Any],
    actions: list[Any],
    workflows: list[Any],
    entry_points: list[dict],
) -> dict:
    """One pass over everything, returning nodes, edges and gaps.

    Takes already-loaded records rather than fetching: the callers each
    have their own Manager and their own failure handling, and a module
    that reached for four of them would decide, on its own, what a
    partially-readable install looks like.
    """
    by_id = {agent.id: agent for agent in agents}
    callable_by: dict[str, set[str]] = {}
    for action in actions:
        allowed = list(getattr(action, "allowed_callers", []) or [])
        for agent in agents:
            if "*" in allowed or agent.id in allowed:
                callable_by.setdefault(agent.id, set()).add(action.id)

    gaps: list[dict] = []

    # -- entry points ---------------------------------------------------
    doors = []
    for door in entry_points:
        reaches = door.get("agent_id") or (door.get("answered_by") or [None])[0]
        doors.append({
            "label": door.get("label") or (door.get("observed") or {}).get("chat_name") or door.get("chat_id"),
            "source": door.get("source"),
            "chat_id": door.get("chat_id"),
            "declared_agent": door.get("agent_id"),
            "answered_by": door.get("answered_by") or [],
            "reaches": reaches,
            "status": door.get("status"),
        })
        if reaches and reaches not in by_id:
            gaps.append(_gap(
                "entry_point_reaches_unknown_agent", str(door.get("chat_id")),
                f"this door reaches {reaches!r}, which is not an agent on this install",
            ))
        if door.get("status") == "observed_only":
            gaps.append(_gap(
                "entry_point_not_declared", str(door.get("chat_id")),
                "real traffic arrives here and nobody has said which agent should take it",
            ))
        if door.get("status") == "drifted":
            gaps.append(_gap(
                "entry_point_drifted", str(door.get("chat_id")),
                f"declared {door.get('agent_id')!r} but "
                f"{', '.join(door.get('answered_by') or []) or 'nothing'} answered",
            ))

    reachable_from_a_door = {d["reaches"] for d in doors if d["reaches"]}

    # -- agents and their routing ---------------------------------------
    nodes = []
    edges = []
    for agent in agents:
        children = [other for other in agents if agent.id in (other.depends_on or [])]
        conditions = getattr(agent, "routing_conditions", {}) or {}
        for child in children:
            when = (conditions.get(child.id) or "").strip()
            edges.append({
                "from": agent.id, "to": child.id,
                "when": when or None,
                "declared": bool(when),
            })
            if not when:
                gaps.append(_gap(
                    "edge_without_a_condition", f"{agent.id} -> {child.id}",
                    "this specialist is offered with no said when, so the agent decides "
                    "from its description alone and nothing records the intent",
                ))
        for named in conditions:
            if named not in {child.id for child in children}:
                gaps.append(_gap(
                    "condition_for_a_non_specialist", f"{agent.id} -> {named}",
                    f"a condition names {named!r}, which is not one of this agent's "
                    "specialists" + ("" if named in by_id else " and is not an agent at all"),
                ))
        nodes.append({
            "id": agent.id,
            "name": getattr(agent, "name", agent.id),
            "type": getattr(agent, "type", None),
            "routes_to": [child.id for child in children],
            "may_call": sorted(callable_by.get(agent.id, set())),
            "is_entry": agent.id in reachable_from_a_door,
        })

    # -- actions ---------------------------------------------------------
    action_rows = []
    for action in actions:
        callers = [agent.id for agent in agents if action.id in callable_by.get(agent.id, set())]
        implementation = getattr(action, "implementation", None)
        action_rows.append({
            "id": action.id,
            "description": getattr(action, "description", ""),
            "callers": callers,
            "is_blocked": bool(getattr(action, "is_blocked", False)),
            "blocked_reason": getattr(action, "blocked_reason", ""),
            "touches": _touches(implementation),
        })
        if not callers:
            gaps.append(_gap(
                "action_nobody_may_call", action.id,
                "this Action is catalogued but no agent is allowed to call it",
            ))
        if implementation is None:
            gaps.append(_gap(
                "action_without_an_implementation", action.id,
                "this Action is catalogued with nothing to perform it",
            ))

    # -- workflows --------------------------------------------------------
    known_actions = {action.id for action in actions}
    workflow_rows = []
    for workflow in workflows:
        steps = list(getattr(workflow, "steps", []) or [])
        rows = []
        for position, step in enumerate(steps, start=1):
            action_id = getattr(step, "action_id", None) or getattr(step, "action", None)
            rows.append({
                "position": position,
                "id": getattr(step, "id", None),
                "action_id": action_id,
                "needs_confirmation": bool(getattr(step, "needs_confirmation", False)),
            })
            if action_id and action_id not in known_actions:
                gaps.append(_gap(
                    "workflow_step_names_a_missing_action",
                    f"{workflow.id} step {position}",
                    f"this step names action {action_id!r}, which is not in the catalogue",
                ))
        workflow_rows.append({
            "id": workflow.id,
            "request_kind": getattr(workflow, "request_kind", None),
            "steps": rows,
        })

    # One fact, said once. When NOTHING declares an edge anywhere, every
    # agent is unreachable for the same single reason, and forty-two
    # identical gaps would bury the one line that explains them -- it
    # reads as forty-two problems when it is one. Measured on the real
    # install: 42 agents, 0 edges, 40 copies of the same sentence.
    if edges:
        for agent in agents:
            if agent.id in reachable_from_a_door:
                continue
            is_a_specialist = any(agent.id in (other.depends_on or []) for other in agents)
            if not is_a_specialist:
                gaps.append(_gap(
                    "agent_nothing_reaches", agent.id,
                    "no door reaches this agent and no other agent routes to it",
                ))
    elif agents:
        gaps.append(_gap(
            "no_routing_declared_anywhere", "this install",
            f"none of the {len(agents)} agents declares a specialist, so there is no "
            "routing to draw. Whatever hands work between them today is written in "
            "their prompts by hand, where nothing can read it -- which is the gap this "
            "map was built to show.",
        ))

    return {
        "entry_points": doors,
        "agents": nodes,
        "edges": edges,
        "actions": action_rows,
        "workflows": workflow_rows,
        "gaps": gaps,
        "counts": {
            "entry_points": len(doors), "agents": len(nodes), "edges": len(edges),
            "actions": len(action_rows), "workflows": len(workflow_rows), "gaps": len(gaps),
        },
        "caveat": (
            "A routing condition is an instruction to a model, not an enforced branch. "
            "This map says what the install tells its agents; a session transcript says "
            "what one actually did."
        ),
    }


def _touches(implementation: Any) -> str | None:
    """What an Action reaches when it runs, in one phrase. The honest
    answer is usually its implementation's own target -- a route, a
    skill, a screen -- and inventing a friendlier description would be
    the guess this map exists to avoid."""
    if implementation is None:
        return None
    for attribute in ("http", "skill", "ui"):
        value = getattr(implementation, attribute, None)
        if value:
            if attribute == "http":
                return f"{getattr(value, 'method', '')} {getattr(value, 'path', '')}".strip()
            if attribute == "skill":
                return f"skill {getattr(value, 'skill_id', value)}"
            return f"screen {getattr(value, 'feature_key', value)}"
    return None
