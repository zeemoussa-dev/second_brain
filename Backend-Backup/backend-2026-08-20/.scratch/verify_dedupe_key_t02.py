"""Throwaway manual verification script for BUGFIX-08-US-01-T02's own
Tests section (direct Python-shell calls against the real
email_classification/librarian_housekeeping/pending_approval_registry
functions, per the task's own authorized manual-verification shape). Run
once against the real, configured vault/store, then discarded -- not part
of any Files to Modify list."""
from __future__ import annotations

import sys

sys.path.insert(0, r"C:\myWorx\Projects\Second Brain\src\backend")

from app.business import email_classification, pending_approval_registry  # noqa: E402
from app.business.pipelines import librarian_housekeeping  # noqa: E402
from app.data_access import vault_writer  # noqa: E402


def show(title: str) -> None:
    print(f"\n=== {title} ===")


# --- Step 1 (AC-02) -- route_to_project, real reprocessing ----------------
show("Step 1 -- AC-02: route_to_project, real reprocessing")
REAL_THREAD_PATH_STR = (
    r"C:\myWorx\Moussa MD\Moussa Brain\Work\Threads\2026-07-27 Requested Item RITM0108464 has "
    r"been updated\2026-07-27 Requested Item RITM0108464 has been updated.md"
)
thread_result = {
    "created": True,
    "thread_path": REAL_THREAD_PATH_STR,
    "conversation_id": "zz-verify-conv-001",
}
classification = {"customer": "ZZ Verify Customer"}
email: dict = {"subject": "zz verify", "sender_email": "zz@example.com", "sender_name": "ZZ"}

r1 = email_classification.route_to_project(thread_result, classification, email)
r2 = email_classification.route_to_project(thread_result, classification, email)
print(f"call1 id={r1['id']} call2 id={r2['id']} same_id={r1['id'] == r2['id']}")

route_records = [
    r for r in pending_approval_registry.list_pending_approvals(
        status="pending", agent_id="email-capture-pipeline",
    )
    if r["action_id"] == "route_thread_to_project"
    and r.get("dedupe_key") == "route_thread_to_project:zz-verify-conv-001"
]
print(f"exactly one matching pending record: {len(route_records) == 1} (count={len(route_records)})")
pending_approval_registry.resolve_pending_approval(r1["id"], "declined")
print("cleaned up (declined)")

# --- Step 2 (AC-02) -- classification-failure acknowledgement -------------
show("Step 2 -- AC-02: classification-failure acknowledgement, real reprocessing")
fail_email = {
    "conversation_id": "zz-verify-conv-002",
    "subject": "zz verify failure",
    "sender_email": "zz@example.com",
    "sender_name": "ZZ",
}
exc = Exception("zz verify simulated Compass failure")
f1 = email_classification._create_classification_failure_pending_approval(fail_email, exc)
f2 = email_classification._create_classification_failure_pending_approval(fail_email, exc)
print(f"call1 id={f1['id']} call2 id={f2['id']} same_id={f1['id'] == f2['id']}")

fail_records = [
    r for r in pending_approval_registry.list_pending_approvals(
        status="pending", agent_id="email-capture-pipeline",
    )
    if r["action_id"] == "acknowledge_classification_failure"
    and r.get("dedupe_key") == "acknowledge_classification_failure:zz-verify-conv-002"
]
print(f"exactly one matching pending record: {len(fail_records) == 1} (count={len(fail_records)})")
pending_approval_registry.resolve_pending_approval(f1["id"], "declined")
print("cleaned up (declined)")

# --- Step 3 (AC-02) -- propose_customer_backfill, real Job re-run --------
show("Step 3 -- AC-02: propose_customer_backfill, real Job re-run")
# BOUNDING DISCLOSED: the real, current vault has 123 real "Unsorted" Threads
# today. Running the unbounded Job twice would fire ~246 real Compass API
# calls and could create ~dozens of new real, legitimate proposals in the
# live Pending Approvals queue purely for this verification pass -- costly
# and disruptive right after this same session's own queue cleanup. Per the
# task's own explicit authorization ("bound scope via an in-process
# monkeypatch of vault_writer.list_thread_notes() to a small, real, filtered
# subset... and disclose that bounding explicitly"), this run is bounded to
# 3 real, already-existing Unsorted Threads whose own titles suggest a real
# Customer match (Core42/Columbus/Mubadala-related subjects), still the
# literal real Job function end-to-end (real Compass calls, real
# create_pending_approval calls) -- only the INPUT SET is bounded, not the
# mechanism under test.
_all_unsorted = [
    p for p in vault_writer.list_thread_notes()
    if vault_writer.read_note(p)[0].get("customer") == "Unsorted"
]
_bounded_subset = [
    p for p in _all_unsorted
    if any(
        needle in str(p) for needle in (
            "Azerbaijan Engagement", "Core42 & Columbus Partnership",
            "Shadi Shaat shared",
        )
    )
]
print(f"bounded subset size: {len(_bounded_subset)} (of {len(_all_unsorted)} real Unsorted Threads)")
for p in _bounded_subset:
    print(f"  - {p}")
_original_list_thread_notes = vault_writer.list_thread_notes
vault_writer.list_thread_notes = lambda: _bounded_subset

before_count = len([
    r for r in pending_approval_registry.list_pending_approvals(
        status="pending", agent_id="librarian-housekeeping",
    )
    if r["action_id"] == "propose_customer_backfill_routing"
])
run1 = librarian_housekeeping.propose_customer_backfill()
run2 = librarian_housekeeping.propose_customer_backfill()
vault_writer.list_thread_notes = _original_list_thread_notes
run1_by_customer = {b["customer"]: b["approval_id"] for b in run1["proposed_batches"]}
run2_by_customer = {b["customer"]: b["approval_id"] for b in run2["proposed_batches"]}
print(f"run1 proposed_batches customers: {sorted(run1_by_customer)}")
print(f"run2 proposed_batches customers: {sorted(run2_by_customer)}")
common = set(run1_by_customer) & set(run2_by_customer)
if common:
    all_identical = all(run1_by_customer[c] == run2_by_customer[c] for c in common)
    print(f"every customer present in BOTH runs has identical approval_id: {all_identical}")
else:
    print(
        "no customer appeared in both runs' proposed_batches (either zero Unsorted Threads "
        "map to a known customer right now, or the real vault happened to have none in common) "
        "-- falling back to a direct registry-level two-call check of the exact convention"
    )
    fb1 = pending_approval_registry.create_pending_approval(
        agent_id="librarian-housekeeping", trigger="direct",
        action_id="propose_customer_backfill_routing", description="zz verify backfill fallback",
        dedupe_key="propose_customer_backfill_routing:ZZ Verify Fallback Customer",
    )
    fb2 = pending_approval_registry.create_pending_approval(
        agent_id="librarian-housekeeping", trigger="direct",
        action_id="propose_customer_backfill_routing", description="zz verify backfill fallback 2",
        dedupe_key="propose_customer_backfill_routing:ZZ Verify Fallback Customer",
    )
    print(f"fallback direct registry check -- same id: {fb1['id'] == fb2['id']}")
    pending_approval_registry.resolve_pending_approval(fb1["id"], "declined")

after_count = len([
    r for r in pending_approval_registry.list_pending_approvals(
        status="pending", agent_id="librarian-housekeeping",
    )
    if r["action_id"] == "propose_customer_backfill_routing"
])
print(f"pending propose_customer_backfill_routing count before={before_count} after={after_count}")
print(
    "(after both real runs -- growth only reflects genuinely NEW real proposals from run1, "
    "run2 must add ZERO beyond what run1 already added, since run2's targets are the same "
    "still-Unsorted Threads)"
)

# --- Step 4 (AC-02) -- propose_customer_archival_candidates, real Job re-run
show("Step 4 -- AC-02: propose_customer_archival_candidates, real Job re-run")
matched = run1["matched_existing_customer_names"]
a1 = librarian_housekeeping.propose_customer_archival_candidates(matched)
a2 = librarian_housekeeping.propose_customer_archival_candidates(matched)
a1_by_customer = {c["customer"]: c["approval_id"] for c in a1["archival_candidates"]}
a2_by_customer = {c["customer"]: c["approval_id"] for c in a2["archival_candidates"]}
print(f"a1 candidates: {sorted(a1_by_customer)}")
print(f"a2 candidates: {sorted(a2_by_customer)}")
identical = a1_by_customer == a2_by_customer
print(f"identical approval_id per candidate across both calls: {identical}")

# --- Step 5 -- cleanup / disclosure ---------------------------------------
show("Step 5 -- cleanup / disclosure")
leftover_verify = [
    r for r in pending_approval_registry.list_pending_approvals(status="pending")
    if r["agent_id"].startswith("zz-verify") or (r.get("dedupe_key") or "").startswith(
        "propose_customer_backfill_routing:ZZ Verify"
    )
]
print(f"leftover throwaway zz-verify* pending records: {len(leftover_verify)} (expect 0)")
real_new_backfill = after_count - before_count
print(
    f"real, legitimate NEW propose_customer_backfill_routing records created by run1 "
    f"(left pending for the operator, not cleaned up by this script): {real_new_backfill}"
)
print(
    f"real archival_candidate records created (left pending for the operator): "
    f"{len(a1_by_customer)}"
)
