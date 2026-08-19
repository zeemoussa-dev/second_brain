"""In-memory sample data shaped to the Agent/Pipeline/Job/Hub taxonomy
(ADR-041) — a demo fixture only, not a real persisted registry. Exists so
the frontend can build against the new domain model's actual shape (two
independent axes: kind-of-work x structural-tier; Pipelines as
user-extensible DAGs, not fixed chains) before the real Pipeline
execution engine/builder exist. Mirrors the operator's own worked
example verbatim (2026-08-15 taxonomy dump): an inbound email forks into
a body-summary Job and an attachment-summary Job, merges back into one
stream, additively branches to a standalone Ops Expert Agent for
prior-context enrichment, then stores — the Store step is not gated on
the Expert branch completing, per ADR-041's own "additive, not a
replacement for the terminal step" rule.
"""

_DEMO_AGENTS: list[dict] = [
    {
        "id": "ops-expert",
        "name": "Ops Expert",
        "kind": "expert",
        "hub_id": "hub-sales",
        "description": (
            "Domain expert on deals and accounts — answers whether we've "
            "worked with a given account before and what happened. "
            "Consulted by other Agents and Pipelines, and directly by chat "
            "or channel."
        ),
        "working_mode": "autonomous",
        "addressable_by": ["chat", "channel", "pipeline", "agent"],
    },
    {
        "id": "vault-expert",
        "name": "Vault Expert",
        "kind": "expert",
        "hub_id": "hub-capture",
        "description": (
            "Domain expert on what has already been captured and filed in "
            "the vault for a given customer or topic."
        ),
        "working_mode": "autonomous",
        "addressable_by": ["chat", "channel", "pipeline", "agent"],
    },
    {
        "id": "email-reply-producer",
        "name": "Email Reply Drafter",
        "kind": "producer",
        "hub_id": "hub-capture",
        "description": (
            "Builds a draft email response on request — a standalone "
            "Producer Agent (asked directly), not a Job embedded in "
            "someone else's Pipeline."
        ),
        "working_mode": "supervised",
        "addressable_by": ["chat", "channel"],
    },
]

_DEMO_PIPELINES: list[dict] = [
    {
        # REQ-SB-55-US-01-T08: renamed from the coincidentally-matching
        # "pipeline-email-capture" id (it never had any real coupling to
        # app/business/agent_registry.py's own now-retired "email-capture"
        # id -- this is an in-memory Pipeline Builder UI demo fixture
        # only) to avoid reader confusion with the real, shipped
        # "email-capture-pipeline" Agent-tier identity this task
        # introduces.
        "id": "pipeline-inbound-email-demo",
        "name": "Inbound Email Pipeline (Demo)",
        "hub_id": "hub-capture",
        "description": (
            "Receives an inbound email, classifies/summarizes its body and "
            "any attachment in parallel, merges both back into one stream, "
            "additively consults the Ops Expert for prior-context "
            "enrichment, then stores the result in the vault."
        ),
        "jobs": [
            {
                "id": "pull-email",
                "name": "Pull Email",
                "kind": "fetch",
                "prompt": "Pull the next unread email from the inbox.",
                "skills": ["outlook-mail-read"],
                "depends_on": [],
            },
            {
                "id": "classify-summarize-body",
                "name": "Classify & Summarize Body",
                "kind": "classify",
                "prompt": "Classify this email by customer and summarize its body.",
                "skills": ["compass-classify", "compass-summarize"],
                "depends_on": ["pull-email"],
            },
            {
                "id": "classify-summarize-attachment",
                "name": "Classify & Summarize Attachment",
                "kind": "classify",
                "prompt": "Classify and summarize the email's attachment, if any.",
                "skills": ["attachment-extract", "compass-summarize"],
                "depends_on": ["pull-email"],
            },
            {
                "id": "merge-summaries",
                "name": "Merge Summaries",
                "kind": "merge",
                "prompt": "Combine the body and attachment summaries into one enriched record.",
                "skills": [],
                "depends_on": ["classify-summarize-body", "classify-summarize-attachment"],
            },
            {
                "id": "consult-ops-expert",
                "name": "Consult Ops Expert",
                "kind": "branch-to-expert",
                "prompt": "Ask the Ops Expert whether we've worked with this account before.",
                "skills": [],
                "depends_on": ["merge-summaries"],
                "branch_target_agent_id": "ops-expert",
                "notes": "Additive enrichment — does not gate the Store step below.",
            },
            {
                "id": "store-in-vault",
                "name": "Store in Vault",
                "kind": "store",
                "prompt": "File the enriched email record into the vault, linked to the customer hub.",
                "skills": ["vault-write"],
                "depends_on": ["merge-summaries"],
            },
        ],
    },
]


# ---------------------------------------------------------------------------
# Bulk generated sample set (operator, 2026-08-15: "Generate a Sample Agents
# 150 Agents that Match the new Taxonomy some of them are 6 Stages Pipeline
# and some are 5 Stages and Some are 4 and Few Experts so we can do some Real
# UI Checks") — additive to the hand-authored worked example above, which
# stays untouched as the one real-narrative reference. Procedurally built,
# not hand-written, since the point is raw volume/variety for UI density
# testing (many Hubs, many Pipelines of different DAG shapes, a realistic
# Job-count spread), not per-entry realism. 10 six-stage + 10 five-stage + 8
# four-stage Pipelines (60 + 50 + 32 = 142 Jobs) + 8 standalone Experts = 150
# generated entities on top of the worked example's own 1 Pipeline/6 Jobs +
# 3 Agents.
_GENERATED_HUB_IDS = [
    "hub-capture", "hub-sales", "hub-support", "hub-hr",
    "hub-finance", "hub-legal", "hub-marketing",
]

# 28 distinct domains — one per generated Pipeline (10 six-stage + 10
# five-stage + 8 four-stage), each a plausible "thing a Pipeline processes".
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

# 8 domains for the standalone generated Experts.
_EXPERT_DOMAINS = [
    "Legal", "HR", "Finance", "Security", "Compliance", "Product",
    "Marketing", "Support",
]


def _slug(text: str) -> str:
    return text.lower().replace(" ", "-").replace("&", "and")


def _make_four_stage_jobs(domain_slug: str) -> list[dict]:
    """Linear: fetch -> classify -> enrich -> store."""
    return [
        {"id": f"{domain_slug}-fetch", "name": "Fetch", "kind": "fetch",
         "prompt": f"Pull the next unprocessed {domain_slug.replace('-', ' ')} item.",
         "skills": [], "depends_on": []},
        {"id": f"{domain_slug}-classify", "name": "Classify", "kind": "classify",
         "prompt": "Classify this item by customer/topic.",
         "skills": ["compass-classify"], "depends_on": [f"{domain_slug}-fetch"]},
        {"id": f"{domain_slug}-enrich", "name": "Enrich", "kind": "enrich",
         "prompt": "Summarize and enrich the classified item.",
         "skills": ["compass-summarize"], "depends_on": [f"{domain_slug}-classify"]},
        {"id": f"{domain_slug}-store", "name": "Store", "kind": "store",
         "prompt": "File the enriched item into the vault.",
         "skills": ["vault-write"], "depends_on": [f"{domain_slug}-enrich"]},
    ]


def _make_five_stage_jobs(domain_slug: str) -> list[dict]:
    """Linear: fetch -> classify -> summarize -> enrich -> store."""
    return [
        {"id": f"{domain_slug}-fetch", "name": "Fetch", "kind": "fetch",
         "prompt": f"Pull the next unprocessed {domain_slug.replace('-', ' ')} item.",
         "skills": [], "depends_on": []},
        {"id": f"{domain_slug}-classify", "name": "Classify", "kind": "classify",
         "prompt": "Classify this item by customer/topic.",
         "skills": ["compass-classify"], "depends_on": [f"{domain_slug}-fetch"]},
        {"id": f"{domain_slug}-summarize", "name": "Summarize", "kind": "summarize",
         "prompt": "Summarize the classified item's contents.",
         "skills": ["compass-summarize"], "depends_on": [f"{domain_slug}-classify"]},
        {"id": f"{domain_slug}-enrich", "name": "Enrich", "kind": "enrich",
         "prompt": "Enrich the summary with related context.",
         "skills": [], "depends_on": [f"{domain_slug}-summarize"]},
        {"id": f"{domain_slug}-store", "name": "Store", "kind": "store",
         "prompt": "File the enriched item into the vault.",
         "skills": ["vault-write"], "depends_on": [f"{domain_slug}-enrich"]},
    ]


def _make_six_stage_jobs(domain_slug: str, branch_target_agent_id: str) -> list[dict]:
    """Fork/merge/branch-to-expert, same shape as the worked email example:
    fetch -> {classify-a, classify-b} -> merge -> branch-to-expert -> store."""
    return [
        {"id": f"{domain_slug}-fetch", "name": "Fetch", "kind": "fetch",
         "prompt": f"Pull the next unprocessed {domain_slug.replace('-', ' ')} item.",
         "skills": [], "depends_on": []},
        {"id": f"{domain_slug}-classify-a", "name": "Classify (Primary)", "kind": "classify",
         "prompt": "Classify the item's primary content.",
         "skills": ["compass-classify"], "depends_on": [f"{domain_slug}-fetch"]},
        {"id": f"{domain_slug}-classify-b", "name": "Classify (Secondary)", "kind": "classify",
         "prompt": "Classify the item's secondary/attached content, if any.",
         "skills": ["compass-classify"], "depends_on": [f"{domain_slug}-fetch"]},
        {"id": f"{domain_slug}-merge", "name": "Merge", "kind": "merge",
         "prompt": "Combine the primary and secondary classifications into one record.",
         "skills": [], "depends_on": [f"{domain_slug}-classify-a", f"{domain_slug}-classify-b"]},
        {"id": f"{domain_slug}-consult-expert", "name": "Consult Expert", "kind": "branch-to-expert",
         "prompt": "Ask the domain Expert for prior-context enrichment.",
         "skills": [], "depends_on": [f"{domain_slug}-merge"],
         "branch_target_agent_id": branch_target_agent_id,
         "notes": "Additive enrichment — does not gate the Store step below."},
        {"id": f"{domain_slug}-store", "name": "Store", "kind": "store",
         "prompt": "File the enriched record into the vault.",
         "skills": ["vault-write"], "depends_on": [f"{domain_slug}-merge"]},
    ]


def _generate_agents_and_pipelines() -> tuple[list[dict], list[dict]]:
    experts: list[dict] = []
    for index, domain in enumerate(_EXPERT_DOMAINS):
        experts.append({
            "id": f"expert-{_slug(domain)}",
            "name": f"{domain} Expert",
            "kind": "expert",
            "hub_id": _GENERATED_HUB_IDS[index % len(_GENERATED_HUB_IDS)],
            "description": f"Domain expert on {domain.lower()} questions — consulted by other Agents and Pipelines, and directly by chat or channel.",
            "working_mode": "autonomous",
            "addressable_by": ["chat", "channel", "pipeline", "agent"],
        })

    # Every generated 6-stage Pipeline's branch-to-expert Job targets one of
    # the two hand-authored Experts or one of the 8 generated ones above,
    # round-robin — so the generated set exercises real cross-references
    # into both the worked example's own Experts and its own new ones.
    expert_pool = ["ops-expert", "vault-expert"] + [expert["id"] for expert in experts]

    pipelines: list[dict] = []
    domain_iter = iter(_PIPELINE_DOMAINS)

    for i in range(10):
        domain = next(domain_iter)
        slug = _slug(domain)
        branch_target = expert_pool[i % len(expert_pool)]
        pipelines.append({
            "id": f"pipeline-{slug}-6stage",
            "name": f"{domain} Pipeline",
            "hub_id": _GENERATED_HUB_IDS[i % len(_GENERATED_HUB_IDS)],
            "description": f"Processes inbound {domain.lower()}: forks into parallel classification, merges, consults an Expert, then stores.",
            "jobs": _make_six_stage_jobs(slug, branch_target),
        })

    for i in range(10):
        domain = next(domain_iter)
        slug = _slug(domain)
        pipelines.append({
            "id": f"pipeline-{slug}-5stage",
            "name": f"{domain} Pipeline",
            "hub_id": _GENERATED_HUB_IDS[i % len(_GENERATED_HUB_IDS)],
            "description": f"Processes inbound {domain.lower()}: classifies, summarizes, enriches, then stores.",
            "jobs": _make_five_stage_jobs(slug),
        })

    for i in range(8):
        domain = next(domain_iter)
        slug = _slug(domain)
        pipelines.append({
            "id": f"pipeline-{slug}-4stage",
            "name": f"{domain} Pipeline",
            "hub_id": _GENERATED_HUB_IDS[i % len(_GENERATED_HUB_IDS)],
            "description": f"Processes inbound {domain.lower()}: classifies, enriches, then stores.",
            "jobs": _make_four_stage_jobs(slug),
        })

    return experts, pipelines


_GENERATED_EXPERTS, _GENERATED_PIPELINES = _generate_agents_and_pipelines()


def get_demo_agents() -> list[dict]:
    return _DEMO_AGENTS + _GENERATED_EXPERTS


def get_demo_pipelines() -> list[dict]:
    return _DEMO_PIPELINES + _GENERATED_PIPELINES
