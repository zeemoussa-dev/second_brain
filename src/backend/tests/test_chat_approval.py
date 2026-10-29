"""Answering what an agent is blocked on (`ADR-006`; operator,
2026-10-24: "it needs some approval to parse JSON, when I reply Always
Approve something crash").

The failure: an `approval.request` was rendered as the turn's own reply
and the `request_id` thrown away, so Hermes sat holding the turn open
waiting for `approval.respond` while the operator's typed answer went
in as a brand-new `prompt.submit`. Nothing ever answered the thing it
was actually waiting for.

`agents_router.py` documented this as unavoidable in August -- "this
REST turn has nowhere to hold that `request_id`". That stopped being
true on 2026-08-24, when sessions began being kept alive per agent: the
id now outlives the request that produced it.

`respond_approval(request_id, choice, resolve_all)` had existed on the
session object the whole time, never called from anywhere. `resolve_all`
is exactly "always approve", and is not expressible as typed text at
all -- which is why that reply could not have worked however it was
phrased.
"""
import asyncio

import pytest

from app.business.hermes import chat_sessions


@pytest.fixture(autouse=True)
def nothing_pending_between_tests():
    chat_sessions._pending_approvals.clear()
    yield
    chat_sessions._pending_approvals.clear()


AN_AGENT = "adnoc-expert"


def test_an_approval_request_is_remembered_against_its_agent() -> None:
    """[ADR-006] The id is what makes an answer possible at all."""
    chat_sessions.remember_approval(AN_AGENT, {
        "request_id": "req-1", "command": "execute_code <<'PY' ...", "reason": "reads a file",
    })

    pending = chat_sessions.pending_approval(AN_AGENT)
    assert pending is not None
    assert pending["request_id"] == "req-1"
    assert pending["command"].startswith("execute_code")


def test_a_request_with_no_id_is_not_remembered() -> None:
    """[ADR-006] An approval with no id cannot be answered, and holding
    it would offer a button that does nothing."""
    chat_sessions.remember_approval(AN_AGENT, {"command": "do a thing"})

    assert chat_sessions.pending_approval(AN_AGENT) is None


def test_one_agents_approval_is_not_anothers() -> None:
    """[ADR-006] Approving on one agent must never answer a request
    another agent is blocked on."""
    chat_sessions.remember_approval(AN_AGENT, {"request_id": "req-adnoc", "command": "a"})
    chat_sessions.remember_approval("masdar-expert", {"request_id": "req-masdar", "command": "b"})

    assert chat_sessions.pending_approval(AN_AGENT)["request_id"] == "req-adnoc"
    assert chat_sessions.pending_approval("masdar-expert")["request_id"] == "req-masdar"


def test_answering_forgets_it_so_it_cannot_be_answered_twice() -> None:
    """[ADR-006] A resolved request must not stay offerable: answering
    a stale id would approve whatever the agent asked NEXT, which is
    the one mistake an approval must never make."""
    chat_sessions.remember_approval(AN_AGENT, {"request_id": "req-1", "command": "a"})

    chat_sessions.forget_approval(AN_AGENT)

    assert chat_sessions.pending_approval(AN_AGENT) is None


def test_discarding_a_session_drops_what_it_was_waiting_on() -> None:
    """[ADR-006] The id belongs to a session. When that session is gone
    -- dropped as dead, or reset by the operator -- the id can never be
    answered, so it must not survive it."""
    chat_sessions.remember_approval(AN_AGENT, {"request_id": "req-1", "command": "a"})

    asyncio.run(chat_sessions.discard_session(AN_AGENT))

    assert chat_sessions.pending_approval(AN_AGENT) is None


def test_answering_nothing_is_refused_rather_than_guessed_at() -> None:
    """[ADR-006] With nothing pending the stream says so instead of
    inventing an id. Hermes auto-resolves an approval on its own
    timeout, so "already answered" is an ordinary state, not an error
    in the caller."""
    from app.business.logic import agent_chat_stream

    async def collect() -> list[str]:
        return [
            frame
            async for frame in agent_chat_stream.answer_approval(AN_AGENT, "approve", False)
        ]

    frames = asyncio.run(collect())

    assert len(frames) == 1
    assert '"type": "error"' in frames[0]
    assert "nothing waiting for your approval" in frames[0]


def test_the_formatted_text_still_says_what_is_being_asked_for() -> None:
    """[ADR-006] The buttons are the new part; the question itself is
    unchanged, and still carries the command so the operator can see
    what they are allowing."""
    said = chat_sessions.format_approval_request({
        "request_id": "req-1",
        "command": "execute_code <<'PY' import json",
        "reason": "needs to read the index",
    })

    assert "execute_code" in said
    assert "needs to read the index" in said
