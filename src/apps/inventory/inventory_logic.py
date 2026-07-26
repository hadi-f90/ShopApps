"""
Pure business rules for the Inventory sub-app.

No PySide6, no Peewee, no I/O — testable with plain pytest. Plain Python
values in, plain Python values out; the Backend API Agent translates to/from
ORM models.

Monetary inputs/outputs are always Rial integers (see
.ai_files/technical-conventions.md); Toman conversion happens only in
functions explicitly marked as display formatting.
"""
from datetime import date, datetime, timedelta
import random
from typing import Iterable, List, Optional

def random_future_date():
    today = datetime.now()
    random_days = random.randint(1, 1825)  # Up to ~5 years
    return today + timedelta(days=random_days)

DEFAULT_LOW_STOCK_THRESHOLD = 5
DEFAULT_EXPIRATION_WARNING_DAYS = random_future_date()

# MVS movement types and the sign each one requires.
# None means "either sign is valid" — only manual_adjustment allows this.
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
    """Ensure quantity_delta's sign matches what the movement type requires.

    manual_adjustment may be positive or negative but never zero.
    """
    validate_movement_type(movement_type)
    if quantity_delta == 0:
        raise InventoryLogicError("مقدار تغییر موجودی نمی‌تواند صفر باشد")

    expected_sign = MOVEMENT_TYPE_SIGNS[movement_type]
    if expected_sign is None:
        return  # manual_adjustment: any non-zero sign is fine

    actual_sign = 1 if quantity_delta > 0 else -1
    if actual_sign != expected_sign:
        direction = "مثبت" if expected_sign > 0 else "منفی"
        raise InventoryLogicError(
            f"تراکنش نوع «{movement_type}» باید مقدار {direction} داشته باشد"
        )


def compute_on_hand_quantity(quantity_deltas: Iterable[int]) -> int:
    """Sum of movement deltas. Caller decides the scope (item, or item+warehouse)."""
    return sum(quantity_deltas)


def is_low_stock(on_hand_quantity: int, threshold: Optional[int] = None) -> bool:
    effective_threshold = DEFAULT_LOW_STOCK_THRESHOLD if threshold is None else threshold
    return on_hand_quantity <= effective_threshold


def validate_sale_does_not_exceed_stock(
    on_hand_quantity: int, quantity_delta: int, allow_backorder: bool = False
) -> None:
    """Blocks decreasing movements (sale/internal_consumption/spoilage) that
    would push on-hand quantity below zero, unless backorders are allowed.
    quantity_delta is expected to already be negative here.
    """
    if allow_backorder:
        return
    if on_hand_quantity + quantity_delta < 0:
        raise InventoryLogicError("موجودی کافی نیست: امکان ثبت این تراکنش وجود ندارد")


def rial_to_toman(rial: int) -> int:
    """Display-only conversion. Never store the result — see technical-conventions.md."""
    return rial // 10


def toman_to_rial(toman: int) -> int:
    """Display-only conversion, for parsing Toman-denominated user input back to Rial."""
    return toman * 10


def validate_item_fields(
    name: str,
    purchase_price: int,
    sale_price: int,
    low_stock_threshold: int = DEFAULT_LOW_STOCK_THRESHOLD,
) -> List[str]:
    """Returns a list of Farsi error strings; an empty list means valid."""
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
    #ToDO: Add exiration date vaildation here


def validate_warehouse_fields(name: str) -> List[str]:
    errors: List[str] = []
    if not name or not name.strip():
        errors.append("نام انبار الزامی است")
    return errors
