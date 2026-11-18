"""Apply AquaLoad's idempotent Supabase PostgreSQL schema migration."""

import os
from functools import lru_cache
from pathlib import Path

from database.db import db_session


MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


@lru_cache(maxsize=1)
def initialize_schema():
    """Create the schema for a new Supabase project.

    The SQL is suitable for the Supabase SQL editor. It is idempotent so local
    development can bootstrap a fresh project, while production should apply
    it through the dashboard or CI migration workflow before deployment.
    """
    if os.environ.get("AQUALOAD_SCHEMA_PREPARED") == "1":
        return
    with db_session() as conn:
        for migration in sorted(MIGRATIONS_DIR.glob("*.sql")):
            statements = [
                part.strip()
                for part in migration.read_text(encoding="utf-8").split(";")
                if part.strip()
            ]
            for statement in statements:
                conn.execute(statement)
