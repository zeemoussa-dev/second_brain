"""Out-of-band derivation of the noise-definition artifact (ADR-018,
REQ-SB-87-US-03-T01) -- a genuinely SEPARATE act from Capture's own
recurring tick, never invoked from ingest_email.py/run_delta_capture.py.
Run this script ON-DEMAND only: for the initial derivation, again during
the 100-email scratch-sample proving phase, and again whenever the
operator wants to retune what counts as noise.

Takes a real sample of email content (a JSON array of
{subject, sender_email, body} objects -- either a hand-curated
--sample-file, or one of list_recent_emails.py's own real JSON pages fed
straight through) and relays ONE one-shot `hermes chat -q ...` question
to a real Hermes profile, asking it to derive a structured noise
definition FROM that sample. The definition's own CONTENT is the
model's real reasoning output (PRD point 7, "prompt-driven, minimal
code") -- this script's own code is limited to building the prompt,
invoking the relay, parsing the structured JSON response, and
persisting it; it never hand-writes a keyword/sender rule itself.

Writes/overwrites `.second-brain/data/EmailCapture/noise_definition.json`
under the vault -- a real sibling to `.second-brain/data/Templates/`,
read directly by every Capture script that already receives
--vault-path (zero deploy step), mirroring Template.json's own
already-established live-vault-path convention (ADR-018). On a relay or
parse failure, the previous artifact is left untouched -- a failed
re-derivation must never clobber a good one.

Usage:
    python derive_noise_definition.py --vault-path P
        [--sample-file F] [--profile PROFILE] [--timeout SECONDS]

`--sample-file` (optional): a JSON array of {subject, sender_email,
body} objects. When omitted, this script grounds the derivation against
its own built-in default -- the five real, live, operator-confirmed
noise-shaped example Threads (REQ-SB-87-US-03, Scenario 10; subjects
verbatim in Constraints), copied directly from the real vault at
`C:\\myWorx\\Moussa MD\\Moussa Brain\\Work\\Threads\\` on 2026-09-02 --
not fabricated content.

`--profile` (optional): which Hermes profile answers the one-shot
relay. Defaults to the root/default profile (no `-p` flag at all --
Hermes' own "default profile needs no -p" convention, matching
app/hermes/cli.py::HermesCLI._profile_args). A dedicated, lightweight
CLASSIFIER profile (fed this artifact at capture time) is
REQ-SB-87-US-03-T02's own separate job -- this script's job is proving
the derivation MECHANISM works and producing a real, grounded first
artifact, not provisioning that later profile.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

import vault_manager

# A real sample/derivation response can carry a Unicode character (the
# CRM Enhancements seed subject itself has an emoji) -- same fix as
# list_recent_emails.py's own 2026-08-24 finding: Windows' default
# console codepage can't encode it, crashing stdout without this.
sys.stdout.reconfigure(encoding="utf-8")

_HERMES_EXE = "hermes"  # resolvable on PATH, matching this Skill's own `python` convention (SKILL.md)
_DEFAULT_TIMEOUT_SECONDS = 420  # a real relay call's own latency is genuinely variable -- tens of seconds to several minutes (Learnings.md) -- never assume a hang from wall-clock alone

_ARTIFACT_RELATIVE_PATH = Path("data") / "EmailCapture" / "noise_definition.json"

# Real, live, operator-confirmed noise-shaped seed content (2026-09-02,
# REQ-SB-87-US-03 Constraints/Scenario 10) -- copied directly from the
# real vault's own RawMessage notes under
# `Work\Threads\<thread>\messages\`, trimmed to what a real classifier
# would actually see (sender, subject, body). This is the built-in
# default sample so the FIRST real derivation run needs no separate
# committed sample file (this task's own `## Files to Modify` names only
# the artifact + this script).
_DEFAULT_SEED_SAMPLE = [
    {
        "subject": "Learning Assignment Changes Email Notification",
        "sender_email": "Ownyourgrowth@core42.ai",
        "body": (
            "The following assignments were added to your Learning Plan: "
            "ONLINE, INFOSEC_M1_001, 8/7/2026 10:37 Asia/Dubai, Core42 "
            "Information Security Awareness Training,"
        ),
    },
    {
        "subject": "New Payslip available for viewing/download",
        "sender_email": "donotreply@ey.com",
        "body": (
            "Hi Mahmoud Moussa, This email is to notify you that a new "
            "Payslip is now available for viewing and download in the EY "
            "Interact Payroll. Click here to login. Regards, EY Payroll "
            "Operator"
        ),
    },
    {
        "subject": "Core42 Information Security Awareness Training",
        "sender_email": "Ownyourgrowth@core42.ai",
        "body": (
            "Hello Moussa, Mahmoud Medhat Mahmoud, You have been assigned "
            "the Core42 e-learning course(s) shown below. You are required "
            "to complete this training as a part of your ongoing "
            "compliance training obligations. Mandatory Training: Core42 "
            "Information Security Awareness Training. Deadline: "
            "31/10/2026. This is an automated notification. To access the "
            "e-learning course(s) now, please click on the link below: "
            "Orbit Learning Hub. Kind Regards, Human Capital and Culture "
            "Team"
        ),
    },
    {
        "subject": "Compass Alert: Failed API Calls",
        "sender_email": "status.notification@compass.core42.ai",
        "body": (
            "Failed API Calls Alert. Hello Mahmoud Moussa, A Failed API "
            "Calls alert has been triggered for overall Compass API "
            "calls. The failure rate over the per minute has reached "
            "100.0%, exceeding your configured threshold of 70.0%. This "
            "alert is sent at most once per day. Review your API call "
            "logs to diagnose potential issues. This is an automated "
            "email notification; please do not reply to this message. "
            "Thank you, The Compass Team"
        ),
    },
    {
        "subject": "CRM Enhancements | Weekly Release Summary \U0001f680",
        "sender_email": "Comms-salesexcellence@core42.ai",
        "body": (
            "Hello Team, In our ongoing commitment to enhance your "
            "digital experience, we have implemented the below new "
            "features to the Core42 Salesforce CRM Platform. On a weekly "
            "basis, we would like to share these with you going forward. "
            "Please find below the enhancements / new features deployed & "
            "summary of benefits. [ticket-by-ticket CRM changelog table]. "
            "For any questions or feedback, please contact the Sales "
            "Excellence Team. Best regards, Sales Excellence Team"
        ),
    },
]

_PROMPT_TEMPLATE = """You are helping derive a real, structured, reusable definition of
"noise" for an automated email-capture pipeline. This definition will be
persisted as JSON and later applied, unattended, to every genuinely new
email conversation the pipeline sees -- so it must be a real, general
CATEGORY description, not a rule that only matches these exact emails
verbatim.

Locked business context (already decided by the operator, not open for
you to re-litigate):
- Literal meeting invites (.ics calendar items) are already filtered out
  upstream, before this classification ever runs -- do NOT define noise
  in terms of meeting invites.
- The real noise category is broader: anything AUTOMATED or BROADCAST --
  system/HR/security notifications, broadcast newsletters, and
  workshop/event-announcement blasts. A genuine one-to-one or small-group
  human conversation (even about a mundane topic) is never noise.

Below are {sample_size} real example emails the operator has already
confirmed are noise-shaped. Use them to GROUND your definition -- study
what they have in common (automated sender patterns, "do not reply"
language, notification/alert framing, broadcast-to-many framing) -- but
state the definition as a general category, not as "matches one of these
five subjects."

{sample_block}

Respond with ONLY a single JSON object (no markdown code fences, no
prose before or after it) with exactly this shape:
{{
  "category": "<a short label for this noise category>",
  "description": "<2-4 sentences describing the category in your own words>",
  "criteria": ["<a natural-language rule an email must match to count as noise>", "..."],
  "positive_signals": ["<a short phrase/pattern that suggests noise>", "..."],
  "negative_signals": ["<a short phrase/pattern that means an email is NOT noise even if it looks automated>", "..."]
}}
"""


def _build_prompt(sample: list[dict]) -> str:
    sample_lines = []
    for i, item in enumerate(sample, start=1):
        sample_lines.append(
            f"Example {i}:\n"
            f"  Subject: {item.get('subject', '')}\n"
            f"  Sender: {item.get('sender_email', '')}\n"
            f"  Body: {item.get('body', '')}"
        )
    return _PROMPT_TEMPLATE.format(
        sample_size=len(sample), sample_block="\n\n".join(sample_lines)
    )


def _extract_json_object(raw: str) -> dict:
    """The relay's own real response can carry leading/trailing prose or
    a ```json fenced block even when explicitly told not to -- locate
    the first '{' and let json.JSONDecoder.raw_decode find the matching
    closing brace from there, rather than assuming the whole string is
    bare JSON."""
    start = raw.find("{")
    if start == -1:
        raise ValueError(f"no JSON object found in relay response: {raw[:500]!r}")
    decoder = json.JSONDecoder()
    obj, _end = decoder.raw_decode(raw, start)
    return obj


def _run_relay(prompt: str, profile: str | None, timeout: int) -> str:
    with tempfile.TemporaryDirectory(prefix="second_brain_noise_derivation_") as tmp_dir:
        query_path = os.path.join(tmp_dir, f"query_{uuid.uuid4().hex}.txt")
        with open(query_path, "w", encoding="utf-8") as f:
            f.write(prompt)

        args = [_HERMES_EXE]
        if profile:
            args += ["-p", profile]
        args += ["chat", "-Q", "--query-file", query_path]

        # Same explicit-UTF-8-both-sides discipline as run_delta_capture.py's
        # own run_script() -- a real relay reply can carry non-ASCII
        # content (an emoji subject, a name) that the OS locale's default
        # encoding (cp1252 here) would silently mangle or crash on.
        proc = subprocess.run(
            args, capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=timeout,
        )
        if proc.returncode != 0:
            raise RuntimeError(
                f"hermes chat relay failed (code {proc.returncode}): "
                f"{(proc.stderr or proc.stdout or '').strip()[:1000]}"
            )
        return (proc.stdout or "").strip()


def derive(vault_path: str, sample: list[dict], profile: str | None, timeout: int) -> dict:
    prompt = _build_prompt(sample)
    raw_response = _run_relay(prompt, profile, timeout)
    definition = _extract_json_object(raw_response)

    artifact = {
        "version": 1,
        "derived_at": datetime.now(timezone.utc).isoformat(),
        "derivation_profile": profile or "default",
        "sample_size": len(sample),
        "sample_subjects": [item.get("subject", "") for item in sample],
        "definition": definition,
    }

    artifact_path = vault_manager.data_root(Path(vault_path)) / _ARTIFACT_RELATIVE_PATH
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(
        json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return artifact


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--vault-path",
        # Defaults to what Second Brain's setup wizard writes into Hermes'
        # own .env, so a Skill never has to name a machine-specific
        # absolute path and a bundle never has to have one rewritten on
        # import. Pass it only to override.
        default=os.environ.get("SECOND_BRAIN_VAULT_PATH", ""),
    )
    parser.add_argument("--sample-file", default=None, help="JSON array of {subject, sender_email, body}; defaults to the built-in 5 real seed examples")
    parser.add_argument("--profile", default=None, help="Hermes profile to relay to; omit for the default/root profile")
    parser.add_argument("--timeout", type=int, default=_DEFAULT_TIMEOUT_SECONDS)
    args = parser.parse_args()
    if not (args.vault_path or "").strip():
        # An empty value would become Path("") -> the CWD, which is exactly the
        # silent-wrong-folder failure this whole change exists to remove.
        raise SystemExit(
            "No vault path. Set SECOND_BRAIN_VAULT_PATH in Hermes' own .env "
            "(Second Brain's setup wizard writes it) or pass --vault-path."
        )

    if args.sample_file:
        with open(args.sample_file, "r", encoding="utf-8") as f:
            sample = json.load(f)
        if not isinstance(sample, list) or not sample:
            print("error: --sample-file must contain a non-empty JSON array", file=sys.stderr)
            return 1
    else:
        sample = _DEFAULT_SEED_SAMPLE

    try:
        artifact = derive(args.vault_path, sample, args.profile, args.timeout)
    except Exception as exc:
        # A failed derivation must degrade explicitly, never silently --
        # and must never overwrite a previously-good, already-persisted
        # artifact (derive() only writes after a successful parse).
        print(f"error: derivation failed, existing artifact (if any) left untouched: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({
        "status": "derived",
        "artifact_path": str(vault_manager.data_root(Path(args.vault_path)) / _ARTIFACT_RELATIVE_PATH),
        "sample_size": artifact["sample_size"],
        "category": artifact["definition"].get("category"),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
