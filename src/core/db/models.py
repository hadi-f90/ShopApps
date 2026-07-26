from datetime import datetime, timezone

from peewee import (
    BooleanField,
    CharField,
    DateTimeField,
    ForeignKeyField,
    IntegerField,
    Model,
    SqliteDatabase,
    TextField,
)

# WAL + busy_timeout + foreign_keys must be set at construction time.
# SQLite silently ignores on_delete constraints (see StockMovement below)
# unless PRAGMA foreign_keys=1 is active on every connection.
db = SqliteDatabase(
    "shopapps.db",
    pragmas={
        "journal_mode": "wal",
        "busy_timeout": 5000,
        "foreign_keys": 1,
    },
)


def _utcnow_naive() -> datetime:
    """Timezone-aware UTC 'now', stripped back to naive before storage.

    datetime.utcnow() is deprecated (Python 3.12+). This keeps the exact
    same on-disk representation (naive UTC, per technical-conventions.md's
    'Gregorian storage' rule) while avoiding the deprecated call.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


class BaseModel(Model):
    class Meta:
        database = db


class Contact(BaseModel):
    name = CharField(null=False)
    phone = CharField(null=True)  # Fixed phone
    mobile = CharField(null=True)  # Mobile
    email = CharField(null=True)
    organization = CharField(null=True)  # Company
    title = CharField(null=True)  # Role / Position
    address = TextField(null=True)
    contact_type = CharField(default="customer")
    tags = CharField(null=True)
    note = TextField(null=True)  # Notes
    tasks = TextField(null=True)  # Future tasks/projects


class Warehouse(BaseModel):
    name = CharField(unique=True, null=False, index=True)
    location = CharField(null=True)
    is_active = BooleanField(default=True)


class Item(BaseModel):
    name = CharField(null=False, index=True)
    # Rial integers only, per technical-conventions.md. Toman is
    # display-only and computed at the UI boundary — never stored.
    purchase_price = IntegerField(default=0)
    sale_price = IntegerField(default=0)
    brand = CharField(null=True)
    # Single "default/preferred supplier" — informational only. This is
    # NOT where per-purchase vendor history lives (multiple suppliers can
    # supply the same item over time); that belongs to Accounting's future
    # Purchase record, linked back to Inventory via StockMovement.reference.
    # SET NULL (not RESTRICT) because this is a convenience pointer, not
    # an audit trail — losing it when a contact is deleted is fine.
    vendor_contact = ForeignKeyField(
        Contact, backref="supplied_items", null=True, on_delete="SET NULL"
    )
    tags = CharField(null=True, index=True)
    low_stock_threshold = IntegerField(default=5)
    is_active = BooleanField(default=True)


class StockMovement(BaseModel):
    """Append-only ledger. Never edited or deleted by application code —
    on_delete='RESTRICT' protects the audit trail at the DB constraint
    level as long as the foreign_keys pragma above is active."""

    item = ForeignKeyField(Item, backref="movements", on_delete="RESTRICT")
    warehouse = ForeignKeyField(Warehouse, backref="movements", on_delete="RESTRICT")
    quantity_delta = IntegerField(null=False)
    movement_type = CharField(null=False, index=True)
    timestamp = DateTimeField(default=_utcnow_naive, index=True)
    reference = CharField(null=True)  # receipt id / purchase id
    note = TextField(null=True)
