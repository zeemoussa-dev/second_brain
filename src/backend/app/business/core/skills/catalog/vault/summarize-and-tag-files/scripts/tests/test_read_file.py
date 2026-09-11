"""The attachment reader, tested on real documents built in each test.

Every fixture is a genuine file in its format, produced by the same library the
reader uses -- not a mock of that library. The failure this Skill had before was
exactly "the tool says it read the file and returned nothing useful", and a mock
would reproduce that silently.
"""
import email.message
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def attachment(tmp_path: Path, filename: str, payload: bytes | None) -> Path:
    """A File companion note plus (optionally) its original, in the real
    `Work/Threads/<T>/files/<slug>/` layout."""
    folder = tmp_path / "Work" / "Threads" / "2026-09-01 Deal" / "files" / f"2026-09-01 {filename}"
    folder.mkdir(parents=True)
    note = folder / f"2026-09-01 {filename}.md"
    note.write_text(
        '---\ntype: "File"\n'
        f'original_filename: "{filename}"\n'
        'source_thread: "[[2026-09-01 Deal]]"\n'
        'tags: ["type/x"]\n---\n\n## Summary\n\n\n## Personal Notes\n',
        encoding="utf-8")
    if payload is not None:
        (folder / filename).write_bytes(payload)
    return note


def minimal_pdf(text: str | None) -> bytes:
    """A real one-page PDF, xref offsets computed rather than hand-typed. `None`
    gives a page with an empty content stream -- a scanned-document stand-in."""
    stream = b"" if text is None else b"BT /F1 18 Tf 20 80 Td (" + text.encode() + b") Tj ET"
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, 1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
    xref_at = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode() + b"0000000000 65535 f \n"
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode()
    out += (f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_at}\n%%EOF\n").encode()
    return bytes(out)


def test_pdf_text_is_extracted(tmp_path):
    import read_file as r
    note = attachment(tmp_path, "proposal.pdf", minimal_pdf("Core42 proposal for ADNOC"))
    out = r.read_file(note)
    assert "Core42 proposal for ADNOC" in out
    assert "--- page 1 ---" in out


def test_a_pdf_with_no_text_layer_says_so(tmp_path):
    """The placeholder failure, the other way round: the reader must be TOLD a
    scan has no text, or it summarizes the filename as if it read the file."""
    import read_file as r
    note = attachment(tmp_path, "scan.pdf", minimal_pdf(None))
    out = r.read_file(note)
    assert "no text layer" in out


def test_docx_paragraphs_and_tables(tmp_path):
    import docx
    import read_file as r
    document = docx.Document()
    document.add_paragraph("Statement of work for the pilot")
    table = document.add_table(rows=2, cols=2)
    table.cell(0, 0).text, table.cell(0, 1).text = "Item", "Cost"
    table.cell(1, 0).text, table.cell(1, 1).text = "GPUs", "1.2M"
    path = tmp_path / "sow.docx"
    document.save(path)
    note = attachment(tmp_path, "sow.docx", path.read_bytes())
    out = r.read_file(note)
    assert "Statement of work for the pilot" in out
    assert "GPUs | 1.2M" in out


def test_xlsx_sheets_rows_and_the_row_cap(tmp_path, monkeypatch):
    import openpyxl
    import read_file as r
    monkeypatch.setattr(r, "_SHEET_ROW_CAP", 5)
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Forecast"
    for n in range(8):
        sheet.append([f"Account {n}", n * 100])
    workbook.create_sheet("Empty")
    path = tmp_path / "f.xlsx"
    workbook.save(path)
    note = attachment(tmp_path, "forecast.xlsx", path.read_bytes())
    out = r.read_file(note)
    assert "--- sheet: Forecast (8 rows) ---" in out
    assert "Account 0 | 0" in out
    assert "Account 7" not in out, "rows beyond the cap must not be shown"
    assert "first 5 of 8" in out, "and the cap must be announced, not silent"
    assert "--- sheet: Empty (0 rows) ---" in out


def test_pptx_slides_groups_and_speaker_notes(tmp_path):
    from pptx import Presentation
    from pptx.util import Inches
    import read_file as r
    presentation = Presentation()
    slide = presentation.slides.add_slide(presentation.slide_layouts[5])
    slide.shapes.title.text = "Sovereign AI offer"
    group = slide.shapes.add_group_shape()
    box = group.shapes.add_textbox(Inches(1), Inches(2), Inches(3), Inches(1))
    box.text_frame.text = "Inside a group"
    slide.notes_slide.notes_text_frame.text = "Mention the France cluster"
    path = tmp_path / "deck.pptx"
    presentation.save(path)
    note = attachment(tmp_path, "deck.pptx", path.read_bytes())
    out = r.read_file(note)
    assert "Sovereign AI offer" in out
    assert "Inside a group" in out, "a grouped text box is invisible to a flat walk"
    assert "[speaker notes] Mention the France cluster" in out


def test_a_forwarded_email_shows_headers_body_and_what_it_carried(tmp_path):
    import read_file as r
    message = email.message.EmailMessage()
    message["From"], message["Subject"] = "a@partner.com", "Revised pricing"
    message.set_content("Please find the revised pricing attached.")
    message.add_attachment(b"x", maintype="application", subtype="pdf", filename="pricing.pdf")
    note = attachment(tmp_path, "fwd.eml", message.as_bytes())
    out = r.read_file(note)
    assert "Subject: Revised pricing" in out
    assert "revised pricing attached" in out
    assert "pricing.pdf" in out


def test_a_small_image_is_flagged_as_a_likely_signature_logo(tmp_path):
    import read_file as r
    note = attachment(tmp_path, "image001.png", b"\x89PNG" + b"0" * 500)
    out = r.read_file(note)
    assert "signature logo" in out


def test_a_missing_original_is_reported_not_crashed_on(tmp_path):
    """Capture skips files over its size cap but still writes the note."""
    import read_file as r
    note = attachment(tmp_path, "huge.pdf", None)
    out = r.read_file(note)
    assert "not in the vault" in out


def test_a_corrupt_file_is_reported_not_crashed_on(tmp_path):
    """One bad attachment must not stop a batch."""
    import read_file as r
    note = attachment(tmp_path, "broken.docx", b"this is not a zip archive")
    out = r.read_file(note)
    assert "extraction failed" in out


def test_long_text_is_truncated_and_says_so(tmp_path):
    import read_file as r
    note = attachment(tmp_path, "notes.txt", b"word " * 5000)
    out = r.read_file(note, max_chars=1000)
    assert "[TRUNCATED: showed 1,000 of" in out


def test_an_unsupported_format_is_named(tmp_path):
    import read_file as r
    note = attachment(tmp_path, "card.vcf", b"BEGIN:VCARD")
    out = r.read_file(note)
    assert "unsupported format .vcf" in out
