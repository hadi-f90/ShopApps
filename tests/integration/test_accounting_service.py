"""Integration: receipt → sale movements; purchase → purchase movements."""

import pytest

from src.core.services.accounting_service import (
    AccountingServiceError,
    LocalAccountingService,
    ReceiptLineInput,
)
from src.core.services.contact_service import LocalContactService
from src.core.services.inventory_service import LocalInventoryService


@pytest.fixture
def services(test_db):
    contacts = LocalContactService()
    inventory = LocalInventoryService(contact_service=contacts)
    accounting = LocalAccountingService(
        inventory_service=inventory, contact_service=contacts
    )
    # Seed warehouse + item + customer
    wh = inventory.create_warehouse("انبار اصلی")
    item = inventory.create_item(
        name="پرینتر", purchase_price=10_000_000, sale_price=15_000_000
    )
    # Stock in via purchase movement first
    inventory.record_movement(
        item_id=item.id,
        warehouse_id=wh.id,
        quantity_delta=10,
        movement_type="purchase",
    )
    customer = contacts.create_contact(
        name="مشتری تست", is_customer=True, is_vendor=False
    )
    vendor = contacts.create_contact(
        name="تأمین‌کننده", is_customer=False, is_vendor=True
    )
    return {
        "accounting": accounting,
        "inventory": inventory,
        "contacts": contacts,
        "wh": wh,
        "item": item,
        "customer": customer,
        "vendor": vendor,
    }


def test_create_receipt_decrements_stock(services):
    acc = services["accounting"]
    inv = services["inventory"]
    item = services["item"]
    wh = services["wh"]
    customer = services["customer"]

    before = inv.get_on_hand_quantity(item.id, wh.id)
    assert before == 10

    receipt = acc.create_receipt(
        customer_id=customer.id,
        warehouse_id=wh.id,
        lines=[
            ReceiptLineInput(
                item_id=item.id, quantity=3, unit_price_rial=15_000_000
            )
        ],
    )
    assert receipt.total_rial == 45_000_000
    assert receipt.contact_id == customer.id

    after = inv.get_on_hand_quantity(item.id, wh.id)
    assert after == 7


def test_receipt_blocks_oversell(services):
    acc = services["accounting"]
    item = services["item"]
    wh = services["wh"]
    with pytest.raises(AccountingServiceError):
        acc.create_receipt(
            customer_id=None,
            warehouse_id=wh.id,
            lines=[
                ReceiptLineInput(
                    item_id=item.id, quantity=999, unit_price_rial=1
                )
            ],
        )


def test_record_purchase_increments_stock(services):
    acc = services["accounting"]
    inv = services["inventory"]
    item = services["item"]
    wh = services["wh"]
    vendor = services["vendor"]

    before = inv.get_on_hand_quantity(item.id, wh.id)
    purchase = acc.record_purchase(
        item_id=item.id,
        warehouse_id=wh.id,
        quantity=5,
        unit_cost_rial=9_000_000,
        vendor_contact_id=vendor.id,
    )
    assert purchase.total_rial == 45_000_000
    after = inv.get_on_hand_quantity(item.id, wh.id)
    assert after == before + 5


def test_today_sales_total(services):
    acc = services["accounting"]
    item = services["item"]
    wh = services["wh"]
    acc.create_receipt(
        customer_id=None,
        warehouse_id=wh.id,
        lines=[
            ReceiptLineInput(
                item_id=item.id, quantity=1, unit_price_rial=15_000_000
            )
        ],
    )
    assert acc.today_sales_total_rial() >= 15_000_000
