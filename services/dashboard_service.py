"""Fast aggregate queries used by the dashboard pages."""

from database.db import db_session
from database.schema import initialize_schema
from constants import LOW_STOCK_THRESHOLD


def staff_dashboard_summary() -> dict:
    """Return all Staff dashboard metrics using one database connection."""
    initialize_schema()
    with db_session() as conn:
        orders = conn.execute(
            """
            SELECT
                COUNT(*) FILTER (WHERE status NOT IN ('Completed', 'Cancelled')) AS active,
                COUNT(*) FILTER (WHERE status = 'Pending') AS pending,
                COUNT(*) FILTER (WHERE status = 'Ready for Loading') AS ready,
                COUNT(*) FILTER (WHERE status = 'Completed') AS completed
            FROM seafood_orders
            """
        ).fetchone()
        seafood = conn.execute(
            """
            SELECT
                COUNT(*) AS total,
                COUNT(*) FILTER (
                    WHERE availability_status = 'Available'
                      AND stock_quantity > 0
                      AND stock_quantity <= ?
                ) AS low_stock,
                COUNT(*) FILTER (
                    WHERE availability_status = 'Available' AND stock_quantity <= 0
                ) AS out_of_stock
            FROM seafood_products
            """,
            (LOW_STOCK_THRESHOLD,),
        ).fetchone()
        lorries = conn.execute(
            "SELECT COUNT(*) AS total FROM lorry_profiles WHERE status = 'Available'"
        ).fetchone()
        boxes = conn.execute(
            """
            SELECT COALESCE(SUM(GREATEST(0, b.inventory_quantity - COALESCE(r.reserved, 0))), 0) AS total
            FROM box_profiles b
            LEFT JOIN (
                SELECT r.box_profile_id, SUM(r.quantity) AS reserved
                FROM order_box_requirements r
                JOIN seafood_orders o ON o.order_id = r.order_id
                WHERE o.status NOT IN ('Completed', 'Cancelled')
                GROUP BY r.box_profile_id
            ) r ON r.box_profile_id = b.box_profile_id
            WHERE b.status = 'Active'
            """
        ).fetchone()
        plans = conn.execute("SELECT COUNT(*) AS total FROM loading_plans").fetchone()

    return {
        "active_orders": int(orders["active"] or 0),
        "seafood_products": int(seafood["total"] or 0),
        "low_or_no_stock": int(seafood["low_stock"] or 0) + int(seafood["out_of_stock"] or 0),
        "available_lorries": int(lorries["total"] or 0),
        "available_boxes": int(boxes["total"] or 0),
        "saved_plans": int(plans["total"] or 0),
    }
