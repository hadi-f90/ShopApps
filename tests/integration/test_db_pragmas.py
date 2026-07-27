"""
:memory: SQLite doesn't exercise WAL-mode/pragma behavior the way a real
file-backed connection does, so the shared `test_db` fixture in
tests/conftest.py can't catch a regression here. This test opens a real
temp-file database specifically to assert the pragmas actually take effect —
per coding-conventions.md §5, this is the exact class of bug the earlier
security review caught once (on_delete='RESTRICT' being silently ignored
without PRAGMA foreign_keys=1 active).
"""

import os
import tempfile

import pytest
from peewee import SqliteDatabase

from src.core.db import init_db
import src.core.db.models as models_module


@pytest.fixture
def temp_file_db(monkeypatch):
    """Points the shared `db` object at a real temp file for the duration
    of the test, then restores it. Necessary because db.database/db.init()
    is process-global in Peewee."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.remove(path)  # init_db()/migrations should create it fresh

    original_database = models_module.db.database
    models_module.db.init(
        path,
        pragmas={"journal_mode": "wal", "busy_timeout": 5000, "foreign_keys": 1},
    )

    yield path

    models_module.db.close()
    models_module.db.init(original_database)
    if os.path.exists(path):
        os.remove(path)
    # SQLite WAL mode also creates -wal/-shm sidecar files
    for suffix in ("-wal", "-shm"):
        sidecar = path + suffix
        if os.path.exists(sidecar):
            os.remove(sidecar)


def test_init_db_applies_wal_journal_mode(temp_file_db):
    init_db()
    check_db = SqliteDatabase(temp_file_db)
    check_db.connect()
    mode = check_db.execute_sql("PRAGMA journal_mode;").fetchone()[0]
    check_db.close()
    assert mode.lower() == "wal"


def test_init_db_applies_foreign_key_enforcement(temp_file_db):
    init_db()
    check_db = SqliteDatabase(temp_file_db, pragmas={"foreign_keys": 1})
    check_db.connect()
    enforced = check_db.execute_sql("PRAGMA foreign_keys;").fetchone()[0]
    check_db.close()
    assert enforced == 1


@pytest.mark.skipif(os.name != "posix", reason="0600 permission check is POSIX-only")
def test_init_db_sets_owner_only_file_permissions(temp_file_db):
    init_db()
    mode = oct(os.stat(temp_file_db).st_mode)[-3:]
    assert mode == "600"
