import logging
import os

from .migrations.runner import run_migrations
from .models import db

logger = logging.getLogger(__name__)


def _secure_db_file_permissions():
    """Restrict shopapps.db to owner read/write only, per
    technical-conventions.md -> Security. POSIX only — Windows relies on
    OS user-profile ACLs by default for MVS, per the same section."""
    if os.name != "posix":
        return
    db_path = db.database
    if db_path and db_path != ":memory:" and os.path.exists(db_path):
        os.chmod(db_path, 0o600)


def init_db():
    """Create/upgrade the database schema via the migration runner (see
    core/db/migrations/), then apply file-permission hardening."""
    run_migrations()
    _secure_db_file_permissions()
    logger.info("Database initialized successfully")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()
