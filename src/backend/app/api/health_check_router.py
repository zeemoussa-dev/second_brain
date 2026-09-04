from fastapi import APIRouter

from app.version import get_version

router = APIRouter()


@router.get("/health")
def get_service_health_status() -> dict[str, str]:
    return {"status": "ok", "version": get_version()}
