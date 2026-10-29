"""Billing months as `YYYY-MM` strings -- the one key every module here shares."""
from __future__ import annotations

from datetime import date


def month_of(day: date | str) -> str:
    if isinstance(day, str):
        return day[:7]
    return f"{day.year:04d}-{day.month:02d}"


def shift(month: str, by: int) -> str:
    year, number = (int(part) for part in month.split("-"))
    index = year * 12 + (number - 1) + by
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


def span(first: str, last: str) -> list[str]:
    """Every month from `first` to `last`, both included; empty when reversed."""
    months, current = [], first
    while current <= last:
        months.append(current)
        current = shift(current, 1)
    return months


def distance(earlier: str, later: str) -> int:
    first_year, first_number = (int(part) for part in earlier.split("-"))
    last_year, last_number = (int(part) for part in later.split("-"))
    return (last_year - first_year) * 12 + (last_number - first_number)
