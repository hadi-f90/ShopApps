import pytest
from src.core.db.models import Contact, db
  # For UI testing later

@pytest.fixture(autouse=True)
def setup_db():
    db.create_tables([Contact])
    yield
    db.drop_tables([Contact])

def test_create_contact():
    contact = Contact.create(name="Test Customer", phone="09123456789", contact_type="customer")
    assert contact.id is not None
    assert contact.name == "Test Customer"

def test_contact_validation():
    # This would test form logic in real UI tests
    pass  # Can be expanded with QTest for PySide6 UI

def test_vcf_export_placeholder():
    # TODO: Implement actual VCF export test in MVS+ phase
    pass