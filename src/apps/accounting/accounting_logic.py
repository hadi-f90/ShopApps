"""
Pure business rules for Accounting (no Peewee, no PySide6, no I/O).

All money values are Rial integers. Toman conversion belongs only at the
UI display boundary (see technical-conventions.md).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence


@dataclass(frozen=True)
class LineInput:
    """One receipt line before persistence."""

    item_id: int
    quantity: int
    unit_price_rial: int


def line_total_rial(quantity: int, unit_price_rial: int) -> int:
    return quantity * unit_price_rial


def receipt_total_rial(lines: Sequence[LineInput]) -> int:
    return sum(line_total_rial(ln.quantity, ln.unit_price_rial) for ln in lines)


def purchase_total_rial(quantity: int, unit_cost_rial: int) -> int:
    return quantity * unit_cost_rial


def validate_receipt_lines(lines: Sequence[LineInput]) -> List[str]:
    """Return Farsi error strings; empty list means valid."""
    errors: List[str] = []
    if not lines:
        errors.append("حداقل یک قلم کالا برای فاکتور لازم است")
        return errors
    for i, ln in enumerate(lines, start=1):
        if ln.quantity <= 0:
            errors.append(f"قلم {i}: تعداد باید بزرگ‌تر از صفر باشد")
        if ln.unit_price_rial < 0:
            errors.append(f"قلم {i}: قیمت واحد نمی‌تواند منفی باشد")
        if ln.item_id is None or ln.item_id <= 0:
            errors.append(f"قلم {i}: کالا نامعتبر است")
    return errors


def validate_purchase_fields(
    quantity: int, unit_cost_rial: int, item_id: int, warehouse_id: int
) -> List[str]:
    errors: List[str] = []
    if quantity <= 0:
        errors.append("تعداد باید بزرگ‌تر از صفر باشد")
    if unit_cost_rial < 0:
        errors.append("بهای واحد نمی‌تواند منفی باشد")
    if item_id is None or item_id <= 0:
        errors.append("کالا الزامی است")
    if warehouse_id is None or warehouse_id <= 0:
        errors.append("انبار الزامی است")
    return errors
