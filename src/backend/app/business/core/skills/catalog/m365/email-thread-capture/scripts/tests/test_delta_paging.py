"""The delta's paging and watermark: what decides whether an email is captured
once, retried, or lost forever.

Run from this Skill's own scripts/ folder:
    python -m pytest tests/test_delta_paging.py

Two incidents shape these. 2026-09-04: the watermark advanced past failed
ingests and 54 emails were never written. 2026-09-11: the delta paged backward
from "now" and saved its watermark only at the end, so a backlog bigger than
one hour was killed by Hermes every run with nothing saved -- it could never
catch up. The fix pages forward from the watermark and saves after each email.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import run_delta_capture as rdc  # noqa: E402

T0 = "2026-09-09 10:00:00.000000+00:00"


def stamp(minute: int, second: int = 0) -> str:
    return f"2026-09-10 12:{minute:02d}:{second:02d}.000000+00:00"


def email(message_id: str, received: str, conversation: str = "conv") -> dict:
    return {"id": message_id, "conversation_id": conversation, "received": received,
            "subject": message_id, "sender_name": "", "sender_email": "", "body": "",
            "recipients": [], "direction": "received", "attachments": []}


# ── trim_page / advance_points ────────────────────────────────────────────

def test_a_short_page_is_the_last_and_comes_back_oldest_first():
    kept, held, final = rdc.trim_page([email("b", stamp(2)), email("a", stamp(1))], 50)
    assert [e["id"] for e in kept] == ["a", "b"] and held == [] and final


def test_a_full_page_holds_back_its_newest_second():
    page = [email("a", stamp(1)), email("b", stamp(2)), email("c", stamp(2))]
    kept, held, final = rdc.trim_page(page, 3)
    assert [e["id"] for e in kept] == ["a"]
    assert sorted(e["id"] for e in held) == ["b", "c"] and not final


def test_a_full_page_of_one_second_is_captured_whole():
    page = [email("a", stamp(1)), email("b", stamp(1))]
    kept, held, final = rdc.trim_page(page, 2)
    assert len(kept) == 2 and held == [] and not final


def test_the_watermark_never_stops_between_two_emails_of_one_second():
    kept = [email("a", stamp(1)), email("b", stamp(2)), email("c", stamp(2)), email("d", stamp(3))]
    assert rdc.advance_points(kept, last_is_safe=False) == [True, False, True, False]
    assert rdc.advance_points(kept, last_is_safe=True)[-1] is True


def test_an_email_with_no_timestamp_never_moves_the_watermark():
    assert rdc.advance_points([email("a", "")], last_is_safe=True) == [False]


def test_downloads_of_emails_not_captured_are_deleted(tmp_path):
    kept_file = tmp_path / "keep.bin"
    gone = tmp_path / "gone.bin"
    kept_file.write_bytes(b"x")
    gone.write_bytes(b"x")
    held = email("a", stamp(1))
    held["attachments"] = [{"filename": "f", "temp_path": str(gone), "size": 1},
                           {"filename": "g", "temp_path": str(tmp_path / "missing"), "size": 1}]
    rdc.discard_downloads([held])
    assert not gone.exists() and kept_file.exists()


# ── already in the vault ──────────────────────────────────────────────────

def _thread(vault: Path, conversation: str, message_ids: list[str]) -> None:
    thread = vault / "Work" / "Threads" / "2026-09-10 Example"
    (thread / "messages").mkdir(parents=True)
    (thread / "2026-09-10 Example.md").write_text(
        f'---\ntype: "Thread"\nid: "{conversation}"\n---\n', encoding="utf-8")
    for message_id in message_ids:
        (thread / "messages" / f"{message_id}.md").write_text(
            f'---\ntype: "RawMessage"\nconversation_id: "{conversation}"\n'
            f'message_id: "{message_id}"\n---\n', encoding="utf-8")


def test_an_email_already_in_the_vault_is_found_by_its_natural_key(tmp_path):
    _thread(tmp_path, "conv", ["m1"])
    threads = rdc.captured_threads(tmp_path)
    assert rdc.already_captured(threads, "conv", "m1").name == "m1.md"
    assert rdc.already_captured(threads, "conv", "m2") is None
    assert rdc.already_captured(threads, "other", "m1") is None


# ── a whole run, against a fake mailbox ───────────────────────────────────

class FakeMailbox:
    """Stands in for list_recent_emails.py and the per-email scripts."""

    def __init__(self, emails, fail=(), stop_after=None):
        self.emails = sorted(emails, key=lambda e: e["received"])
        self.fail = set(fail)
        self.ingested: list[str] = []
        self.stop_after = stop_after
        self.now = 0.0

    def clock(self) -> float:
        return self.now

    def run_script(self, args):
        name = args[0]
        if name == "list_recent_emails.py":
            since = args[args.index("--since") + 1]
            limit = int(args[args.index("--limit") + 1])
            assert "--oldest-first" in args
            page = [e for e in self.emails if e["received"] > since][:limit]
            return 0, json.dumps(page), ""
        if name == "ingest_email.py":
            payload = json.loads(Path(args[args.index("--input-file") + 1]).read_text(encoding="utf-8"))
            self.ingested.append(payload["message_id"])
            if self.stop_after is not None and len(self.ingested) >= self.stop_after:
                self.now = 10 ** 9            # the run's time is up after this email
            if payload["message_id"] in self.fail:
                return 1, "", "boom"
            return 0, json.dumps({"message_created": True, "message_path": "x"}), ""
        return 0, "{}", ""


@pytest.fixture()
def delta(tmp_path, monkeypatch):
    state = tmp_path / "state.json"
    state.write_text(json.dumps({"last_captured_at": T0}), encoding="utf-8")
    monkeypatch.setattr(rdc, "VAULT_PATH", str(tmp_path))
    monkeypatch.setattr(rdc, "_state_path", lambda: state)
    monkeypatch.setattr(rdc, "SUMMARY_PATH", str(tmp_path / "summary.json"))
    monkeypatch.setattr(rdc, "SCRATCH_DIR", str(tmp_path))
    monkeypatch.setattr(rdc, "ensure_pywin32", lambda: (True, "ok"))

    def run(mailbox):
        monkeypatch.setattr(rdc, "run_script", mailbox.run_script)
        monkeypatch.setattr(rdc, "_clock", mailbox.clock)
        assert rdc.main([]) == 0
        return json.loads(state.read_text(encoding="utf-8"))["last_captured_at"]

    return run


def test_a_run_cut_off_keeps_what_it_captured_and_the_next_continues(delta):
    mail = [email(f"m{i}", stamp(i)) for i in range(1, 6)]
    first = FakeMailbox(mail, stop_after=2)
    assert delta(first) == stamp(2), "the watermark moved with each email"
    second = FakeMailbox(mail)
    assert delta(second) == stamp(5)
    assert first.ingested + second.ingested == ["m1", "m2", "m3", "m4", "m5"], "each email once"


def test_a_failure_freezes_the_watermark_but_later_mail_is_still_captured(delta):
    mailbox = FakeMailbox([email(f"m{i}", stamp(i)) for i in range(1, 5)], fail={"m2"})
    assert delta(mailbox) == stamp(1)
    assert mailbox.ingested == ["m1", "m2", "m3", "m4"]


def test_mail_already_in_the_vault_is_not_ingested_again(delta, tmp_path):
    _thread(tmp_path, "conv", ["m1", "m2"])
    mailbox = FakeMailbox([email(f"m{i}", stamp(i)) for i in range(1, 4)])
    assert delta(mailbox) == stamp(3)
    assert mailbox.ingested == ["m3"]


def test_two_emails_in_one_second_survive_a_page_boundary(delta, monkeypatch):
    monkeypatch.setattr(rdc, "PAGE_SIZE", 2)
    mail = [email("a", stamp(1)), email("b", stamp(2)), email("c", stamp(2)), email("d", stamp(3))]
    mailbox = FakeMailbox(mail)
    assert delta(mailbox) == stamp(3)
    assert sorted(mailbox.ingested) == ["a", "b", "c", "d"] and len(mailbox.ingested) == 4
