---
name: summarize-and-tag-files
description: One-time, long-running captured-file summarization and company wiki-tagging pass -- Job 5 of the company/partner discovery sequence.
version: 0.1.0
author: second-brain
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [second-brain, company, files, summary, one-time]
---

# Summarize & Tag Files (Job 5)

Real work, not mechanical: read every captured File's own actual content
(PDF/DOCX/PPTX/XLSX/image/etc.), understand what it actually is, write a
real summary, and recognize which known Companies (Customers/Partners/
Affiliates -- Step 3 already built their real hub notes) it's genuinely
about. Same discipline as `summarize-and-tag-threads` -- this has to be
YOUR OWN judgment every time; `apply_file_review.py` exists ONLY to
apply a decision you already made, never to decide anything itself.

## Prerequisites

- Run `entity-domain-extraction` then `create-companies-partners` first
  -- this Skill needs real Customer/Partner/Affiliate hub notes to
  recognize company names against.
- Vault path (pass as `--vault-path` on every script call):
  `C:\myWorx\Moussa MD\Moussa Brain`

## Before you start: build your own company list

Same as `summarize-and-tag-threads`'s own Step 0 -- `search_files`/
`read_file` every `Work/Customers/**/*.md` and `Work/Partners/**/*.md`
except `-log.md`/`-captures.md`, note each one's own `name`/`aliases`.
This is the real, authoritative list; a company mentioned in a file that
ISN'T on this list is not this Skill's job to add.

## Finding the files that need this

Every captured File note lives at `Work/Threads/<Thread>/files/<slug>/
<slug>.md`, with the REAL file sitting alongside it in the same folder
(same `<slug>` directory, original filename). **Skip any File whose own
`## Summary` section is already non-empty** -- a captured file's content
never changes after capture, so once summarized it never needs
re-visiting (unlike Threads, which need a timestamp-based skip rule
because new messages keep arriving -- Files don't have that problem).

209 Threads produced roughly 80 captured files total -- small enough
this Job likely doesn't need `summarize-and-tag-threads`'s own
multi-session batching discipline, but still work through them in
batches of 10-20 and stop/report progress if you're running low on
context, rather than trying to force all of them into one sitting.

## The real per-file judgment

For each File:

1. **Read the actual file**, not just its companion note's frontmatter.
   **The plain `read_file` tool cannot extract real content from Office
   binary formats -- live-confirmed 2026-08-22** (a first real run of
   this Skill produced a placeholder "no extractable text; use filename
   context only" fallback for 36 of 71 files, because `read_file` alone
   reported them as unreadable binary and the agent gave up instead of
   reaching for the right tool). **Use the dedicated skill for the
   file's own extension, never fall back to a placeholder without
   trying the real one first:**
   - `.pdf` -- the `pdf`/`nano-pdf` skill (OCR the `ocr-and-documents`
     skill if it's a scanned/image-only PDF with no text layer).
   - `.docx` -- the `docx` skill.
   - `.pptx` -- the `powerpoint` skill.
   - `.xlsx` -- the `xlsx` skill.
   - image formats (`.jpg`/`.png`/etc.) -- vision/image reading.
   - a genuinely unreadable format (`.vcf`/`.pkpass`/`.ics`/`.zip`/no
     extension) -- these are fine to summarize from their own real
     metadata (filename, type) per point 6 below; that is a REAL summary
     of what they are, not the same thing as giving up on a real
     document.
   A placeholder "no extractable text" summary is only acceptable after
   you've actually tried the right dedicated skill for that extension
   and it genuinely failed -- never as a first resort.
2. **Write a real prose summary** -- what the document actually
   contains/is about, in your own words. **Not a raw dump of extracted
   table/slide text** (also live-confirmed 2026-08-22: one `.xlsx`'s own
   "summary" was just the raw extracted cell contents pasted in,
   unreadable as a summary) -- extract the content, then genuinely
   summarize it, the same judgment you'd apply reading it yourself.
3. **Wiki-tag every company you recognize IN the summary text itself**
   -- same convention as Threads: `[[Masdar]]`, matched against your own
   company list from the step above (name OR alias), not raw text.
4. **List every company this file is genuinely about** -- can be more
   than one; use the SPECIFIC entity, never its parent (a deck about
   Masdar gets `Masdar`, not `Mubadala` -- identical rule to Threads).
5. **Write one short, one-line summary too** -- this becomes the entry
   in its own parent Thread's own `## Files` section (operator,
   2026-08-22: "create a log in every thread with files and the summary
   (shorter one)") -- keep it genuinely short, like a filename caption,
   not the full summary repeated.
6. **Some captured files are genuinely not documents** -- a `.vcf`
   contact card, a `.pkpass` wallet pass, a `.ics` calendar invite, a
   `.zip` archive, a no-extension inline-image blob. Don't force a deep
   summary onto these -- one honest short line ("Contact card for X",
   "Calendar invite for the Y kickoff") is a real, complete summary for
   what they actually are. Never skip the file entirely just because
   it's not a "real document" -- same "never skip for looking
   unimportant" rule Threads already follow.

## Applying it

For each File you've just reasoned about, `write_file` a scratch JSON
payload, then call the one script -- as a PLAIN, direct `terminal` call,
using the script's own full absolute path:

```
terminal(command="python \"C:\\Users\\mahmoud.moussa\\AppData\\Local\\hermes\\skills\\company-review\\summarize-and-tag-files\\scripts\\apply_file_review.py\" --vault-path \"C:\\myWorx\\Moussa MD\\Moussa Brain\" --input-file <scratch path>")
```

**Never wrap this in `bash -lc "..."`** (or any other `-c`/`-lc`
shell-string form) -- the same categorical Hermes `terminal`-tool
approval-block documented in every other Skill in this sequence, and
**never a bare filename either** -- both are confirmed live-bug root
causes elsewhere in this vault's own pipelines (see
`summarize-and-tag-threads`'s own SKILL.md for the full incidents). The
absolute-path, no-shell-wrapper form above is confirmed to run without a
prompt and without depending on `cwd` being set correctly.

Payload shape: `{"file_path": "<the File's own concept .md path>",
"summary": "<full summary, with your own [[wikilinks]] already in
it>", "short_summary": "<one line>", "companies": ["Name1", "Name2"]}`.

The script handles everything mechanical from there: writes your summary
onto the File's own `## Summary`, tags the File with `customer/<slug>`/
`partner/<slug>` (one per company you listed), and updates the File's
own parent Thread's `## Files` section -- the existing bare
`- [[file-slug]]` line becomes `- [[file-slug]] -- <your short_summary>`,
replaced in place (idempotent, never duplicated) rather than a separate
log file, since Threads don't get their own Log/Captures companion
files.

## Job 2: Add more detail (and diagrams) to an already-summarized File

Triggered when Mahmoud wants a deeper pass on a File you (or an earlier
turn) already summarized -- e.g. "look closer at that deck." **This is the
ONLY place further analysis output goes -- never a new file, never sent
anywhere.** Read the real file again (same per-format tooling as Job 1),
write your detailed findings as real prose (with your own `[[wikilinks]]`,
same convention as the Summary), `write_file` a scratch JSON payload
`{"file_path": "<the File's own real captured file path>", "details":
"<your detailed findings>"}`, then call the SAME script with `--append`:

```
terminal(command="python \"C:\\Users\\mahmoud.moussa\\AppData\\Local\\hermes\\skills\\company-review\\summarize-and-tag-files\\scripts\\apply_file_review.py\" --vault-path \"C:\\myWorx\\Moussa MD\\Moussa Brain\" --append --input-file <scratch path>")
```

This appends a `## Details` section to the File's existing note (creating
it on the first pass, appending further points on a later one) -- the
`## Summary` from Job 1 stays untouched above it.

**If the file contains an architecture diagram, system diagram, or similar
visual worth seeing (not just describing)**, render THAT specific
slide/page to a real image first:

- **`.pptx`** -- use THIS Skill's own `render_pptx_slide_win32.py`, not the
  `powerpoint` Skill's `pptx_render.py`. That one needs LibreOffice
  (`soffice`) + poppler, which cannot be installed in this environment
  (confirmed 2026-08-22); `render_pptx_slide_win32.py` drives the REAL,
  locally-installed PowerPoint via COM instead (pywin32, already present
  in the Hermes venv from the Outlook integration) -- full fidelity, no
  LibreOffice needed, verified live. Only render the specific slide
  numbers worth it:
  `terminal(command="python \"...\\summarize-and-tag-files\\scripts\\render_pptx_slide_win32.py\" --pptx \"<deck path>\" --slides \"3,12\" --outdir <scratch dir>")`
- **`.pdf`** -- the `pdf`/`nano-pdf` skill's own page-to-image conversion
  (`pdf_page_image.py`, pypdfium2-based, unaffected by the LibreOffice gap).

Then pass the rendered image(s) in the same payload: `{"file_path": "...",
"details": "...", "images": [{"source_path": "<rendered PNG path>"}, ...]}`
-- the script copies each into the File's own folder (handling name
collisions) and embeds it (`![[filename]]`) right after your `details`
text. Put any caption you want IN `details` itself, since the embed always
lands after it -- you don't know the final (possibly collision-suffixed)
filename in advance, so never write the `![[...]]` syntax yourself.

## Pitfalls

- **Never fabricate a company hub note.** Same rule as Threads -- an
  unrecognized name stays unresolved, reported via
  `companies_unresolved`, never invented.
- **Never skip a file for looking unimportant, boring, or non-document.**
  Every captured file gets a real summary line, even a one-line one.
- **The short_summary is genuinely short** -- it's read inline as part
  of a Thread's own file listing, not a separate detail view.

## Verification

- Track running totals: files summarized, distinct companies tagged,
  distinct unresolved company names seen.
- Spot-check one File's own `## Summary` (real content, correctly
  wikilinked) and its own parent Thread's `## Files` section (short
  summary now showing next to the right file, other files' own lines
  untouched).
- Report the final totals, and the full distinct `companies_unresolved`
  list if non-empty.
