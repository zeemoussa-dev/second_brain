"""Agent chat trigger-phrase matching mechanism (ADR-011) — exact-phrase/
keyword substring matching against a small, per-agent-declared trigger
phrase set, NOT an NLU/LLM pipeline (ADR-007 keeps that class of
capability out of Second Brain's own stack). Pure matching only — the
caller (app/api/agents_router.py, T05) is responsible for actually
invoking the matched action's handler and appending history entries, so
both the direct-action-trigger endpoint and the chat endpoint invoke the
identical handler."""
from app.business import agent_registry


def handle_chat_message(agent_id: str, message: str) -> dict:
    """Returns {"matched_action_id": <action id> | None,
    "fallback_reply": <str> | None}. Exactly one of the two is non-None:
    a match sets matched_action_id and leaves fallback_reply None (the
    caller composes the real confirmation reply after invoking the
    handler); no match sets fallback_reply to a canned, honestly
    non-conversational message listing the agent's available actions,
    and leaves matched_action_id None."""
    agent = agent_registry.get_agent(agent_id)
    if agent is None:
        return {"matched_action_id": None, "fallback_reply": "Unknown agent."}

    lowered_message = message.lower()
    for action in agent["actions"]:
        for phrase in action["trigger_phrases"]:
            if phrase in lowered_message:
                return {"matched_action_id": action["id"], "fallback_reply": None}

    action_labels = ", ".join(action["label"] for action in agent["actions"])
    fallback_reply = (
        f"I didn't understand that. {agent['name']} can: {action_labels}."
    )
    return {"matched_action_id": None, "fallback_reply": fallback_reply}
