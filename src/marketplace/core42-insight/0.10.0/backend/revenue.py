"""What a customer's Insight terms earn, month by month. Pure: no files, no
services, so every figure on the screen can be pinned by a test.

A percentage is earned when the month ends (operator, 2026-10-18): a closed
month is actual, measured on the consumption Cost Manager synced; the current,
partial month and every later one are forecast, on Cost Manager's forecast. A
fixed fee is billed in its month -- actual once that month has come.
"""
from __future__ import annotations

from . import months, terms

ACTUAL = "actual"
FORECAST = "forecast"


def measure_key(line: dict) -> tuple[bool, bool]:
    return bool(line.get("include_marketplace", True)), bool(line.get("subtract_credits", True))


def measures_needed(lines: list[dict]) -> set[tuple[bool, bool]]:
    """The consumption measures the lines charge on, plus the default one the
    report shows beside a fee."""
    return {(True, True)} | {measure_key(line) for line in lines if line["model"] == terms.PERCENTAGE}


def horizon(current_month: str, commitment: dict | None) -> str:
    """The forecast's last month: the year's end, or the MACC's end when later."""
    year_end = f"{current_month[:4]}-12"
    term_end = months.month_of(commitment["end"]) if commitment and commitment.get("end") else None
    return max(year_end, term_end) if term_end else year_end


def _consumption_by_month(consumption: dict | None) -> tuple[dict[str, float], dict[str, float]]:
    if not consumption:
        return {}, {}
    actual = {row["month"]: float(row.get("total") or 0.0) for row in consumption.get("months") or []
              if row.get("closed", True)}
    forecast = {row["month"]: float(row.get("total") or 0.0) for row in consumption.get("forecast") or []}
    return actual, forecast


def monthly(lines: list[dict], consumption: dict[tuple[bool, bool], dict | None], current_month: str,
            last: str) -> list[dict]:
    """One row per month from the first line's start to `last` (or the last
    line's end, when every line has ended): the line in force, the consumption it
    charges on, and the revenue -- actual or forecast."""
    if not lines:
        return []
    ends = [terms.last_month(line) for line in lines]
    if all(ends):
        last = max(ends)
    # An instalment beyond the forecast horizon is still a payment due.
    last = max([last, *(month for line in lines if (month := terms.last_payment_month(line)))])
    measured = {key: _consumption_by_month(value) for key, value in consumption.items()}
    rows = []
    for month in months.span(terms.first_month(lines[0]), last):
        line = terms.in_force(lines, month)
        key = measure_key(line) if line and line["model"] == terms.PERCENTAGE else (True, True)
        actual, forecast = measured.get(key, ({}, {}))
        closed = month < current_month
        if closed:
            base = actual.get(month)
        else:
            base = forecast.get(month)
        row = {"month": month, "kind": ACTUAL if closed else FORECAST,
               "model": line["model"] if line else None, "line": terms.describe(line) if line else None,
               "consumption": round(base, 2) if base is not None else None,
               "missing_consumption": False, "revenue": 0.0}
        if line and line["model"] == terms.PERCENTAGE:
            row["percent"] = line["percent"]
            if base is None:
                row["missing_consumption"] = closed
            else:
                row["revenue"] = round(base * line["percent"] / 100, 2)
        elif line:
            row["revenue"] = round(terms.fee_due(line, month), 2)
            # A fee billed this month is billed, not forecast.
            if month == current_month:
                row["kind"] = ACTUAL
        rows.append(row)
    return rows


def combined(member_rows: list[list[dict]]) -> list[dict]:
    """A parent with its affiliates: each month's revenue and consumption summed."""
    by_month: dict[str, dict] = {}
    for rows in member_rows:
        for row in rows:
            into = by_month.setdefault(row["month"], {"month": row["month"], "kind": row["kind"],
                                                      "consumption": None, "revenue": 0.0,
                                                      "missing_consumption": False, "lines": []})
            if row.get("line"):
                into["lines"].append(row["line"])
            into["revenue"] = round(into["revenue"] + row["revenue"], 2)
            if row["consumption"] is not None:
                into["consumption"] = round((into["consumption"] or 0.0) + row["consumption"], 2)
            into["missing_consumption"] = into["missing_consumption"] or row["missing_consumption"]
            if row["kind"] == FORECAST:
                into["kind"] = FORECAST
    rows = []
    for month in sorted(by_month):
        row = by_month[month]
        lines = row.pop("lines")
        # One member's terms read as they are; a group's months mix several.
        row["line"] = lines[0] if len(set(lines)) == 1 else ("several terms" if lines else None)
        rows.append(row)
    return rows


def cumulative(rows: list[dict]) -> list[dict]:
    running = 0.0
    out = []
    for row in rows:
        running = round(running + row["revenue"], 2)
        out.append({**row, "cumulative": running})
    return out


def summary(rows: list[dict], current_month: str) -> dict:
    year = current_month[:4]
    actual = [row for row in rows if row["kind"] == ACTUAL]
    closed = [row for row in actual if row["month"] < current_month]
    in_year = [row for row in rows if row["month"].startswith(year)]
    return {
        "year": year,
        "last_month": {"month": closed[-1]["month"], "revenue": closed[-1]["revenue"]} if closed else None,
        "ytd": round(sum(row["revenue"] for row in in_year if row["kind"] == ACTUAL), 2),
        "lifetime": round(sum(row["revenue"] for row in actual), 2),
        "forecast_year_end": round(sum(row["revenue"] for row in in_year), 2),
        "forecast_total": round(sum(row["revenue"] for row in rows), 2),
    }
