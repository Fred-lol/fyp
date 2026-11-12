"""PostgreSQL-only helpers for integration tests."""

import os

import database.db as db
from database.schema import initialize_schema


def reset_test_database():
    """Reset a dedicated disposable test database; never point this at production."""
    url = os.getenv("AQUALOAD_TEST_DATABASE_URL")
    if not url:
        raise RuntimeError("AQUALOAD_TEST_DATABASE_URL is required for database integration tests.")
    db.DATABASE_URL = url
    initialize_schema.cache_clear()
    initialize_schema()
    with db.db_session() as conn:
        conn.execute(
            "TRUNCATE TABLE users, collection_points, seafood_products, lorry_profiles, box_profiles "
            "RESTART IDENTITY CASCADE"
        )
