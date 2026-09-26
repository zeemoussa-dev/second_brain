"""My Day's HTTP surface. The host mounts this router under `/plugins/my-day/`."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .day_view import DayOutsideWindowError, DayView
from .thread_emails import MessageNotFoundError, SubjectNotFoundError, ThreadEmails


def build_router(view: DayView, thread_emails: ThreadEmails) -> APIRouter:
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

    # The emails one Thread is made of, for this plugin's own Cockpit tab. The
    # Cockpit is a generic component; a Thread's shape is My Day's knowledge.
    @router.get("/threads/{subject_note_stem}/emails")
    def get_thread_emails(subject_note_stem: str) -> list[dict]:
        return thread_emails.list_for(subject_note_stem)

    # What the Emails tab reads: the thread's summary, its emails and its files.
    @router.get("/threads/{subject_note_stem}")
    def get_thread(subject_note_stem: str) -> dict:
        try:
            return thread_emails.detail_for(subject_note_stem)
        except SubjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail=f"No indexed note '{subject_note_stem}'") from exc

    @router.get("/threads/{subject_note_stem}/emails/{message_stem}")
    def get_thread_email(subject_note_stem: str, message_stem: str) -> dict:
        try:
            return thread_emails.body_for(subject_note_stem, message_stem)
        except (SubjectNotFoundError, MessageNotFoundError) as exc:
            raise HTTPException(status_code=404, detail=f"No email '{message_stem}' in this thread") from exc

    @router.post("/refresh")
    def post_refresh() -> list[dict]:
        return view.trigger_refresh()

    return router
