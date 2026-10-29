"""The two plugins Insight reads, through their services, asked for at call
time -- either may be installed, updated or removed while the backend runs.

- Entities (`entities.customers` `insight`/`set_insight`): the terms, kept in a
  separate Insight note per customer, never on the hub (operator, 2026-10-18).
- Azure Cost Manager (`azure-cost-manager.consumption`): which customers are
  linked to notes, and their monthly consumption. Never its HTTP routes.
"""
from __future__ import annotations

import threading
import time

ENTITIES_SERVICE = "entities.customers"
CONSUMPTION_SERVICE = "azure-cost-manager.consumption"
ENTITIES_MISSING = ("The Entities plugin is not running, so Insight cannot read or save customers' terms (they are "
                    "safe in the vault). Check Settings > Plugins: Entities may need updating for this framework "
                    "version")
# Cost Manager merges every synced month per answer (seconds each), and its data
# only changes when it syncs -- weekly or on demand -- so an answer is kept briefly.
CONSUMPTION_CACHE_SECONDS = 120
# Cost Manager's customer list takes seconds (2026-10-18: ~7 s for 99 customers)
# and changes only when a customer is added or linked.
CUSTOMERS_CACHE_SECONDS = 120
# An Entities note read costs 1-2 s, and the customer screen reads one per
# customer; a save drops the customer's kept terms at once.
NOTE_CACHE_SECONDS = 30


class SourceMissing(RuntimeError):
    pass


def vault_not_ready(error: BaseException) -> bool:
    """Entities' `VaultNotReady` (1.7.1+): for some seconds after every backend
    reload the vault index is empty and no note can be found. That is "try again",
    never "no terms" or "no agreement" -- reading it as either made Insight data
    "load sometimes, not others" (operator, 2026-10-18). Matched by name: a plugin
    may not import another plugin's types."""
    return type(error).__name__ == "VaultNotReady"


class Sources:
    def __init__(self, api, clock=time.monotonic) -> None:
        self._api = api
        self._clock = clock
        self._monthly_cache: dict[tuple, tuple[float, dict | None]] = {}
        self._cache_lock = threading.Lock()

    def _entities(self):
        service = self._api.get_service(ENTITIES_SERVICE)
        return service if service is not None and hasattr(service, "set_insight") else None

    def _consumption(self):
        service = self._api.get_service(CONSUMPTION_SERVICE)
        return service if service is not None and hasattr(service, "monthly") else None

    def status(self) -> dict:
        return {"entities": self._entities() is not None, "cost_manager": self._consumption() is not None}

    def insight(self, customer_stem: str) -> dict | None:
        service = self._entities()
        if service is None:
            # Not "no terms": the terms are in the vault, Insight just cannot reach them
            # (2026-10-18: Entities refused at load, and every customer read "No Insight").
            raise SourceMissing(ENTITIES_MISSING)
        return self._cached(("insight", customer_stem), lambda: service.insight(customer_stem), NOTE_CACHE_SECONDS)

    def set_insight(self, customer_stem: str, value: dict | None) -> dict | None:
        service = self._entities()
        if service is None:
            raise SourceMissing(ENTITIES_MISSING)
        with self._cache_lock:
            self._monthly_cache.pop(("insight", customer_stem), None)
        return service.set_insight(customer_stem, value)

    def insights(self, stems: list[str] | None = None) -> dict[str, dict | None]:
        """Insight terms for many customers at once -- stem -> terms or None -- every
        Customer hub when `stems` is None. A stem with no hub is left out. Uncached:
        an export or import must see the notes as they are now."""
        service = self._entities()
        if service is None:
            raise SourceMissing(ENTITIES_MISSING)
        if hasattr(service, "insights"):
            return service.insights(stems)
        found: dict[str, dict | None] = {}
        for stem in stems if stems is not None else [row["stem"] for row in self.customers() if row["stem"]]:
            try:
                found[stem] = service.insight(stem)
            except ValueError as exc:
                if type(exc).__name__ != "OpportunityNotFound":
                    raise
        return found

    def agreement(self, customer_stem: str, ask_cost_manager: bool = True) -> dict | None:
        """The customer's agreement (MACC, EA commitment, ...) that Insight is
        attached to: the `macc_*` on its Customer note through Entities, else the
        commitment Cost Manager keeps for it. None when neither has one."""
        service = self._api.get_service(ENTITIES_SERVICE)
        if service is not None and hasattr(service, "commitment"):
            try:
                found = self._cached(("commitment", customer_stem), lambda: service.commitment(customer_stem),
                                     NOTE_CACHE_SECONDS)
            except Exception as exc:
                if vault_not_ready(exc):
                    raise
                found = None
            if found:
                return {key: found.get(key) for key in
                        ("type", "amount", "currency", "start", "end", "include_marketplace", "subtract_credits")}
        if not ask_cost_manager:
            return None
        consumption = self.monthly(customer_stem, True, True) or {}
        kept = consumption.get("commitment")
        return {"type": None, "currency": consumption.get("currency"), **kept} if kept else None

    def customers(self) -> list[dict]:
        """Every Cost Manager customer, note or not (operator, 2026-10-18: DGE has
        fifty affiliates and only one has a Customer note), as
        `{key, stem, cost_id, name, parent_key, currency, route}`. `key` is the
        note's stem, or `cm:<id>` for a customer without a note. A Cost Manager
        older than `customers()` gives its note-linked customers only."""
        service = self._consumption()
        if service is None:
            raise SourceMissing("Insight reads customers and consumption from the Azure Customer 360 plugin: "
                                "install or update it to a version with the consumption service")
        return self._cached(("customers",), lambda: self._customers(service), CUSTOMERS_CACHE_SECONDS)

    @staticmethod
    def _customers(service) -> list[dict]:
        if not hasattr(service, "customers"):
            return [{"key": row["customer_stem"], "stem": row["customer_stem"], "cost_id": None,
                     "name": row["name"], "parent_key": row.get("parent_stem"),
                     "currency": row.get("currency"), "route": row.get("route"),
                     "affiliates": "roll up"} for row in service.linked()]
        rows = service.customers()
        # Two customers on one note: the top-level one speaks for it, as in Cost Manager.
        speakers: dict[str, str] = {}
        for row in sorted(rows, key=lambda row: (bool(row.get("parent_id")), row["name"].lower())):
            if row.get("customer_stem"):
                speakers.setdefault(row["customer_stem"], row["id"])
        stems = {row["id"]: row["customer_stem"] for row in rows
                 if row.get("customer_stem") and speakers[row["customer_stem"]] == row["id"]}
        keys = {row["id"]: stems.get(row["id"]) or f"cm:{row['id']}" for row in rows}
        return [{"key": keys[row["id"]], "stem": stems.get(row["id"]), "cost_id": row["id"],
                 "name": row["name"], "parent_key": keys.get(row.get("parent_id")),
                 "currency": row.get("currency"), "route": row.get("route"),
                 # Cost Manager 0.29+: "own" when each affiliate signed its own MACC (Mubadala).
                 "affiliates": "own" if row.get("affiliates") == "own" else "roll up"} for row in rows]

    def monthly_for(self, customer: dict, include_marketplace: bool, subtract_credits: bool) -> dict | None:
        """A customer's own monthly consumption, by its note when it has one, else by its Cost Manager id."""
        if customer.get("stem"):
            return self.monthly(customer["stem"], include_marketplace, subtract_credits)
        service = self._consumption()
        if service is None or not hasattr(service, "monthly_of") or not customer.get("cost_id"):
            return None
        return self._cached(("cm", customer["cost_id"], bool(include_marketplace), bool(subtract_credits)),
                            lambda: service.monthly_of(customer["cost_id"], include_marketplace=include_marketplace,
                                                       subtract_credits=subtract_credits))

    def monthly(self, customer_stem: str, include_marketplace: bool, subtract_credits: bool) -> dict | None:
        service = self._consumption()
        if service is None:
            return None
        return self._cached((customer_stem, bool(include_marketplace), bool(subtract_credits)),
                            lambda: service.monthly(customer_stem, include_marketplace=include_marketplace,
                                                    subtract_credits=subtract_credits))

    def _cached(self, key: tuple, ask, seconds: float = CONSUMPTION_CACHE_SECONDS):
        """An answer kept for `seconds`. A failure is never kept: just after a
        backend restart Entities reports every note as not found until the vault
        is read (2026-10-18), and keeping that would blank the page for a while."""
        now = self._clock()
        with self._cache_lock:
            kept = self._monthly_cache.get(key)
        if kept and now - kept[0] < seconds:
            return kept[1]
        answer = ask()
        with self._cache_lock:
            self._monthly_cache[key] = (now, answer)
        return answer
