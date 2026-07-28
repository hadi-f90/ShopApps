"""Unit tests for ContactService (is_customer / is_vendor flags)."""

import pytest

from src.core.services.contact_service import (
    ContactServiceError,
    LocalContactService,
)


@pytest.fixture
def svc(test_db):
    return LocalContactService()


def test_create_customer_and_vendor_flags(svc):
    c = svc.create_contact(name="علی", is_customer=True, is_vendor=False)
    assert c.is_customer is True
    assert c.is_vendor is False

    v = svc.create_contact(name="شرکت تأمین", is_customer=False, is_vendor=True)
    assert v.is_customer is False
    assert v.is_vendor is True

    both = svc.create_contact(
        name="دوگانه", is_customer=True, is_vendor=True, mobile="09120000000"
    )
    assert both.is_customer and both.is_vendor


def test_list_customers_vendors_filter(svc):
    svc.create_contact(name="C1", is_customer=True, is_vendor=False)
    svc.create_contact(name="V1", is_customer=False, is_vendor=True)
    svc.create_contact(name="Both", is_customer=True, is_vendor=True)

    customers = svc.list_customers()
    vendors = svc.list_vendors()
    assert {c.name for c in customers} == {"C1", "Both"}
    assert {v.name for v in vendors} == {"V1", "Both"}


def test_name_required(svc):
    with pytest.raises(ContactServiceError):
        svc.create_contact(name="  ")


def test_update_and_delete(svc):
    c = svc.create_contact(name="قدیمی", is_customer=True)
    updated = svc.update_contact(c.id, name="جدید", is_vendor=True)
    assert updated.name == "جدید"
    assert updated.is_vendor is True
    svc.delete_contact(c.id)
    with pytest.raises(ContactServiceError):
        svc.get_contact(c.id)
