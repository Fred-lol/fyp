"""Customer-scoped persistent seafood favorites."""

from database.db import db_session
from database.schema import initialize_schema


def list_favorite_product_ids(customer_id: int) -> set[int]:
    """Load favorite product ids for one authenticated customer."""
    initialize_schema()
    with db_session() as conn:
        rows = conn.execute(
            """SELECT f.product_id FROM customer_favorites f
               JOIN users u ON u.user_id=f.user_id
               WHERE f.user_id=? AND u.role='Customer'""",
            (int(customer_id),),
        ).fetchall()
    return {int(row["product_id"]) for row in rows}


def set_favorite(customer_id: int, product_id: int, favorite: bool) -> tuple[bool, str]:
    """Persist a favorite change after checking the account is a customer."""
    initialize_schema()
    try:
        with db_session() as conn:
            account = conn.execute(
                "SELECT user_id FROM users WHERE user_id=? AND role='Customer' AND status='Active'",
                (int(customer_id),),
            ).fetchone()
            if not account:
                return False, "Sign in with an active customer account to manage favorites."
            if favorite:
                product = conn.execute(
                    "SELECT product_id FROM seafood_products WHERE product_id=?",
                    (int(product_id),),
                ).fetchone()
                if not product:
                    return False, "This seafood product is no longer available."
                conn.execute(
                    "INSERT INTO customer_favorites(user_id,product_id) VALUES(?,?) ON CONFLICT(user_id,product_id) DO NOTHING",
                    (int(customer_id), int(product_id)),
                )
            else:
                conn.execute(
                    "DELETE FROM customer_favorites WHERE user_id=? AND product_id=?",
                    (int(customer_id), int(product_id)),
                )
        return True, "Favorite saved." if favorite else "Removed from favorites."
    except (TypeError, ValueError):
        return False, "Invalid customer or seafood product."
