from fastapi import APIRouter

from app.business import agent_activity

router = APIRouter(prefix="/agent-activity")


@router.get("")
def get_agent_activity() -> dict:
    # Recomputed fresh on every call -- agent_activity.get_agent_activity()
    # has no caching of its own (Scenario 7).
    return agent_activity.get_agent_activity()
