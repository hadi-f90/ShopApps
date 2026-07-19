from datetime import datetime

from peewee import (
    CharField,
    DateTimeField,
    ForeignKeyField,
    IntegerField,
    Model,
    SqliteDatabase,
    TextField,
)

db = SqliteDatabase('shopapps.db')


class BaseModel(Model):
    class Meta:
        database = db


class Contact(BaseModel):
    name = CharField(null=False)
    phone = CharField(null=True)           # Fixed phone
    mobile = CharField(null=True)          # Mobile
    email = CharField(null=True)
    organization = CharField(null=True)    # Company
    title = CharField(null=True)           # Role / Position
    address = TextField(null=True)
    contact_type = CharField(default='customer')
    tags = CharField(null=True)
    note = TextField(null=True)            # Notes
    tasks = TextField(null=True)           # Future tasks/projects


# ---------------------------------------------------------------------------
# Inventory models — see .ai_files/specs/inventory-mvs-spec.md
# Currency: Rial integers only (technical-conventions.md). Toman is a
# display-only conversion done at the UI boundary — never stored here.
# ---------------------------------------------------------------------------

class Warehouse(BaseModel):
    name = CharField(null=False, unique=True)
    location = CharField(null=True)
    note = TextField(null=True)


class Item(BaseModel):
    name = CharField(null=False, index=True)
    purchase_price = IntegerField(default=0)   # Rial
    sale_price = IntegerField(default=0)       # Rial
    brand = CharField(null=True)
    vendor = CharField(null=True)              # Plain field for MVS; may
    # become a ForeignKeyField(Contact, is_vendor=True) once core/services
    # exists and cross-app FK access goes through it rather than direct ORM.
    tags = CharField(null=True, index=True)
    low_stock_threshold = IntegerField(default=5)  # per-item override, spec default = 5


class StockMovement(BaseModel):
    """
    Append-only ledger. Stock quantity is NEVER mutated directly — every
    change is a row here. On-hand quantity for an item/warehouse is always
    the sum of its movements (see Item.on_hand / StockMovement.on_hand_for).
    """

    MOVEMENT_TYPES = (
        ('purchase', 'purchase'),                     # +
        ('sale', 'sale'),                              # -
        ('internal_consumption', 'internal_consumption'),  # -
        ('spoilage', 'spoilage'),                      # -
        ('manual_adjustment', 'manual_adjustment'),    # +/-
    )

    item = ForeignKeyField(Item, backref='movements', on_delete='CASCADE')
    warehouse = ForeignKeyField(Warehouse, backref='movements', on_delete='CASCADE')
    quantity_delta = IntegerField(null=False)  # signed; sign convention enforced
    # by App Logic Agent, not here (e.g. 'sale' must be negative). This layer
    # only stores what it's given.
    movement_type = CharField(choices=MOVEMENT_TYPES, null=False)
    timestamp = DateTimeField(default=datetime.utcnow)  # Gregorian storage;
    # Jalali conversion happens only at the UI boundary.
    reference = CharField(null=True)  # e.g. receipt id / purchase id
    note = TextField(null=True)

    @staticmethod
    def on_hand_for(item: Item, warehouse: Warehouse) -> int:
        """Sum of movement deltas for one item in one warehouse. Basic
        derived-quantity query only — validation rules (e.g. can't sell more
        than on-hand) belong to App Logic Agent, not here."""
        total = (
            StockMovement
            .select()
            .where(
                (StockMovement.item == item)
                & (StockMovement.warehouse == warehouse)
            )
        )
        return sum(m.quantity_delta for m in total)