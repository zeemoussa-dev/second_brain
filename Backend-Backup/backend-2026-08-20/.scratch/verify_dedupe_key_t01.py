"""Throwaway manual verification script for BUGFIX-08-US-01-T01's own
Tests section (direct Python-shell calls against the real registry/skill
functions, per the task's own authorized manual-verification shape). Run
once against the real, configured vault/store, then discarded -- not part
of any Files to Modify list."""
from __future__ import annotations

import sys

sys.path.insert(0, r"C:\myWorx\Projects\Second Brain\src\backend")

from app.business import (  # noqa: E402
    pending_approval_registry,
    skill_registry,
    working_mode_registry,
)


def show(title: str) -> None:
    print(f"\n=== {title} ===")


# --- Step 1 (AC-01) -- registry-level mechanism, isolated -----------------
show("Step 1 -- AC-01: registry-level mechanism, isolated")
first = pending_approval_registry.create_pending_approval(
    agent_id="zz-verify", trigger="scheduled", action_id="run_capture_now",
    description="verify dedupe A", dedupe_key="run_capture_now:zz-verify",
)
second = pending_approval_registry.create_pending_approval(
    agent_id="zz-verify", trigger="direct", action_id="run_capture_now",
    description="verify dedupe B", dedupe_key="run_capture_now:zz-verify",
)
print(f"first id={first['id']} second id={second['id']} same_id={first['id'] == second['id']}")
print(f"second description still first's own: {second['description']!r} (expect 'verify dedupe A')")
only_records = pending_approval_registry.list_pending_approvals(status="pending", agent_id="zz-verify")
print(f"exactly one pending record for zz-verify: {len(only_records) == 1} (count={len(only_records)})")
cleanup1 = pending_approval_registry.resolve_pending_approval(first["id"], "declined")
print(f"cleanup declined ok: {cleanup1['status'] == 'declined'}")

# --- Step 2 (AC-01) -- real end-to-end race, through invoke_skill ---------
show("Step 2 -- AC-01: real end-to-end race through invoke_skill")
AGENT_ID = "meeting-capture"
SKILL_ID = "run_capture_now"
original_mode = working_mode_registry.get_agent_working_mode(AGENT_ID)
print(f"original working mode for {AGENT_ID}: {original_mode!r}")
mode_was_changed = False
if original_mode != "supervised":
    working_mode_registry.set_agent_working_mode(AGENT_ID, "supervised")
    mode_was_changed = True

result_a = skill_registry.invoke_skill(AGENT_ID, SKILL_ID, args=None, trigger="scheduled")
result_b = skill_registry.invoke_skill(AGENT_ID, SKILL_ID, args=None, trigger="direct")
print(f"result_a: {result_a}")
print(f"result_b: {result_b}")
same_pending_id = (
    result_a.get("status") == "pending"
    and result_b.get("status") == "pending"
    and result_a.get("pending_approval_id") == result_b.get("pending_approval_id")
)
print(f"both pending with identical pending_approval_id: {same_pending_id}")

records = pending_approval_registry.list_pending_approvals(status="pending", agent_id=AGENT_ID)
matching = [r for r in records if r["action_id"] == SKILL_ID]
print(f"exactly one pending run_capture_now record for {AGENT_ID}: {len(matching) == 1} (count={len(matching)})")
if matching:
    print(f"record dedupe_key: {matching[0].get('dedupe_key')!r} (expect '{AGENT_ID}:{SKILL_ID}')")

if mode_was_changed:
    working_mode_registry.set_agent_working_mode(AGENT_ID, original_mode)
    print(f"restored working mode to {original_mode!r}")
else:
    print("working mode was already 'supervised' -- not restoring (per task instruction)")

# --- Step 3 (AC-01) -- surviving record stays normally resolvable --------
show("Step 3 -- AC-01: surviving record stays normally resolvable")
survivor_id = result_a.get("pending_approval_id")
resolved = pending_approval_registry.resolve_pending_approval(survivor_id, "approved")
print(f"resolved: status={resolved['status']!r} resolved_at not null={resolved['resolved_at'] is not None}")

# --- Step 4 -- regression check (Constraints, not itself a locked AC) ----
show("Step 4 -- regression: background guard unchanged; different dedupe_keys never collapse")
bg1 = pending_approval_registry.create_pending_approval(
    agent_id="zz-verify-bg", trigger="background", action_id="x", description="bg1",
)
bg2 = pending_approval_registry.create_pending_approval(
    agent_id="zz-verify-bg", trigger="background", action_id="x", description="bg2",
)
print(f"background guard still fires (same id): {bg1['id'] == bg2['id']}")
pending_approval_registry.resolve_pending_approval(bg1["id"], "declined")

dk1 = pending_approval_registry.create_pending_approval(
    agent_id="zz-verify-dk", trigger="direct", action_id="x", description="dk1",
    dedupe_key="x:target-1",
)
dk2 = pending_approval_registry.create_pending_approval(
    agent_id="zz-verify-dk", trigger="direct", action_id="x", description="dk2",
    dedupe_key="x:target-2",
)
print(f"different dedupe_key values create distinct records: {dk1['id'] != dk2['id']}")
pending_approval_registry.resolve_pending_approval(dk1["id"], "declined")
pending_approval_registry.resolve_pending_approval(dk2["id"], "declined")

show("Final cleanup check -- no lingering zz-verify* pending records")
leftover = [
    r for r in pending_approval_registry.list_pending_approvals(status="pending")
    if r["agent_id"].startswith("zz-verify")
]
print(f"leftover pending zz-verify* records: {len(leftover)} (expect 0)")
