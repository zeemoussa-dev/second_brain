"""My Day's HTTP surface. The host mounts this router under `/plugins/my-day/`."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .day_view import DayOutsideWindowError, DayView


def build_router(view: DayView) -> APIRouter:
    router = APIRouter()

    def validated_day(day: str | None) -> str | None:
        try:
            return view.validate_day(day)
        except DayOutsideWindowError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/summary")
    def get_summary(day: str | None = None) -> dict:
        return view.summary(validated_day(day))

    @router.get("/emails")
    def get_emails(day: str | None = None) -> list[dict]:
        return view.list_email_items(validated_day(day))

    @router.get("/calendar")
    def get_calendar(day: str | None = None) -> list[dict]:
        return view.list_calendar_items(validated_day(day))

    @router.get("/todo")
    def get_todo() -> list[dict]:
        return view.list_todo_items()

    @router.post("/refresh")
    def post_refresh() -> list[dict]:
        return view.trigger_refresh()

    return router
