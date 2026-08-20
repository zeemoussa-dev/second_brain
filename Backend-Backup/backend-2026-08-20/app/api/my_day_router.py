from fastapi import APIRouter, HTTPException

from app.business import my_day

router = APIRouter(prefix="/my-day")


def _validate_day(day: str | None) -> str | None:
    """A `day` query param is only meaningful (and only safe to hand to
    my_day's string-prefix date comparisons) if it's a real date inside
    the current 7-day window — the same day-navigator a user could
    actually reach. Anything else is a 400, not a silently-empty result
    or a window bypass."""
    if day is None:
        return None
    window_start, window_end = my_day._compute_window()
    if not (window_start <= day <= window_end):
        raise HTTPException(
            status_code=400,
            detail=f"day must be within the current window ({window_start} to {window_end})",
        )
    return day


@router.get("/summary")
def get_summary(day: str | None = None) -> dict:
    return my_day.summary(_validate_day(day))


@router.get("/emails")
def get_emails(day: str | None = None) -> list[dict]:
    return my_day.list_email_items(_validate_day(day))


@router.get("/calendar")
def get_calendar(day: str | None = None) -> list[dict]:
    return my_day.list_calendar_items(_validate_day(day))


@router.get("/todo")
def get_todo() -> list[dict]:
    return my_day.list_todo_items()
