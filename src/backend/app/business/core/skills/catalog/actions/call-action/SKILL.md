---
name: call-action
description: Perform one of this app's catalogued Actions, and report back only what really happened. Use it for ANY operation the "What this app can do" block lists -- and use report-unmet-request when it lists nothing that fits, instead of inventing an action or describing an outcome that did not happen.
version: 0.1.0
author: second-brain
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [second-brain, actions, catalogue, enforcement]
---

# Call an Action

This is the **one door** onto what Second Brain can do. Your own context
carries a `What this app can do` block listing the Actions you may call,
their inputs, and which of those inputs are required. This Skill is how
you call one.

The app validates every call against that same live catalogue before
anything runs. An unknown action id, a missing required input, an action
you are not permitted to call, and an action still waiting on the
operator's confirmation are each **refused by the app**, named, and
recorded in its Action-call ledger. The refusal is an answer: relay it.

## When to use this

- The operator asks for something and the catalogue block lists an
  Action that does it. Call that Action.
- The operator asks for something and **nothing in the block fits**.
  Call `report-unmet-request` with their own words. That records the
  gap so a genuinely missing capability gets discovered instead of
  fabricated. Then tell the operator plainly that this app has no action
  for it.

Do **not** use it to read the vault -- `vault-search` and
`vault_manager.py` are the direct lookups and cost nothing.

## Prerequisites

**Second Brain's backend must be running** (default
`http://127.0.0.1:8001`, override with `SECOND_BRAIN_API_URL`). If it is
not, this script says so on stderr and exits non-zero. That is a real
answer, not a reason to improvise: nothing was performed, and saying it
was would be false.

## How to run

Call it through the `terminal` tool as a PLAIN command starting with
`python`, never wrapped in `bash -c`/`-lc` (Hermes requires human
approval for any `-c` shell-string invocation, which stalls a
cron-triggered run with nobody there to approve it):

```
terminal(command="python \"${HERMES_SKILL_DIR}\call_action.py\" refresh-the-index --input scope=Projects")
```

Options:

- `--input NAME=VALUE` -- one input, repeatable. Sent as a string.
- `--inputs-json '{"force": true}'` -- all inputs at once, for inputs
  that are not strings.
- `--caller <agent id>` -- only if the default is wrong. By default the
  script names the Hermes profile it is deployed in, which IS your agent
  id.
- `--confirmed-call-id <call id>` -- see **Confirmation** below.
- `--base-url URL` -- a backend somewhere other than the default port.

## What the answers mean

Read the first line. It is one of:

- `PERFORMED` -- the app really did it, and prints what it returned.
- `RECORDED, NOT PERFORMED` -- the Action is something only the operator
  can do, on a screen the message names. Tell them where. Do not claim
  it was done.
- `AUTHORISED` -- the Action is a Skill, so the app granted it to you
  **once** and this script then ran that Skill here, in your own
  profile. The message carries that Skill's real output and its real
  exit status. A Skill that failed is reported as failed.
- `REFUSED BY THE APP` -- the gate said no and named why. Relay it
  verbatim. Do not substitute another action, do not do it another way.
- `WAITING FOR THE OPERATOR` -- see **Confirmation**.
- Anything else, or a non-zero exit with no verdict -- nothing can be
  claimed. Say that.

## Confirmation

Some Actions need the operator's say-so before they run. The first call
performs nothing and comes back `WAITING FOR THE OPERATOR` with a
`call_id` and the exact instruction. Tell the operator, and stop. When
they have confirmed it in the app, call the **same action with the same
inputs** again, adding `--confirmed-call-id <that call id>`. The
confirmation is single-use: it is spent by that one re-call, and a
decline is refused with `declined`.

## A Skill called as an Action

When an Action's implementation is a Skill, the app authorises it and
this script runs it in this profile. That Skill receives its validated
inputs as JSON in **two** places, so it may read whichever it prefers:
on **stdin**, and in the **`SECOND_BRAIN_ACTION_INPUTS`** environment
variable. `SECOND_BRAIN_ACTION_CALL_ID` carries the ledger id of the
call that granted it.

## What it will not do

Never invents an outcome. Never substitutes a different action, a search
or a plausible narrative for a call it could not make. Never reports a
refusal, a failed Skill or an unreachable backend as a success. It does
not decide anything itself: the catalogue, the permission check and the
confirmation all belong to the app, which is what makes "I cannot do
that" a true statement rather than a polite one.
