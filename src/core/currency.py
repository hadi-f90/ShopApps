"""
Shared Rial ↔ Toman display conversion.

Per technical-conventions.md: monetary values are stored as Rial integers only.
Toman is display-only (Toman = Rial // 10). Never store Toman.
"""

from __future__ import annotations


def rial_to_toman(rial: int) -> int:
    """Display-only conversion. Never store the result."""
    return rial // 10


def toman_to_rial(toman: int) -> int:
    """Parse Toman-denominated user input back to Rial for storage."""
    return toman * 10
