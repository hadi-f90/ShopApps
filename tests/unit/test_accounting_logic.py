"""Unit tests for pure accounting rules (no DB)."""

from src.apps.accounting.accounting_logic import (
    LineInput,
    line_total_rial,
    purchase_total_rial,
    receipt_total_rial,
    validate_purchase_fields,
    validate_receipt_lines,
)


def test_line_and_receipt_totals():
    lines = [
        LineInput(item_id=1, quantity=2, unit_price_rial=1_500_000),
        LineInput(item_id=2, quantity=1, unit_price_rial=500_000),
    ]
    assert line_total_rial(2, 1_500_000) == 3_000_000
    assert receipt_total_rial(lines) == 3_500_000


def test_validate_receipt_lines_empty():
    errs = validate_receipt_lines([])
    assert errs
    assert "حداقل" in errs[0]


def test_validate_receipt_lines_bad_qty():
    errs = validate_receipt_lines(
        [LineInput(item_id=1, quantity=0, unit_price_rial=100)]
    )
    assert any("تعداد" in e for e in errs)


def test_purchase_total_and_validation():
    assert purchase_total_rial(5, 9_000_000) == 45_000_000
    errs = validate_purchase_fields(0, 100, 1, 1)
    assert any("تعداد" in e for e in errs)
    assert not validate_purchase_fields(1, 100, 1, 1)
