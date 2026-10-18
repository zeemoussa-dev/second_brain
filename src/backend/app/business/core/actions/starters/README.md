# Starter Actions — the Actions the framework itself ships

One folder per Action id, each holding an `Action.json` in exactly the shape
`data/Actions/<id>/Action.json` has on a real install. `ADR-032` allows the
framework to ship starter Actions; `ActionManager.seed_shipped_starters()`
installs any this install does not already have.

This mirrors `business/core/templates/masters/` — shipped source, not user
data — and inherits its one hard rule: **a starter is never overwritten.** An
id already in the store is left exactly as it is, whatever it now contains,
because the operator's own edit to a starter outranks the shipped copy and the
seed runs on every boot rather than once.

## Why `report-unmet-request` ships

`REQ-SB-95`'s "I cannot do that must be a first-class answer — that is how a
missing capability gets discovered instead of fabricated". A refusal that is
only a sentence leaves nothing behind; calling this Action leaves a row in the
Action-call ledger carrying the operator's own words. It is a `ui`
implementation on purpose: the app genuinely cannot do anything about an unmet
request, so it performs nothing and points at the screen where a human decides
whether to build the capability.
