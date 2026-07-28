"""
Contacts UI/form smoke tests — aligned with is_customer/is_vendor schema
and ContactService (no contact_type).
"""

import pytest
from PySide6.QtWidgets import QApplication, QDialog

from src.apps.contacts.forms import ContactForm
from src.core.services.contact_service import LocalContactService


@pytest.fixture
def svc(test_db):
    return LocalContactService()


def test_create_contact_via_service(svc):
    contact = svc.create_contact(
        name="تست مشتری", mobile="09123456789", is_customer=True, is_vendor=False
    )
    assert contact.id is not None
    assert contact.name == "تست مشتری"
    assert contact.is_customer is True
    assert contact.is_vendor is False


def test_form_rejects_empty_name(qtbot):
    """Name is required — form must not accept empty name."""
    _ = QApplication.instance() or QApplication([])
    form = ContactForm(service=LocalContactService())
    form.name_edit.clear()
    form.mobile_edit.setText("09123456789")
    form.save_contact()
    assert form.result() != QDialog.Accepted


def test_form_fields_accept_dual_role_flags(qtbot):
    _ = QApplication.instance() or QApplication([])
    form = ContactForm(service=LocalContactService())
    assert form.is_customer_cb.isChecked() is True
    form.is_vendor_cb.setChecked(True)
    assert form.is_vendor_cb.isChecked() is True
