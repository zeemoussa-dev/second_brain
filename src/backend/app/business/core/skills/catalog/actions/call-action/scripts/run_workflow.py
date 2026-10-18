"""run_workflow.py -- start one documented Workflow and step through it.

The second door in the same Skill as `call_action.py`, for the requests
the operator has already decided the handling of. Your own context
carries a `How these requests are handled` block naming the Workflows
you can run and the kind of request each one is for. When a request is
one of them, this script is how you act on it.

**It does not know the steps, and that is the point** (`ADR-034`). It
asks Second Brain to start a run, asks for ONE step, does what that step
says, reports what really happened, and asks for the next -- until the
app says there is no next step. A step the operator must confirm stops
it there, naming the run to come back to with `--resume`: a second
`run_workflow.py <workflow id>` would open a NEW run and perform the
earlier steps all over again. The order, which step needs the
operator's confirmation, which steps are skipped (none) and what is
reported back are all decided by the app against the run record at
`<DATA_PATH>/data/WorkflowRuns/<run_id>.json`. This script could not run
them out of order if it tried: the app hands out one step at a time and
refuses to advance until the current one's outcome is recorded.

**The final report is the app's, relayed, never composed here.** What it
prints at the end is the report the run engine composed from the
recorded step outcomes, verbatim. This script keeps no running tally of
what went well, because a tally is a second copy of the answer and can
disagree with it -- which is exactly how a failed step comes to be
reported as done.

Standalone and stdlib-only beside `call_action.py`, in the same deployed
Skill folder, and it reuses that script for the two things both doors
need: working out which agent this profile is, and really running a
Skill the app AUTHORISED. One copy, so the honest-reporting rules in
`perform_granted_skill()` cannot drift between the two.

Exit codes, so a caller can branch without reading prose:

  0  the run ran every documented step and finished
  1  nothing can be claimed -- the app is unreachable, it answered
     something this script will not interpret, or a step really failed
  2  the run is paused waiting for the operator, or the app refused
     something. This is a first-class answer, not a crash: relay it as
     it is written.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

import call_action

_DEFAULT_BASE_URL = os.environ.get("SECOND_BRAIN_API_URL", "http://127.0.0.1:8001")
_TIMEOUT_SECONDS = 190

# A run cannot loop -- there is no branching and no repetition in a
# Workflow (story Non-Goals) -- so the only way round this loop more
# times than the run has steps is the app and this script disagreeing
# about whether progress is being made. The bound turns that into a
# reported stop rather than a script that spins against the backend
# forever. Generous, because a confirmation re-call legitimately costs a
# step two passes.
_MOST_PASSES_A_RUN_CAN_NEED = 200


def post(base_url: str, path: str, payload: dict) -> tuple[int, dict]:
    """(status, body) for one POST. A 404/409 is the app answering, not
    a crash -- urllib raises on both, so they are caught and returned
    like any other, body and all."""
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            return exc.code, json.loads(raw)
        except ValueError:
            return exc.code, {"detail": raw[:1000]}


def refusal_text(status: int, body: dict) -> str:
    """The app's own sentence, taken out of the envelope it arrived in
    and never reworded. The run routes answer a refusal as
    `{"detail": "<the whole sentence>"}` (`MEMORY.md`, 2026-10-17)."""
    detail = body.get("detail")
    if isinstance(detail, str) and detail:
        return detail
    return f"the app answered HTTP {status} with {json.dumps(body, default=str)[:600]}"


def what_to_do_with(run_id: str, step: dict, call_record: dict | None) -> tuple[str | None, str, int]:
    """(the outcome to report, what to say about it, this runner's exit
    code if it has to stop here).

    The outcome is `None` when this script must NOT report one: the run
    is waiting for the operator, or the app said something this script
    will not interpret. Reporting `done` or `failed` in either case
    would be asserting an outcome nobody observed.

    Branching on the app's own `dispatch_outcome` and never on the
    action id or its inputs, for the same reason `call_action.py`
    branches on `accepted`: the outcome vocabulary grows, and a runner
    that enumerated the ones it knew would read each new one as success.
    """
    status = step.get("status")
    if status == "awaiting_confirmation":
        return None, (
            f"WAITING FOR THE OPERATOR at step {step.get('step_id')!r} (position "
            f"{step.get('position')}), on action call {step.get('awaiting_call_id')!r}. The run "
            "is paused there and NOTHING beyond it has run. Tell the operator what is waiting "
            "and stop. Once they have answered in the app, continue THIS run with "
            f"--resume {run_id} -- starting a fresh run would run the earlier steps a second "
            "time. Do not retry, do not work around it, and do not describe the operation as "
            "done."
        ), 2

    dispatched = step.get("dispatch_outcome")
    detail = step.get("detail") or "(the app said nothing further)"

    if dispatched == "performed":
        return "done", f"the app performed it. {detail}", 0
    if dispatched == "pointed_at":
        # Recorded, not performed -- and reported `done` because the
        # step's handling is complete as far as the framework defines
        # it. The run record keeps `pointed_at` as the dispatch outcome
        # whatever is reported over it, so the operator reading it still
        # sees that they are the one who does this.
        return "done", (
            f"RECORDED, NOT PERFORMED. {detail} Say this plainly to the operator -- claiming "
            "the app did it would be false."
        ), 0
    if dispatched == "authorised":
        grant = (call_record or {}).get("grant") or {}
        code, what_happened = call_action.perform_granted_skill(grant)
        return ("done" if code == 0 else "failed"), f"{detail} {what_happened}", code

    return None, (
        f"the app answered {dispatched!r} for step {step.get('step_id')!r}, which this runner "
        f"does not know how to interpret, so it will not say what happened and reported no "
        f"outcome. The app's own words: {detail}"
    ), 1


def relay_the_apps_report(body: dict) -> int:
    """The end of a run: the app's own composed report, printed as it
    came, plus the app's own one-sentence summary of where the run
    stands. Nothing here is this script's own account of what
    happened."""
    report = body.get("report")
    print(body.get("detail") or "(the app said nothing about where this run stands)")
    print("\nTHE APP'S OWN REPORT, composed from what each step really did:")
    print(json.dumps(report, indent=2, default=str))

    if (report or {}).get("every_documented_step_done"):
        return 0
    if body.get("status") == "awaiting_confirmation":
        return 2
    if any(step.get("status") == "refused" for step in (report or {}).get("steps") or []):
        return 2
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run one documented Second Brain Workflow: the app hands out one step at a time, "
            "in the order the operator documented, and composes the report."
        ),
    )
    parser.add_argument(
        "workflow_id", nargs="?", default=None,
        help="The id of the Workflow, exactly as your context lists it.",
    )
    parser.add_argument(
        "--resume", default=None, metavar="RUN_ID",
        help=(
            "Continue a run that is already open instead of starting one -- the run id a "
            "confirmation pause named. Starting a fresh run would run the earlier steps again."
        ),
    )
    parser.add_argument(
        "--caller", default=None,
        help="This agent's own id (its Hermes profile id). Defaults to the profile this script is deployed in.",
    )
    parser.add_argument("--base-url", default=_DEFAULT_BASE_URL)
    args = parser.parse_args()

    if not (args.workflow_id or args.resume):
        print("Nothing was run: name a workflow id, or --resume the run id of an open run.",
              file=sys.stderr)
        return 1

    caller_agent_id = call_action.caller_agent_id_of_this_profile(args.caller)
    if not caller_agent_id:
        print(
            "No run was started: this script cannot tell which agent it is running as. Pass "
            "--caller <your own agent id> rather than letting it be guessed -- the app believes "
            "the id it is given.",
            file=sys.stderr,
        )
        return 1

    if args.resume:
        # The run already exists and already holds its steps and their
        # outcomes; the app is what remembers where it got to.
        run_id = args.resume
        print(f"Continuing run {run_id} as {caller_agent_id!r}, from wherever the app left it.")
    else:
        try:
            status, body = post(
                args.base_url, f"/workflows/{args.workflow_id}/run",
                {"caller_agent_id": caller_agent_id},
            )
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            print(
                f"NO RUN WAS STARTED: Second Brain could not be reached at {args.base_url} "
                f"({exc}). Tell the operator the app is not running -- do not handle the request "
                "yourself and do not describe any of it as done.",
                file=sys.stderr,
            )
            return 1
        except ValueError as exc:
            print(f"NO RUN WAS STARTED: Second Brain answered something that is not JSON ({exc}).",
                  file=sys.stderr)
            return 1

        if status != 200 or not body.get("run_id"):
            print(
                f"NO RUN WAS STARTED ({status}). NOTHING WAS PERFORMED.\n"
                f"{refusal_text(status, body)}\n"
                "Relay this to the operator as it is written. Do not handle the request step by "
                "step yourself instead.",
                file=sys.stderr,
            )
            return 2 if status in (404, 409) else 1

        run_id = body["run_id"]
        print(
            f"Started run {run_id} of workflow {args.workflow_id!r} as {caller_agent_id!r}. The "
            f"app holds {len(body.get('steps') or [])} documented steps and hands them out one "
            "at a time."
        )

    for _ in range(_MOST_PASSES_A_RUN_CAN_NEED):
        try:
            status, body = post(args.base_url, f"/workflows/runs/{run_id}/next-step", {})
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            print(
                f"RUN {run_id} IS UNFINISHED: Second Brain stopped answering ({exc}). Some steps "
                "may have run and some did not -- the run record is the only honest account. Do "
                "not describe the request as handled.",
                file=sys.stderr,
            )
            return 1
        if status != 200:
            print(f"RUN {run_id} STOPPED ({status}).\n{refusal_text(status, body)}", file=sys.stderr)
            return 2 if status in (404, 409) else 1

        step = body.get("step")
        if step is None:
            code = relay_the_apps_report(body)
            return code

        print(f"\nStep {step.get('position')} ({step.get('step_id')}): action {step.get('action_id')!r}.")
        outcome, what_happened, code = what_to_do_with(run_id, step, body.get("call"))
        if outcome is None:
            print(what_happened, file=sys.stderr if code else sys.stdout)
            return code
        print(what_happened)

        try:
            status, body = post(
                args.base_url, f"/workflows/runs/{run_id}/steps/{step['step_id']}/outcome",
                {"outcome": outcome, "detail": what_happened},
            )
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            print(
                f"RUN {run_id} IS UNFINISHED: step {step.get('step_id')!r} really ran, and its "
                f"outcome could not be recorded because Second Brain stopped answering ({exc}). "
                "The run is stuck on that step until it is.",
                file=sys.stderr,
            )
            return 1
        if status != 200:
            print(
                f"RUN {run_id} STOPPED: the app would not record step {step.get('step_id')!r}'s "
                f"outcome ({status}).\n{refusal_text(status, body)}",
                file=sys.stderr,
            )
            return 2 if status in (404, 409) else 1

    print(
        f"RUN {run_id} WAS ABANDONED after {_MOST_PASSES_A_RUN_CAN_NEED} passes without reaching "
        "the end. The run record is still open and is the only honest account of what ran. Tell "
        "the operator; do not describe the request as handled.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
