"""
Pure business rules for the Inventory sub-app.

No PySide6, no Peewee, no I/O — testable with plain pytest.
Currency conversion lives in src.core.currency (shared across domains).
"""

from typing import Iterable, List, Optional

# Re-export for backward-compatible imports during migration
from src.core.currency import rial_to_toman, toman_to_rial  # noqa: F401

DEFAULT_LOW_STOCK_THRESHOLD = 5

MOVEMENT_TYPE_SIGNS = {
    "purchase": 1,
    "sale": -1,
    "internal_consumption": -1,
    "spoilage": -1,
    "manual_adjustment": None,
}

MOVEMENT_TYPES = tuple(MOVEMENT_TYPE_SIGNS.keys())


class InventoryLogicError(ValueError):
    """Domain-rule violation. Message text is Farsi-facing (shown as-is in UI)."""


def validate_movement_type(movement_type: str) -> None:
    if movement_type not in MOVEMENT_TYPE_SIGNS:
        raise InventoryLogicError(f"نوع تراکنش نامعتبر است: {movement_type}")


def validate_movement_sign(movement_type: str, quantity_delta: int) -> None:
    validate_movement_type(movement_type)
    if quantity_delta == 0:
        raise InventoryLogicError("مقدار تغییر موجودی نمی‌تواند صفر باشد")

    expected_sign = MOVEMENT_TYPE_SIGNS[movement_type]
    if expected_sign is None:
        return

    actual_sign = 1 if quantity_delta > 0 else -1
    if actual_sign != expected_sign:
        direction = "مثبت" if expected_sign > 0 else "منفی"
        raise InventoryLogicError(
            f"تراکنش نوع «{movement_type}» باید مقدار {direction} داشته باشد"
        )


def compute_on_hand_quantity(quantity_deltas: Iterable[int]) -> int:
    return sum(quantity_deltas)


def is_low_stock(on_hand_quantity: int, threshold: Optional[int] = None) -> bool:
    effective_threshold = DEFAULT_LOW_STOCK_THRESHOLD if threshold is None else threshold
    return on_hand_quantity <= effective_threshold


def validate_sale_does_not_exceed_stock(
    on_hand_quantity: int, quantity_delta: int, allow_backorder: bool = False
) -> None:
    if allow_backorder:
        return
    if on_hand_quantity + quantity_delta < 0:
        raise InventoryLogicError("موجودی کافی نیست: امکان ثبت این تراکنش وجود ندارد")


def validate_item_fields(
    name: str,
    purchase_price: int,
    sale_price: int,
    low_stock_threshold: int = DEFAULT_LOW_STOCK_THRESHOLD,
) -> List[str]:
    errors: List[str] = []
    if not name or not name.strip():
        errors.append("نام کالا الزامی است")
    if purchase_price < 0:
        errors.append("قیمت خرید نمی‌تواند منفی باشد")
    if sale_price < 0:
        errors.append("قیمت فروش نمی‌تواند منفی باشد")
    if low_stock_threshold < 0:
        errors.append("آستانه هشدار موجودی کم نمی‌تواند منفی باشد")
    return errors


def validate_warehouse_fields(name: str) -> List[str]:
    errors: List[str] = []
    if not name or not name.strip():
        errors.append("نام انبار الزامی است")
    return errors
