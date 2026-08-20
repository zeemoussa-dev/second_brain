from fastapi import APIRouter

from app.business import system_health

router = APIRouter(prefix="/system-health")


@router.get("")
def get_system_health() -> dict:
    # Recomputed fresh on every call -- system_health.get_system_health()
    # has no caching of its own (Scenario 7).
    return system_health.get_system_health()
