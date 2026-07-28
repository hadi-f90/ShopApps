import pytest

from src.core.db.models import (
    Contact,
    Item,
    Purchase,
    Receipt,
    ReceiptLine,
    StockMovement,
    Warehouse,
    db,
)

ALL_TABLES = [
    Contact,
    Warehouse,
    Item,
    StockMovement,
    Receipt,
    ReceiptLine,
    Purchase,
]


@pytest.fixture
def test_db():
    """In-memory DB for unit/integration tests."""
    db.init(":memory:")
    db.connect()
    db.create_tables(ALL_TABLES, safe=True)
    yield db
    db.drop_tables(ALL_TABLES)
    db.close()
