"""Static, hardcoded known-agent/settings/actions/trigger-phrases registry
(ADR-011) — deliberately NOT vault-derived, unlike list_known_customers/
list_known_kinds (see ADR-011's own reasoning: which agents exist is
app/deployment configuration, not open-ended vault content). Only
email-capture's run_capture_now has a real handler this pass (see
app/api/agents_router.py, T05) — every other declared action has none yet.
"""

AGENTS: dict[str, dict] = {
    "email-capture": {
        "name": "Email Capture",
        "type": "worker",
        "settings": [
            {"key": "Schedule", "value": "Hourly + once on app start"},
            {"key": "Vault target", "value": "Work/Emails/"},
            {"key": "Classifier", "value": "Compass (GPT-5)"},
            {"key": "Missed-run catch-up", "value": "Enabled"},
        ],
        "actions": [
            {
                "id": "run_capture_now",
                "label": "Run capture now",
                "trigger_phrases": ["run capture now", "run capture", "capture now"],
                "mutates": True,
            },
            {
                "id": "view_last_run",
                "label": "View last run",
                "trigger_phrases": ["view last run", "last run"],
                "mutates": False,
            },
            {
                "id": "pause_schedule",
                "label": "Pause schedule",
                "trigger_phrases": ["pause schedule", "pause capture"],
                "mutates": True,
            },
        ],
    },
    "meeting-capture": {
        "name": "Meeting Capture",
        "type": "worker",
        "settings": [
            {"key": "Schedule", "value": "Hourly + once on app start"},
            {"key": "Vault target", "value": "Work/Meetings/"},
            {"key": "Classification", "value": "By customer (shared with Email Capture)"},
            {"key": "Duplicate handling", "value": "Skipped on rerun"},
        ],
        "actions": [
            {
                "id": "run_capture_now",
                "label": "Run capture now",
                "trigger_phrases": ["run capture now", "run capture", "capture now"],
                "mutates": True,
            },
            {
                "id": "view_last_run",
                "label": "View last run",
                "trigger_phrases": ["view last run", "last run"],
                "mutates": False,
            },
            {
                "id": "pause_schedule",
                "label": "Pause schedule",
                "trigger_phrases": ["pause schedule", "pause capture"],
                "mutates": True,
            },
        ],
    },
    "todo-capture": {
        "name": "To-Do Capture",
        "type": "worker",
        "settings": [
            {"key": "Schedule", "value": "Hourly + once on app start"},
            {"key": "Task source", "value": "Outlook Tasks folder"},
        ],
        "actions": [
            {
                "id": "run_capture_now",
                "label": "Run capture now",
                "trigger_phrases": ["run capture now", "run capture", "capture now"],
                "mutates": True,
            },
            {
                "id": "view_last_run",
                "label": "View last run",
                "trigger_phrases": ["view last run", "last run"],
                "mutates": False,
            },
            {
                "id": "pause_schedule",
                "label": "Pause schedule",
                "trigger_phrases": ["pause schedule", "pause capture"],
                "mutates": True,
            },
        ],
    },
    "people-producer": {
        "name": "People Notes",
        "type": "producer",
        "settings": [
            {"key": "Triggers on", "value": "New sender / meeting attendee"},
            {"key": "Vault target", "value": "Work/People/"},
            {"key": "Manual-edit protection", "value": "Preserves user-added content"},
        ],
        "actions": [
            {
                "id": "rebuild_person_note",
                "label": "Rebuild a person note",
                "trigger_phrases": ["rebuild person note", "rebuild a person note"],
                "mutates": True,
            },
            {
                "id": "view_last_run",
                "label": "View last run",
                "trigger_phrases": ["view last run", "last run"],
                "mutates": False,
            },
        ],
    },
    "vault-qa": {
        "name": "Vault Q&A",
        "type": "expert",
        "settings": [
            {"key": "Grounding", "value": "Indexed vault (REQ-SB-01/02)"},
            {"key": "Reachable via", "value": "This panel + Hermes channels"},
            {"key": "Write access", "value": "Read-only here (see REQ-SB-04 for write scope)"},
        ],
        "actions": [
            {
                "id": "ask_question",
                "label": "Ask a question",
                "trigger_phrases": ["ask a question", "ask question"],
                "mutates": False,
            },
            {
                "id": "view_channel_status",
                "label": "View channel status",
                "trigger_phrases": ["view channel status", "channel status"],
                "mutates": False,
            },
        ],
    },
    "vault-filing-expert": {
        "name": "Vault Filing Expert",
        "type": "expert",
        "settings": [
            {"key": "Grounding", "value": "Beyond the Second Brain methodology + live vault structure"},
            {"key": "Reachable via", "value": "REQ-SB-20 Hub-to-Hub cross-Section routing only"},
            {"key": "New top-level area", "value": "Pauses for operator approval (Tier 2)"},
        ],
        "actions": [],
    },
    "compass-expert": {
        "name": "Compass Expert",
        "type": "expert",
        "settings": [
            {"key": "Subject", "value": "Compass"},
            {"key": "Starting knowledge", "value": "None — bootstrapped via delegated research"},
            {"key": "Vault scope", "value": "Not yet assigned (REQ-SB-29)"},
        ],
        "actions": [
            {
                "id": "build_knowledge",
                "label": "Build my knowledge",
                "trigger_phrases": ["build my knowledge", "build knowledge", "research my subject"],
                "mutates": True,
            },
        ],
    },
}


def get_agent(agent_id: str) -> dict | None:
    return AGENTS.get(agent_id)


def list_agents() -> list[dict]:
    return [
        {"id": agent_id, "name": agent["name"], "type": agent["type"]}
        for agent_id, agent in AGENTS.items()
    ]


def get_action(agent_id: str, action_id: str) -> dict | None:
    """Resolves one action's own definition dict (including its
    "mutates" classification) by agent_id + action_id — the one place
    app/api/agents_router.py's working-mode gate (ADR-020 point 2)
    reads an action's own read-only-vs-mutating nature, so the nested-
    list search isn't duplicated inline at every call site."""
    agent = AGENTS.get(agent_id)
    if agent is None:
        return None
    return next((a for a in agent["actions"] if a["id"] == action_id), None)
