"""Plain, hardcoded sample data — no Outlook/Compass/vault calls, no
Skill/Tool execution, no persistence beyond this process's own memory
(resets every restart). This file IS the "database": every route in
main.py reads/mutates the module-level dicts below directly. Field
names mirror the REAL backend's today's-shape contracts exactly
(src/backend/app/api/agents_router.py, sections_router.py,
providers_router.py, skills_router.py, agent_schedules_router.py) so
the frontend's existing api clients (agentsApiClient.ts,
settingsApiClient.ts, skillsApiClient.ts, agentSchedulesApiClient.ts)
work against this server unmodified — only VITE_API_BASE_URL changes.

Every user-visible `name` in this file deliberately avoids the word
"Demo" (operator, 2026-08-15: "Remove the word Demo as It might affect
the UI") — this data IS sample/demo data, but nothing rendered to the
screen says so. `id` values keep their own `demo-`/generator-derived
prefixes; those are never rendered as text anywhere in the UI (agent
nodes/lists/panels all render `name`, never `id`), so they're left
alone rather than mass-renamed for no visible benefit.
"""

# PORT-TO-REAL-API: `subtitle`/`description` are new here, demo-only for
# now — the real `section_registry.py`/`sections_router.py`/
# `SectionSummary` (settingsApiClient.ts) don't carry them yet (operator,
# 2026-08-15: "I need to have a Section Subtitle and Description The
# Subtitle will be Displayed in the Agent Map The Description will be
# used later Generate Some Dummy Info for now and update the API to get
# those in Section Call"). `subtitle` was this same field under an
# earlier working name, `slogan` — renamed here to match the operator's
# own terminology now that it has a real consumer (AgentsMapCanvas.tsx's
# own Section title block); values are unchanged, still reusing the
# html-prototype/agents-map-skilltree-exploration.html's own real
# slogans verbatim where a Section name matches 1:1 (Capture, Sales) and
# its own short-noun-phrases-joined-by-"·" style for the rest.
# `description` is genuinely new dummy copy — one real sentence per
# Section, plausible business-domain text — NOT rendered anywhere yet
# (the operator's own "will be used later" framing); it exists so a
# future Section detail/about surface has real data to read instead of
# a placeholder. `agent_ids` is filled in at the bottom of this module,
# once every Agent below actually exists, rather than hand-maintained
# here. `color`/`icon` (operator, 2026-08-15: "every section Should have
# its own Color and Icon, The Hub should Match the Color of the
# Section") reuse the SAME curated palette/icon language already
# established for Agents (VisualPicker.tsx's own VISUAL_COLORS; Material
# Symbols ligature names, tokens.css's own self-hosted icon font) rather
# than inventing a second one — one consistent visual system, not two.
SECTIONS: dict[str, dict] = {
    "capture": {"id": "capture", "name": "Capture", "subtitle": "email · meetings · to-dos", "description": "Watches incoming email, meeting notes, and to-dos, then files each one into the vault under the right person or topic automatically.", "color": "#2563eb", "icon": "inbox", "agent_ids": []},
    "sales": {"id": "sales", "name": "Sales", "subtitle": "deals · pipeline · proposals", "description": "Tracks open deals through the pipeline and keeps proposal and account history up to date without manual data entry.", "color": "#16a34a", "icon": "sell", "agent_ids": []},
    "productivity": {"id": "productivity", "name": "Productivity", "subtitle": "notes · follow-ups · reminders", "description": "Builds and maintains person notes, chases follow-ups, and surfaces reminders so nothing raised in a conversation gets dropped.", "color": "#7c3aed", "icon": "task_alt", "agent_ids": []},
    # New sections (operator, 2026-08-15: "Bring the 150 Agents to the
    # Demo Backend") — the generated 150 span 7 domains; capture/sales
    # already existed above and are reused, the other 5 are new.
    "support": {"id": "support", "name": "Support", "subtitle": "tickets · incidents · bugs", "description": "Triages incoming tickets and incident reports, classifying and routing each one so nothing sits unowned in a queue.", "color": "#0891b2", "icon": "support_agent", "agent_ids": []},
    "hr": {"id": "hr", "name": "HR", "subtitle": "onboarding · applications · timesheets", "description": "Moves new-hire onboarding, job applications, and timesheet corrections through their own multi-stage review pipelines.", "color": "#db2777", "icon": "groups", "agent_ids": []},
    "finance": {"id": "finance", "name": "Finance", "subtitle": "invoices · expenses · refunds", "description": "Processes vendor invoices, expense reports, and customer refunds, matching each against the right account before it's filed.", "color": "#b45309", "icon": "account_balance", "agent_ids": []},
    "legal": {"id": "legal", "name": "Legal", "subtitle": "contracts · filings · compliance", "description": "Reviews contracts, legal filings, and compliance audits, flagging anything that needs a human sign-off before it moves on.", "color": "#4f46e5", "icon": "gavel", "agent_ids": []},
    "marketing": {"id": "marketing", "name": "Marketing", "subtitle": "campaigns · reviews · mentions", "description": "Tracks ad campaign performance, product reviews, and social mentions, rolling each up into a single running summary.", "color": "#c58b5f", "icon": "campaign", "agent_ids": []},
}

PROVIDERS: dict[str, dict] = {
    "compass-demo": {
        "id": "compass-demo",
        "name": "Compass",
        "endpoint": "https://demo.invalid/v1",
        "model": "demo-model",
        "credential_set": True,
        "is_default": True,
        "has_real_client": True,
        # Filled in at the bottom of this module, once AGENTS is complete.
        "agent_ids": [],
    },
}

SKILLS: dict[str, dict] = {
    "view-last-run": {"id": "view-last-run", "name": "View Last Run", "description": "Reports the outcome of this agent's most recent run.", "tool": "Outlook", "mutates": False},
    "rebuild-note": {"id": "rebuild-note", "name": "Rebuild a Note", "description": "Rebuilds this agent's target vault note from scratch.", "tool": "Vault", "mutates": True},
    "run-capture-now": {"id": "run-capture-now", "name": "Run Capture Now", "description": "Triggers an immediate capture run outside its normal schedule.", "tool": "Outlook", "mutates": True},
}

# Icons are deliberately mixed here — some Agents have one, some don't
# (operator, 2026-08-15: "Some Agents will have Icons some will not") —
# so the Map/Visual-tab UI gets exercised on both the icon-glyph render
# path AND the plain-dot fallback path, not just one. `demo-deal-tracker`
# is the one hand-authored Agent left without an icon on purpose.
#
# `depends_on`/`branch_target_agent_id` (operator, 2026-08-15: "Some
# Agents are connected in a Pipeline some Are Experts some Experts are
# connected to a pipeline, The Data About the Agent should have who is
# connected to who in order to have a tree, Check LangGraph Data") —
# the same two-field relationship shape LangGraph itself uses to
# describe a graph (`StateGraph.add_edge(from, to)` for a structural
# edge; a conditional/branch edge for "this node can also reach a
# different node") and the shape this project's own taxonomy-modeled
# demo data already used (src/backend/app/business/demo_taxonomy.py's
# Job `depends_on`/`branch_target_agent_id`) before being flattened out
# of THIS backend's own sample data for the "150 Agents" pass. Brought
# back here, on the flat Agent shape directly, so a future tree/graph
# view has real connection data to read: `depends_on` = ids of Agents
# this one structurally receives from (empty = a pipeline's own entry
# point, or a standalone Agent with no pipeline at all);
# `branch_target_agent_id` = the ONE specific Expert Agent id a
# "Consult Expert" stage additively branches out to (distinct from
# `depends_on` — a consultation, not a structural predecessor). None of
# the 5 hand-authored Agents below are wired into any pipeline (both
# fields stay empty/None); the generated stage-Agents below ARE.
AGENTS: dict[str, dict] = {
    "demo-email-capture": {
        "id": "demo-email-capture",
        "name": "Email Capture",
        "type": "worker",
        "settings": [{"key": "Purpose", "value": "Captures incoming email into the vault, classified by customer — sample data only."}],
        "capabilities": [{"id": "run-capture-now", "label": "Run Capture Now", "kind": "skill", "tool": "Outlook"}],
        "section_id": "capture",
        "provider_id": "compass-demo",
        "keywords": ["email", "inbox"],
        "working_mode": "autonomous",
        "scope": ["Work/Emails/"],
        "is_background_agent": True,
        "icon": "mail",
        "color": None,
        "depends_on": [],
        "branch_target_agent_id": None,
    },
    "demo-vault-expert": {
        "id": "demo-vault-expert",
        "name": "Vault Expert",
        "type": "expert",
        "settings": [{"key": "Domain", "value": "What has already been captured and filed in the vault for a given customer or topic."}],
        "capabilities": [{"id": "view-last-run", "label": "View Last Run", "kind": "skill", "tool": "Outlook"}],
        "section_id": "capture",
        "provider_id": "compass-demo",
        "keywords": ["vault", "search"],
        "working_mode": "autonomous",
        "scope": [],
        "is_background_agent": False,
        "icon": "search",
        "color": None,
        "depends_on": [],
        "branch_target_agent_id": None,
    },
    "demo-ops-expert": {
        "id": "demo-ops-expert",
        "name": "Ops Expert",
        "type": "expert",
        "settings": [{"key": "Domain", "value": "Deals and accounts — answers whether we've worked with a given account before and what happened."}],
        "capabilities": [{"id": "view-last-run", "label": "View Last Run", "kind": "skill", "tool": "Outlook"}],
        "section_id": "sales",
        "provider_id": "compass-demo",
        "keywords": ["deals", "accounts"],
        "working_mode": "autonomous",
        "scope": [],
        "is_background_agent": False,
        "icon": "handshake",
        "color": None,
        "depends_on": [],
        "branch_target_agent_id": None,
    },
    "demo-deal-tracker": {
        "id": "demo-deal-tracker",
        "name": "Deal Tracker",
        "type": "worker",
        "settings": [{"key": "Purpose", "value": "Tracks open deals through the pipeline — sample data only."}],
        "capabilities": [{"id": "run-capture-now", "label": "Run Capture Now", "kind": "skill", "tool": "Outlook"}],
        "section_id": "sales",
        "provider_id": "compass-demo",
        "keywords": ["deals"],
        "working_mode": "supervised",
        "scope": [],
        "is_background_agent": False,
        "icon": None,
        "color": None,
        "depends_on": [],
        "branch_target_agent_id": None,
    },
    "demo-people-notes": {
        "id": "demo-people-notes",
        "name": "People Notes",
        "type": "producer",
        "settings": [{"key": "Purpose", "value": "Builds and maintains a person note for every new email sender or meeting attendee — sample data only."}],
        "capabilities": [{"id": "rebuild-note", "label": "Rebuild a Note", "kind": "skill", "tool": "Vault"}],
        "section_id": "productivity",
        "provider_id": "compass-demo",
        "keywords": ["people"],
        "working_mode": "autonomous",
        "scope": [],
        "is_background_agent": False,
        "icon": "person",
        "color": None,
        "depends_on": [],
        "branch_target_agent_id": None,
    },
}

# agent_id -> set of granted skill ids. Absence (e.g. every generated
# Agent below) reads back as "no skills granted" — main.py's
# get_agent_skills does `AGENT_SKILL_GRANTS.get(agent_id, set())`, so
# nothing needs adding here for them.
AGENT_SKILL_GRANTS: dict[str, set[str]] = {
    "demo-email-capture": {"view-last-run", "run-capture-now"},
    "demo-vault-expert": {"view-last-run"},
    "demo-ops-expert": {"view-last-run"},
    "demo-deal-tracker": {"run-capture-now"},
    "demo-people-notes": {"rebuild-note"},
}

# agent_id -> list of history entries (AgentHistoryEntry shape). Same
# "absence is fine" convention as AGENT_SKILL_GRANTS above.
AGENT_HISTORY: dict[str, list[dict]] = {
    "demo-email-capture": [
        {"kind": "run_event", "text": "Sample run — filed 3 emails.", "timestamp": "2026-08-14T09:00:00Z"},
    ],
}

# agent_id -> list of schedules (AgentSchedule shape).
AGENT_SCHEDULES: dict[str, list[dict]] = {}


# ---------------------------------------------------------------------------
# Bulk generated sample set (operator, 2026-08-15: "Bring the 150 Agents to
# the Demo Backend") — the same 150-entity spread originally built for the
# real backend's taxonomy-shaped `/demo/agents`+`/demo/pipelines`
# (src/backend/app/business/demo_taxonomy.py), reshaped flat to match THIS
# backend's own today's-contract Agent shape instead (that taxonomy module
# is real-backend-only code, not importable here — this standalone backend
# has its own separate .venv and deliberately no dependency on src/backend).
# A Pipeline's "stage" (Job) has no equivalent concept in the flat contract,
# so each stage just becomes its own ordinary Agent — the DAG/depends_on
# shape from the taxonomy version is not reproduced here, only the volume
# and section spread, since that's what "so we can do some Real UI checks"
# actually needs. 10 six-stage + 10 five-stage + 8 four-stage domains (142
# stage-Agents) + 8 standalone Expert Agents = 150.
_GENERATED_SECTION_IDS = ["capture", "sales", "support", "hr", "finance", "legal", "marketing"]

_PIPELINE_DOMAINS = [
    "Meetings", "Support Tickets", "Sales Leads", "Documents", "Invoices",
    "Job Applications", "Expense Reports", "Feedback Forms", "Contracts",
    "Onboarding", "Incident Reports", "Product Reviews", "Chat Transcripts",
    "Legal Filings", "Ad Campaign Reports", "Survey Responses",
    "Vendor Invoices", "Shipment Tracking", "Customer Refunds",
    "Compliance Audits", "Marketing Assets", "Bug Reports",
    "Partnership Proposals", "Renewal Notices", "Warranty Claims",
    "Timesheet Corrections", "Social Mentions", "Purchase Orders",
]

_EXPERT_DOMAINS = [
    "Legal", "HR", "Finance", "Security", "Compliance", "Product",
    "Marketing", "Support",
]

# Every generated Expert gets an icon (unlike the stage Agents above,
# where only Fetch/Store do) — Experts are the "full identity" tier,
# reasonable to always visually distinguish on the Map.
_EXPERT_ICONS: dict[str, str] = {
    "Legal": "gavel",
    "HR": "badge",
    "Finance": "payments",
    "Security": "shield",
    "Compliance": "policy",
    "Product": "widgets",
    "Marketing": "campaign",
    "Support": "support_agent",
}

# Most Experts are autonomous by default; Security/Compliance get the
# strictest oversight ("manual") — the one place in this demo's own
# sample set that exercises all 3 real working-mode values, not just
# the autonomous/supervised split every stage Agent above uses.
_EXPERT_WORKING_MODES: dict[str, str] = {
    "Legal": "autonomous",
    "HR": "autonomous",
    "Finance": "autonomous",
    "Security": "manual",
    "Compliance": "manual",
    "Product": "autonomous",
    "Marketing": "autonomous",
    "Support": "autonomous",
}

_SIX_STAGE_NAMES = ["Fetch", "Classify (Primary)", "Classify (Secondary)", "Merge", "Consult Expert", "Store"]
_FIVE_STAGE_NAMES = ["Fetch", "Classify", "Summarize", "Enrich", "Store"]
_FOUR_STAGE_NAMES = ["Fetch", "Classify", "Enrich", "Store"]

# The 6-stage shape forks/merges (LangGraph's own "add_edge into a
# fan-in node" pattern) rather than a straight chain, so its own
# predecessor-per-stage map is explicit, not positional — Store depends
# on Merge, NOT on Consult Expert, matching that branch's own
# "additive, doesn't gate the terminal step" rule (same rule the
# original taxonomy-shaped worked example established). 5-/4-stage are
# both pure linear chains — computed generically in _stage_depends_on
# below instead of a second hardcoded map.
_SIX_STAGE_DEPENDS_ON: dict[str, list[str]] = {
    "Fetch": [],
    "Classify (Primary)": ["Fetch"],
    "Classify (Secondary)": ["Fetch"],
    "Merge": ["Classify (Primary)", "Classify (Secondary)"],
    "Consult Expert": ["Merge"],
    "Store": ["Merge"],
}

# Per-stage description template + icon (operator, 2026-08-15: "update
# the Agents Data to have Icons and Description... Match the New Agent
# Data we added in the Taxonomy" — i.e. reuse the same real, specific
# phrasing style the taxonomy version's own Job prompts already
# established (src/backend/app/business/demo_taxonomy.py's own
# `_make_six_stage_jobs`/etc.), not the flat placeholder text this file
# had before, but still within THIS backend's existing flat
# type/section_id contract — "the new UI still Looks for Worker,
# Capture[-style Sections] and Expert", not the taxonomy's own
# Agent/Pipeline/Job shape). Only Fetch/Store carry an icon — keyed by
# stage NAME, one icon per stage kind, reused across every domain — the
# middle processing stages (Classify/Merge/Consult Expert/Summarize/
# Enrich) are the "some will not" half of the mixed icon coverage.
_STAGE_DESCRIPTIONS: dict[str, str] = {
    "Fetch": "Pulls the next unprocessed {domain} item into the pipeline — sample data only.",
    "Classify": "Classifies {domain} items by customer or topic — sample data only.",
    "Classify (Primary)": "Classifies the {domain} item's primary content — sample data only.",
    "Classify (Secondary)": "Classifies the {domain} item's secondary/attached content, if any — sample data only.",
    "Merge": "Combines parallel {domain} branches back into one enriched record — sample data only.",
    "Consult Expert": "Asks a domain Expert for prior-context enrichment on this {domain} item — sample data only.",
    "Summarize": "Summarizes the classified {domain} item's contents — sample data only.",
    "Enrich": "Enriches the {domain} record with related context — sample data only.",
    "Store": "Files the finished {domain} record into the vault — sample data only.",
}

# Operator, 2026-08-16: "Add Some Icons to the Agents and Jobs So I can
# See the Bugs" — previously only Fetch/Store had an icon, so most of the
# 142 generated stage-Agents rendered as plain empty circles, hiding any
# icon-related rendering bug (clipping, oval shape, contrast) from view.
# Every stage now gets one.
_STAGE_ICONS: dict[str, str] = {
    "Fetch": "download",
    "Classify": "category",
    "Classify (Primary)": "category",
    "Classify (Secondary)": "category",
    "Merge": "call_merge",
    "Consult Expert": "forum",
    "Summarize": "summarize",
    "Enrich": "auto_awesome",
    "Store": "save",
}

# Mutating/consulting stages get more oversight than pure read/classify
# ones (operator, 2026-08-15: "The Autonmous Agents will be Filled and
# Human Assistant will be a border..." needs real variety to actually
# see on the Map, not near-uniform "autonomous") — Store actually
# writes to the vault, Consult Expert reaches out to another Agent;
# both default to "supervised" rather than the "autonomous" every other
# stage keeps.
_STAGE_WORKING_MODES: dict[str, str] = {
    "Fetch": "autonomous",
    "Classify": "autonomous",
    "Classify (Primary)": "autonomous",
    "Classify (Secondary)": "autonomous",
    "Merge": "autonomous",
    "Consult Expert": "supervised",
    "Summarize": "autonomous",
    "Enrich": "autonomous",
    "Store": "supervised",
}


def _slug(text: str) -> str:
    return text.lower().replace(" ", "-").replace("&", "and")


def _stage_depends_on(domain_slug: str, stage_names: list[str], stage_index: int) -> list[str]:
    stage_name = stage_names[stage_index]
    if stage_names is _SIX_STAGE_NAMES:
        predecessor_names = _SIX_STAGE_DEPENDS_ON[stage_name]
    else:
        # Pure linear chain — every stage but the first depends only on
        # the one immediately before it.
        predecessor_names = [stage_names[stage_index - 1]] if stage_index > 0 else []
    return [f"{domain_slug}-{_slug(name)}" for name in predecessor_names]


def _make_stage_agent(
    domain: str, stage_names: list[str], stage_index: int, section_id: str, branch_target_agent_id: str | None,
) -> dict:
    stage_name = stage_names[stage_index]
    domain_slug = _slug(domain)
    agent_id = f"{domain_slug}-{_slug(stage_name)}"
    description = _STAGE_DESCRIPTIONS[stage_name].format(domain=domain.lower())
    return {
        "id": agent_id,
        "name": f"{domain} — {stage_name}",
        "type": "worker",
        "settings": [{"key": "Purpose", "value": description}],
        "capabilities": [],
        "section_id": section_id,
        "provider_id": "compass-demo",
        "keywords": [domain.lower(), stage_name.lower()],
        "working_mode": _STAGE_WORKING_MODES[stage_name],
        "scope": [],
        "is_background_agent": False,
        "icon": _STAGE_ICONS[stage_name],
        "color": None,
        "depends_on": _stage_depends_on(domain_slug, stage_names, stage_index),
        # Only the "Consult Expert" stage ever branches to an Expert —
        # every other stage's own connections are purely structural
        # (depends_on), no consultation.
        "branch_target_agent_id": branch_target_agent_id if stage_name == "Consult Expert" else None,
    }


def _generate_agents() -> dict[str, dict]:
    generated: dict[str, dict] = {}
    domain_iter = iter(_PIPELINE_DOMAINS)
    # Known ahead of generating the Experts themselves below (their ids
    # are fully deterministic from _EXPERT_DOMAINS) — every 6-stage
    # pipeline's own "Consult Expert" stage round-robins across this
    # same pool, real Expert Agents this data already has, not a
    # placeholder id.
    expert_pool = ["demo-vault-expert", "demo-ops-expert"] + [f"expert-{_slug(d)}" for d in _EXPERT_DOMAINS]

    stage_groups = [(_SIX_STAGE_NAMES, 10), (_FIVE_STAGE_NAMES, 10), (_FOUR_STAGE_NAMES, 8)]
    for stage_names, count in stage_groups:
        for i in range(count):
            domain = next(domain_iter)
            section_id = _GENERATED_SECTION_IDS[i % len(_GENERATED_SECTION_IDS)]
            branch_target = expert_pool[i % len(expert_pool)]
            for stage_index in range(len(stage_names)):
                agent = _make_stage_agent(domain, stage_names, stage_index, section_id, branch_target)
                generated[agent["id"]] = agent

    for i, domain in enumerate(_EXPERT_DOMAINS):
        agent_id = f"expert-{_slug(domain)}"
        section_id = _GENERATED_SECTION_IDS[i % len(_GENERATED_SECTION_IDS)]
        generated[agent_id] = {
            "id": agent_id,
            "name": f"{domain} Expert",
            "type": "expert",
            "settings": [{"key": "Domain", "value": f"{domain} questions — consulted by other Agents and Pipelines, and directly by chat or channel — sample data only."}],
            "capabilities": [],
            "section_id": section_id,
            "provider_id": "compass-demo",
            "keywords": [domain.lower()],
            "working_mode": _EXPERT_WORKING_MODES[domain],
            "scope": [],
            "is_background_agent": False,
            "icon": _EXPERT_ICONS[domain],
            "color": None,
            "depends_on": [],
            "branch_target_agent_id": None,
        }

    return generated


AGENTS.update(_generate_agents())

# Backfill Section.agent_ids and Provider.agent_ids now that every Agent
# (hand-authored + generated) actually exists — derived, not
# hand-maintained, so it can never drift out of sync with AGENTS itself.
for _agent in AGENTS.values():
    SECTIONS[_agent["section_id"]]["agent_ids"].append(_agent["id"])
PROVIDERS["compass-demo"]["agent_ids"] = list(AGENTS.keys())

_NEXT_AGENT_SEQ = [len(AGENTS) + 1]


def next_agent_id() -> str:
    seq = _NEXT_AGENT_SEQ[0]
    _NEXT_AGENT_SEQ[0] += 1
    return f"demo-agent-{seq}"
