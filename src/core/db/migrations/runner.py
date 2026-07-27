"""
Lightweight schema migration runner.

Why this exists: technical-conventions.md already commits to Peewee's
`playhouse.migrate` path ("has a working migration path"), and
database-agent/SKILL.md already says "every schema change ships with a
migration — never assume a fresh DB." Neither was actually built until now.
Every prior schema change relied on `create_tables(..., safe=True)`, which
only creates *missing* tables — it never alters an existing one. That's the
exact bug that made past changes (e.g. Item.vendor -> Item.vendor_contact)
silently do nothing against a real, already-populated shopapps.db.

How it works
------------
Each migration module in this package is named `m<NNNN>_<description>.py`
and exposes:

    VERSION: int              # target schema version this migration produces
    def up(migrator, db):     # apply the change using playhouse.migrate ops

Applied-migration tracking uses SQLite's built-in `PRAGMA user_version` —
no extra tracking table needed. run_migrations() applies every migration
whose VERSION is greater than the current user_version, in ascending order,
each wrapped in its own transaction.

Adding a new migration
-----------------------
1. Create `m0002_<short_description>.py` in this package.
2. Set `VERSION = 2` (one higher than the previous highest).
3. Write `up(migrator, db)` using playhouse.migrate operations
   (migrator.add_column / drop_column / rename_column / add_index, wrapped
   in a single `migrate(*ops)` call) or plain `db.execute_sql()` for things
   migrate() doesn't cover.
4. Never edit a migration that has already shipped — add a new one instead,
   even to fix a mistake in an earlier one.

Usage: called automatically from core/db/__init__.py's init_db(). Also
runnable standalone: `python -m src.core.db.migrations.runner`.
"""

import importlib
import logging
import pkgutil

from playhouse.migrate import SqliteMigrator

from src.core.db.models import db

logger = logging.getLogger(__name__)


def _get_user_version() -> int:
    cursor = db.execute_sql("PRAGMA user_version;")
    return cursor.fetchone()[0]


def _set_user_version(version: int) -> None:
    db.execute_sql(f"PRAGMA user_version = {int(version)};")


def _discover_migrations():
    import src.core.db.migrations as pkg

    modules = []
    for _, name, _ in pkgutil.iter_modules(pkg.__path__):
        if name.startswith("m") and name[1:5].isdigit():
            modules.append(importlib.import_module(f"{pkg.__name__}.{name}"))
    return sorted(modules, key=lambda m: m.VERSION)


def run_migrations() -> None:
    db.connect(reuse_if_open=True)
    current = _get_user_version()
    migrator = SqliteMigrator(db)

    for module in _discover_migrations():
        if module.VERSION <= current:
            continue
        logger.info("Applying migration %s -> schema v%s", module.__name__, module.VERSION)
        with db.atomic():
            module.up(migrator, db)
            _set_user_version(module.VERSION)

    db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_migrations()
