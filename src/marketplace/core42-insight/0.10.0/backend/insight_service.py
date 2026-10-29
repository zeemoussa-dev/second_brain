"""Answering for one customer and across customers, from the terms on the notes
and Cost Manager's consumption.

A customer is named by its key: its Customer note's stem, or `cm:<id>` for a
Cost Manager customer without a note. Only a customer with a note can hold its
own terms; an affiliate without its own follows its parent's percentage
(operator, 2026-10-18: "Both" -- the parent's terms cover the affiliates unless
an affiliate has its own). A fixed fee is the parent's alone, billed once.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Callable
from urllib.parse import urlencode

from . import months, revenue, terms, terms_transfer
from .sources import Sources

REPORT_PATH = "/core42-insight/report"
_NO_TERMS = {"terms": [], "note": "", "error": None, "unreadable": False}


class CustomerNotFound(LookupError):
    pass


class InsightService:
    def __init__(self, sources: Sources, today: Callable[[], date] = date.today) -> None:
        self._sources = sources
        self._today = today

    def _current_month(self) -> str:
        return months.month_of(self._today())

    def _stored(self, stem: str | None) -> dict:
        """The note's terms, read leniently: a note edited by hand in Obsidian that
        no longer validates shows its error instead of failing the whole page."""
        if not stem:
            return dict(_NO_TERMS)
        try:
            raw = self._sources.insight(stem) or {}
        except ValueError as exc:
            # Entities raises its own error types, which this plugin may not import.
            if type(exc).__name__ == "OpportunityNotFound":
                return dict(_NO_TERMS)
            # Otherwise it refuses an Insight note whose data block was broken by hand.
            return {"terms": [], "note": "", "error": str(exc), "unreadable": True}
        try:
            lines, error = terms.validated(raw.get("terms")), None
        except terms.TermsError as exc:
            lines, error = [], str(exc)
        return {"terms": lines, "note": raw.get("note") or "", "error": error, "unreadable": False}

    def _everyone(self) -> list[dict]:
        return self._sources.customers()

    @staticmethod
    def _find(everyone: list[dict], key: str) -> dict:
        for customer in everyone:
            if customer["key"] == key:
                return customer
        raise CustomerNotFound(f"no Cost Manager customer is known as {key!r}")

    def _effective(self, customer: dict, everyone: list[dict]) -> dict:
        """The lines a customer is charged on: its own, or -- when it has none --
        the percentage lines of the nearest ancestor with terms (affiliates nest
        at any depth), marked as inherited."""
        stored = self._stored(customer["stem"])
        if stored["terms"] or stored["error"]:
            return {**stored, "lines": stored["terms"], "inherited_from": None}
        by_key = {row["key"]: row for row in everyone}
        seen = {customer["key"]}
        ancestor = by_key.get(customer.get("parent_key"))
        while ancestor is not None and ancestor["key"] not in seen:
            seen.add(ancestor["key"])
            own = self._stored(ancestor["stem"])["terms"]
            if own:
                inherited = [line for line in own if line["model"] == terms.PERCENTAGE]
                return {**stored, "lines": inherited, "inherited_from": ancestor["name"] if inherited else None}
            ancestor = by_key.get(ancestor.get("parent_key"))
        return {**stored, "lines": [], "inherited_from": None}

    def customer_list(self) -> list[dict]:
        """The customer screen's skeleton, fast: who is listed and how they nest --
        from Cost Manager's (kept) customer list alone, no note read and no
        consumption. Each row's figures come from `customer_row`, so the screen
        shows at once and fills in (operator, 2026-10-18: "Use Lazy Loading")."""
        everyone = self._everyone()
        keys = {customer["key"] for customer in everyone}
        out = []
        for customer in everyone:
            parent = customer.get("parent_key")
            out.append({"stem": customer["key"], "name": customer["name"], "has_note": bool(customer["stem"]),
                        "parent": parent if parent in keys else None,
                        "affiliates": [row["key"] for row in everyone
                                       if row.get("parent_key") == customer["key"] and row["key"] != customer["key"]]})
        names = {row["stem"]: row["name"].lower() for row in out}
        return sorted(out, key=lambda row: (names.get(row["parent"] or row["stem"], ""), row["parent"] is not None,
                                            row["name"].lower()))

    def customer_row(self, key: str) -> dict:
        """One customer's row: the agreement, the terms today, and -- for a customer
        charged anything -- last month's Insight revenue, the trend, the year so far
        and the forecast to year end."""
        current = self._current_month()
        everyone = self._everyone()
        customer = self._find(everyone, key)
        effective = self._effective(customer, everyone)
        line = terms.in_force(effective["lines"], current)
        # Cost Manager is asked only for a customer charged on something: seconds per answer.
        member = self._member(customer, everyone, current, effective) if effective["lines"] else None
        agreement = member["agreement"] if member else (
            self._sources.agreement(customer["stem"], ask_cost_manager=False) if customer["stem"] else None)
        # An affiliate that signs no agreement of its own, under a parent whose
        # affiliates roll up (DGE's, operator 2026-10-21), is covered by the parent's.
        covered_by = None
        parent = next((row for row in everyone if row["key"] == customer.get("parent_key")), None)
        if not agreement and parent and parent.get("affiliates") != "own" and parent.get("stem") \
                and self._sources.agreement(parent["stem"], ask_cost_manager=False):
            covered_by = parent["name"]
        closed = [row for row in (member["rows"] if member else []) if row["kind"] == revenue.ACTUAL
                  and row["month"] < current]
        recent = [{"month": row["month"], "revenue": row["revenue"]} for row in closed[-6:]]
        previous = closed[-2]["revenue"] if len(closed) >= 2 else None
        last = closed[-1]["revenue"] if closed else None
        return {
            "stem": key, "name": customer["name"], "has_note": bool(customer["stem"]),
            "currency": customer.get("currency"),
            "has_terms": bool(effective["terms"]), "terms_error": effective["error"],
            "inherited_from": effective["inherited_from"],
            "in_force": terms.describe(line) if line else None,
            "model": line["model"] if line else None,
            "agreement": agreement,
            "agreement_from": covered_by,
            "summary": member["summary"] if member else None,
            "recent": recent,
            "mom_pct": round((last - previous) / previous * 100, 1) if previous else None,
            "status": self._status(effective, line),
        }

    def customers(self) -> list[dict]:
        """The whole customer screen in one answer -- the list with every row
        filled. Slow with many customers; the screen itself loads lazily."""
        return [{**listed, **self.customer_row(listed["stem"])} for listed in self.customer_list()]

    @staticmethod
    def _status(effective: dict, line: dict | None) -> str:
        if effective["error"]:
            return "unreadable"
        if effective["inherited_from"]:
            return "inherited" if line else "ended"
        if line:
            return "active"
        return "ended" if effective["terms"] else "no-terms"

    def terms(self, key: str) -> dict:
        everyone = self._everyone()
        customer = self._find(everyone, key)
        effective = self._effective(customer, everyone)
        agreement = self._sources.agreement(customer["stem"]) if customer["stem"] else None
        stored = {name: effective[name] for name in ("terms", "note", "error", "unreadable")}
        return {"stem": key, "name": customer["name"], "currency": customer.get("currency"),
                "has_note": bool(customer["stem"]), **stored, "agreement": agreement,
                "inherited_from": effective["inherited_from"],
                "inherited": effective["lines"] if effective["inherited_from"] else [],
                "outside_agreement": [reason for line in stored["terms"]
                                      if (reason := terms.outside_agreement(line, agreement))],
                "models": [{"id": model, "label": terms.MODEL_LABELS[model]} for model in terms.MODELS]}

    def save_terms(self, key: str, submitted: dict) -> dict:
        customer = self._find(self._everyone(), key)
        if not customer["stem"]:
            raise ValueError(f"{customer['name']} has no Customer note, so it cannot hold its own Insight terms -- "
                             "create its note in Customers & Partners and link it in Azure Cost Manager; until "
                             "then it follows its parent's percentage")
        stored = self._stored(customer["stem"])
        if stored["unreadable"]:
            raise ValueError(f"the Insight note does not read, so saving would overwrite it -- fix it in Obsidian "
                             f"first: {stored['error']}")
        lines = terms.validated(submitted.get("terms"))
        note = str(submitted.get("note") or "").strip()
        value = {"terms": lines, "note": note} if (lines or note) else None
        self._sources.set_insight(customer["stem"], value)
        return self.terms(key)

    def _member(self, customer: dict, everyone: list[dict], current: str, effective: dict | None = None) -> dict:
        effective = effective or self._effective(customer, everyone)
        lines = effective["lines"]
        # A customer without terms earns nothing, and Cost Manager takes seconds per answer.
        consumption = {key: self._sources.monthly_for(customer, *key) for key in revenue.measures_needed(lines)} \
            if lines else {}
        default = consumption.get((True, True)) or {}
        last = revenue.horizon(current, default.get("commitment"))
        rows = revenue.monthly(lines, consumption, current, last)
        own_lines = [] if effective["inherited_from"] else lines
        agreement = self._sources.agreement(customer["stem"]) if own_lines and customer["stem"] else None
        warnings = [f"{customer['name']}: {reason}" for line in own_lines
                    if (reason := terms.outside_agreement(line, agreement))]
        if effective["error"]:
            warnings.append(f"{customer['name']}: the terms on its note do not read: {effective['error']}")
        currency = default.get("currency") or customer.get("currency")
        if lines and currency and currency != "USD":
            warnings.append(f"{customer['name']}: Cost Manager reports {currency}, Insight counts USD -- "
                            "the percentage is applied to the figures as they are, not converted")
        if any(row["missing_consumption"] for row in rows):
            warnings.append(f"{customer['name']}: some closed months have no synced consumption in Cost Manager")
        return {"stem": customer["key"], "name": customer["name"], "currency": currency, "terms": lines,
                "inherited_from": effective["inherited_from"], "has_note": bool(customer["stem"]),
                "agreement": agreement, "rows": rows, "warnings": warnings,
                "cost_route": default.get("route") or customer.get("route"),
                "summary": revenue.summary(rows, current)}

    def report(self, key: str) -> dict:
        """One customer, its affiliates rolled up under it: each member's monthly
        revenue, and the group's. A parent whose affiliates each signed their own
        MACC (as Mubadala) is reported alone; its affiliates have their own reports
        (operator, 2026-10-18)."""
        current = self._current_month()
        everyone = self._everyone()
        customer = self._find(everyone, key)
        separate = customer.get("affiliates") == "own"
        affiliates, frontier = [], [] if separate else [key]
        while frontier:  # affiliates nest at any depth; the group rolls them all up
            children = [row for row in everyone if row.get("parent_key") in frontier
                        and row["key"] != key and row not in affiliates]
            affiliates.extend(children)
            frontier = [row["key"] for row in children]
        members = [self._member(row, everyone, current) for row in [customer, *affiliates]]
        rows = revenue.cumulative(revenue.combined([member["rows"] for member in members]))
        own = members[0]
        reported_alone = [{"stem": row["key"], "name": row["name"]} for row in everyone
                          if separate and row.get("parent_key") == key]
        return {"stem": key, "name": customer["name"], "currency": "USD", "current_month": current,
                "parent": customer.get("parent_key"), "members": members, "rows": rows,
                "affiliates_reported_alone": reported_alone,
                "summary": revenue.summary(rows, current),
                "warnings": [warning for member in members for warning in member["warnings"]],
                "cost_route": own["cost_route"]}

    def portfolio(self) -> dict:
        """Every customer charged anything, its own figures (an affiliate is not
        counted twice -- a parent's row is its own, the group rolls up on its report)."""
        current = self._current_month()
        everyone = self._everyone()
        keys = {row["key"] for row in everyone}
        rows, warnings = [], []
        for customer in everyone:
            effective = self._effective(customer, everyone)
            if not effective["lines"]:
                continue
            member = self._member(customer, everyone, current, effective)
            line = terms.in_force(member["terms"], current)
            parent = customer.get("parent_key")
            rows.append({"stem": member["stem"], "name": member["name"],
                         "parent": parent if parent in keys else None,
                         "inherited_from": member["inherited_from"],
                         "in_force": terms.describe(line) if line else None,
                         "model": line["model"] if line else None,
                         "summary": member["summary"], "months": member["rows"]})
            warnings.extend(member["warnings"])
        rows.sort(key=lambda row: -row["summary"]["ytd"])
        year = current[:4]
        by_month = revenue.cumulative(revenue.combined([row["months"] for row in rows]))
        totals = revenue.summary(by_month, current)
        return {"currency": "USD", "current_month": current, "year": year, "customers": rows,
                "totals": totals, "months": by_month, "warnings": warnings}

    def summary_for(self, stem: str) -> dict | None:
        """The Customer page's panel: None when the note is charged nothing."""
        current = self._current_month()
        everyone = self._everyone()
        customer = next((row for row in everyone if row["stem"] == stem), None)
        if customer is None:
            return None
        member = self._member(customer, everyone, current)
        if not member["terms"]:
            return None
        line = terms.in_force(member["terms"], current)
        return {"currency": "USD", "in_force": terms.describe(line) if line else None,
                "inherited_from": member["inherited_from"],
                "model": line["model"] if line else None, **member["summary"],
                "route": f"{REPORT_PATH}?{urlencode({'customer': customer['key']})}"}

    def export_terms(self) -> tuple[str, bytes]:
        """Every customer's terms, for another machine (operator, 2026-10-23)."""
        content = terms_transfer.build(self._sources.insights(), datetime.now(timezone.utc))
        return f"Core42 Insight terms - {self._today().isoformat()}.json", content

    def import_terms(self, content: bytes, replace: bool = False) -> dict:
        """Writes an export's terms to the matching Customer notes. A customer this
        vault has no hub for is skipped, and so -- unless `replace` -- is one whose
        note already holds terms: the terms here may be newer than the export's."""
        exported = terms_transfer.read(content)
        here = self._sources.insights(sorted(exported))
        missing = sorted(stem for stem in exported if stem not in here)
        kept = sorted(stem for stem in exported if stem in here and here[stem] and not replace)
        imported = []
        for stem, value in sorted(exported.items()):
            if stem in missing or stem in kept:
                continue
            self._sources.set_insight(stem, value if (value["terms"] or value["note"]) else None)
            imported.append(stem)
        return {"imported": imported, "kept": kept, "missing": missing}

    def settings(self) -> dict:
        return {"sources": self._sources.status()}
