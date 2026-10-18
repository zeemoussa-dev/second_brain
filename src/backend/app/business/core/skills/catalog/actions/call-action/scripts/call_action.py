"""call_action.py -- the agent's ONE door onto what Second Brain can do.

Posts an Action call to Second Brain's own backend over loopback and
reports what really happened, in the app's own words. The app validates
every call against its live catalogue (`ADR-032`, `ADR-033`): an unknown
action id, a missing required input, a caller not permitted and a
confirmation not yet given are all refused BY THE FRAMEWORK, and this
script relays that refusal verbatim.

Standalone and stdlib-only, the same deployment model as
search_vault.py/vault_manager.py: physically copied into whichever
Hermes profile needs it, no Second Brain package import. Like
search_vault.py -- and unlike vault_manager.py -- it deliberately DOES
need the backend running: the catalogue, the gate and the Action-call
ledger all live there, which is the whole point of calling it rather
than acting directly.

**It never invents an outcome.** Every sentence it prints about what
happened comes from the app's own verdict or from the real exit status
of a Skill it was granted. There is no fallback path: no substituted
action, no search instead, no "I will do it later". A backend that
cannot be reached is a connection failure on stderr and a non-zero exit
-- never a claimed success.

Exit codes, so a caller can branch without reading prose:

  0  the call passed the gate and what happened is reported truthfully
  1  nothing happened and something is wrong -- the app is unreachable,
     it answered something this script will not interpret, or a granted
     Skill really ran and really failed
  2  the app REFUSED the call, or is waiting for the operator to confirm
     it. Nothing was performed. This is a first-class answer, not a
     crash: relay it to the operator as it is written.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

# Second Brain's own backend, same default port the app and its launcher
# use. Overridable for an install that moved it.
_DEFAULT_BASE_URL = os.environ.get("SECOND_BRAIN_API_URL", "http://127.0.0.1:8001")
_TIMEOUT_SECONDS = 190
# Longer than the app's own 180s http-dispatch timeout, so a slow Action
# is reported by the app rather than guessed at from this side.

# How a granted Skill receives its validated inputs: the same JSON on
# stdin and in this variable. Two ways because a Skill script may be
# written either way, and neither can be mistaken for a command-line
# flag whose name this script would have had to invent.
_GRANTED_INPUTS_ENV = "SECOND_BRAIN_ACTION_INPUTS"
_GRANTED_CALL_ID_ENV = "SECOND_BRAIN_ACTION_CALL_ID"
_GRANTED_SKILL_TIMEOUT_SECONDS = 900


def caller_agent_id_of_this_profile(explicit: str | None) -> str | None:
    """Which agent this call is made as -- the Hermes profile id, which
    IS the agent id everywhere in this codebase (`ADR-033`).

    An explicit `--caller` wins, then `HERMES_PROFILE_ID`, then the
    profile this very script was deployed into, read off its own path:
    `<home>/profiles/<profile-id>/skills/<tool>/<slug>/call_action.py`,
    or `<home>/skills/...` for the `default` profile.

    None when it cannot be told, and the caller must then refuse to
    call: the app believes the id it is given, so a guessed one would
    record a call nobody made.
    """
    if explicit:
        return explicit
    from_environment = os.environ.get("HERMES_PROFILE_ID", "").strip()
    if from_environment:
        return from_environment
    here = Path(__file__).resolve()
    if len(here.parents) < 5:
        return None
    skills_dir = here.parents[2]
    if skills_dir.name != "skills":
        return None
    profile_dir = here.parents[3]
    if profile_dir.parent.name == "profiles":
        return profile_dir.name
    # Hermes' own home IS the `default` profile's directory -- there is
    # no `profiles/default/`.
    return "default"


def post_call(base_url: str, action_id: str, payload: dict) -> tuple[int, dict]:
    """(status, body) for one POST to the call route. A 409 is the gate
    refusing, which is an ANSWER -- urllib raises on it, so it is caught
    and returned like any other, body and all."""
    url = f"{base_url.rstrip('/')}/actions/{action_id}/call"
    request = urllib.request.Request(
        url,
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


def verdict_of(status: int, body: dict) -> dict:
    """The app answers a refusal as `{"detail": <the whole verdict>}` and
    an accepted call as the verdict itself. One shape from here on."""
    if status == 409 and isinstance(body.get("detail"), dict):
        return body["detail"]
    return body


def granted_skill_directory(skill_id: str) -> Path | None:
    """Where that Skill is deployed in THIS profile, found from this
    script's own location -- `<profile>/skills/<tool>/<slug>/`. The tool
    folder is globbed because a slug is globally unique and may sit
    under a different tool than this runner does."""
    here = Path(__file__).resolve()
    if len(here.parents) < 3:
        return None
    skills_dir = here.parents[2]
    if skills_dir.name != "skills":
        return None
    for candidate in sorted(skills_dir.glob(f"*/{skill_id}")):
        if (candidate / "SKILL.md").is_file():
            return candidate
    return None


def entry_script_of(skill_dir: Path) -> Path | None:
    """The one script that Skill is run by.

    Its own SKILL.md is asked first -- the documented command is what an
    agent would run by hand, and `test_skill_command_paths.py` already
    pins that command against what the deploy really writes. A Skill
    carrying exactly one script needs no documentation to be
    unambiguous. Anything else returns None rather than picking one: a
    guessed entry point is the silent fallback this whole path exists to
    avoid.
    """
    skill_md = skill_dir / "SKILL.md"
    if skill_md.is_file():
        text = skill_md.read_text(encoding="utf-8", errors="replace")
        for token in text.replace("\\", "/").split():
            name = token.strip("\"'`(),")
            if name.endswith(".py"):
                script = skill_dir / Path(name).name
                if script.is_file():
                    return script
    scripts = sorted(p for p in skill_dir.glob("*.py") if p.is_file())
    return scripts[0] if len(scripts) == 1 else None


def perform_granted_skill(grant: dict) -> tuple[int, str]:
    """Run the Skill the app AUTHORISED, here, in this profile -- the app
    never performs one itself (`ADR-019`, `ADR-033`).

    Returns (exit code for this runner, what to tell the operator). The
    Skill's own stdout and stderr are relayed verbatim and a non-zero
    exit is reported as a failure: this function has no idea what the
    Skill was supposed to produce, so the only honest report is the real
    one.
    """
    skill_id = str(grant.get("skill_id") or "")
    inputs = grant.get("inputs") or {}
    skill_dir = granted_skill_directory(skill_id)
    if skill_dir is None:
        return 1, (
            f"the app authorised skill {skill_id!r} for this call, but it is not deployed in "
            "this profile, so NOTHING WAS PERFORMED. Tell the operator the grant could not be "
            "used; do not describe the operation as done."
        )
    script = entry_script_of(skill_dir)
    if script is None:
        return 1, (
            f"the app authorised skill {skill_id!r} and it is deployed at {str(skill_dir)!r}, "
            "but which script runs it could not be determined without guessing, so NOTHING WAS "
            "PERFORMED. Tell the operator; do not describe the operation as done."
        )

    payload = json.dumps(inputs)
    environment = {
        **os.environ,
        _GRANTED_INPUTS_ENV: payload,
        _GRANTED_CALL_ID_ENV: str(grant.get("call_id") or ""),
    }
    try:
        completed = subprocess.run(
            [sys.executable, str(script)],
            cwd=str(skill_dir), input=payload, env=environment,
            capture_output=True, text=True, timeout=_GRANTED_SKILL_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return 1, (
            f"the granted skill {skill_id!r} could not be run ({exc}), so NOTHING WAS PERFORMED."
        )

    output = "\n".join(part for part in (completed.stdout.strip(), completed.stderr.strip()) if part)
    if completed.returncode != 0:
        return 1, (
            f"the granted skill {skill_id!r} RAN AND FAILED (exit {completed.returncode}). "
            f"Report this failure, not a success. What it said:\n{output}"
        )
    return 0, (
        f"the granted skill {skill_id!r} ran in this profile and finished successfully. "
        f"What it said:\n{output}"
    )


def report(verdict: dict) -> tuple[int, str]:
    """What to print, and this runner's exit code -- derived from the
    app's own verdict and never from an assumption about it.

    `accepted` is the one field branched on, deliberately: the outcome
    vocabulary grows, and a runner that enumerated outcomes to decide
    whether it was refused would read each new one as success.
    """
    call_id = verdict.get("call_id") or "(no call id)"
    outcome = verdict.get("outcome") or "(no outcome)"
    refusal = verdict.get("refusal") or ""
    detail = verdict.get("detail") or ""

    if not verdict.get("accepted"):
        if outcome == "awaiting_confirmation":
            return 2, (
                f"WAITING FOR THE OPERATOR ({outcome}, call {call_id}). NOTHING WAS PERFORMED.\n"
                f"{refusal}\n"
                "Tell the operator what is waiting and stop here. Do not retry, do not work "
                "around it, and do not describe the operation as done."
            )
        return 2, (
            f"REFUSED BY THE APP ({outcome}, call {call_id}). NOTHING WAS PERFORMED.\n"
            f"{refusal}\n"
            "Relay this to the operator as it is written. Do not substitute another action, "
            "do not do it another way, and do not describe an outcome that did not happen."
        )

    if outcome == "performed":
        result = verdict.get("result")
        rendered = json.dumps(result, indent=2, default=str) if result is not None else "(no result body)"
        return 0, f"PERFORMED (call {call_id}).\n{detail}\nWhat the app returned:\n{rendered}"

    if outcome == "pointed_at":
        where = verdict.get("where_the_operator_does_it") or "(the app did not say where)"
        return 0, (
            f"RECORDED, NOT PERFORMED (call {call_id}).\n{detail}\n"
            f"The operator does this themselves at {where}. Say so plainly; claiming it was "
            "done would be false."
        )

    if outcome == "authorised":
        grant = verdict.get("grant") or {}
        code, what_happened = perform_granted_skill(grant)
        return code, f"AUTHORISED (call {call_id}).\n{detail}\n{what_happened}"

    if outcome == "failed":
        return 1, (
            f"THE APP TRIED AND FAILED (call {call_id}). The operation did NOT happen.\n{detail}\n"
            "Report the failure to the operator exactly as written."
        )

    return 1, (
        f"the app answered {outcome!r} for call {call_id}, which this runner does not know how "
        f"to interpret, so it will not say what happened. The app's own words:\n{detail or refusal}"
    )


def parse_inputs(pairs: list[str], inputs_json: str | None) -> dict:
    """`--input name=value` pairs stay strings; `--inputs-json` carries
    real types. Nothing is coerced between the two: a `"true"` the agent
    typed is not silently turned into a boolean, because the gate
    validates what it is sent and the operator sees what was recorded."""
    inputs: dict = {}
    if inputs_json:
        parsed = json.loads(inputs_json)
        if not isinstance(parsed, dict):
            raise ValueError("--inputs-json must be a JSON object of input names to values")
        inputs.update(parsed)
    for pair in pairs or []:
        name, separator, value = pair.partition("=")
        if not separator:
            raise ValueError(f"--input expects name=value, got {pair!r}")
        inputs[name.strip()] = value
    return inputs


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Call one catalogued Second Brain Action and report what really happened.",
    )
    parser.add_argument("action_id", help="The id of the Action, exactly as the catalogue lists it.")
    parser.add_argument(
        "--input", action="append", default=[], metavar="NAME=VALUE",
        help="One input, repeatable. Values are sent as strings.",
    )
    parser.add_argument(
        "--inputs-json", default=None,
        help="All inputs as one JSON object, for inputs that are not strings.",
    )
    parser.add_argument(
        "--caller", default=None,
        help="This agent's own id (its Hermes profile id). Defaults to the profile this script is deployed in.",
    )
    parser.add_argument(
        "--confirmed-call-id", default=None,
        help="The call_id the operator confirmed, when re-calling an action that needs confirmation.",
    )
    parser.add_argument("--base-url", default=_DEFAULT_BASE_URL)
    args = parser.parse_args()

    try:
        inputs = parse_inputs(args.input, args.inputs_json)
    except ValueError as exc:
        print(f"Nothing was called: {exc}", file=sys.stderr)
        return 1

    caller_agent_id = caller_agent_id_of_this_profile(args.caller)
    if not caller_agent_id:
        print(
            "Nothing was called: this script cannot tell which agent it is running as. Pass "
            "--caller <your own agent id> rather than letting it be guessed -- the app believes "
            "the id it is given.",
            file=sys.stderr,
        )
        return 1

    payload = {
        "caller_agent_id": caller_agent_id,
        "inputs": inputs,
        "confirmed_call_id": args.confirmed_call_id,
    }
    try:
        status, body = post_call(args.base_url, args.action_id, payload)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        print(
            f"NOTHING WAS PERFORMED: Second Brain could not be reached at {args.base_url} "
            f"({exc}). Tell the operator the app is not running -- do not report the action as "
            "done and do not attempt it another way.",
            file=sys.stderr,
        )
        return 1
    except ValueError as exc:
        print(
            f"NOTHING WAS PERFORMED: Second Brain answered something that is not JSON ({exc}).",
            file=sys.stderr,
        )
        return 1

    verdict = verdict_of(status, body)
    if not isinstance(verdict, dict) or "accepted" not in verdict:
        print(
            f"NOTHING CAN BE CLAIMED: Second Brain answered HTTP {status} with a body this "
            f"runner does not recognise as a verdict: {json.dumps(body, default=str)[:600]}",
            file=sys.stderr,
        )
        return 1

    code, message = report(verdict)
    print(message, file=sys.stderr if code else sys.stdout)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
