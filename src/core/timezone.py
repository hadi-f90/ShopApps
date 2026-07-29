"""
Iran business calendar helpers.

Storage rule (technical-conventions.md): timestamps are naive UTC on disk.
Calendar-day boundaries for "today / this week / this month" must be computed
in Iran Standard Time (UTC+3:30, no DST), then converted back to naive UTC
ranges for comparison against stored values.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

# Iran Standard Time — fixed offset, no daylight saving since 2022.
IRAN_TZ = timezone(timedelta(hours=3, minutes=30))
UTC = timezone.utc


def now_iran() -> datetime:
    """Aware datetime in Iran Standard Time."""
    return datetime.now(IRAN_TZ)


def today_iran() -> date:
    """Current calendar date in Iran (business 'today')."""
    return now_iran().date()


def iran_day_bounds_as_naive_utc(day: date) -> tuple[datetime, datetime]:
    """Return (start, end) as naive UTC datetimes covering the full Iran day.

    Inclusive of the entire calendar day in Iran: [00:00:00, 23:59:59.999999]
    expressed as naive UTC for comparison with models._utcnow_naive() values.
    """
    start_iran = datetime.combine(day, time.min, tzinfo=IRAN_TZ)
    end_iran = datetime.combine(day, time.max, tzinfo=IRAN_TZ)
    start_utc = start_iran.astimezone(UTC).replace(tzinfo=None)
    end_utc = end_iran.astimezone(UTC).replace(tzinfo=None)
    return start_utc, end_utc


def today_bounds_naive_utc() -> tuple[datetime, datetime]:
    """Naive-UTC [start, end] for the current Iran business day."""
    return iran_day_bounds_as_naive_utc(today_iran())
