"""BUG-081 -- a captured email's body is HTML, and every note view rendered it
as markdown, so 98% of one install's 10,219 message notes opened as `<html><head>`
and read as markup for their whole length.

What is pinned here: a mail reads as a mail, a markdown note is untouched, and
deciding between them prefers what the note says about itself over a guess.
"""
from app.business.core.vault import note_text

OUTLOOK_MAIL = """<html><head><meta charset="utf-8"><style>p { margin: 0 }</style></head>
<body lang="EN-GB">
<div class="WordSection1">
<p class="MsoNormal">Hi Mahmoud,</p>
<p class="MsoNormal">Attached is the <b>signed order form</b>. Legal asked for one
change &mdash; see the <a href="https://masdar.example/redline">redline</a>.</p>
<ul><li>Clause 7.2 reworded</li><li>Termination notice 60 days</li></ul>
<p class="MsoNormal">Thanks,<br>Procurement</p>
<img src="https://tracker.example/pixel.gif" width="1" height="1">
</div></body></html>"""


def test_a_mail_reads_as_a_mail():
    markdown = note_text.readable_body({"body_type": "html"}, OUTLOOK_MAIL)

    assert "<html>" not in markdown and "<p" not in markdown
    assert "Hi Mahmoud," in markdown
    assert "**signed order form**" not in markdown  # bold is not modelled; the words survive
    assert "signed order form" in markdown
    assert "[redline](https://masdar.example/redline)" in markdown
    assert "- Clause 7.2 reworded" in markdown
    assert "- Termination notice 60 days" in markdown
    # The stylesheet and the tracking pixel are machinery, not reading matter.
    assert "margin: 0" not in markdown
    assert "pixel.gif" not in markdown


def test_a_markdown_note_is_returned_untouched():
    """This converts; it never reformats. A note's own markdown must come back
    byte for byte, or every note in the vault would drift through its renderer."""
    body = "## Summary\n\nMasdar returned the [[Order Form]].\n\n| a | b |\n|---|---|\n| 1 | 2 |\n"

    assert note_text.readable_body({"body_type": "markdown"}, body) == body
    assert note_text.readable_body({}, body) == body


def test_the_note_is_believed_over_the_sniff():
    """The capture knows what the server told it (Graph's `body.contentType`);
    a sniff never will."""
    plain = "Hi Mahmoud, see attached."

    assert note_text.body_kind({"body_type": "html"}, plain) == "html"
    assert note_text.body_kind({"body_type": "text"}, OUTLOOK_MAIL) == "markdown"


def test_a_note_written_before_the_field_existed_is_sniffed():
    """The reporting install backfilled 10,219 notes, but a fix cannot assume
    every install has."""
    assert note_text.body_kind({}, OUTLOOK_MAIL) == "html"
    assert note_text.body_kind({}, "Hi Mahmoud,\n\nsee attached.\n") == "markdown"


def test_a_note_that_merely_mentions_a_tag_is_still_markdown():
    """The obvious false positive: a note explaining HTML. One `<br/>` in a
    sentence, or a fenced block of markup, is not a mail."""
    assert note_text.body_kind({}, "Use a `<br/>` to break the line.") == "markdown"
    assert note_text.body_kind({}, "Example:\n\n```html\n<div><p>hi</p></div>\n```\n") == "markdown"


def test_a_table_survives_as_a_table():
    """GFM tables render (`BUG-080`), so an email's table should arrive as one."""
    html = ("<table><tr><th>Route</th><th>Fee</th></tr>"
            "<tr><td>Marketplace</td><td>3%</td></tr></table>")

    markdown = note_text.html_to_markdown(html)

    assert "| Route | Fee |" in markdown
    # Without the separator row GFM renders pipes, not a table.
    assert "|---|---|" in markdown
    assert "| Marketplace | 3% |" in markdown


def test_an_entity_is_decoded_not_left_as_markup():
    assert "Core42 & Masdar" in note_text.html_to_markdown("<p>Core42 &amp; Masdar</p>")


def test_broken_markup_still_reads_rather_than_raising():
    """One malformed mail must not take a note view down with it."""
    markdown = note_text.readable_body({"body_type": "html"}, "<p>unclosed <b>bold <div>and more")

    assert "unclosed" in markdown and "and more" in markdown
    assert "<p>" not in markdown


def test_an_empty_body_is_empty():
    assert note_text.readable_body({"body_type": "html"}, "") == ""


# -- the read paths that show a note -------------------------------------------------


def test_the_note_view_serves_a_readable_body_and_says_what_it_was(tmp_path, monkeypatch):
    """`/browse/<stem>` is where the bug was reported; the note on disk is
    untouched, the view just converts on the way out."""
    from app.business.core.vault import vault_manager as module
    from app.business.core.vault.vault_manager import VaultManager
    from app.config import settings

    monkeypatch.setattr(settings, "vault_path", tmp_path)
    path = tmp_path / "Work" / "Threads" / "T" / "messages" / "2026-10-09-Mail.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f'---\ntype: "RawMessage"\nbody_type: "html"\n---\n\n{OUTLOOK_MAIL}', encoding="utf-8")
    monkeypatch.setattr(module.vault_writer, "list_all_note_paths", lambda: [path])
    manager = VaultManager()
    manager.rebuild_index()

    detail = manager.get_note_detail("2026-10-09-Mail")

    assert detail["body_type"] == "html"
    assert "<html>" not in detail["body"] and "Hi Mahmoud," in detail["body"]
    # On disk it is still the original mail.
    assert "<html>" in path.read_text(encoding="utf-8")


def test_a_plugin_reading_a_message_note_gets_it_readable(tmp_path):
    """My Day's Cockpit Emails tab reads bodies through the Plugin API, so the
    conversion has to reach it too -- one answer, not one per screen."""
    from app import plugin_api

    path = tmp_path / "mail.md"
    path.write_text(f'---\ntype: "RawMessage"\nbody_type: "html"\n---\n\n{OUTLOOK_MAIL}', encoding="utf-8")

    frontmatter, body = plugin_api.VaultApi().read_note(path)

    assert frontmatter["body_type"] == "html"
    assert "<html>" not in body and "Clause 7.2 reworded" in body
