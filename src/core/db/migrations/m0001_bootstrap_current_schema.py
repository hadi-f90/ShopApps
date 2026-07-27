"""
Bootstrap migration: brings an existing shopapps.db — including one already
in use before this migration system existed, in whatever intermediate state
it happens to be in — up to the schema as of this migration system's
introduction. Also creates everything from scratch for a brand-new DB.

Every check below inspects the actual table/column state via introspection
rather than assuming a specific prior version, because a real, already-in-use
shopapps.db can't be assumed to match any single known-good snapshot.
"""

from peewee import IntegerField
from playhouse.migrate import migrate

from src.core.db.models import Contact, Item, StockMovement, Warehouse

VERSION = 1


def _table_exists(db, table_name: str) -> bool:
    return table_name in db.get_tables()


def _column_names(db, table_name: str) -> set:
    return {col.name for col in db.get_columns(table_name)}


def up(migrator, db):
    # 1. Create any wholly-missing tables. No-op for tables that already
    #    exist (safe=True), so this is fine to run against a partially
    #    populated DB too.
    db.create_tables([Contact, Warehouse, Item, StockMovement], safe=True)

    # 2. Reconcile `item` if it predates the vendor_contact FK change: older
    #    schema versions had a free-text `vendor` CharField instead of the
    #    `vendor_contact` FK introduced later.
    if _table_exists(db, "item"):
        columns = _column_names(db, "item")
        ops = []

        if "vendor_contact_id" not in columns:
            ops.append(migrator.add_column("item", "vendor_contact_id", IntegerField(null=True)))

        if "vendor" in columns:
            # Old free-text vendor values can't be reliably auto-mapped to a
            # specific Contact row (no guaranteed name match), so this is a
            # deliberate, one-time data loss on upgrade rather than a guess.
            # If you need to preserve the old free-text values, read them out
            # of the `vendor` column before running this migration.
            ops.append(migrator.drop_column("item", "vendor"))

        if ops:
            migrate(*ops)
