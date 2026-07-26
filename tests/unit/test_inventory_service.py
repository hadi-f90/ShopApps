import pytest
from peewee import IntegrityError

from src.core.db.models import Item, StockMovement, Warehouse, db
from src.core.services.inventory_service import InventoryServiceError, LocalInventoryService


@pytest.fixture(autouse=True)
def setup_database():
    db.connect(reuse_if_open=True)
    db.create_tables([Warehouse, Item, StockMovement], safe=True)
    yield
    db.drop_tables([StockMovement, Item, Warehouse])
    db.close()


@pytest.fixture
def service():
    return LocalInventoryService()


def test_create_and_list_item(service):
    service.create_item(name="خودکار", purchase_price=1000, sale_price=2000)
    items = service.list_items()
    assert len(items) == 1
    assert items[0].name == "خودکار"
    assert items[0].on_hand_quantity == 0


def test_purchase_then_sale_updates_on_hand(service):
    item = service.create_item(name="کاغذ A4", purchase_price=500, sale_price=1000)
    wh = service.create_warehouse(name="انبار مرکزی")

    service.record_movement(item.id, wh.id, 100, "purchase")
    service.record_movement(item.id, wh.id, -30, "sale")

    assert service.get_on_hand_quantity(item.id) == 70


def test_movement_math_across_all_mvs_types(service):
    item = service.create_item(name="جوهر پرینتر", purchase_price=1000, sale_price=1500)
    wh = service.create_warehouse(name="انبار اصلی")

    service.record_movement(item.id, wh.id, 50, "purchase")
    service.record_movement(item.id, wh.id, -10, "sale")
    service.record_movement(item.id, wh.id, -5, "internal_consumption")
    service.record_movement(item.id, wh.id, -2, "spoilage")
    service.record_movement(item.id, wh.id, 3, "manual_adjustment")

    assert service.get_on_hand_quantity(item.id) == 50 - 10 - 5 - 2 + 3


def test_cannot_sell_more_than_on_hand(service):
    item = service.create_item(name="پرینتر", purchase_price=5_000_000, sale_price=7_000_000)
    wh = service.create_warehouse(name="انبار اصلی")
    service.record_movement(item.id, wh.id, 2, "purchase")

    with pytest.raises(InventoryServiceError):
        service.record_movement(item.id, wh.id, -5, "sale")


def test_low_stock_is_store_wide_across_warehouses(service):
    item = service.create_item(
        name="تونر", purchase_price=200_000, sale_price=300_000, low_stock_threshold=5
    )
    wh1 = service.create_warehouse(name="انبار ۱")
    wh2 = service.create_warehouse(name="انبار ۲")

    service.record_movement(item.id, wh1.id, 3, "purchase")
    service.record_movement(item.id, wh2.id, 3, "purchase")

    # 6 total across both warehouses -> not low stock, even though each
    # individual warehouse has fewer than the threshold on its own.
    low_stock_ids = [i.id for i in service.get_low_stock_items()]
    assert item.id not in low_stock_ids


def test_duplicate_warehouse_name_rejected(service):
    service.create_warehouse(name="انبار مرکزی")
    with pytest.raises(InventoryServiceError):
        service.create_warehouse(name="انبار مرکزی")


def test_stock_movement_ledger_blocks_item_deletion():
    """Append-only ledger: deleting an item referenced by a movement must be
    blocked by the RESTRICT foreign key (requires PRAGMA foreign_keys=1,
    set at SqliteDatabase construction — see core/db/models.py)."""
    service = LocalInventoryService()
    item = service.create_item(name="زونکن", purchase_price=50_000, sale_price=80_000)
    wh = service.create_warehouse(name="انبار اصلی")
    service.record_movement(item.id, wh.id, 10, "purchase")

    with pytest.raises(IntegrityError):
        Item.get_by_id(item.id).delete_instance()
