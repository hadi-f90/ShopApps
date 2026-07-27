import pytest
from peewee import IntegrityError

from src.core.db.models import Contact, Item
from src.core.services.contact_service import LocalContactService
from src.core.services.inventory_service import InventoryServiceError, LocalInventoryService


@pytest.fixture(autouse=True)
def _db(test_db):
    """Applies the shared in-memory test_db fixture (tests/conftest.py) to
    every test in this module without changing each test's signature."""
    yield test_db


@pytest.fixture
def service():
    return LocalInventoryService()


def _make_vendor_contact(name="فروشنده تست", mobile="09120000000"):
    return Contact.create(name=name, mobile=mobile, contact_type="vendor")


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


def test_high_value_item_price_survives_round_trip(service):
    """Regression test for the QSpinBox 32-bit overflow bug: a price well
    above the old ~2.1 billion Rial ceiling must save and read back intact."""
    item = service.create_item(
        name="دستگاه کپی صنعتی", purchase_price=45_000_000_000, sale_price=60_000_000_000
    )
    fetched = service.get_item(item.id)
    assert fetched.purchase_price == 45_000_000_000
    assert fetched.sale_price == 60_000_000_000


def test_stock_movement_ledger_blocks_item_deletion(service):
    """Append-only ledger: deleting an item referenced by a movement must be
    blocked by the RESTRICT foreign key (requires PRAGMA foreign_keys=1,
    set at SqliteDatabase construction — see core/db/models.py)."""
    item = service.create_item(name="زونکن", purchase_price=50_000, sale_price=80_000)
    wh = service.create_warehouse(name="انبار اصلی")
    service.record_movement(item.id, wh.id, 10, "purchase")

    with pytest.raises(IntegrityError):
        Item.get_by_id(item.id).delete_instance()


def test_item_can_reference_default_vendor_contact(service):
    vendor = _make_vendor_contact()
    item = service.create_item(
        name="کاغذ A4", purchase_price=500, sale_price=1000, vendor_contact_id=vendor.id
    )
    assert item.vendor_contact_id == vendor.id
    assert item.vendor_name == vendor.name


def test_item_vendor_reference_rejects_unknown_contact_id(service):
    with pytest.raises(InventoryServiceError):
        service.create_item(
            name="کاغذ A4", purchase_price=500, sale_price=1000, vendor_contact_id=999999
        )


def test_item_vendor_cleared_when_contact_deleted(service):
    """vendor_contact uses on_delete='SET NULL' — it's a convenience
    pointer, not an audit trail, so deleting the contact should silently
    clear the reference rather than being blocked."""
    vendor = _make_vendor_contact()
    item = service.create_item(
        name="کاغذ A4", purchase_price=500, sale_price=1000, vendor_contact_id=vendor.id
    )
    vendor.delete_instance()

    refetched = service.get_item(item.id)
    assert refetched.vendor_contact_id is None
    assert refetched.vendor_name == ""


def test_contact_service_lists_only_vendors():
    Contact.create(name="مشتری عادی", contact_type="customer")
    vendor = _make_vendor_contact(name="تامین‌کننده لوازم اداری")

    vendors = LocalContactService().list_vendors()
    assert [v.id for v in vendors] == [vendor.id]


def test_contact_service_search_filters_by_name():
    _make_vendor_contact(name="کاغذ سازان ایران")
    _make_vendor_contact(name="لوازم التحریر پارس", mobile="09121111111")

    results = LocalContactService().list_vendors(search="کاغذ")
    assert len(results) == 1
    assert results[0].name == "کاغذ سازان ایران"
