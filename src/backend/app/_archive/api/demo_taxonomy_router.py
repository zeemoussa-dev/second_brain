from fastapi import APIRouter

from app.business import demo_taxonomy

router = APIRouter()


@router.get("/demo/agents")
def list_demo_agents() -> list[dict]:
    return demo_taxonomy.get_demo_agents()


@router.get("/demo/pipelines")
def list_demo_pipelines() -> list[dict]:
    return demo_taxonomy.get_demo_pipelines()
