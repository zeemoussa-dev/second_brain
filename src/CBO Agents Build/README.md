# CBO Agents Build — reference only

**Nothing in this folder runs.** It is not deployed to Hermes, not scheduled,
not imported by the app, and not shown on the Agents Map. It records the
one-time pipelines used to *build* a CBO install — the backfills, first builds,
migrations and retrofits — so they can be understood and re-run deliberately
on a new install. Every file carries `"reference": true`.

## Why these are separated

The Agents Map is what the CBO watches, and what the CBO needs to see is the
**steady state**: what happens to a new email, a new meeting, a new attachment.
A one-time backfill sitting beside those, with a "last run" weeks old and no
schedule, reads as a broken pipeline. So the map shows only the delta
pipelines, and the build pipelines live here.

| Live on the map (delta) | What it does to NEW data |
|---|---|
| Email Capture | new mail → Thread + messages + attachments, hourly |
| Meeting Capture | calendar changes (2 days back, 14 ahead) → Meetings, hourly |
| Metadata | hubs, folders, People, tags — nightly; missing hubs every 30 min |
| Thread Enrichment | summary, people, actions from each new or grown Thread |
| File Enrichment | summary, caption and companies for each new attachment |

A delta pipeline is also what clears its own backlog: Enrichment is the same
pipeline whether it faces 2,000 unread Threads or 20.

## What is here

| Reference pipeline | Built | Script |
|---|---|---|
| [Email History Backfill](pipelines/email-history-backfill.json) | Threads for the last N months of mail | `m365/email-thread-capture/scripts/run_full_capture.py` |
| [Meeting History Backfill](pipelines/meeting-history-backfill.json) | Meetings over a wide window | `m365/meeting-capture/scripts/run_full_meeting_capture.py` |
| [Company Discovery — First Build](pipelines/company-discovery-first-build.json) | `Entities.md`, the Customer and Partner hubs | `vault/entity-domain-extraction`, `vault/create-companies-partners` |
| [Entity Curation](pipelines/entity-curation.json) | real company names, merges, classification | operator review + online research |
| [Hub Template Migration](pipelines/hub-template-migration.json) | existing hubs brought to a new template shape | `vault/create-companies-partners/scripts/migrate_hub_children.py` |
| [Thread Retrofit](pipelines/thread-retrofit.json) | Conversation index and kind tags on the backlog | `m365/email-thread-capture/scripts/retrofit_conversation_index.py` |

Script paths are relative to `src/backend/app/business/core/skills/catalog/`.

## Order on a new install

1. Email History Backfill, then Meeting History Backfill.
2. Company Discovery — First Build, stopping for the operator's review.
3. Entity Curation, then let the Metadata pipeline create the hubs.
4. Turn on the delta pipelines. Enrichment works through the backlog first.

Hub Template Migration and Thread Retrofit are only needed when a template or a
capture format changes after notes already exist — a template shapes only the
notes created after it changed.

## What must never be moved here

A script a live pipeline calls. Several scripts are both: the retrofit is a
one-time build step AND the last step of the nightly Metadata pass, and
`run_full_meeting_capture.py` over a short window IS the meeting delta. This
folder describes the build runs; the scripts stay in their Skills.
