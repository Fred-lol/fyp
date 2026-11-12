"""PostgreSQL connection utilities for AquaLoad.

The application connects directly to the PostgreSQL database provisioned by
Supabase. Keep the connection string in ``SUPABASE_DB_URL`` (preferred) or
``DATABASE_URL``; neither value belongs in source control.
"""

from contextlib import contextmanager
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from psycopg import connect
from psycopg.rows import dict_row


PROJECT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_DIR / ".env")
DATABASE_URL = os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL")

# Existing services use cursor.lastrowid. This adapter preserves that service
# contract while issuing PostgreSQL INSERT ... RETURNING queries.
_PRIMARY_KEYS = {
    "users": "user_id", "collection_points": "collection_point_id",
    "seafood_products": "product_id", "seafood_orders": "order_id",
    "order_items": "order_item_id", "order_status_history": "history_id",
    "seafood_stock_movements": "movement_id", "payments": "payment_id",
    "lorry_profiles": "lorry_id", "box_profiles": "box_profile_id",
    "box_inventory_movements": "movement_id", "order_box_requirements": "requirement_id",
    "loading_plans": "plan_id", "box_placements": "placement_id",
    "loading_reports": "report_id", "lorry_locations": "location_id",
}


def _postgres_sql(sql: str) -> str:
    """Translate the project's DB-API qmark placeholders to psycopg format."""
    return sql.replace("?", "%s")


def _returning_sql(sql: str) -> tuple[str, str | None]:
    """Append RETURNING for inserts whose callers expect ``lastrowid``."""
    match = re.match(r"\s*INSERT\s+INTO\s+([a-z_]+)", sql, re.IGNORECASE)
    if not match or re.search(r"\bRETURNING\b", sql, re.IGNORECASE):
        return sql, None
    primary_key = _PRIMARY_KEYS.get(match.group(1).lower())
    if not primary_key:
        return sql, None
    return f"{sql.rstrip().rstrip(';')} RETURNING {primary_key}", primary_key


class PostgresResult:
    def __init__(self, cursor, primary_key: str | None = None):
        self._cursor = cursor
        self._primary_key = primary_key
        self._inserted_row = None

    @property
    def lastrowid(self):
        if not self._primary_key:
            return None
        if self._inserted_row is None:
            self._inserted_row = self._cursor.fetchone()
        return self._inserted_row[self._primary_key] if self._inserted_row else None

    @property
    def rowcount(self):
        return self._cursor.rowcount

    def fetchone(self):
        if self._inserted_row is not None:
            row, self._inserted_row = self._inserted_row, None
            return row
        return self._cursor.fetchone()

    def fetchall(self):
        rows = []
        if self._inserted_row is not None:
            rows.append(self._inserted_row)
            self._inserted_row = None
        return rows + list(self._cursor.fetchall())


class PostgresConnection:
    def __init__(self, connection):
        self._connection = connection

    def execute(self, sql: str, params=None):
        sql, primary_key = _returning_sql(_postgres_sql(sql))
        cursor = self._connection.cursor()
        cursor.execute(sql, params or ())
        return PostgresResult(cursor, primary_key)


def get_connection():
    if not DATABASE_URL:
        raise RuntimeError(
            "Supabase PostgreSQL is not configured. Set SUPABASE_DB_URL in your local .env or deployment secrets."
        )
    return PostgresConnection(connect(DATABASE_URL, row_factory=dict_row))


@contextmanager
def db_session():
    conn = get_connection()
    try:
        yield conn
        conn._connection.commit()
    except Exception:
        conn._connection.rollback()
        raise
    finally:
        conn._connection.close()
