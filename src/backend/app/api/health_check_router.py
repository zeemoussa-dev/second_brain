from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def get_service_health_status() -> dict[str, str]:
    return {"status": "ok"}
