import pytest

from src.apps.inventory import inventory_logic as logic


def test_movement_sign_purchase_must_be_positive():
    logic.validate_movement_sign("purchase", 5)
    with pytest.raises(logic.InventoryLogicError):
        logic.validate_movement_sign("purchase", -5)


def test_movement_sign_sale_must_be_negative():
    logic.validate_movement_sign("sale", -3)
    with pytest.raises(logic.InventoryLogicError):
        logic.validate_movement_sign("sale", 3)


def test_movement_sign_internal_consumption_must_be_negative():
    logic.validate_movement_sign("internal_consumption", -1)
    with pytest.raises(logic.InventoryLogicError):
        logic.validate_movement_sign("internal_consumption", 1)


def test_movement_sign_spoilage_must_be_negative():
    logic.validate_movement_sign("spoilage", -2)
    with pytest.raises(logic.InventoryLogicError):
        logic.validate_movement_sign("spoilage", 2)


def test_movement_sign_manual_adjustment_allows_either_sign():
    logic.validate_movement_sign("manual_adjustment", 4)
    logic.validate_movement_sign("manual_adjustment", -4)


def test_movement_sign_rejects_zero():
    with pytest.raises(logic.InventoryLogicError):
        logic.validate_movement_sign("manual_adjustment", 0)


def test_movement_sign_rejects_unknown_type():
    with pytest.raises(logic.InventoryLogicError):
        logic.validate_movement_sign("transfer", 1)  # Phase 3, not MVS


@pytest.mark.parametrize(
    "deltas,expected",
    [
        ([], 0),
        ([5], 5),
        ([10, -3, -2], 5),
        ([10, -3, -2, 4, -1], 8),
    ],
)
def test_compute_on_hand_quantity(deltas, expected):
    assert logic.compute_on_hand_quantity(deltas) == expected


def test_is_low_stock_uses_default_threshold():
    assert logic.is_low_stock(5) is True
    assert logic.is_low_stock(6) is False


def test_is_low_stock_uses_per_item_override():
    assert logic.is_low_stock(20, threshold=25) is True
    assert logic.is_low_stock(30, threshold=25) is False


def test_validate_sale_does_not_exceed_stock_blocks_overselling():
    with pytest.raises(logic.InventoryLogicError):
        logic.validate_sale_does_not_exceed_stock(on_hand_quantity=2, quantity_delta=-5)


def test_validate_sale_does_not_exceed_stock_allows_exact_depletion():
    logic.validate_sale_does_not_exceed_stock(on_hand_quantity=5, quantity_delta=-5)


def test_validate_sale_does_not_exceed_stock_respects_backorder_flag():
    logic.validate_sale_does_not_exceed_stock(
        on_hand_quantity=0, quantity_delta=-5, allow_backorder=True
    )


def test_rial_toman_conversion_round_trip():
    assert logic.rial_to_toman(1000) == 100
    assert logic.toman_to_rial(100) == 1000


def test_validate_item_fields_requires_name():
    errors = logic.validate_item_fields("", 1000, 2000)
    assert any("نام" in e for e in errors)


def test_validate_item_fields_rejects_negative_prices():
    errors = logic.validate_item_fields("Item", -1, -1)
    assert len(errors) == 2


def test_validate_item_fields_accepts_valid_input():
    assert logic.validate_item_fields("Item", 1000, 2000) == []


def test_validate_warehouse_fields_requires_name():
    assert logic.validate_warehouse_fields("") != []
    assert logic.validate_warehouse_fields("Main") == []
