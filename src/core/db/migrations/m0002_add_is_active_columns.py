"""
DRAFT — verify against your actual schema/migrations folder before running.

Adds `is_active` to `item` and `warehouse` for any shopapps.db created
before that field was added to the models. Same class of gap m0001 already
handles for `item.vendor` -> `item.vendor_contact_id`: a model field shipped
without a matching migration, so Peewee's Model.select() (which lists every
declared field explicitly) fails with "no such column: t1.is_active" against
an older database.

Before running:
  1. Confirm no other migration file already claims VERSION = 2 in
     src/core/db/migrations/ — if one exists, bump this file's VERSION (and
     filename) to the next free number instead.
  2. Back up shopapps.db first: `cp shopapps.db shopapps.db.bak`
  3. Run just the migration, not the full UI, so you can see the outcome
     before opening the app:
         python -m src.core.db.migrations.runner
"""

from peewee import BooleanField
from playhouse.migrate import migrate

VERSION = 2  # CONFIRM this is actually the next free version in your repo


def _table_exists(db, table_name: str) -> bool:
    return table_name in db.get_tables()


def _column_names(db, table_name: str) -> set:
    return {col.name for col in db.get_columns(table_name)}


def up(migrator, db):
    ops = []

    for table_name in ("item", "warehouse"):
        if not _table_exists(db, table_name):
            continue
        columns = _column_names(db, table_name)
        if "is_active" not in columns:
            # BooleanField(default=True, null=False): playhouse's migrator
            # backfills existing rows to the default automatically, so
            # existing items/warehouses come back as active=True rather
            # than NULL — a reasonable assumption, since nothing could have
            # been explicitly deactivated before this field existed.
            ops.append(migrator.add_column(table_name, "is_active", BooleanField(default=True)))

    if ops:
        migrate(*ops)