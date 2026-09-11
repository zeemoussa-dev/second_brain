"""The read-side HTML strip, tested where getting it wrong would cost something.

The point of this converter is to cut ~83% of the tokens a summarizing agent
would otherwise pay for. So the failures that matter are the ones that either
LOSE content (a summary written from half a thread is confidently wrong) or
QUIETLY KEEP the markup (the cost saving silently does not happen).
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from read_thread import html_to_text, read_thread  # noqa: E402


def test_markup_goes_and_the_words_stay():
    raw = ('<html><head><style>p{font-family:Aptos}</style></head><body>'
           '<div style="font-family:Aptos,-apple-system">Hi Sherif,</div>'
           '<div>Confirming <strong>Tuesday</strong> works.</div></body></html>')
    text = html_to_text(raw)
    assert "Hi Sherif," in text and "Confirming" in text and "Tuesday" in text
    assert "<" not in text and "font-family" not in text, (
        "a <style> block must be dropped whole -- stripping only tags would "
        "flatten the CSS into the text as a wall of unreadable content"
    )


def test_block_boundaries_become_line_breaks():
    """Without this, every paragraph runs into the next and the transcript
    becomes one line -- readable to nobody, including the model.

    Asserts SEPARATION, not an exact blank-line count: `</div><div>` is two
    boundaries and legitimately reads as a paragraph break. Pinning the exact
    whitespace would fail on correct output."""
    text = html_to_text("<div>First line</div><div>Second line</div>")
    assert "First line" in text and "Second line" in text
    assert "First lineSecond line" not in text
    between = text[text.index("First line") + len("First line"):text.index("Second line")]
    assert between.strip() == "" and "\n" in between


def test_entities_are_decoded():
    text = html_to_text("<p>Core42 &amp; Adobe &mdash; &quot;partners&quot;</p>")
    assert "Core42 & Adobe" in text
    assert "&amp;" not in text and "&quot;" not in text


def test_plain_text_is_left_alone():
    """Not every body is HTML. Running the converter over plain text must not
    damage it -- three of the 151 real messages measured were already plain."""
    assert html_to_text("Just a plain body.\n\nSecond para.") == "Just a plain body.\n\nSecond para."


def test_empty_body_does_not_raise():
    assert html_to_text("") == ""
    assert html_to_text(None or "") == ""


def _thread(tmp_path: Path, messages: list[tuple[str, str, str, str]]) -> Path:
    thread_dir = tmp_path / "2026-09-09 Example"
    (thread_dir / "messages").mkdir(parents=True)
    (thread_dir / "2026-09-09 Example.md").write_text(
        '---\ntype: "Thread"\nclassification: "partner"\n'
        'last_message_at: "2026-09-09 10:00:00.000000+00:00"\n---\n\n## Summary\n\n',
        encoding="utf-8")
    for index, (received, direction, sender, body) in enumerate(messages):
        (thread_dir / "messages" / f"m{index}.md").write_text(
            f'---\ntype: "RawMessage"\nreceived: "{received}"\ndirection: "{direction}"\n'
            f'sender: "{sender}"\nsender_email: "{sender.lower()}@x.com"\n'
            f'subject: "Subject {index}"\n---\n\n{body}',
            encoding="utf-8")
    return thread_dir


def test_messages_come_out_in_time_order_not_filename_order(tmp_path):
    """Message filenames are subject-based, so they say nothing about when a
    message arrived. A transcript out of order misrepresents who replied to
    whom -- which is exactly what a summary is supposed to get right."""
    thread_dir = _thread(tmp_path, [
        ("2026-09-09 12:00:00.000000+00:00", "sent", "Later", "<p>second thing</p>"),
        ("2026-09-09 09:00:00.000000+00:00", "received", "Earlier", "<p>first thing</p>"),
    ])
    transcript = read_thread(thread_dir)
    assert transcript.index("first thing") < transcript.index("second thing")


def test_direction_is_visible_in_the_transcript(tmp_path):
    thread_dir = _thread(tmp_path, [
        ("2026-09-09 09:00:00.000000+00:00", "received", "Them", "<p>hello</p>"),
        ("2026-09-09 10:00:00.000000+00:00", "sent", "Us", "<p>reply</p>"),
    ])
    transcript = read_thread(thread_dir)
    assert "RECEIVED" in transcript and "SENT" in transcript


def test_truncation_announces_itself(tmp_path):
    """A silently truncated thread would be summarized as though complete --
    the summary would then be confidently missing whatever came after the cut."""
    thread_dir = _thread(tmp_path, [
        ("2026-09-09 09:00:00.000000+00:00", "received", "Them", "<p>" + "x" * 5000 + "</p>"),
    ])
    transcript = read_thread(thread_dir, max_chars=500)
    assert "TRUNCATED" in transcript


def test_a_real_sized_body_actually_shrinks(tmp_path):
    """The whole reason this exists. Outlook wraps every paragraph in its own
    inline-styled div; if that does not collapse, nothing was gained."""
    outlook_div = ('<div style="font-family:Aptos,Aptos_MSFontService,-apple-system,'
                   'Roboto,Arial,Helvetica,sans-serif; font-size:12pt">Some real content here.</div>')
    raw = "<html><body>" + outlook_div * 40 + "</body></html>"
    text = html_to_text(raw)
    assert len(text) < len(raw) * 0.35, (
        f"expected a large reduction, got {len(text)} from {len(raw)}"
    )
    assert text.count("Some real content here.") == 40, "no content may be lost"


def test_a_thread_is_found_by_its_id_not_a_typed_path(tmp_path, monkeypatch):
    """The batch hands the agent an id. A path typed from a Thread's title
    breaks on a `|`, an 80-character cut, or an invisible character the prompt
    strips -- this folder carries one."""
    monkeypatch.setenv("SECOND_BRAIN_DATA_PATH", str(tmp_path / "config"))
    from read_thread import resolve_thread_dir
    folder = tmp_path / "Work" / "Threads" / "2026-06-08 Task assigned to you​ in Board"
    (folder / "messages").mkdir(parents=True)
    (folder / f"{folder.name}.md").write_text('---\ntype: "Thread"\nid: "conv-9"\n---\n',
                                             encoding="utf-8")
    assert resolve_thread_dir(tmp_path, "conv-9") == folder
    with pytest.raises(SystemExit, match="no Thread with id"):
        resolve_thread_dir(tmp_path, "conv-missing")
