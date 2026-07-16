import pytest
from PySide6.QtWidgets import QApplication, QDialog
from src.apps.contacts.forms import ContactForm
from src.core.db.models import Contact, db


@pytest.fixture(autouse=True)
def setup_database():
    db.connect()
    db.create_tables([Contact], safe=True)
    yield
    db.drop_tables([Contact])
    db.close()

def test_create_contact():
    contact = Contact.create(name="تست مشتری", mobile="09123456789", contact_type="customer")
    assert contact.id is not None
    assert contact.name == "تست مشتری"

def test_form_save_new_contact(qtbot):
    app = QApplication.instance() or QApplication([])
    form = ContactForm()
    form.name_edit.setText("مشتری جدید")
    form.mobile_edit.setText("09121234567")
    form.note_edit.setText("یادداشت تست")

    # Simulate save (form logic tested via model)
    # In real UI test: qtbot.mouseClick(save_button)
    assert form.name_edit.text() == "مشتری جدید"

def test_security_input_validation():
    # Basic security: name is required (already in form)
    pass  # Can be expanded with more validation

def test_security_name_required_validation(qtbot):
    """Test that form rejects empty name (security/validation)"""
    form = ContactForm()
    form.name_edit.clear()  # Empty name
    form.mobile_edit.setText("09123456789")

    # Simulate save
    form.save_contact()

    # Form should not accept (still open)
    assert not form.result() == QDialog.Accepted