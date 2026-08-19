"""Standalone demo backend — a SEPARATE process from the real
src/backend app, deliberately NOT wired into it. Mirrors today's real
endpoint contract (same paths, same response shapes) but every route
reads/writes the plain in-memory dicts in sample_data.py: no Outlook,
no Compass, no vault I/O, no Skill/Tool execution, no persistence
across restarts. Purpose: let the frontend be pointed at this server
(VITE_API_BASE_URL) to keep iterating on UI without depending on the
real backend's actual logic — once the UI is settled, the gaps this
surfaces get built for real against src/backend, this server is not
that build target itself.

Deliberately NOT layered into api/business/data_access (ADR-003) —
that separation exists for the real app's own long-lived business
rules; this file has none, on purpose.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import sample_data as data

app = FastAPI(title="Second Brain — Demo Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", "http://127.0.0.1:5173",
        "http://localhost:5174", "http://127.0.0.1:5174",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _agent_or_404(agent_id: str) -> dict:
    agent = data.AGENTS.get(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Unknown agent")
    return agent


def _agent_summary(agent: dict) -> dict:
    return {
        "id": agent["id"],
        "name": agent["name"],
        "type": agent["type"],
        "section_id": agent["section_id"],
        "is_background_agent": agent["is_background_agent"],
        "icon": agent["icon"],
        "color": agent["color"],
        # First settings entry's own value ("Purpose" for worker/producer,
        # "Domain" for expert — sample_data.py's own per-agent settings
        # convention, already shown in AgentDetailPanel's Settings tab) —
        # exposed here too (not just on the detail fetch) so the Map's own
        # hover card (operator, 2026-08-16: "show the Agent name we zoomed
        # on and a Description of that Agent if Exist") has it up front,
        # without an extra per-agent fetch on every hover.
        "description": agent["settings"][0]["value"] if agent["settings"] else None,
        # Mirrors the real backend's own list_agents() — it already
        # includes working_mode in the summary shape, this one didn't
        # yet (operator, 2026-08-15: "The Autonmous Agents will be
        # Filled and Human Assistant will be a border..." needs it on
        # every Map node, not just the full per-agent detail fetch).
        "working_mode": agent["working_mode"],
        # LangGraph-style connection data (operator, 2026-08-15: "Check
        # Langraph Data and Add that to the Agent info... so we can
        # start having a tree view") — see sample_data.py's own AGENTS
        # docstring for the full field-meaning writeup. On the summary
        # too, not just the detail fetch below, since a future tree
        # view needs every Agent's own connections up front to lay the
        # whole Map out, not one at a time.
        "depends_on": agent["depends_on"],
        "branch_target_agent_id": agent["branch_target_agent_id"],
    }


def _agent_detail(agent: dict) -> dict:
    section = data.SECTIONS.get(agent["section_id"])
    provider = data.PROVIDERS.get(agent["provider_id"])
    return {
        "id": agent["id"],
        "name": agent["name"],
        "type": agent["type"],
        "settings": agent["settings"],
        "capabilities": agent["capabilities"],
        "section_id": agent["section_id"],
        "section_name": section["name"] if section else None,
        "provider_id": agent["provider_id"],
        "provider_name": provider["name"] if provider else None,
        "provider_available": provider["has_real_client"] if provider else False,
        "keywords": agent["keywords"],
        "working_mode": agent["working_mode"],
        "scope": agent["scope"],
        "is_background_agent": agent["is_background_agent"],
        "icon": agent["icon"],
        "color": agent["color"],
        "depends_on": agent["depends_on"],
        "branch_target_agent_id": agent["branch_target_agent_id"],
    }


class AgentUpdateBody(BaseModel):
    section_id: str | None = None
    provider_id: str | None = None
    keywords: list[str] | None = None
    working_mode: str | None = None
    scope: list[str] | None = None
    is_background_agent: bool | None = None
    icon: str | None = None
    color: str | None = None


class CreateAgentBody(BaseModel):
    name: str
    type: str
    domain: str | None = None
    purpose: str | None = None
    trigger: str | None = None


class ChatMessageBody(BaseModel):
    message: str


@app.get("/agents")
def list_agents() -> list[dict]:
    return [_agent_summary(agent) for agent in data.AGENTS.values()]


@app.post("/agents")
def create_agent(body: CreateAgentBody) -> dict:
    agent_id = data.next_agent_id()
    section_id = next(iter(data.SECTIONS), None)
    provider_id = next(iter(data.PROVIDERS), None)
    setting_value = body.domain or body.purpose or "Sample data only."
    data.AGENTS[agent_id] = {
        "id": agent_id,
        "name": body.name,
        "type": body.type,
        "settings": [{"key": "Purpose", "value": setting_value}],
        "capabilities": [],
        "section_id": section_id,
        "provider_id": provider_id,
        "keywords": [],
        "working_mode": "autonomous",
        "scope": [],
        "is_background_agent": False,
        "icon": None,
        "color": None,
        "depends_on": [],
        "branch_target_agent_id": None,
    }
    data.AGENT_SKILL_GRANTS[agent_id] = set()
    return _agent_detail(data.AGENTS[agent_id])


@app.get("/agents/{agent_id}")
def get_agent(agent_id: str) -> dict:
    return _agent_detail(_agent_or_404(agent_id))


@app.patch("/agents/{agent_id}")
def update_agent(agent_id: str, body: AgentUpdateBody) -> dict:
    agent = _agent_or_404(agent_id)
    if body.section_id is not None:
        agent["section_id"] = body.section_id
    if body.provider_id is not None:
        agent["provider_id"] = body.provider_id
    if body.keywords is not None:
        agent["keywords"] = body.keywords
    if body.working_mode is not None:
        agent["working_mode"] = body.working_mode
    if body.scope is not None:
        agent["scope"] = body.scope
    if body.is_background_agent is not None:
        agent["is_background_agent"] = body.is_background_agent
    if body.icon is not None:
        agent["icon"] = body.icon or None
    if body.color is not None:
        agent["color"] = body.color or None
    return _agent_detail(agent)


@app.get("/agents/{agent_id}/history")
def get_history(agent_id: str) -> list[dict]:
    _agent_or_404(agent_id)
    return data.AGENT_HISTORY.get(agent_id, [])


@app.post("/agents/{agent_id}/chat")
def chat(agent_id: str, body: ChatMessageBody) -> dict:
    agent = _agent_or_404(agent_id)
    reply = f"[Demo backend — no real model wired up] {agent['name']} received: \"{body.message}\""
    data.AGENT_HISTORY.setdefault(agent_id, []).append(
        {"kind": "chat_user", "text": body.message, "timestamp": "1970-01-01T00:00:00Z"},
    )
    data.AGENT_HISTORY[agent_id].append(
        {"kind": "chat_agent", "text": reply, "timestamp": "1970-01-01T00:00:00Z"},
    )
    return {"reply": reply, "action_triggered": None}


@app.get("/agents/{agent_id}/knowledge-gaps")
def get_knowledge_gaps(agent_id: str) -> dict:
    _agent_or_404(agent_id)
    return {"gaps": [], "open_count": 0}


@app.get("/agents/{agent_id}/skills")
def get_agent_skills(agent_id: str) -> list[dict]:
    _agent_or_404(agent_id)
    granted = data.AGENT_SKILL_GRANTS.get(agent_id, set())
    return [skill for skill in data.SKILLS.values() if skill["id"] in granted]


@app.post("/agents/{agent_id}/skills/{skill_id}")
def grant_skill(agent_id: str, skill_id: str) -> dict:
    _agent_or_404(agent_id)
    if skill_id not in data.SKILLS:
        raise HTTPException(status_code=404, detail="Unknown skill")
    data.AGENT_SKILL_GRANTS.setdefault(agent_id, set()).add(skill_id)
    return {"granted": True}


@app.delete("/agents/{agent_id}/skills/{skill_id}")
def revoke_skill(agent_id: str, skill_id: str) -> dict:
    _agent_or_404(agent_id)
    data.AGENT_SKILL_GRANTS.setdefault(agent_id, set()).discard(skill_id)
    return {"revoked": True}


@app.get("/agents/{agent_id}/schedules")
def get_schedules(agent_id: str) -> list[dict]:
    _agent_or_404(agent_id)
    return data.AGENT_SCHEDULES.get(agent_id, [])


@app.get("/sections")
def list_sections() -> list[dict]:
    return list(data.SECTIONS.values())


@app.get("/providers")
def list_providers() -> list[dict]:
    return list(data.PROVIDERS.values())


@app.get("/skills")
def list_skills() -> list[dict]:
    return list(data.SKILLS.values())


@app.get("/vault-search/scope-suggestions")
def scope_suggestions() -> dict:
    return {"tags": [], "folders": []}
