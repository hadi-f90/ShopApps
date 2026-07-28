"""
Migration v3: Contact is_customer/is_vendor flags + Accounting tables.

Runs AFTER m0002_add_is_active_columns (VERSION=2).

- Replaces single contact_type CharField with independent boolean flags
  (a contact may be both customer and vendor).
- Creates Receipt, ReceiptLine, Purchase tables for Accounting MVS.

Safe on DBs that already ran m0001 + m0002: only adds missing columns/tables.
"""

from peewee import BooleanField
from playhouse.migrate import migrate

from src.core.db.models import Contact, Purchase, Receipt, ReceiptLine

VERSION = 3


def _table_exists(db, table_name: str) -> bool:
    return table_name in db.get_tables()


def _column_names(db, table_name: str) -> set:
    return {col.name for col in db.get_columns(table_name)}


def up(migrator, db):
    # --- Contact flags ---
    if _table_exists(db, "contact"):
        columns = _column_names(db, "contact")
        ops = []

        if "is_customer" not in columns:
            ops.append(
                migrator.add_column(
                    "contact", "is_customer", BooleanField(default=True)
                )
            )
        if "is_vendor" not in columns:
            ops.append(
                migrator.add_column(
                    "contact", "is_vendor", BooleanField(default=False)
                )
            )

        if ops:
            migrate(*ops)

        # Data migration from legacy contact_type (if present)
        if "contact_type" in _column_names(db, "contact"):
            db.execute_sql(
                """
                UPDATE contact SET
                    is_customer = CASE
                        WHEN contact_type IN ('customer', 'staff') OR contact_type IS NULL
                        THEN 1 ELSE 0
                    END,
                    is_vendor = CASE
                        WHEN contact_type = 'vendor' THEN 1 ELSE 0
                    END
                """
            )
            # Contacts that were pure vendors should still be usable as customers
            # if the shop later sells to them; keep is_customer True for dual-role
            # safety only when type was 'customer'. Pure vendor stays is_customer=0.
            # Spec allows both flags True; we map 1:1 from old single type.
            migrate(migrator.drop_column("contact", "contact_type"))

    # Ensure tables exist for brand-new DBs / partial states
    db.create_tables([Contact, Receipt, ReceiptLine, Purchase], safe=True)
