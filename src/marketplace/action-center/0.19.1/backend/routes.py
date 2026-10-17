"""The Action Center's HTTP surface. The host mounts it under `/plugins/action-center/`."""
from __future__ import annotations

from fastapi import APIRouter, Body, HTTPException, Query

from . import chase_rules, chasing, recipients
from .action_view import GROUPABLE, ActionView
from .task_writer import TaskError, TaskNotFound, TaskWriter


def _written(call):
    """A write the operator can fix is a 400 with the reason; a missing action a 404."""
    try:
        return call()
    except TaskNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TaskError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def build_router(view: ActionView, writer: TaskWriter) -> APIRouter:
    router = APIRouter()

    def filters(status: str | None, owner: str | None, customer: str | None,
                source: str | None, priority: str | None, overdue: bool,
                due_before: str | None, due_after: str | None, q: str | None,
                scope: str | None = None, unaddressed: bool = False,
                no_source: bool = False, not_a_person: bool = False,
                entity: str | None = None, entity_tag: str | None = None) -> dict:
        return {"status": status, "owner": owner, "customer": customer, "source": source,
                "priority": priority, "overdue": overdue, "due_before": due_before,
                "due_after": due_after, "q": q, "scope": scope, "unaddressed": unaddressed,
                "no_source": no_source, "not_a_person": not_a_person,
                "entity": entity, "entity_tag": entity_tag}

    @router.get("/summary")
    def get_summary() -> dict:
        return view.summary()

    @router.get("/facets")
    def get_facets(status: str = Query("Open")) -> dict:
        """The filter choices for the status being looked at: the Completed
        screen filters by the same things, over its own actions."""
        return view.facets(status)

    @router.get("/actions")
    def get_actions(status: str | None = None, owner: str | None = None,
                    customer: str | None = None, source: str | None = None,
                    priority: str | None = None, overdue: bool = False,
                    due_before: str | None = None, due_after: str | None = None,
                    q: str | None = None, scope: str | None = None,
                    unaddressed: bool = False, no_source: bool = False,
                    not_a_person: bool = False, entity: str | None = None,
                    entity_tag: str | None = None) -> list[dict]:
        return view.list_actions(**filters(status, owner, customer, source, priority,
                                           overdue, due_before, due_after, q, scope,
                                           unaddressed, no_source, not_a_person,
                                           entity, entity_tag))

    @router.get("/grouped")
    def get_grouped(group_by: str = Query("owner"), status: str | None = None,
                    owner: str | None = None, customer: str | None = None,
                    source: str | None = None, priority: str | None = None,
                    overdue: bool = False, due_before: str | None = None,
                    due_after: str | None = None, q: str | None = None,
                    scope: str | None = None, unaddressed: bool = False,
                    no_source: bool = False, not_a_person: bool = False,
                    entity: str | None = None, entity_tag: str | None = None) -> list[dict]:
        if group_by not in GROUPABLE:
            raise HTTPException(status_code=400,
                                detail=f"group_by must be one of {sorted(GROUPABLE)}")
        return view.grouped(group_by, **filters(status, owner, customer, source, priority,
                                                overdue, due_before, due_after, q, scope,
                                                unaddressed, no_source, not_a_person,
                                                entity, entity_tag))

    @router.get("/actions/{stem}")
    def get_action(stem: str) -> dict:
        found = view.detail(stem)
        if found is None:
            raise HTTPException(status_code=404, detail=f"no action named {stem!r}")
        return found

    @router.post("/actions")
    def create_action(fields: dict = Body(...)) -> dict:
        return _written(lambda: writer.create(fields))

    @router.patch("/actions/{stem}")
    def update_action(stem: str, fields: dict = Body(...)) -> dict:
        return _written(lambda: writer.update(stem, fields))

    @router.post("/actions/{stem}/complete")
    def complete_action(stem: str, payload: dict = Body(...)) -> dict:
        return _written(lambda: writer.complete(
            stem, payload.get("evidence", ""), status=payload.get("status") or "Completed",
            evidence_source=payload.get("evidence_source", ""),
            condition_met=bool(payload.get("condition_met"))))

    @router.post("/actions/{stem}/reopen")
    def reopen_action(stem: str, payload: dict = Body(...)) -> dict:
        return _written(lambda: writer.reopen(
            stem, payload.get("reason", ""), keep_open_until=payload.get("keep_open_until", "")))

    @router.post("/actions/{stem}/notes")
    def add_note(stem: str, payload: dict = Body(...)) -> dict:
        return _written(lambda: writer.add_note(stem, payload.get("text", "")))

    @router.get("/chase-rules")
    def get_chase_rules() -> dict:
        """What the chasing agent may do without being asked. One rule so far."""
        return chase_rules.read(view)

    @router.put("/chase-rules")
    def set_chase_rules(payload: dict = Body(...)) -> dict:
        return chase_rules.save(view, bool(payload.get("internal_only", True)))

    @router.get("/actions/{stem}/recipients")
    def chase_recipients(stem: str) -> dict:
        """Who a chase about this action would go to, before he presses Chase.

        An ask owed by two people is one email to both (operator, 2026-09-26),
        and he may know that one of them has already done their half -- so the
        screen shows the list, everyone with an address ticked."""
        action = view.detail(stem)
        if action is None:
            raise HTTPException(status_code=404, detail=f"no action named {stem!r}")
        # Across the whole ask: the same thing given to four people is four
        # actions and one email (operator, 2026-09-26).
        people, stems = recipients.across_the_ask(view, action)
        # Ticked as he last left it, where he has settled this action; otherwise
        # everyone with an address -- and never somebody the standing rule says
        # the agent may not write to.
        settled = recipients.settled_on(action)
        rule = chase_rules.read(view)
        rows = []
        for person in people:
            outside = bool(person["email"]) and rule["internal_only"] and not chase_rules.is_internal(
                person["email"], rule["domains"])
            rows.append({
                **person,
                "external": outside,
                "selected": (not outside) and (person["email"] in settled if settled
                                               else bool(person["email"])),
            })
        return {"stem": stem, "owner": action["owner"], "settled": settled,
                "internal_only": rule["internal_only"], "recipients": rows,
                # Every action this one email covers, so the screen can say so.
                "stems": stems, "shared_with": len(stems) - 1}

    @router.post("/actions/{stem}/chase")
    def chase_owner(stem: str, payload: dict = Body(default={})) -> dict:
        """Chase about THIS action -- one action, one email, to everyone on it.

        `to` is who he left ticked; without it, everyone the action names."""
        action = view.detail(stem)
        if action is None:
            raise HTTPException(status_code=404, detail=f"no action named {stem!r}")
        if action["scope"] == "mine":
            raise HTTPException(status_code=400, detail="this is the CBO's own action")
        people, stems = recipients.across_the_ask(view, action)
        known = {address.lower() for address in recipients.addressable(people)}
        if not known:
            raise HTTPException(status_code=400,
                                detail=f"{action['owner'] or 'nobody'} has no address to write to")
        asked_for = [str(a).strip().lower() for a in (payload or {}).get("to") or []]
        outside = chase_rules.allowed(view, asked_for or sorted(known))[1]
        if outside:
            raise HTTPException(
                status_code=400,
                detail=(f"{', '.join(outside)} is outside the company, and chases are set to "
                        "internal people only. Turn that off in the Action Center first."))
        strangers = [address for address in asked_for if address not in known]
        if strangers:
            # A chase goes to the people who owe the thing, never to an address
            # the screen was talked into sending.
            raise HTTPException(
                status_code=400,
                detail=f"{', '.join(strangers)} does not owe {stem!r}")
        chosen = asked_for or sorted(known)

        def ask() -> dict:
            # Written on the action first: the tray is consumed by the job, so
            # this is the only copy that outlives the press -- and the one an
            # unattended chase would read. Every action of a shared ask is
            # queued, and the job collapses them back into one email.
            for one in stems:
                writer.set_chase_to(one, chosen if asked_for else [])
            return chasing.request(view.api, stems, {one: chosen for one in stems})

        return _written(ask)

    @router.post("/chase")
    def chase_many(payload: dict = Body(...)) -> dict:
        """Queue every named action for chasing -- one email each, still.

        The screen sends the stems it is showing, so "this person" and
        "everyone" are the same call with a different list, and what is chased
        is exactly what he was looking at. In bulk nobody is picked off by hand:
        each action goes to everyone who owes it."""
        wanted = [str(s) for s in (payload.get("stems") or []) if str(s).strip()]
        if not wanted:
            raise HTTPException(status_code=400, detail="no actions to chase")
        queued, skipped = [], []
        for stem in wanted:
            action = view.detail(stem)
            if action is None:
                skipped.append({"stem": stem, "why": "no such action"})
            elif action["status"] != "Open":
                skipped.append({"stem": stem, "why": f"is {action['status']}"})
            elif action["scope"] == "mine":
                skipped.append({"stem": stem, "why": "the CBO's own"})
            elif not recipients.addressable(recipients.for_action(view, action)):
                skipped.append({"stem": stem, "why": "no address"})
            elif not chase_rules.allowed(
                    view, recipients.addressable(recipients.for_action(view, action)))[0]:
                skipped.append({"stem": stem, "why": "outside the company"})
            else:
                queued.append(stem)
        if not queued:
            raise HTTPException(status_code=400,
                                detail=f"none of those can be chased: {skipped[0]['why']}")
        asked = _written(lambda: chasing.request(view.api, queued))
        return {**asked, "skipped": skipped}

    @router.get("/doubts")
    def get_doubts() -> dict:
        return view.doubts()

    @router.post("/owners")
    def set_owner(payload: dict = Body(...)) -> dict:
        return _written(lambda: writer.set_owner(
            payload.get("owner", ""), name=payload.get("name", ""),
            email=payload.get("email", ""),
            clear_address=bool(payload.get("clear_address"))))

    @router.get("/owners")
    def get_owners() -> list[dict]:
        return [{"owner": g["key"], "open": g["count"], "overdue": g["overdue"]}
                for g in view.grouped("owner", status="Open")]

    return router
