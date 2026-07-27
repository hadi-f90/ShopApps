import pytest

from src.core.db.models import Contact, Item, StockMovement, Warehouse, db

ALL_TABLES = [Contact, Warehouse, Item, StockMovement]


@pytest.fixture
def test_db():
    """In-memory DB for unit/integration tests. Does NOT exercise WAL-mode
    or pragma behavior (SQLite ':memory:' ignores journal_mode=wal) — see
    tests/integration/test_db_pragmas.py for a real temp-file test of that
    specifically."""
    db.init(":memory:")
    db.connect()
    db.create_tables(ALL_TABLES, safe=True)
    yield db
    db.drop_tables(ALL_TABLES)
    db.close()
