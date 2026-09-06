"""Failures must reach the operator as something they can act on.

Three reports, one theme: the server knew what went wrong and the user saw
either nothing or the wrong thing.
"""
import json

import pytest
import websockets.exceptions
from fastapi import APIRouter
from fastapi.testclient import TestClient

import app.main as main_app
from app.business.hermes import chat_sessions
from app.business.logic import agent_chat_stream

_router = APIRouter()


@_router.get("/__test_boom")
def _boom():
    raise RuntimeError("kaboom")


main_app.app.include_router(_router)
client = TestClient(main_app.app, raise_server_exceptions=False)


def test_an_unhandled_error_is_a_readable_500_not_a_dropped_connection() -> None:
    """BUG-045: FastAPI mounts ServerErrorMiddleware ABOVE user middleware, so
    a 500 skipped CORS and the browser saw `TypeError: Failed to fetch` -- no
    status, no body, indistinguishable from the backend being down."""
    response = client.get("/__test_boom", headers={"Origin": "http://localhost:5173"})

    assert response.status_code == 500
    assert response.json()["detail"] == "The server failed handling this request."
    assert "access-control-allow-origin" in {k.lower() for k in response.headers}


def test_the_500_body_does_not_leak_the_traceback() -> None:
    """Truthful, not verbose: the operator gets something to act on, the
    traceback stays in the server log."""
    body = client.get("/__test_boom").text

    assert "kaboom" not in body and "Traceback" not in body


def test_a_dropped_socket_yields_an_error_frame_not_an_empty_200(monkeypatch) -> None:
    """BUG-050: the WS closing mid-turn raised after StreamingResponse had
    already sent headers, so the client got HTTP 200 with zero bytes -- a turn
    that looks successful and produced nothing."""
    import asyncio

    class _Session:
        async def send_prompt(self, message):
            raise websockets.exceptions.ConnectionClosedError(None, None)

    async def _get_or_create(agent_id):
        return _Session()

    monkeypatch.setattr(chat_sessions, "get_or_create_session", _get_or_create)
    monkeypatch.setattr(chat_sessions, "discard_session", lambda aid: asyncio.sleep(0))

    async def collect():
        return [frame async for frame in agent_chat_stream.stream_chat_turn("default", "hi")]

    frames = asyncio.run(collect())

    assert len(frames) == 1
    payload = json.loads(frames[0].removeprefix("data: ").strip())
    assert payload["type"] == "error"
    assert "dropped mid-turn" in payload["detail"], "must name WHAT failed"


def test_hermes_unreachable_is_visible_in_boot_status() -> None:
    """BUG-049: the stage read `done` whether the check passed or failed, so
    boot-status said ready with error: null while agent chat could not work."""
    status = client.post("/boot-status/recheck-hermes").json()

    stage = next(s for s in status["stages"] if s["id"] == "checking_hermes")
    expected = "done" if status["hermes_reachable"] else "failed"
    assert stage["status"] == expected
