# `meeting-prep-agent` — cron job declaration

`REQ-SB-82-US-05`, `ADR-010`. Declares the new `meeting-prep-agent` Hermes
profile's own cron job — schedule, delivery, prompt — matching this
folder's own stated convention (`cron/README.md`: "its declaration...
goes here as its own file"). Mirrors the real, live `new-company-
discovery` cron's shape (`hermes/cron/jobs.json`, confirmed directly
2026-08-25: `schedule: {"kind": "interval", "minutes": 1440}`,
`deliver: "whatsapp"`, silent-unless-real-findings) — halved to 720
minutes (twice daily) per this agent's own PRD requirement (`REQ-SB-82`:
"can run 2 times a day").

Unlike `new-company-discovery` (a job on the shared default/Primary
profile), this job is created ON THE NEW `meeting-prep-agent` PROFILE
itself (`hermes -p meeting-prep-agent cron create ...`, not a bare
`hermes cron create ...`) — confirmed live 2026-08-25 that a cloned
profile inherits the same real WhatsApp `home_channel` config from
`default` (`profiles/<name>/config.yaml`'s own `platforms.whatsapp`
block), so `deliver: "whatsapp"` works identically per-profile, not only
from Primary.

## Schedule

```yaml
schedule:
  kind: interval
  minutes: 720
deliver: whatsapp
skill: person-lookup   # Hermes-Provisioning/skills/librarian/person-lookup/ (T01) — preloaded every run via --skill
```

## Prompt

The exact `prompt` argument passed to `hermes cron create`:

```
Run your own twice-daily meeting-prep scan. Follow your own SOUL.md exactly: find every real Meeting occurrence note in the vault ($SECOND_BRAIN_VAULT_PATH\Work\Meetings\) whose own `start` falls within the next 24 hours. For each one, check your own learned-suppression memory FIRST (keyed by the meeting's own series note `calendar_series_id`, falling back to its own `customer`/`partner` tag for a one-off meeting with no series note) -- skip a suppressed meeting entirely: no lookups, no notification, move to the next meeting. Delegate any genuinely unfamiliar technology/topic mentioned in the meeting to research-agent via the one-shot relay (`hermes -p research-agent chat -q "..." -Q`) -- never research it yourself, and fully specify what you need in that one call since the relay has no live back-channel. For every attendee, run `check_person_note_empty.py --note-path "Work/People/<their email>.md"` FIRST, every time, before ever doing a real web lookup -- only if it reports empty, perform the lookup and, if you find something real, call `append_person_findings.py` with the genuine findings; never fabricate, and never call it for an inconclusive result. After processing every meeting: if any non-suppressed meeting turned up real data worth checking, compose ONE WhatsApp message summarizing every such meeting (name/time, what you found, why it matters before that meeting). If nothing worth checking was found anywhere this run, or everything found was for a suppressed meeting, reply with nothing substantive -- do not send a no-op notification, matching new-company-discovery's own real, confirmed convention (never a "nothing new today" ping).
```

This prompt defers the bulk of the agent's own identity/logic to its
`SOUL.md` (real, live, provisioned directly on the profile — no
checked-in-repo copy, per this task's own Constraints and
`REQ-SB-82-US-02-T02`'s established precedent) — the prompt itself is
the concise, per-run recap `new-company-discovery`'s own real cron
prompt already uses ("Read SKILL.md fully and follow it exactly...").

## Real command run to provision this live

```
hermes -p meeting-prep-agent cron create "every 720m" "<prompt above, as one line>" --deliver whatsapp --skill person-lookup --name meeting-prep-agent
```

## Applied

**2026-08-25:** job `7b8f10e528ab`, created live on the real
`meeting-prep-agent` profile (`hermes -p meeting-prep-agent cron create
"every 720m" ... --deliver whatsapp --skill person-lookup --name
meeting-prep-agent`). Confirmed via `hermes -p meeting-prep-agent cron
list`/`cron status`: `Schedule: every 720m` (recurring, not a one-shot —
the real `"every "`-prefixed form), `Deliver: whatsapp`, `Skills:
person-lookup`, first `Next run: 2026-08-26T04:16:46.897109+04:00`.

**Real, disclosed gap found live:** the profile's own gateway (needed
for the schedule to actually fire unattended) exited immediately on
start — `WhatsApp enabled but not paired` for this NEW profile (its own
`platforms/whatsapp/session/creds.json` doesn't exist yet; pairing is a
real, human-interactive QR-code scan, `hermes whatsapp`, out of this
session's own reach). The Windows login item is installed
(`hermes gateway install`, confirmed), so the gateway will attempt to
start on every login and begin firing this job for real once the
operator completes that one-time pairing step. Every OTHER specialist
profile in this install (`opp-manager`, `research-agent`,
`daily-briefing`, etc.) shows the identical "gateway not running" state
by default — this is this install's own standing operational pattern,
not a defect introduced by this task. See `REQ-SB-82-US-05-T02`'s own
Implementation Log for the full, disclosed live-vs-configured
verification breakdown.
