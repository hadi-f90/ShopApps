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
    phone = CharField(null=True)
    mobile = CharField(null=True)
    email = CharField(null=True)
    organization = CharField(null=True)
    title = CharField(null=True)
    address = TextField(null=True)
    # Independent flags — a contact may be both customer and vendor
    # (see contacts-mvs-spec.md revision notes).
    is_customer = BooleanField(default=True)
    is_vendor = BooleanField(default=False)
    tags = CharField(null=True)
    note = TextField(null=True)
    tasks = TextField(null=True)


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
    # supply the same item over time); that belongs to Accounting's
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


class Receipt(BaseModel):
    """Customer sale receipt. Identified by DB id for MVS (no formal
    sequential invoice numbering yet — see accounting-mvs-spec.md)."""

    contact = ForeignKeyField(
        Contact, backref="receipts", null=True, on_delete="SET NULL"
    )
    timestamp = DateTimeField(default=_utcnow_naive, index=True)
    total_rial = IntegerField(default=0)
    note = TextField(null=True)


class ReceiptLine(BaseModel):
    receipt = ForeignKeyField(Receipt, backref="lines", on_delete="CASCADE")
    item = ForeignKeyField(Item, backref="receipt_lines", on_delete="RESTRICT")
    quantity = IntegerField(null=False)
    unit_price_rial = IntegerField(null=False)
    line_total_rial = IntegerField(null=False)


class Purchase(BaseModel):
    """Vendor purchase that also replenishes stock via a purchase movement."""

    vendor_contact = ForeignKeyField(
        Contact, backref="purchases", null=True, on_delete="SET NULL"
    )
    item = ForeignKeyField(Item, backref="purchases", on_delete="RESTRICT")
    warehouse = ForeignKeyField(Warehouse, backref="purchases", on_delete="RESTRICT")
    quantity = IntegerField(null=False)
    unit_cost_rial = IntegerField(null=False)
    total_rial = IntegerField(null=False)
    timestamp = DateTimeField(default=_utcnow_naive, index=True)
    note = TextField(null=True)
