"""Known-agent registry: a static, in-code seed set (_SEED_AGENTS,
ADR-011 points 1/3/4, still Accepted) merged at read time with a new
persisted .second-brain/agents_registry.json overlay for runtime-
created agents (ADR-030, supersedes ADR-011 point 2 only). The 7
shipped agents remain app/deployment configuration, in code, never
migrated into the persisted store. Only email-capture-pipeline's
run_capture_now and compass-expert's build_knowledge have a real
handler this pass (see app/api/agents_router.py) — every other
declared action has none yet, seed or created.
"""
from app.data_access import vault_writer

_SEED_AGENTS: dict[str, dict] = {
    # REQ-SB-55-US-01-T08 (ADR-043 point 6) -- replaces the former
    # single-stage "email-capture" Worker 1:1, same type ("worker"), same
    # three real Action ids. Settings text now describes the real Pipeline
    # shape (Fetch -> Classify -> Thread-Match/Merge -> Route-to-Project,
    # plus the two branch Jobs) rather than the old single-stage
    # "classify + file" description.
    "email-capture-pipeline": {
        "name": "Email Capture Pipeline",
        "type": "worker",
        "settings": [
            {"key": "Schedule", "value": "Hourly + once on app start"},
            {"key": "Vault target", "value": "Work/Threads/"},
            {"key": "Job chain", "value": "Fetch -> Classify -> Thread-Match/Merge -> Route-to-Project"},
            {"key": "Branch Jobs", "value": "Summarize-Attachment, Detect-Recurring-Pattern"},
            {"key": "Classifier", "value": "Compass (GPT-5)"},
            {"key": "Missed-run catch-up", "value": "Enabled"},
            {"key": "Purpose", "value": "Automatically captures incoming Outlook email, merges each conversation into one running Thread note, proposes a Project placement for approval, summarizes attachments as dated sub-entries, and proposes a new standing Pipeline when a recurring, structured pattern is detected."},
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
            {"key": "Purpose", "value": "Automatically captures Outlook Calendar meetings into the vault on an hourly schedule, classified by customer and deduplicated across reruns."},
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
            {"key": "Purpose", "value": "Automatically captures Outlook Tasks into the vault on an hourly schedule."},
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
            {"key": "Purpose", "value": "Builds and maintains a person note for every new email sender or meeting attendee, preserving any user-added content."},
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
            {"key": "Purpose", "value": "Answers questions about the vault's contents, grounded in the indexed vault; reachable from this panel and Hermes channels."},
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
            {"key": "Purpose", "value": "Decides where new vault content belongs using the Second Brain filing methodology, pausing for approval when a new top-level area is needed."},
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
            {"key": "Purpose", "value": "A subject-matter expert on Compass, built from delegated research rather than pre-loaded knowledge."},
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
    # REQ-SB-57-US-01-T01 -- one Agent-tier identity covering both the
    # Project- and Customer-level synthesis mechanisms (decomposer's own
    # implementation choice, story's own ## Notes: "the same mechanism
    # applied at two levels, not two independently designed things").
    # Evidence-triggered only (never a fixed schedule, per the story's own
    # Context) -- no run_capture_now-style action exists here, mirroring
    # vault-filing-expert's own actions: [] shape, since nothing in this
    # story's scope manually triggers a run.
    "project-customer-synthesizer": {
        "name": "Project & Customer Synthesizer",
        "type": "worker",
        "settings": [
            {"key": "Trigger", "value": "Evidence-triggered only — a Thread update, a Meeting link-in, or a Project status change; never a fixed schedule"},
            {"key": "Vault target", "value": "Work/Customers/<slug>/(projects/<slug>/)<slug>.md ## Glimpse + log.md"},
            {"key": "History-line bar", "value": "A dated log.md line is appended only when a Project's status transitions into won, lost, or renewed"},
            {"key": "Purpose", "value": "Keeps every Project's and Customer's own Glimpse current and appends a History line only when a Project genuinely concludes, so no Glimpse/History section is ever manually maintained."},
        ],
        "actions": [],
    },
}


def _load_state() -> dict:
    state = vault_writer.load_agents_registry_state()
    if state is None:
        state = {"created_agents": {}}
        vault_writer.save_agents_registry_state(state)
    return state


def get_agent(agent_id: str) -> dict | None:
    if agent_id in _SEED_AGENTS:
        return _SEED_AGENTS[agent_id]
    return _load_state()["created_agents"].get(agent_id)


def list_agents(include_retired: bool = False) -> list[dict]:
    state = _load_state()
    seed_entries = [
        {"id": agent_id, "name": agent["name"], "type": agent["type"]}
        for agent_id, agent in _SEED_AGENTS.items()
    ]
    created_entries = [
        {"id": agent_id, "name": agent["name"], "type": agent["type"]}
        for agent_id, agent in state["created_agents"].items()
        if include_retired or not agent.get("retired", False)
    ]
    return seed_entries + created_entries


def get_action(agent_id: str, action_id: str) -> dict | None:
    """Resolves one action's own definition dict (including its
    "mutates" classification) by agent_id + action_id — the one place
    app/api/agents_router.py's working-mode gate (ADR-020 point 2)
    reads an action's own read-only-vs-mutating nature, so the nested-
    list search isn't duplicated inline at every call site."""
    agent = get_agent(agent_id)
    if agent is None:
        return None
    return next((a for a in agent["actions"] if a["id"] == action_id), None)


def create_agent(name: str, type: str, settings: list[dict] | None = None) -> dict:
    """agent_id is derived via vault_writer.tag_slug(name), keeping
    every agent-identifying id in this codebase human-readable and
    consistent (email-capture-pipeline, compass-expert, widgets-expert), not a
    UUID/integer. Unlike create_section's idempotent-collapse-on-
    collision semantic, disambiguates on collision (-2, -3, ...)
    against the union of _SEED_AGENTS and created_agents keys — two
    distinct agent-creation calls must never silently collide into
    one shared identity, and a created agent's slug must never be
    allowed to shadow a shipped agent's id. actions: [] mirrors the
    already-Done vault-filing-expert/compass-expert "starts with zero
    pre-seeded actions" precedent — REQ-SB-39's Skills unification
    remains the only path to a created agent gaining a capability,
    via the already-Done skill_registry.grant_skill_access."""
    state = _load_state()
    known_ids = set(_SEED_AGENTS.keys()) | set(state["created_agents"].keys())
    base_id = vault_writer.tag_slug(name)
    agent_id = base_id
    suffix = 2
    while agent_id in known_ids:
        agent_id = f"{base_id}-{suffix}"
        suffix += 1
    record = {"name": name, "type": type, "settings": settings or [], "actions": [], "retired": False}
    state["created_agents"][agent_id] = record
    vault_writer.save_agents_registry_state(state)
    return {"id": agent_id, **record}


def retire_agent(agent_id: str) -> bool:
    """The first "retire without delete" primitive (REQ-SB-79-US-01,
    ADR-058 Decision 2) -- marks a CREATED agent's own record retired so
    list_agents() stops surfacing it by default, while get_agent() keeps
    resolving it forever so every already-existing Pending Approval/Agent
    History record attributed to it keeps a real, honest agent_name.
    Idempotent -- retiring an already-retired agent is a safe no-op,
    still returning True (needed for an "every app start" bootstrap
    call). _SEED_AGENTS entries (shipped, static agents) can never be
    retired -- returns False, never mutates _SEED_AGENTS."""
    if agent_id in _SEED_AGENTS:
        return False
    state = _load_state()
    record = state["created_agents"].get(agent_id)
    if record is None:
        return False
    record["retired"] = True
    vault_writer.save_agents_registry_state(state)
    return True
