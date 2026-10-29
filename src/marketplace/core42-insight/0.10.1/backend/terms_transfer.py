"""Moving every customer's Insight terms to another machine (operator, 2026-10-23:
"when I move this into another machine I would not need to sync everything again").

The terms live in the vault, one `<stem> - Insight.md` note per customer, so a
machine that gets the vault gets them too. This file is for a machine that does
not: one JSON file naming its format, with each customer's `{terms, note}` by
the Customer note's stem. An import checks every customer's terms before it
writes any, so a damaged file changes nothing.
"""
from __future__ import annotations

import json
from datetime import datetime

from . import terms

FORMAT = "core42-insight-terms"
FORMAT_VERSION = 1


class TermsImportError(ValueError):
    pass


def build(found: dict[str, dict | None], exported_at: datetime) -> bytes:
    """`found`: stem -> its Insight terms (None for a customer without any)."""
    customers = {stem: {"terms": value.get("terms") or [], "note": value.get("note") or ""}
                 for stem, value in sorted(found.items()) if value}
    return json.dumps({"format": FORMAT, "format_version": FORMAT_VERSION, "exported_at": exported_at.isoformat(),
                       "customers": customers}, indent=1).encode("utf-8")


def read(content: bytes) -> dict[str, dict]:
    """The customers' terms in an export, each validated: stem -> `{terms, note}`."""
    try:
        exported = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise TermsImportError("this is not a Core42 Insight export (not JSON)") from exc
    if not isinstance(exported, dict) or exported.get("format") != FORMAT:
        raise TermsImportError("this is not a Core42 Insight export")
    if int(exported.get("format_version") or 0) > FORMAT_VERSION:
        raise TermsImportError("this export is from a newer Core42 Insight; update the plugin first")
    customers = exported.get("customers")
    if not isinstance(customers, dict) or not customers:
        raise TermsImportError("the export holds no customers' terms")
    checked: dict[str, dict] = {}
    for stem, value in customers.items():
        try:
            lines = terms.validated((value or {}).get("terms"))
        except (terms.TermsError, AttributeError) as exc:
            raise TermsImportError(f"{stem}'s terms in the export do not read ({exc}); nothing was imported") from exc
        checked[stem] = {"terms": lines, "note": str(value.get("note") or "").strip()}
    return checked
