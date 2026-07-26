"""
Shared Gregorian <-> Jalali (Solar Hijri) display conversion.

Per .ai_files/technical-conventions.md: all dates are stored as Gregorian;
Jalali display is a presentation-layer-only conversion, applied when
rendering to the user and when parsing Jalali input fields. Never store a
Jalali date directly.

Requires the `jdatetime` package — add it to pyproject.toml dependencies
(it is not yet listed there as of the Inventory MVS work).
"""

from datetime import date
from typing import Optional

import jdatetime


def gregorian_to_jalali_display(value: Optional[date]) -> str:
    """Render a Gregorian date as a Jalali display string,
    e.g. date(2026, 3, 21) -> '1405/01/01'. Returns '' for None."""
    if value is None:
        return ""
    j = jdatetime.date.fromgregorian(date=value)
    return j.strftime("%Y/%m/%d")


def jalali_str_to_gregorian(jalali_str: str) -> Optional[date]:
    """Parse a 'YYYY/MM/DD' Jalali string (as typed by a user) into a
    Gregorian date for storage. Returns None for an empty string."""
    jalali_str = (jalali_str or "").strip()
    if not jalali_str:
        return None
    year, month, day = (int(part) for part in jalali_str.split("/"))
    return jdatetime.date(year, month, day).togregorian()
