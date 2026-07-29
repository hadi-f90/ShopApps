"""Shared Rial amount spin box for Inventory and Accounting forms."""

from __future__ import annotations

from PySide6.QtWidgets import QDoubleSpinBox

# QSpinBox is 32-bit; office equipment prices exceed that. QDoubleSpinBox with
# 0 decimals holds integer Rial up to ~10^12 safely.
MAX_RIAL_AMOUNT = 999_999_999_999


def make_rial_spinbox() -> QDoubleSpinBox:
    """QDoubleSpinBox configured for integer Rial amounts with clear unit suffix."""
    box = QDoubleSpinBox()
    box.setDecimals(0)
    box.setRange(0, MAX_RIAL_AMOUNT)
    box.setSuffix(" ریال")
    box.setGroupSeparatorShown(True)
    return box
