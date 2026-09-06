"""graph_lib must produce records outlook_lib's consumers already accept.

Run from this Skill's own scripts/ folder:
    python -m pytest tests/test_graph_lib.py

These are contract tests, not unit trivia. The Graph path replaces Outlook COM
underneath a pipeline that was written against Outlook's own record shape, so
the things worth asserting are the ones a silent mismatch would break:

  * the `received` FORMAT, because run_delta_capture.py compares watermarks as
    plain strings and ISO's "T" sorts above a space -- a wrong format here does
    not error, it makes every same-day message look older than the watermark
    and skips it forever;
  * the exact record keys, because ingest_email.py reads them by name;
  * the oversize/inline attachment rules, because dropping an attachment
    silently loses evidence a Thread is supposed to record.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import graph_lib  # noqa: E402

FIXTURES = json.loads((Path(__file__).parent / "fixtures" / "graph_messages.json").read_text(encoding="utf-8"))

# The record outlook_lib.py emits, field for field. If this set changes, the
# Outlook path changed and both capture routes must move together.
EXPECTED_KEYS = {
    "id", "subject", "sender_name", "sender_email", "sender_department",
    "sender_job_title", "sender_company_name", "received", "body",
    "attachments", "conversation_id", "recipients", "direction",
}

# "2026-09-04 09:12:33.482000+00:00" -- note the SPACE, not a "T".
OUTLOOK_STAMP = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6}\+00:00$")


def _inbox(index=0):
    return FIXTURES["inbox"]["value"][index]


# ── the record contract ───────────────────────────────────────────────

def test_record_has_exactly_the_outlook_keys():
    record = graph_lib.message_to_record(_inbox(), "received")
    assert set(record) == EXPECTED_KEYS


def test_core_fields_map_across():
    record = graph_lib.message_to_record(_inbox(), "received")
    assert record["id"] == "AAMkAGI2-msg-0001"
    assert record["subject"] == "Q3 renewal - pricing"
    assert record["conversation_id"] == "AAQkAGI2-conv-0001"
    assert record["sender_name"] == "Alice Baker"
    assert record["direction"] == "received"
    assert "revised pricing" in record["body"]


def test_sender_email_is_lowercased():
    """Graph preserves the sender's own casing ("Alice.Baker@Contoso.com").
    Thread/Person identity keys off the address, so two casings would create
    two Person notes for one human."""
    assert graph_lib.message_to_record(_inbox(), "received")["sender_email"] == "alice.baker@contoso.com"


# ── the watermark format trap ─────────────────────────────────────────

def test_received_uses_the_outlook_space_separated_format():
    assert OUTLOOK_STAMP.match(graph_lib.message_to_record(_inbox(), "received")["received"])


def test_received_is_never_iso_t_form():
    assert "T" not in graph_lib.message_to_record(_inbox(), "received")["received"]


def test_a_whole_second_timestamp_still_gets_microseconds():
    """Graph omits fractional seconds when they are zero ("...T16:45:00Z").
    Without padding, string comparison against a watermark that HAS
    microseconds mis-orders them."""
    assert OUTLOOK_STAMP.match(graph_lib.message_to_record(_inbox(1), "received")["received"])


def test_string_comparison_orders_the_same_day_correctly():
    """The actual failure mode, reproduced: watermark comparison is a plain
    string compare, so this is what protects against skipping mail."""
    earlier = graph_lib.message_to_record(_inbox(1), "received")["received"]   # 2026-09-03
    later = graph_lib.message_to_record(_inbox(), "received")["received"]      # 2026-09-04
    assert earlier < later
    watermark = "2026-09-04 00:00:00.000000+00:00"
    assert later > watermark, "a same-day message must read as NEWER than the watermark"


def test_unparseable_timestamp_yields_empty_not_a_guess():
    record = graph_lib.message_to_record({"receivedDateTime": "not-a-date"}, "received")
    assert record["received"] == ""


# ── recipients ────────────────────────────────────────────────────────

def test_recipients_carry_to_and_cc_with_the_outlook_shape():
    recipients = graph_lib.message_to_record(_inbox(), "received")["recipients"]
    assert [r["type"] for r in recipients] == ["to", "cc"]
    assert recipients[0]["email"] == "sherif.tawfik@core42.ai"
    for entry in recipients:
        assert set(entry) == {"name", "email", "type", "department", "job_title", "company_name"}


# ── signature parsing, in place of User.Read.All ──────────────────────

def test_signature_supplies_the_three_directory_fields():
    record = graph_lib.message_to_record(_inbox(), "received")
    assert record["sender_job_title"] == "Account Director"
    assert record["sender_department"] == "Enterprise Sales"
    assert record["sender_company_name"] == "Contoso Ltd"


def test_no_signature_leaves_them_empty_rather_than_guessing():
    record = graph_lib.message_to_record(_inbox(1), "received")
    assert record["sender_job_title"] == ""
    assert record["sender_department"] == ""
    assert record["sender_company_name"] == ""


def test_only_a_labelled_line_counts():
    """A bare line under a name is NOT read as a job title. A wrong title
    written onto a real Person note is worse than a blank one."""
    assert graph_lib.parse_signature_fields("Regards,\nAlice Baker\nAccount Director\n") == {
        "sender_department": "", "sender_job_title": "", "sender_company_name": "",
    }


def test_a_quoted_earlier_signature_is_not_attributed_to_this_sender():
    """Only the tail of the body is scanned, so a signature quoted from an
    earlier reply in the chain cannot be mined as though it were this one."""
    body = "Title: Chief Astronomer\n" + "\n".join(f"line {n}" for n in range(60))
    assert graph_lib.parse_signature_fields(body)["sender_job_title"] == ""


# ── attachments ───────────────────────────────────────────────────────

def _attachments(fetch=None):
    return graph_lib._attachment_records(FIXTURES["attachments_for_msg_0001"]["value"], fetch=fetch)


def test_inline_attachments_are_skipped():
    """A signature logo is not an attachment a Thread should record."""
    assert "signature-logo.png" not in [a["filename"] for a in _attachments()]


def test_oversize_attachment_is_recorded_but_not_downloaded():
    """outlook_lib's own rule: past the size cap, keep the row with
    temp_path None so the Thread still shows the file existed."""
    huge = next(a for a in _attachments(fetch=lambda a: b"x") if a["filename"] == "huge-recording.mp4")
    assert huge["temp_path"] is None
    assert huge["size"] == 41943040


def test_normal_attachment_is_written_to_a_temp_file():
    written = next(a for a in _attachments(fetch=lambda a: b"spreadsheet-bytes")
                   if a["filename"] == "Q3-pricing.xlsx")
    assert written["temp_path"] and Path(written["temp_path"]).read_bytes() == b"spreadsheet-bytes"
    Path(written["temp_path"]).unlink(missing_ok=True)


def test_attachment_records_have_the_outlook_shape():
    for entry in _attachments():
        assert set(entry) == {"filename", "temp_path", "size"}


# ── direction, and the merge ──────────────────────────────────────────

def test_sent_items_are_marked_sent_not_received():
    sent = FIXTURES["sentitems"]["value"][0]
    assert graph_lib.message_to_record(sent, "sent")["direction"] == "sent"


def test_a_reply_shares_the_conversation_id_of_its_thread():
    """What makes the Thread note idempotent: the reply must land on the same
    conversation, not open a second one."""
    inbound = graph_lib.message_to_record(_inbox(), "received")
    outbound = graph_lib.message_to_record(FIXTURES["sentitems"]["value"][0], "sent")
    assert inbound["conversation_id"] == outbound["conversation_id"]


# ── $filter round-trip ────────────────────────────────────────────────

def test_watermark_converts_back_into_a_graph_filter_value():
    """The watermark is stored in Outlook's space form; Graph will not accept
    it. This is the inverse conversion the query depends on."""
    assert graph_lib._outlook_stamp_to_graph_filter(
        "2026-09-04 09:12:33.482000+00:00") == "2026-09-04T09:12:33Z"


def test_filter_and_paging_land_in_the_query():
    url = graph_lib._folder_url("a@b.com", "inbox", 25, "2026-09-04 09:12:33.482000+00:00", None)
    assert "%24top=25" in url or "$top=25" in url
    assert "2026-09-04T09%3A12%3A33Z" in url or "2026-09-04T09:12:33Z" in url
    assert "mailFolders/inbox/messages" in url


def test_named_mailbox_is_used_not_me():
    """App-only auth has no signed-in user, so /me does not exist."""
    url = graph_lib._folder_url("sherif.tawfik@core42.ai", "inbox", 5, None, None)
    assert "/users/sherif.tawfik%40core42.ai/" in url
    assert "/me/" not in url
