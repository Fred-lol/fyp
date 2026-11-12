"""Safely remove AquaLoad's known seeded demo records from PostgreSQL.

This keeps the Warehouse Administrator account and standard box templates so
the system remains usable after cleanup. It deliberately avoids deleting a
matching seed item when it has non-demo references.
"""

from database.db import db_session
from services.auth_service import create_user
from constants import ROLES


ADMIN_EMAIL = "admin.aquaload@gmail.com"
DEMO_USER_EMAILS = (
    "supervisor.aquaload@gmail.com",
    "supplier.aquaload@gmail.com",
    "demo.customer@gmail.com",
)
DEMO_PRODUCTS = ("Mackerel", "Red Snapper", "Pomfret", "Prawn", "Squid", "Crab")
DEMO_LORRIES = ("JTU 4821", "VCA 1234", "BKM 7788")


def _placeholders(values) -> str:
    return ",".join("?" for _ in values)


def _ids(conn, sql: str, params=(), key="id") -> list[int]:
    return [int(row[key]) for row in conn.execute(sql, params).fetchall()]


def _delete_ids(conn, table: str, column: str, ids: list[int]) -> int:
    if not ids:
        return 0
    result = conn.execute(
        f"DELETE FROM {table} WHERE {column} IN ({_placeholders(ids)})", ids
    )
    return result.rowcount


def ensure_warehouse_administrator() -> bool:
    """Create the documented administrator only when it is absent."""
    with db_session() as conn:
        existing = conn.execute(
            "SELECT user_id FROM users WHERE LOWER(email)=LOWER(?)", (ADMIN_EMAIL,)
        ).fetchone()
    if existing:
        return False

    ok, message = create_user(
        "AquaLoad Warehouse Admin",
        ADMIN_EMAIL,
        "0123000001",
        "Admin12345",
        ROLES["WAREHOUSE_ADMIN"],
        city="Kangar",
        state="Perlis",
        postcode="01000",
    )
    if not ok:
        raise RuntimeError(f"Could not create the administrator: {message}")
    return True


def cleanup_demo_data() -> dict:
    """Delete the known demo workflow while preserving real records and admin."""
    admin_created = ensure_warehouse_administrator()
    summary = {"administrator_created": int(admin_created)}

    with db_session() as conn:
        demo_orders = _ids(
            conn,
            """
            SELECT DISTINCT order_id AS id
            FROM order_status_history
            WHERE POSITION('AQUALOAD_DEMO_ORDER_' IN note)=1
            """,
        )

        # Only delete a plan if every linked order is a marked demo order.
        demo_plans = []
        if demo_orders:
            plan_rows = conn.execute(
                """
                SELECT po.plan_id, COUNT(*) AS linked_orders,
                       COUNT(*) FILTER (WHERE po.order_id IN ("""
                + _placeholders(demo_orders)
                + ")) AS demo_orders "
                  "FROM loading_plan_orders po GROUP BY po.plan_id",
                demo_orders,
            ).fetchall()
            demo_plans = [
                int(row["plan_id"])
                for row in plan_rows
                if int(row["linked_orders"] or 0) == int(row["demo_orders"] or 0)
            ]

        summary["loading_reports"] = _delete_ids(conn, "loading_reports", "plan_id", demo_plans)
        summary["loading_plans"] = _delete_ids(conn, "loading_plans", "plan_id", demo_plans)
        summary["stock_movements"] = _delete_ids(
            conn, "seafood_stock_movements", "reference_order_id", demo_orders
        )
        summary["demo_orders"] = _delete_ids(conn, "seafood_orders", "order_id", demo_orders)

        # Remove only the initial inventory created by the seed script. Standard
        # templates remain so staff can enter genuine box stock later.
        initial_box_rows = conn.execute(
            """
            SELECT DISTINCT m.box_profile_id
            FROM box_inventory_movements m
            WHERE m.movement_type='Initial Stock'
              AND m.note='Initial standardized box inventory.'
              AND NOT EXISTS (
                SELECT 1 FROM box_inventory_movements other
                WHERE other.box_profile_id=m.box_profile_id
                  AND other.movement_id<>m.movement_id
              )
            """
        ).fetchall()
        initial_box_ids = [int(row["box_profile_id"]) for row in initial_box_rows]
        if initial_box_ids:
            conn.execute(
                f"UPDATE box_profiles SET inventory_quantity=0 WHERE box_profile_id IN ({_placeholders(initial_box_ids)})",
                initial_box_ids,
            )
        summary["initial_box_stock"] = _delete_ids(
            conn, "box_inventory_movements", "box_profile_id", initial_box_ids
        )

        product_params = list(DEMO_PRODUCTS)
        product_result = conn.execute(
            """
            DELETE FROM seafood_products p
            WHERE p.product_name IN ("""
            + _placeholders(product_params)
            + ") AND NOT EXISTS (SELECT 1 FROM order_items i WHERE i.product_id=p.product_id)"
              " AND NOT EXISTS (SELECT 1 FROM seafood_stock_movements m WHERE m.product_id=p.product_id)",
            product_params,
        )
        summary["seafood_products"] = product_result.rowcount

        lorry_ids = _ids(
            conn,
            "SELECT lorry_id AS id FROM lorry_profiles WHERE plate_number IN ("
            + _placeholders(DEMO_LORRIES)
            + ")",
            DEMO_LORRIES,
        )
        summary["lorry_locations"] = _delete_ids(conn, "lorry_locations", "lorry_id", lorry_ids)
        lorry_result = conn.execute(
            """
            DELETE FROM lorry_profiles l
            WHERE l.plate_number IN ("""
            + _placeholders(DEMO_LORRIES)
            + ") AND NOT EXISTS (SELECT 1 FROM loading_plans p WHERE p.lorry_id=l.lorry_id)",
            DEMO_LORRIES,
        )
        summary["lorries"] = lorry_result.rowcount

        summary["demo_users"] = conn.execute(
            "DELETE FROM users WHERE LOWER(email) IN ("
            + _placeholders(DEMO_USER_EMAILS)
            + ")",
            DEMO_USER_EMAILS,
        ).rowcount

        collection_result = conn.execute(
            """
            DELETE FROM collection_points cp
            WHERE cp.point_name ~ ' Wholesale Collection Point$'
              AND NOT EXISTS (SELECT 1 FROM seafood_orders o WHERE o.collection_point_id=cp.collection_point_id)
              AND NOT EXISTS (SELECT 1 FROM loading_plans p WHERE p.collection_point_id=cp.collection_point_id)
            """
        )
        summary["collection_points"] = collection_result.rowcount

    return summary


if __name__ == "__main__":
    result = cleanup_demo_data()
    print("Demo cleanup complete.")
    for name, count in result.items():
        print(f"{name}: {count}")
