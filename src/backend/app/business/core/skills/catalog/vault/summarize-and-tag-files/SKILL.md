---
name: summarize-and-tag-files
description: Enrichment for email attachments. Extracts each captured file's text in code (PDF, Word, Excel, PowerPoint, forwarded email), then the model writes one real summary, a one-line caption and the companies it is about -- applied to the File note, its company tags, and the parent Thread's Files section. Use when asked to summarize attachments or files, and as the File Enrichment pipeline's scheduled job.
version: 0.5.0
author: second-brain
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [second-brain, company, files, summary, enrichment]
writes:
  - action: apply_file_review
    template: thread
    requires: 1
    sections: [Files]
  - action: apply_file_review
    template: file
    requires: 1
    sections: [Summary, Details]
---

# Enrich Files

Every attachment captured with an email gets a real summary: what the
document actually contains, in your own words, plus a one-line caption
for its Thread and the companies it is about. You do the reading and the
judgment; the scripts do the extracting and the writing.

## What is yours and what is not

**Extraction is not your job.** `read_file.py` pulls the text out of the
file in code. The first run of this Skill left 36 of 71 files with a
"no extractable text" placeholder because the agent's own file reader
cannot open Office binaries, and pointing it at other skills per
extension did not fix that. So do not reach for another tool to open a
file: read what `read_file.py` gives you.

**Metadata is not your job either.** Company tags from email domains,
hubs, People -- all mechanical, all nightly. Yours is only what needs a
reader.

## The loop

A scheduled run hands you the batch and the EXACT commands at the top of
the prompt -- the interpreter to use and the folder the scripts are in.
Use them verbatim. The interpreter matters: it is the one with the
document parsers installed.

### 1. Take the batch you were given

Do not pick files yourself and do not widen the batch. The selector
already knows which files are unsummarized, and the batch size is what
keeps a run inside your context.

### 2. Read each file

```
"<interpreter>" "<scripts folder>\read_file.py" --file-note "<file_note from the batch>"
```

It prints a header -- filename, type, size, parent Thread -- then the
text. **Read the `NOTES:` line.** It tells you what the extractor could
not do, and your summary must not pretend otherwise:

- `no text layer` -- a scan or image-only PDF. Summarize from the
  filename and the Thread, and say that is what you did.
- `TRUNCATED` -- you saw only the start. Say the summary covers the
  start of the document.
- `extraction failed` -- corrupt or password-protected. Say so.
- `not in the vault` -- capture skipped the file (size cap). Summarize
  from the filename and Thread, and say the file was not available.
- `an image` -- view it at the `PATH:` if you can read images. A
  `small ... signature logo` note means one honest line is complete.

### 3. Write one review per file

Write the JSON to a scratch file, then apply it:

```
"<interpreter>" "<scripts folder>\apply_file_review.py" --input-file "<scratch path>"
```

```json
{
  "file_path": "<the file_note path from the batch>",
  "summary": "What the document contains, in your own words, with [[Company]] wikilinks.",
  "short_summary": "One-line caption for the Thread's Files list.",
  "companies": ["Masdar"]
}
```

#### summary

What the document actually is and says -- a proposal's scope and price,
a deck's argument, a spreadsheet's purpose and headline numbers. **Not a
dump of the extracted text**: a pasted table is not a summary. Wiki-tag
every company you recognize in the prose (`[[ADNOC]]`), matched against
a hub's real `name` or `aliases`.

#### short_summary

A caption, not a paragraph -- it is read inline in the Thread's list of
files. "Core42 proposal to Dell for EHS Compass, v1.0", not the summary
again.

#### companies

Every company the file is genuinely about. **The specific entity, never
its parent**: a deck about Masdar gets `Masdar`, not `Mubadala`.

Name a company you are confident about even if you suspect it has no hub
yet. Anything that matches no real hub is filed for the operator to
review -- never created. An attachment is often the only place a company
appears at all: a proposal naming the end customer, a partner deck
listing its clients.

#### Not every file is a document

A calendar invite, a contact card, a signature logo, an archive. One
honest line is a complete summary for what they are. **Never skip a file
for looking unimportant** -- every file gets a summary, even a short one.

## Two rules that cost real runs to learn

**Always the full path to both the interpreter and the script.** A bare
script name failed 19 times in a row in one cron run, because a
scheduled agent's working directory is the user's home folder.

**Never wrap a call in `bash -lc "..."`** or any `-c`/`-lc` form. Hermes
requires human approval for those, which stalls a scheduled run with
nobody there. If a script will not run, **stop and report it** -- never
edit a note by hand to work around it.

## What the applier guarantees

- **Skips a file that already has a summary**, so a re-picked file is
  not overwritten.
- **Never creates a company.** Unresolved names are reported and filed
  in `<data>/data/UnknownCompanies.json` for review.
- **Replaces the Thread's Files line in place** -- `- [[file]]` becomes
  `- [[file]] -- <short_summary>`, never duplicated on a rerun.
