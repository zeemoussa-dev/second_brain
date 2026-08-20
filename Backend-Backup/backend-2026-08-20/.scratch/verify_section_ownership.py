"""Throwaway manual verification script for REQ-SB-71-US-01-T01's own
Tests section (explicitly authorized: "In a Python shell (or a small
throwaway script)"). Run once, against the real vault, then discarded --
not part of any Files to Modify list."""
from __future__ import annotations

import sys

sys.path.insert(0, r"C:\myWorx\Projects\Second Brain\src\backend")

from app.data_access import section_ownership, vault_writer  # noqa: E402

REAL_THREAD_PATH = vault_writer.settings.vault_path / "Work" / "Threads" / \
    "Requested Item RITM0108464 has been updated-2026-07-27-025663bd.md"


def show(title: str) -> None:
    print(f"\n=== {title} ===")


before_text = REAL_THREAD_PATH.read_text(encoding="utf-8")

# Step 1 (AC-02): a registered caller naming a header OUTSIDE its own
# allow-list must be rejected outright.
show("Step 1 -- AC-02: caller outside its own allow-list")
try:
    vault_writer.replace_body_section(
        REAL_THREAD_PATH, "## Personal Notes", "x",
        caller="thread_summary_backfill.backfill_thread_summaries",
    )
    print("FAIL -- no exception raised")
except section_ownership.SectionWriteNotAllowed as exc:
    print(f"PASS -- SectionWriteNotAllowed raised: {exc}")
after_text = REAL_THREAD_PATH.read_text(encoding="utf-8")
print(f"Content unchanged: {after_text == before_text}")

# Step 2 (AC-03): EVERY registered caller id is rejected against BOTH
# human-owned headers, uniformly -- including a caller otherwise permitted
# to write something.
show("Step 2 -- AC-03: human-owned headers unconditionally unwritable, all 5 callers")
all_caller_ids = list(section_ownership._CALLER_ALLOW_LISTS.keys())
for caller_id in all_caller_ids:
    for human_header in sorted(section_ownership._HUMAN_OWNED_HEADERS):
        try:
            vault_writer.replace_body_section(
                REAL_THREAD_PATH, human_header, "x", caller=caller_id,
            )
            print(f"FAIL -- {caller_id} / {human_header} -- no exception raised")
        except section_ownership.SectionWriteNotAllowed:
            print(f"PASS -- {caller_id} / {human_header} -- rejected")
after_text = REAL_THREAD_PATH.read_text(encoding="utf-8")
print(f"Content unchanged after all 10 attempts: {after_text == before_text}")

read_result = vault_writer.read_body_section(REAL_THREAD_PATH, "## Personal Notes")
print(f"read_body_section still succeeds for a human-owned header: {read_result!r}")

# Step 3 -- non-AC regression: an ALLOWED caller/header pair still succeeds.
show("Step 3 -- non-AC regression: allowed caller/header pair still succeeds")
allowed_write_ok = vault_writer.replace_body_section(
    REAL_THREAD_PATH, "## Summary", "Verification round-trip content.",
    caller="thread_summary_backfill.backfill_thread_summaries",
)
round_tripped = vault_writer.read_body_section(REAL_THREAD_PATH, "## Summary")
print(f"Allowed write returned: {allowed_write_ok}, round-tripped content: {round_tripped!r}")
# Restore the real Thread note's own pre-verification content -- this
# script must not leave the real vault altered by its own throwaway probe.
REAL_THREAD_PATH.write_text(before_text, encoding="utf-8")
restored_text = REAL_THREAD_PATH.read_text(encoding="utf-8")
print(f"Real note restored to its pre-verification content: {restored_text == before_text}")

# Step 4 -- non-AC regression: an unregistered caller is denied-by-default.
show("Step 4 -- non-AC regression: unregistered caller denied-by-default")
try:
    vault_writer.replace_body_section(
        REAL_THREAD_PATH, "## Summary", "x", caller="nonexistent.function",
    )
    print("FAIL -- no exception raised")
except section_ownership.SectionWriteNotAllowed as exc:
    print(f"PASS -- SectionWriteNotAllowed raised: {exc}")
final_text = REAL_THREAD_PATH.read_text(encoding="utf-8")
print(f"Real note still matches its pre-verification content: {final_text == before_text}")

# Step 5 (AC-04 support) -- confirm the exact caller+header pair
# finalize_background_amendment_proposal uses is itself allowed, at the
# guard layer this function's own retrofitted call goes through.
show("Step 5 -- exact finalize_background_amendment_proposal caller/header pair")
print(
    "is_header_allowed check:",
    section_ownership.is_header_allowed(
        "project_customer_synthesizer.finalize_background_amendment_proposal",
        "## Background",
    ),
)
