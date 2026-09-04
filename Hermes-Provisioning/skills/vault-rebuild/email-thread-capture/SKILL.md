---
name: email-thread-capture
description: Full-history (one-time) or incremental (recurring) Outlook capture into Second Brain's vault via standalone scripts.
version: 0.3.0
author: second-brain
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [second-brain, email, vault, capture, recurring]
---

# Email Thread Capture

Pulls email from the Outlook inbox into Second Brain's vault, structuring
it into Threads -- either the initial **one-time, full-history** rebuild
(`run_full_capture.py`) or the **recurring, incremental** delta pass
(`run_delta_capture.py`, 2026-08-22) that keeps the vault current after
that. Either way this is the **Capture** phase only -- you never
summarize, never judge importance, never skip an email because it looks
unimportant. A separate, later Enrich pipeline (`summarize-and-tag-
threads`) handles summarization and Customer/Partner company-matching.

**2026-08-21 rewrite:** this Skill used to call Second Brain's own MCP
server. It's now fully self-hosted -- every script below is a standalone
Python file in this Skill's own `scripts/` folder, invoked directly
through the `terminal` tool. No MCP server, no Second Brain backend
process, no shared venv. See
`Implementation/Plans/2026-08-20-backend-architecture-redesign.md`, "MCP
server vs. Hermes-native Skill scripts," for why.

## Prerequisites

- **Windows only** -- these scripts use `pywin32` COM automation against
  Outlook desktop.
- Outlook desktop must be running and signed in on this machine.
- `pywin32` must be importable. **Do not check this with an inline
  `python -c "..."` command, and never wrap ANY script call in this Skill
  in `bash -lc "..."` either** -- Hermes' own `terminal` tool
  categorically requires human approval for any `-c`/`-lc` shell-string
  invocation (confirmed live 2026-08-21: `hermes approvals test`,
  rule `shell command via -c/-lc flag`), which stalls a cron-triggered
  run with no one there to approve it. Every script call in this Skill
  must be a PLAIN, direct `terminal` call (`command` starting with
  `python` itself, no shell wrapper at all). Just try
  `list_recent_emails.py` (step 1 below) directly -- if it fails with an
  import error, THEN run
  `terminal(command="python -m pip install pywin32")` (a real `.py`/
  module-args invocation, not `-c`/`-lc`, so it runs without a prompt) and
  retry.
- Vault path: the scripts read `SECOND_BRAIN_VAULT_PATH` from Hermes' own
  `.env` themselves (written there by Second Brain's setup wizard), so
  `--vault-path` only needs passing to override it. Never hardcode an
  absolute path here -- this Skill has to work on any machine.

## How to Run

**One-time path: run `run_full_capture.py` (full history).** For a
RECURRING/incremental capture, see "Recurring path" below instead --
`run_full_capture.py` re-walks the entire mailbox every time and is only
meant to run once, at initial vault setup.

It implements the entire loop (Procedure steps 1-5) as one Python
process -- fetch a page, ingest/link/rename/capture-attachments for every
email in it, page backward, repeat until empty -- so a full-history pull
costs ONE long-running `terminal` call instead of ~4 calls x every single
email in your inbox history. **Always use the script's own full absolute
path, never a bare filename** (2026-08-21 bug fix, live-confirmed: a bare
filename with no `cwd` set failed 19 times in a row in a real cron run
of a sibling Skill -- `python.exe: can't open file
'C:\Users\mahmoud.moussa\apply_thread_review.py'` -- because a
cron-triggered agent's own default working directory is the user's home
folder, not this Skill's own `scripts/`, and nothing in a bare `terminal`
call tells it otherwise. The absolute-path form removes that dependency
entirely -- always use it, even if a `cwd` parameter is also available.)
Run it as a background process so you can keep checking in rather than
blocking on it:

```
terminal(command="python \"C:\\Users\\mahmoud.moussa\\AppData\\Local\\hermes\\skills\\vault-rebuild\\email-thread-capture\\scripts\\run_full_capture.py\"", background=true)
```

Poll its progress periodically (it prints one `PAGE N done: ...` line per
page) rather than waiting on a single call -- a full-history pull can run
long. When it prints `CAPTURE COMPLETE` it also writes a JSON summary to
`%LOCALAPPDATA%\Temp\second_brain_capture_cli\email_capture_summary.json`
(pages, totals, date range) -- read that if you need the final numbers
after checking back in.

## Recurring path (delta capture)

**`run_delta_capture.py`** (2026-08-22) is the RECURRING sibling --
same per-email steps, same single-process/O(1)-LLM-calls design, but
pages backward only until it reaches its own persisted watermark
(`.second-brain/email_capture_state.json`'s own `last_captured_at`,
the newest `received` this script has ever actually captured) instead of
walking the entire mailbox to true zero every run. A missing/first-run
watermark seeds a conservative 2-day lookback -- never a full-history
redo (that's `run_full_capture.py`'s own, separate, one-time job) and
never blind trust in "now" (which could silently miss a real gap).

```
terminal(command="python \"C:\\Users\\mahmoud.moussa\\AppData\\Local\\hermes\\skills\\vault-rebuild\\email-thread-capture\\scripts\\run_delta_capture.py\"")
```

Prints `{"status", "pages", "watermark_before", "watermark_after",
"total_new_emails", "threads_created", "messages_created",
"attachments_captured", "progress"}`. Intended for a recurring Hermes
cron job (`hermes cron create ... --repeat 0` for indefinite, or omit
`--repeat`) on an hourly-ish cadence -- new mail arrives continuously,
unlike Meetings' own naturally-bounded calendar window. Idempotent and
safe to run more often than needed: every per-email step it calls
(`ingest_email.py`, `rename_thread.py`, etc.) already dedupes on its own,
the watermark is just an efficiency optimization so a normal run only
re-walks a handful of pages instead of the whole mailbox.

**Fallback path** (only if `run_full_capture.py` itself fails to run, or
you're debugging one specific step): every script also works standalone,
invoked directly through the `terminal` tool from this Skill's own
`scripts/` folder, e.g. `terminal(command="python list_recent_emails.py
--limit 50")`. Two scripts (`ingest_email.py`, `capture_attachments.py`)
take structured input too large/binary for a safe CLI argument (email
bodies up to 50,000 chars; attachment bytes) -- `write_file` the JSON
payload to a scratch file first, then pass `--input-file <path>`. The
full per-email Procedure is below for this fallback case.

## Quick Reference

- `python list_recent_emails.py --vault-path P --limit N [--since S] [--before B]`
  -- fetch-only, zero side effects. Returns a JSON array of email dicts:
  `{id, subject, sender_name, sender_email, received, body, attachments:
  [{filename, temp_path, size}], conversation_id, recipients: [{name, email}]}`.
  `attachments[].temp_path` is a real file on disk holding that
  attachment's bytes (or `null` if it was too large) -- pass it straight
  through to `capture_attachments.py`, don't try to read/re-encode it
  yourself.
- `python ingest_email.py --vault-path P --input-file F` -- creates the
  Thread (first sight of `conversation_id`) and writes the message.
  Idempotent. `F`: `{conversation_id, message_id, received, sender_name,
  sender_email, subject, body, recipients, sender_department,
  sender_job_title, sender_company_name}` (the last three, and each
  recipient's own `department`/`job_title`/`company_name`, are 2026-08-21
  additions -- pass `list_recent_emails.py`'s own fields straight
  through, don't drop them). Returns `{thread_created, message_created,
  thread_path, message_path}`. Also keeps the Thread's own
  `last_message_at` frontmatter field current (the newest `received`
  seen for it across every call) -- summarize-and-tag-threads reads this
  to know whether a Thread needs a fresh summary.
- `python rename_thread.py --vault-path P --conversation-id ID` --
  relabels the Thread directory to `<date> <subject>` (Re:/RE: stripped).
  Idempotent.
- `python link_person_to_thread.py --vault-path P --conversation-id ID --sender-name NAME --sender-email EMAIL`
  -- ensures a Person note exists for the sender (no Customer/Partner
  match, no hub-linking -- that's the later Enrich pass) and links it
  into the Thread's own `## Related` section, alongside any Company
  wikilinks `create-companies-partners`'s own
  `retag_threads_by_participant_company` puts there separately
  (2026-08-21).
- `python capture_attachments.py --vault-path P --input-file F` -- saves
  real attachment bytes under the Thread's `files/` folder with a bare
  companion note (empty `## Summary`), and links it into the Thread's own
  `## Files` section (so the file is discoverable by opening the Thread
  note, not only by browsing the file tree). `F`: `{conversation_id,
  message_id, received, message_path, attachments}` (the exact
  `attachments` array `list_recent_emails.py` returned for this email).
  Returns `{captured: [...], skipped: [...]}`.
- `python capture_file_link.py --vault-path P --conversation-id ID --message-path MP --received R --label LABEL --url URL`
  -- for a file referenced only by a URL in the body (not a real
  attachment). Also links into the Thread's `## Files` section. **This
  one needs your own judgment** -- see step 2e below.

## Procedure (fallback -- see "Primary path" above)

1. Call `list_recent_emails.py --limit 50` to get the newest page.
2. For each email in the page, in order:
   a. `write_file` its data to a scratch JSON file, then call
      `ingest_email.py --input-file` with it.
   b. Call `link_person_to_thread.py` with the sender's name/email.
   c. Call `rename_thread.py`.
   d. If `attachments` is non-empty, `write_file` a
      `capture_attachments.py`-shaped payload (conversation_id,
      message_id, received, the `message_path` `ingest_email.py` just
      returned, and the email's own `attachments` array verbatim) and
      call `capture_attachments.py --input-file` with it.
   e. Read the email body. If it plainly references an external file by
      link (not a real attachment -- a genuine shared document/file
      reference, not just any random URL), call `capture_file_link.py`
      for it with a short, readable `--label`. If unsure, skip it -- a
      missed link-file can be added later; a false-positive junk note is
      harder to clean up.
3. After the page, note the OLDEST `received` timestamp you just saw.
4. Call `list_recent_emails.py --limit 50 --before <that timestamp>` to
   get the next, older page.
5. Repeat until a page comes back with zero emails -- that means you've
   reached the full history. Stop there.

## Pitfalls

- **Never skip step 2a-2c for any email**, even one that looks like
  spam, a notification, or unimportant. Every email gets a
  Thread/Message note. Judgment about importance is NOT this Skill's
  job.
- **Never summarize** an email, a Thread, or an attachment. Every `##
  Summary` section stays empty -- that is correct, expected behavior,
  not something to fix.
- **Person notes carry name/email/phone/linkedin/department/role/company**
  (2026-08-21: department/role/company are Outlook's own GAL fields --
  `GetExchangeUser().Department`/`.JobTitle`/`.CompanyName` -- populated
  automatically for internal, Exchange-resolved senders/recipients, left
  blank for anyone external; this Skill never guesses or looks them up
  any other way). **Still no Customer/Partner match, no hub-linking** --
  `company` above is a raw, plain-text signal, not the same thing as the
  real wikilinked relationship. That match/link is a separate, later pass
  (`create-companies-partners`'s own `retag_people_by_domain`), not this
  Skill's job. Don't try to add it here.
- **Always pass `recipients`** to `ingest_email.py` -- every participant
  (sender AND every recipient) gets a Person note and a link, not just
  the sender.
- If a script exits non-zero for one email, note the error and continue
  with the next -- one bad email must never stop the whole pull.
- An orphaned attachment temp file (a `capture_attachments.py` call that
  never ran, or failed mid-way) is harmless -- it just sits in the OS
  temp directory (`second_brain_capture_*` prefix) until cleaned up
  manually. Not worth chasing during this run.
- `run_full_capture.py` (the primary path) has external file-link
  capture (step 2e) **disabled by default** -- it only has a mechanical
  domain-match heuristic available (no real judgment inside a plain
  Python loop), and a wrong capture is worse than a missed one. This
  means externally-linked files (SharePoint/OneDrive "shared with you"
  links) are NOT captured during the bulk pull -- a real, disclosed gap,
  not a bug. If real judgment-based file-link capture matters, run the
  per-email Procedure fallback instead (step 2e uses your own judgment
  per email), or do a separate later pass.
- **Never run more than one capture job concurrently against the same
  vault.** Found live 2026-08-21: two concurrent cron jobs independently
  walking overlapping Outlook history caused a real Windows file-write
  race on `capture_attachments.py`'s raw attachment bytes (no locking, no
  atomic temp-file+rename) -- some attachments silently lost their bytes,
  a few lost their companion note entirely. One job at a time.

## Verification

- Report progress periodically (e.g. every page): how many emails
  processed so far, and the date range covered.
- When you reach an empty page, report that the pull is complete, with a
  final count of Threads/emails/attachments processed.
