from fastapi import APIRouter

from app.version import get_loaded_commit, get_version

router = APIRouter()


@router.get("/health")
def get_service_health_status() -> dict[str, str | None]:
    return {"status": "ok", "version": get_version(), "commit": get_loaded_commit()}
