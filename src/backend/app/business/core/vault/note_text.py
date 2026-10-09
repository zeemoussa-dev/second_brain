"""Reading a note whose body is not markdown (`BUG-081`).

A captured email's body IS the original HTML, deliberately: the evidence is kept
faithful and conversion happens on the way out. Nothing converted it on the way
out, so every note view handed it to a markdown renderer, which renders no raw
HTML by design (`ADR-050`) -- a mail note opened with `<html><head>` and read as
markup for its whole length, on 9,999 of one install's 10,219 message notes.

`rehype-raw` is not the answer: rendering a note's own markup is what the
no-raw-HTML rule exists to prevent, and an agent writes notes. Converting to
markdown at the read is, which is what the capture Skills already do with
`HTMLParser` before handing a body to a model.

Standard library only, and deliberately small: an email is prose, links, lists
and the occasional table. Anything it cannot model becomes text rather than
markup -- the worst outcome is plain prose, never a tag on screen.
"""
from __future__ import annotations

import re
from html.parser import HTMLParser

# What a note says about itself. The capture writes it (`body_type: "html"`);
# an older note has nothing, which is what the sniff below is for.
_BODY_TYPE_FIELD = "body_type"
_HTML = "html"
_MARKDOWN = "markdown"

# Tags whose CONTENT is machinery, never reading matter. Only tags that really
# close belong here: a void tag (`<meta>`, `<link>`) never fires an end tag, so
# skipping on it would swallow the rest of the mail -- which is exactly what the
# first run of this converter did.
_DROPPED_CONTENT = {"script", "style", "head", "title"}
_IGNORED_VOID = {"meta", "link", "base", "col", "source", "track", "wbr", "input"}
_BLOCK_TAGS = {
    "p", "div", "section", "article", "header", "footer", "table", "tr", "ul", "ol",
    "li", "blockquote", "pre", "h1", "h2", "h3", "h4", "h5", "h6", "br", "hr", "body",
}
_HEADINGS = {"h1": "#", "h2": "##", "h3": "###", "h4": "####", "h5": "#####", "h6": "######"}

# A closing block tag is the strongest signal that a body is markup rather than
# prose that happens to mention one: markdown with an inline `<br/>` has none.
_CLOSING_BLOCK = re.compile(
    r"</(p|div|table|tr|td|th|ul|ol|li|h[1-6]|span|body|html|blockquote)\s*>", re.I)
_DOCUMENT_TAG = re.compile(r"<\s*(!doctype\s+html|html|body)\b", re.I)
_CODE_FENCE = re.compile(r"```.*?```", re.S)
_MANY_BLANK_LINES = re.compile(r"\n{3,}")
_TRAILING_SPACES = re.compile(r"[ \t]+\n")


def body_kind(frontmatter: dict | None, body: str) -> str:
    """`"html"` or `"markdown"`, from the note's own `body_type` when it has one
    and from the body itself when it does not.

    The field is the answer wherever it exists -- the capture knows what the
    server told it (Graph's `body.contentType`), and a sniff never will. The
    sniff is for the notes written before the field existed."""
    declared = str((frontmatter or {}).get(_BODY_TYPE_FIELD) or "").strip().lower()
    if declared in (_HTML, "text/html"):
        return _HTML
    if declared:
        return _MARKDOWN
    return _HTML if looks_like_html(body) else _MARKDOWN


def looks_like_html(body: str) -> bool:
    """Markup, not a note that mentions a tag. A fenced code block is ignored --
    a note explaining HTML is the obvious false positive, and it is markdown."""
    text = _CODE_FENCE.sub("", body or "")
    if _DOCUMENT_TAG.search(text):
        return True
    return len(_CLOSING_BLOCK.findall(text)) >= 3


class _MarkdownFromHtml(HTMLParser):
    """Emails, not documents: prose, links, lists and the occasional table."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._skip_depth = 0
        self._list_stack: list[str] = []
        self._link_target: str | None = None
        self._link_text: list[str] = []
        self._in_table_cell = False
        self._row_cells = 0
        self._row_is_header = False

    # -- output -------------------------------------------------------------------

    def _write(self, text: str) -> None:
        if self._link_target is not None:
            self._link_text.append(text)
        else:
            self._parts.append(text)

    def _break(self, blank_line: bool = False) -> None:
        """Ends the current line, or leaves a blank one. Never stacks a break on
        an existing one -- a `</li><li>` pair would otherwise open a blank line
        between every item, which markdown reads as a loose list and wraps each
        item in a paragraph of its own."""
        if not self._parts:
            return
        tail = "".join(self._parts[-3:])
        if blank_line:
            if tail.endswith("\n\n"):
                return
            self._parts.append("\n" if tail.endswith("\n") else "\n\n")
        elif not tail.endswith("\n"):
            self._parts.append("\n")

    # -- parsing ------------------------------------------------------------------

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag in _DROPPED_CONTENT:
            self._skip_depth += 1
            return
        if self._skip_depth or tag in _IGNORED_VOID:
            return
        if tag == "br":
            self._write("\n")
        elif tag == "hr":
            self._break(blank_line=True)
            self._write("---")
            self._break(blank_line=True)
        elif tag in _HEADINGS:
            self._break(blank_line=True)
            self._write(_HEADINGS[tag] + " ")
        elif tag in ("ul", "ol"):
            self._break()
            self._list_stack.append(tag)
        elif tag == "li":
            self._break()
            depth = max(0, len(self._list_stack) - 1)
            marker = "1." if (self._list_stack or ["ul"])[-1] == "ol" else "-"
            self._write("  " * depth + marker + " ")
        elif tag == "blockquote":
            self._break(blank_line=True)
            self._write("> ")
        elif tag == "a":
            self._link_target = (attributes.get("href") or "").strip()
            self._link_text = []
        elif tag == "img":
            # A tracking pixel has no alt; a real image's alt is the only thing
            # worth keeping, since the file itself is not in the vault.
            alt = (attributes.get("alt") or "").strip()
            if alt:
                self._write(f"[image: {alt}]")
        elif tag in ("td", "th"):
            self._write("| ")
            self._in_table_cell = True
            self._row_cells += 1
            self._row_is_header = self._row_is_header or tag == "th"
        elif tag == "tr":
            self._break()
            self._row_cells, self._row_is_header = 0, False
        elif tag in _BLOCK_TAGS:
            self._break(blank_line=True)

    def handle_endtag(self, tag):
        if tag in _DROPPED_CONTENT:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if self._skip_depth:
            return
        if tag == "a":
            text = "".join(self._link_text).strip()
            target, self._link_target, self._link_text = self._link_target, None, []
            if not text:
                self._write(target or "")
            elif target and target != text and not target.startswith("#"):
                self._write(f"[{text}]({target})")
            else:
                self._write(text)
        elif tag in ("ul", "ol"):
            if self._list_stack:
                self._list_stack.pop()
            self._break(blank_line=True)
        elif tag == "li":
            # A single newline: a blank line between items makes markdown treat
            # the list as loose and wrap every item in its own paragraph.
            self._break()
        elif tag in ("td", "th"):
            self._write(" ")
            self._in_table_cell = False
        elif tag == "tr":
            self._write("|")
            # GFM needs the separator row, or the table renders as pipes
            # (`BUG-080` taught the renderer tables; this is what feeds it one).
            if self._row_is_header and self._row_cells:
                self._break()
                self._write("|" + "---|" * self._row_cells)
            self._row_is_header = False
        elif tag in _HEADINGS or tag in _BLOCK_TAGS:
            self._break(blank_line=True)

    def handle_data(self, data):
        if self._skip_depth or not data:
            return
        # Collapse the whitespace HTML ignores anyway -- an email's markup is
        # mostly indentation, and keeping it would make the note a column of gaps.
        text = re.sub(r"[ \t\r\n ]+", " ", data)
        if not text.strip():
            if self._parts and not "".join(self._parts[-1:]).endswith((" ", "\n")):
                self._write(" ")
            return
        self._write(text)

    def markdown(self) -> str:
        text = "".join(self._parts)
        text = _TRAILING_SPACES.sub("\n", text)
        text = _MANY_BLANK_LINES.sub("\n\n", text)
        return text.strip()


def html_to_markdown(html: str) -> str:
    """One email's HTML as markdown a note view can render.

    A body that cannot be parsed comes back as its own text with the tags
    stripped: unreadable prose beats a screen of markup, and raising here would
    take down a note view over one bad mail."""
    parser = _MarkdownFromHtml()
    try:
        parser.feed(html or "")
        parser.close()
    except Exception:  # noqa: BLE001 -- html.parser raises a variety on broken input
        return _MANY_BLANK_LINES.sub("\n\n", re.sub(r"<[^>]+>", " ", html or "")).strip()
    return parser.markdown()


def readable_body(frontmatter: dict | None, body: str) -> str:
    """The note's body as something a markdown renderer can show. Markdown is
    returned untouched -- this converts, it never reformats."""
    if body_kind(frontmatter, body) != _HTML:
        return body
    return html_to_markdown(body)
