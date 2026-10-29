"""A customer's Insight terms: dated lines, one charging model each.

Operator, 2026-10-18: one model at a time -- lines never overlap -- and a line
counts whole months, from the month its start falls in to the month its end
falls in. Every amount is USD.
"""
from __future__ import annotations

from datetime import date

from . import months

PERCENTAGE = "percentage"
UPFRONT = "upfront"
YEARLY = "yearly"
MODELS = (PERCENTAGE, UPFRONT, YEARLY)
MODEL_LABELS = {PERCENTAGE: "% of monthly consumption", UPFRONT: "Up-front fixed fee", YEARLY: "Yearly fixed fee"}


class TermsError(ValueError):
    pass


def _day(value, field: str) -> str:
    text = str(value or "").strip()[:10]
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError:
        raise TermsError(f"{field} must be a date, YYYY-MM-DD, not {value!r}") from None


def _number(value, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise TermsError(f"{field} must be a number, not {value!r}") from None
    if number < 0:
        raise TermsError(f"{field} cannot be negative")
    return number


def _line(raw: dict, position: int) -> dict:
    where = f"line {position}"
    if not isinstance(raw, dict):
        raise TermsError(f"{where} is not a set of fields")
    model = str(raw.get("model") or "").strip().lower()
    if model not in MODELS:
        raise TermsError(f"{where}: model must be one of {', '.join(MODELS)}, not {raw.get('model')!r}")
    line = {"model": model, "start": _day(raw.get("start"), f"{where} start")}
    if raw.get("end"):
        line["end"] = _day(raw.get("end"), f"{where} end")
        if line["end"] < line["start"]:
            raise TermsError(f"{where} ends before it starts")
    if model == PERCENTAGE:
        line["percent"] = _number(raw.get("percent"), f"{where} percent")
        if line["percent"] > 100:
            raise TermsError(f"{where} percent cannot be above 100")
        line["include_marketplace"] = bool(raw.get("include_marketplace", True))
        line["subtract_credits"] = bool(raw.get("subtract_credits", True))
    elif model == UPFRONT and raw.get("payments"):
        line["payments"] = _payments(raw["payments"], line, where)
        line["amount"] = round(sum(payment["amount"] for payment in line["payments"]), 2)
    else:
        line["amount"] = _number(raw.get("amount"), f"{where} amount")
    if raw.get("note"):
        line["note"] = str(raw["note"]).strip()
    return line


def _payments(raw, line: dict, where: str) -> list[dict]:
    """An up-front fee paid in instalments on different dates (operator,
    2026-10-18), each within the line's dates, oldest first."""
    if not isinstance(raw, list):
        raise TermsError(f"{where}: payments must be a list")
    payments = []
    for number, payment in enumerate(raw, start=1):
        label = f"{where} payment {number}"
        if not isinstance(payment, dict):
            raise TermsError(f"{label} is not a set of fields")
        clean = {"date": _day(payment.get("date"), f"{label} date"),
                 "amount": _number(payment.get("amount"), f"{label} amount")}
        if clean["date"] < line["start"] or (line.get("end") and clean["date"] > line["end"]):
            raise TermsError(f"{label} ({clean['date']}) is outside the line's dates")
        if payment.get("note"):
            clean["note"] = str(payment["note"]).strip()
        payments.append(clean)
    return sorted(payments, key=lambda payment: payment["date"])


def last_payment_month(line: dict) -> str | None:
    payments = line.get("payments") or []
    return months.month_of(payments[-1]["date"]) if payments else None


def first_month(line: dict) -> str:
    return months.month_of(line["start"])


def last_month(line: dict) -> str | None:
    return months.month_of(line["end"]) if line.get("end") else None


def validated(terms) -> list[dict]:
    """The lines in start order, each checked, refusing any two that share a month."""
    if terms in (None, ""):
        return []
    if not isinstance(terms, list):
        raise TermsError("terms must be a list of lines")
    lines = sorted((_line(raw, position) for position, raw in enumerate(terms, start=1)),
                   key=lambda line: line["start"])
    for earlier, later in zip(lines, lines[1:]):
        if last_month(earlier) is None or last_month(earlier) >= first_month(later):
            raise TermsError(f"the line starting {later['start']} overlaps the one starting {earlier['start']}: "
                             "end the earlier line before the month the next one starts")
    return lines


def in_force(lines: list[dict], month: str) -> dict | None:
    for line in lines:
        end = last_month(line)
        if first_month(line) <= month and (end is None or month <= end):
            return line
    return None


def fee_due(line: dict, month: str) -> float:
    """What a fixed-fee line bills in `month`: up front once, in its start month
    -- or each instalment in its own month; yearly in its start month and every
    twelve months after."""
    gap = months.distance(first_month(line), month)
    if line["model"] == UPFRONT and line.get("payments"):
        return round(sum(payment["amount"] for payment in line["payments"]
                         if months.month_of(payment["date"]) == month), 2)
    if line["model"] == UPFRONT:
        return line["amount"] if gap == 0 else 0.0
    if line["model"] == YEARLY:
        return line["amount"] if gap >= 0 and gap % 12 == 0 else 0.0
    return 0.0


def outside_agreement(line: dict, agreement: dict | None) -> str | None:
    """Why a line does not sit within the customer's agreement, or None. Insight
    is attached to the agreement (operator, 2026-10-18): its dates are the
    default, and a line beyond them is allowed but called out."""
    if not agreement:
        return None
    start, end = _iso(agreement.get("start")), _iso(agreement.get("end"))
    if start and line["start"] < start:
        return f"the line starting {line['start']} starts before the agreement ({start})"
    if end and line.get("end") and line["end"] > end:
        return f"the line starting {line['start']} ends after the agreement ({end})"
    return None


def _iso(value) -> str | None:
    try:
        return date.fromisoformat(str(value or "").strip()[:10]).isoformat()
    except ValueError:
        return None


def describe(line: dict) -> str:
    if line["model"] == PERCENTAGE:
        return f"{line['percent']:g}% of monthly consumption"
    if line["model"] == UPFRONT and line.get("payments"):
        return f"Up-front fee ${line['amount']:,.0f} in {len(line['payments'])} payments"
    if line["model"] == UPFRONT:
        return f"Up-front fee ${line['amount']:,.0f}"
    return f"Yearly fee ${line['amount']:,.0f}"
