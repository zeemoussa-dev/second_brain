from fastapi import APIRouter, HTTPException

from app.business import my_day
from app.business.logic import my_day_window

router = APIRouter(prefix="/my-day")


def _validated_day(day: str | None) -> str | None:
    try:
        return my_day_window.validate_day(day)
    except my_day_window.DayOutsideWindowError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/summary")
def get_summary(day: str | None = None) -> dict:
    return my_day.summary(_validated_day(day))


@router.get("/emails")
def get_emails(day: str | None = None) -> list[dict]:
    return my_day.list_email_items(_validated_day(day))


@router.get("/calendar")
def get_calendar(day: str | None = None) -> list[dict]:
    return my_day.list_calendar_items(_validated_day(day))


@router.get("/todo")
def get_todo() -> list[dict]:
    return my_day.list_todo_items()
