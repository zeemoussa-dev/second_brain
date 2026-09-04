---
name: capture-files
description: Catch-all capture for a file uploaded with no stated context (e.g. WhatsApp media with no message attached). Reads the file, writes a real summary, files both under today's date. Use this whenever a file arrives that isn't part of an existing Thread/Meeting capture pipeline and nothing else claims it.
version: 0.1.0
author: second-brain
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [second-brain, files, whatsapp, quick-capture]
---

# Capture Files

The file-capture sibling of `capture-notes` -- same catch-all role, same
"General for now, we'll reason over it later" philosophy, but for an
uploaded file instead of text/voice content.

## Prerequisites

- Vault path (pass as `--vault-path` on every script call):
  `$SECOND_BRAIN_VAULT_PATH`

## What this builds

```
Work/Files/<YYYY-MM-DD>/<original filename stem>/
    <original filename>              -- the real file, untouched
    <original filename stem>.md      -- description (Summary, then
                                         optionally Details -- see Job 2)
```

One folder per FILE (not per day -- corrected 2026-08-22, mirrors this
vault's own established pattern of Threads/Meetings/Opportunities each
getting a folder named after the thing), nested under today's date folder.
Deliberately NOT filed under any Customer/Partner (same reasoning as
`capture-notes`: capture now, a later pass reasons over and re-files
these).

## Job 1: Capture

Triggered whenever a file is relayed to you with no other specialist
claiming it. Two real steps before the script call:

1. **Read the actual file -- never summarize from the filename alone.**
   The plain `read_file` tool cannot extract real content from Office
   binary formats or PDFs (live-confirmed elsewhere in this vault: a first
   real run of a similar Job produced placeholder "no extractable text"
   summaries for half its files, because the agent gave up instead of
   reaching for the right tool). **Use the dedicated skill for the file's
   own extension, never fall back to a placeholder without trying the real
   one first:**
   - `.pdf` -- the `pdf`/`nano-pdf` skill (OCR via `ocr-and-documents` if
     it's a scanned/image-only PDF with no text layer).
   - `.docx` -- the `docx` skill.
   - `.pptx` -- the `powerpoint` skill.
   - `.xlsx` -- the `xlsx` skill.
   - image formats (`.jpg`/`.png`/etc.) -- vision/image reading.
   - a genuinely unreadable format (`.vcf`/`.zip`/no extension) -- fine to
     summarize from real metadata (filename, type) -- that's a real summary
     of what it is, not giving up on a real document.
2. **Write a real prose summary** -- what the file actually contains/is
   about, in your own words. Not a raw dump of extracted text, not a
   restatement of the filename.

Then `write_file` a scratch JSON payload `{"source_path": "<the file's
current local path>", "summary": "<your real summary>", "filename":
"<the real original filename, if known>"}`, and call the script as a
PLAIN, direct `terminal` call using its own full absolute path:

**Always pass `filename` when you know the real original name** -- a
platform's local download cache commonly renames the file (e.g. WhatsApp
media lands as something like `doc_e9675ce5da81_<original name>` locally)
and that is NEVER what the sender actually called it. If whoever relayed
this to you told you the real filename, or it's visible in the message/
media metadata, use that. Only fall back to omitting `filename` (the script
then uses the download path's own name) when you genuinely don't know the
real one.

```
terminal(command="python \"C:\\Users\\mahmoud.moussa\\AppData\\Local\\hermes\\profiles\\files-manager\\skills\\notes-capture\\capture-files\\scripts\\capture_file.py\" --input-file <scratch path>")
```

The script creates the file's own folder (handles same-day name collisions
on its own), moves the file into it, writes the companion note, and
best-effort wikilinks any real Customer/Partner name your summary mentions
(e.g. "about Adnoc renewal" becomes "about [[Adnoc]] renewal") --
automatic, not something you do yourself.

## Job 2: Add more detail to an already-captured file

Triggered when Mahmoud wants a deeper pass on a file you (or an earlier
turn) already captured -- e.g. "look closer at that deck" after Job 1
reported it captured. **This is the ONLY place further analysis output
goes -- never a new file, never sent anywhere.** Read the real file again
(same per-format tooling as Job 1), write your detailed findings as real
prose, `write_file` a scratch JSON payload `{"file_path": "<the real
captured file's own path, as returned by Job 1>", "details": "<your
detailed findings>"}`, then call the SAME script with `--append`:

```
terminal(command="python \"C:\\Users\\mahmoud.moussa\\AppData\\Local\\hermes\\profiles\\files-manager\\skills\\notes-capture\\capture-files\\scripts\\capture_file.py\" --append --input-file <scratch path>")
```

This appends a `## Details` section to the file's existing description note
(creating it if this is the first pass, appending further points under it
on a later pass) -- the `## Summary` from Job 1 stays untouched above it.

### Diagrams and architecture visuals

If the file contains an architecture diagram, system diagram, or similar
visual worth seeing (not just describing), render THAT specific slide/page
to a real image:

- **`.pptx`** -- use THIS Skill's own `render_pptx_slide_win32.py`, not the
  `powerpoint` Skill's `pptx_render.py`. That one needs LibreOffice
  (`soffice`) + poppler, which cannot be installed in this environment
  (confirmed 2026-08-22); `render_pptx_slide_win32.py` instead drives the
  REAL, locally-installed PowerPoint via COM (pywin32, already present in
  the Hermes venv from the Outlook integration) -- no LibreOffice needed,
  and it renders at full fidelity (verified live). Only render the specific
  slide numbers worth it:
  `terminal(command="python \"...\\capture-files\\scripts\\render_pptx_slide_win32.py\" --pptx \"<deck path>\" --slides \"3,12\" --outdir <scratch dir>")`
- **`.pdf`** -- the `pdf`/`nano-pdf` skill's own page-to-image conversion
  (`pdf_page_image.py`, pypdfium2-based -- pip-installable, no system
  dependency, unaffected by the LibreOffice gap).

Then include the rendered image(s) in the same payload:

```
{"file_path": "...", "details": "...", "images": [
  {"source_path": "<rendered PNG path>", "caption": "Slide 12: target architecture"}
]}
```

The script copies each image into the file's own folder and embeds it
(`![[filename]]`) with its caption right after the details text -- don't
embed it yourself by hand, and don't skip the caption (a bare image with no
label is much less useful later). Only render slides/pages that are
genuinely diagram-like; don't render every slide "just in case."

## Pitfalls

- **Never ask what this file is about or which Customer it belongs to.**
  Same catch-all discipline as `capture-notes` -- this Skill exists so a
  file with no context still gets captured instead of lost.
- **Never wrap the script in `bash -lc "..."`** -- same categorical Hermes
  `terminal`-tool approval-block documented throughout this vault's Skills.
- **Don't paste a placeholder summary to move faster.** A real summary
  written after actually reading the file is the entire point -- see step 1.

## Verification

- After a capture, confirm `file_path` is the real moved file (not still
  sitting at its original download location) and `description_path`'s own
  `## Summary` reflects what the file actually contains.
