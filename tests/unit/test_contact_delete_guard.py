"""Contact delete must be blocked when business records reference the contact."""

import pytest

from src.core.errors import ContactInUseError
from src.core.services.accounting_service import LocalAccountingService, ReceiptLineInput
from src.core.services.contact_service import LocalContactService
from src.core.services.inventory_service import LocalInventoryService


@pytest.fixture
def services(test_db):
    contacts = LocalContactService()
    inventory = LocalInventoryService(contact_service=contacts)
    accounting = LocalAccountingService(
        inventory_service=inventory, contact_service=contacts
    )
    return contacts, inventory, accounting


def test_delete_blocked_when_receipt_exists(services):
    contacts, inventory, accounting = services
    customer = contacts.create_contact(name="مشتری", is_customer=True)
    wh = inventory.create_warehouse("انبار")
    item = inventory.create_item(name="کالا", purchase_price=100, sale_price=200)
    inventory.record_movement(item.id, wh.id, 5, "purchase")
    accounting.create_receipt(
        customer_id=customer.id,
        warehouse_id=wh.id,
        lines=[ReceiptLineInput(item_id=item.id, quantity=1, unit_price_rial=200)],
    )
    with pytest.raises(ContactInUseError):
        contacts.delete_contact(customer.id)


def test_delete_allowed_when_unused(services):
    contacts, _, _ = services
    c = contacts.create_contact(name="آزاد", is_customer=True)
    contacts.delete_contact(c.id)
    with pytest.raises(Exception):
        contacts.get_contact(c.id)
