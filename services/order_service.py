from itertools import product as cartesian_product
from contextlib import nullcontext
from math import isfinite
from math import ceil

from database.db import db_session
from database.schema import initialize_schema
from constants import (
    EDITABLE_ORDER_STATUSES,
    CANCELLABLE_ORDER_STATUSES,
    MIN_WHOLESALE_ORDER_KG,
    OPTIMIZATION_ELIGIBLE_STATUSES,
    ORDER_STATUS_TRANSITIONS,
)
from services.collection_point_service import (
    recommend_collection_point,
    get_collection_point,
    is_lorry_delivery_supported,
    is_local_kuala_perlis_pickup,
)
from services.box_service import list_box_inventory


def list_products(search="", category="All", availability="Available"):
    initialize_schema()
    sql = "SELECT * FROM seafood_products WHERE 1=1"
    params = []
    if search.strip():
        sql += " AND LOWER(product_name) LIKE ?"
        params.append(f"%{search.strip().lower()}%")
    if category != "All":
        sql += " AND category=?"
        params.append(category)
    if availability != "All":
        sql += " AND availability_status=?"
        params.append(availability)
    if availability == "Available":
        sql += " AND stock_quantity > 0"
    sql += " ORDER BY product_name"
    with db_session() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def product_categories():
    initialize_schema()
    with db_session() as conn:
        return [r["category"] for r in conn.execute(
            "SELECT DISTINCT category FROM seafood_products ORDER BY category"
        ).fetchall()]


def _record_stock(conn, product_id, change, movement_type, order_id=None, updated_by=None, note=None):
    conn.execute(
        """
        INSERT INTO seafood_stock_movements(
            product_id,quantity_change,movement_type,reference_order_id,updated_by,note
        ) VALUES(?,?,?,?,?,?)
        """,
        (product_id, float(change), movement_type, order_id, updated_by, note),
    )


def _customer(conn, customer_id):
    return conn.execute("SELECT * FROM users WHERE user_id=?", (customer_id,)).fetchone()


def place_order(customer_id, items, collection_point_id=None, *, _connection=None, expected_total=None):
    """Create a Pending order with a chosen collection point and reserve stock.

    ``collection_point_id`` is optional only for older internal callers such
    as seed data. Customer checkout always supplies it before payment.
    """
    initialize_schema()
    requested = {}
    for product_id, quantity in items:
        try:
            quantity = float(quantity)
        except (TypeError, ValueError):
            return False, "Enter a valid seafood quantity.", None
        if not isfinite(quantity) or quantity <= 0:
            return False, "Seafood quantities must be positive finite numbers.", None
        if quantity > 0:
            product_id = int(product_id)
            requested[product_id] = requested.get(product_id, 0.0) + quantity
    clean_items = list(requested.items())
    if not clean_items:
        return False, "Select at least one seafood item.", None
    if any(quantity < MIN_WHOLESALE_ORDER_KG for _, quantity in clean_items):
        return False, f"Each seafood product must be ordered in quantities of at least {MIN_WHOLESALE_ORDER_KG:g} kg.", None

    selected_point_id = None
    if collection_point_id is not None:
        try:
            selected_point_id = int(collection_point_id)
        except (TypeError, ValueError):
            return False, "Select an available collection point before payment.", None

    with (nullcontext(_connection) if _connection is not None else db_session()) as conn:
        customer = _customer(conn, customer_id)
        if not customer or customer["role"] != "Customer" or customer["status"] != "Active":
            return False, "Customer account was not found.", None
        if not is_lorry_delivery_supported(dict(customer)):
            service_area = customer["city"] or customer["state"] or "this location"
            return False, f"Lorry delivery is not available to {service_area}. AquaLoad currently serves West Malaysia road-accessible locations only.", None

        product_ids = [pid for pid, _ in clean_items]
        placeholders = ",".join("?" for _ in product_ids)
        available = {
            r["product_id"]: r
            for r in conn.execute(
                f"SELECT * FROM seafood_products WHERE product_id IN ({placeholders}) ORDER BY product_id FOR UPDATE",
                product_ids,
            ).fetchall()
        }

        for product_id, qty in clean_items:
            seafood = available.get(product_id)
            if not seafood or seafood["availability_status"] != "Available":
                return False, "One of the selected seafood items is no longer available.", None
            stock = float(seafood["stock_quantity"] or 0)
            if qty > stock + 1e-9:
                return False, f"Only {stock:g} {seafood['unit']} of {seafood['product_name']} is currently available.", None

        # Compare the total shown at checkout with authoritative, row-locked
        # prices before creating an order or reserving stock.
        if expected_total is not None:
            try:
                expected_total = float(expected_total)
            except (TypeError, ValueError):
                return False, "The order total is invalid. Return to checkout and review your order.", None
            current_total = sum(
                qty * float(available[product_id]["unit_price"] or 0)
                for product_id, qty in clean_items
            )
            if not isfinite(expected_total) or expected_total <= 0:
                return False, "The order total is invalid. Return to checkout and review your order.", None
            if abs(round(current_total, 2) - round(expected_total, 2)) > 0.009:
                return False, "A seafood price changed while you were checking out. Review the latest total before placing your order.", None

        if selected_point_id is not None:
            selected_point = conn.execute(
                "SELECT * FROM collection_points WHERE collection_point_id=? AND status='Available'",
                (selected_point_id,),
            ).fetchone()
            if not selected_point:
                return False, "The selected collection point is no longer available. Please choose another point.", None
            point = dict(selected_point)
            if (customer["state"] or "").strip() == "Perlis" and point["state"] != "Perlis":
                return False, "Customers registered in Perlis must choose a Perlis pickup point. Lorry delivery is not used for Perlis orders.", None
        else:
            point = recommend_collection_point(dict(customer))
        point_id = point["collection_point_id"] if point else None
        point_name = point["point_name"] if point else None
        local_pickup = bool(point and is_local_kuala_perlis_pickup(dict(customer), point))
        collection_assignment = "Local Pickup" if local_pickup else (
            "Customer Selected" if selected_point_id is not None else "Automatic"
        )

        cur = conn.execute(
            """
            INSERT INTO seafood_orders(
                customer_id,status,collection_point_id,collection_point,collection_assignment
            ) VALUES(?, 'Pending', ?, ?, ?)
            """,
            (customer_id, point_id, point_name, collection_assignment),
        )
        order_id = cur.lastrowid

        for product_id, qty in clean_items:
            seafood = available[product_id]
            conn.execute(
                "INSERT INTO order_items(order_id,product_id,quantity,unit) VALUES(?,?,?,?)",
                (order_id, product_id, qty, seafood["unit"]),
            )
            stock_update = conn.execute(
                """
                UPDATE seafood_products
                SET stock_quantity=stock_quantity-?,updated_at=CURRENT_TIMESTAMP
                WHERE product_id=? AND stock_quantity>=?
                """,
                (qty, product_id, qty),
            )
            if stock_update.rowcount != 1:
                raise RuntimeError("Stock changed while the order was being placed. Please try again.")
            _record_stock(
                conn, product_id, -qty, "Order Reserved", order_id, customer_id,
                f"Reserved for Order #{order_id}.",
            )

        note = "Order submitted by Customer."
        if point:
            if local_pickup:
                note += f" Local pickup is arranged at {point['point_name']}; no lorry delivery is required."
            elif selected_point_id is not None:
                note += f" Customer selected collection point: {point['point_name']}."
            else:
                note += f" Collection point automatically assigned to {point['point_name']} from the Customer's registered location."
        conn.execute(
            "INSERT INTO order_status_history(order_id,status,updated_by,note) VALUES(?,?,?,?)",
            (order_id, "Pending", customer_id, note),
        )

    if local_pickup:
        return True, f"Seafood order placed successfully. Please collect it from {point_name} after staff confirms it; no lorry delivery is required.", order_id
    return True, "Seafood order placed successfully.", order_id


def list_customer_orders(customer_id, view_filter="All"):
    """Return only the authenticated Customer's orders, optionally filtered for My Orders."""
    archive_expired_completed_orders()

    # The UI exposes only these four values. Unknown values safely fall back to All.
    filter_sql = {
        "All": "",
        "Active": " AND o.status NOT IN ('Completed','Cancelled')",
        "Completed": " AND o.status='Completed'",
        "Cancelled": " AND o.status='Cancelled'",
    }.get(view_filter, "")

    sql = f"""
        SELECT o.*,
               COUNT(oi.order_item_id) AS item_count,
               COALESCE(SUM(CASE WHEN oi.unit='kg' THEN oi.quantity ELSE 0 END),0) AS total_weight_kg,
               COALESCE(SUM(oi.quantity * COALESCE(p.unit_price,0)),0) AS order_total_amount,
               COALESCE(pay.payment_status,'Not Paid') AS payment_status,
               pay.payment_method, pay.transaction_reference
        FROM seafood_orders o
        LEFT JOIN order_items oi ON oi.order_id=o.order_id
        LEFT JOIN seafood_products p ON p.product_id=oi.product_id
        LEFT JOIN payments pay ON pay.order_id=o.order_id
        WHERE o.customer_id=? AND (o.archived_at IS NULL OR o.status='Cancelled')
        {filter_sql}
        GROUP BY o.order_id, pay.payment_id
        ORDER BY o.order_date DESC, o.order_id DESC
    """

    with db_session() as conn:
        rows = conn.execute(sql, (customer_id,)).fetchall()

    return [dict(r) for r in rows]


def get_order(order_id, customer_id=None):
    initialize_schema()
    sql = """
        SELECT o.*, u.full_name customer_name, u.email customer_email,
               u.phone_number customer_phone, u.address customer_address,
               u.city customer_city, u.state customer_state, u.postcode customer_postcode,
               cp.point_name collection_point_name, cp.address collection_point_address,
               cp.city collection_point_city, cp.state collection_point_state,
               cp.latitude collection_point_latitude, cp.longitude collection_point_longitude
        FROM seafood_orders o
        JOIN users u ON u.user_id=o.customer_id
        LEFT JOIN collection_points cp ON cp.collection_point_id=o.collection_point_id
        WHERE o.order_id=?
    """
    params = [order_id]
    if customer_id is not None:
        sql += " AND o.customer_id=?"
        params.append(customer_id)

    with db_session() as conn:
        order = conn.execute(sql, params).fetchone()
        if not order:
            return None
        items = conn.execute(
            """
            SELECT oi.order_item_id, oi.product_id, p.product_name, p.category,
                   oi.quantity, oi.unit, p.unit_price,
                   (oi.quantity * COALESCE(p.unit_price,0)) AS line_total,
                   p.stock_quantity current_stock, p.availability_status
            FROM order_items oi
            JOIN seafood_products p ON p.product_id=oi.product_id
            WHERE oi.order_id=?
            ORDER BY p.product_name
            """,
            (order_id,),
        ).fetchall()
        history = conn.execute(
            """
            SELECT h.*, COALESCE(u.full_name,'System') updated_by_name
            FROM order_status_history h
            LEFT JOIN users u ON u.user_id=h.updated_by
            WHERE h.order_id=?
            ORDER BY h.updated_at ASC, h.history_id ASC
            """,
            (order_id,),
        ).fetchall()
        reqs = conn.execute(
            """
            SELECT r.*, b.box_name, b.capacity_litre, b.length, b.width, b.height,
                   b.max_seafood_weight_kg
            FROM order_box_requirements r
            JOIN box_profiles b ON b.box_profile_id=r.box_profile_id
            WHERE r.order_id=?
            ORDER BY b.capacity_litre DESC
            """,
            (order_id,),
        ).fetchall()
        payment = conn.execute(
            "SELECT * FROM payments WHERE order_id=?",
            (order_id,),
        ).fetchone()

    result = dict(order)
    result["items"] = [dict(r) for r in items]
    result["history"] = [dict(r) for r in history]
    result["box_requirements"] = [dict(r) for r in reqs]
    result["total_weight_kg"] = round(sum(float(i["quantity"]) for i in result["items"] if i["unit"] == "kg"), 3)
    result["total_amount"] = round(sum(float(i.get("line_total") or 0) for i in result["items"]), 2)
    result["payment"] = dict(payment) if payment else None
    return result


def update_customer_order(order_id, customer_id, quantities):
    order = get_order(order_id, customer_id)
    if not order:
        return False, "Order not found."
    if order["status"] not in EDITABLE_ORDER_STATUSES:
        return False, "This order can no longer be updated."
    if (order.get("payment") or {}).get("payment_status") in {"Paid", "Simulated"}:
        return False, "Paid orders are locked. You may cancel before the seafood is loaded for delivery."

    current = {item["order_item_id"]: item for item in order["items"]}
    proposed = {
        oid: max(0.0, float(quantities.get(oid, item["quantity"])))
        for oid, item in current.items()
    }
    if not any(qty > 0 for qty in proposed.values()):
        return False, "An order must contain at least one item."

    with db_session() as conn:
        for order_item_id, new_qty in proposed.items():
            item = current[order_item_id]
            old_qty = float(item["quantity"])
            delta = new_qty - old_qty
            if delta > 0:
                seafood = conn.execute("SELECT * FROM seafood_products WHERE product_id=?", (item["product_id"],)).fetchone()
                if not seafood or seafood["availability_status"] != "Available":
                    return False, f"{item['product_name']} is no longer available."
                stock = float(seafood["stock_quantity"] or 0)
                if delta > stock + 1e-9:
                    return False, f"Only {stock:g} {item['unit']} additional {item['product_name']} is available."

        for order_item_id, new_qty in proposed.items():
            item = current[order_item_id]
            old_qty = float(item["quantity"])
            delta = new_qty - old_qty
            if abs(delta) < 1e-9:
                continue
            conn.execute(
                "UPDATE seafood_products SET stock_quantity=stock_quantity-?,updated_at=CURRENT_TIMESTAMP WHERE product_id=?",
                (delta, item["product_id"]),
            )
            _record_stock(
                conn, item["product_id"], -delta, "Order Updated", order_id, customer_id,
                f"Order #{order_id} quantity changed.",
            )
            if new_qty <= 0:
                conn.execute("DELETE FROM order_items WHERE order_item_id=? AND order_id=?", (order_item_id, order_id))
            else:
                conn.execute(
                    "UPDATE order_items SET quantity=? WHERE order_item_id=? AND order_id=?",
                    (new_qty, order_item_id, order_id),
                )
        conn.execute("UPDATE seafood_orders SET updated_at=CURRENT_TIMESTAMP WHERE order_id=?", (order_id,))
        updated_amount = conn.execute(
            """
            SELECT COALESCE(SUM(oi.quantity * COALESCE(p.unit_price,0)),0) amount
            FROM order_items oi
            JOIN seafood_products p ON p.product_id=oi.product_id
            WHERE oi.order_id=?
            """,
            (order_id,),
        ).fetchone()["amount"]
        conn.execute(
            "UPDATE payments SET amount=? WHERE order_id=?",
            (float(updated_amount or 0), order_id),
        )
    return True, "Order updated successfully."


def _restore_order_stock(conn, order_id, updated_by, movement_type="Order Cancelled"):
    items = conn.execute("SELECT product_id,quantity FROM order_items WHERE order_id=?", (order_id,)).fetchall()
    for item in items:
        qty = float(item["quantity"])
        conn.execute(
            "UPDATE seafood_products SET stock_quantity=stock_quantity+?,updated_at=CURRENT_TIMESTAMP WHERE product_id=?",
            (qty, item["product_id"]),
        )
        _record_stock(
            conn, item["product_id"], qty, movement_type, order_id, updated_by,
            f"Stock restored from Order #{order_id}.",
        )


def cancellation_customer_message(payment_status=None, *, by_staff=False):
    """Customer notice for a simulated cancellation; no financial refund occurs."""
    if by_staff:
        return "Your order has been cancelled. Refund will be processed within 14 days (demo simulation)."
    return "Order cancelled successfully. Refund will be processed within 14 days (demo simulation)."


def cancel_order(order_id, customer_id):
    with db_session() as conn:
        order = conn.execute(
            "SELECT status FROM seafood_orders WHERE order_id=? AND customer_id=? FOR UPDATE",
            (order_id, customer_id),
        ).fetchone()
        if not order:
            return False, "Order not found."
        if order["status"] not in CANCELLABLE_ORDER_STATUSES:
            return False, "This order can no longer be cancelled."
        _restore_order_stock(conn, order_id, customer_id)
        conn.execute(
            """
            UPDATE seafood_orders
            SET status='Cancelled', archived_at=CURRENT_TIMESTAMP, updated_at=CURRENT_TIMESTAMP
            WHERE order_id=?
            """,
            (order_id,),
        )
        conn.execute("UPDATE payments SET payment_status='Demo Refund Pending' WHERE order_id=? AND payment_status IN ('Paid','Simulated')", (order_id,))
        conn.execute(
            "INSERT INTO order_status_history(order_id,status,updated_by,note) VALUES(?,?,?,?)",
            (order_id, "Cancelled", customer_id, cancellation_customer_message()),
        )
    return True, cancellation_customer_message()


def archive_expired_completed_orders():
    """Keep completed and cancelled orders in the database but outside normal views."""
    initialize_schema()
    with db_session() as conn:
        conn.execute(
            """
            UPDATE seafood_orders
            SET archived_at=CURRENT_TIMESTAMP
            WHERE status IN ('Completed','Cancelled')
              AND archived_at IS NULL
            """
        )


def _release_lorry_after_completed_trip(conn, order_id):
    """Release the trip's lorry only once every order on that plan is final."""
    trip = conn.execute(
        """
        SELECT p.plan_id,p.lorry_id,l.plate_number
        FROM loading_plan_orders po
        JOIN loading_plans p ON p.plan_id=po.plan_id
        JOIN lorry_profiles l ON l.lorry_id=p.lorry_id
        WHERE po.order_id=?
        ORDER BY p.created_at DESC,p.plan_id DESC
        LIMIT 1
        """,
        (order_id,),
    ).fetchone()
    if not trip:
        return None

    still_active = conn.execute(
        """
        SELECT 1
        FROM loading_plan_orders po
        JOIN seafood_orders o ON o.order_id=po.order_id
        WHERE po.plan_id=? AND o.status NOT IN ('Completed','Cancelled')
        LIMIT 1
        """,
        (trip["plan_id"],),
    ).fetchone()
    if still_active:
        return None

    released = conn.execute(
        """
        UPDATE lorry_profiles
        SET status='Available',updated_at=CURRENT_TIMESTAMP
        WHERE lorry_id=? AND status='In Transit'
        """,
        (trip["lorry_id"],),
    )
    return trip["plate_number"] if released.rowcount else None


def list_all_orders(status="All", search="", archived_only=False):
    archive_expired_completed_orders()
    sql = """
        SELECT o.order_id, o.order_date, o.status, o.collection_point, o.collection_assignment,
               o.updated_at, u.full_name customer_name, u.email customer_email,
               u.city customer_city, u.state customer_state,
               COUNT(oi.order_item_id) item_count,
               COALESCE(SUM(oi.quantity),0) total_weight_kg,
               COALESCE(SUM(oi.quantity * COALESCE(p.unit_price,0)),0) order_total_amount,
               COALESCE(pay.payment_status,'Not Paid') payment_status
        FROM seafood_orders o
        JOIN users u ON u.user_id=o.customer_id
        LEFT JOIN order_items oi ON oi.order_id=o.order_id
        LEFT JOIN seafood_products p ON p.product_id=oi.product_id
        LEFT JOIN payments pay ON pay.order_id=o.order_id
        WHERE 1=1
    """
    params = []
    sql += " AND o.archived_at IS NOT NULL" if archived_only else " AND o.archived_at IS NULL"
    if status != "All":
        sql += " AND o.status=?"
        params.append(status)
    if search.strip():
        q = f"%{search.strip().lower()}%"
        sql += " AND (CAST(o.order_id AS TEXT) LIKE ? OR LOWER(u.full_name) LIKE ? OR LOWER(u.email) LIKE ?)"
        params += [q, q, q]
    sql += " GROUP BY o.order_id,u.user_id,pay.payment_id ORDER BY o.order_date DESC"
    with db_session() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def order_counts():
    archive_expired_completed_orders()
    with db_session() as conn:
        total_active = conn.execute("SELECT COUNT(*) c FROM seafood_orders WHERE archived_at IS NULL AND status NOT IN ('Completed','Cancelled')").fetchone()["c"]
        pending = conn.execute("SELECT COUNT(*) c FROM seafood_orders WHERE archived_at IS NULL AND status='Pending'").fetchone()["c"]
        ready = conn.execute("SELECT COUNT(*) c FROM seafood_orders WHERE archived_at IS NULL AND status='Ready for Loading'").fetchone()["c"]
        completed = conn.execute("SELECT COUNT(*) c FROM seafood_orders WHERE archived_at IS NULL AND status='Completed'").fetchone()["c"]
    return {"active": total_active, "pending": pending, "ready": ready, "completed": completed}


def allowed_next_statuses(current_status):
    return ORDER_STATUS_TRANSITIONS.get(current_status, [])


def _validate_saved_box_requirements(conn, order_id, order=None):
    """Validate persisted box assignments before an order can enter loading."""
    order = order or conn.execute(
        "SELECT * FROM seafood_orders WHERE order_id=? FOR UPDATE", (order_id,)
    ).fetchone()
    if not order:
        return "Order not found."
    if order.get("archived_at"):
        return "Archived orders are read-only."
    if order.get("collection_assignment") == "Local Pickup":
        return "Local pickup orders do not enter lorry loading."
    if not order.get("collection_point_id"):
        return "The order needs a collection point before loading can be prepared."
    payment = conn.execute(
        "SELECT payment_status FROM payments WHERE order_id=?", (order_id,)
    ).fetchone()
    if not payment or payment["payment_status"] not in {"Paid", "Simulated"}:
        return "A successful payment is required before loading can be prepared."
    total_weight = float(conn.execute(
        "SELECT COALESCE(SUM(CASE WHEN unit='kg' THEN quantity ELSE 0 END),0) total_weight "
        "FROM order_items WHERE order_id=?", (order_id,)
    ).fetchone()["total_weight"] or 0)
    if not isfinite(total_weight) or total_weight <= 0:
        return "The order must have a valid seafood weight greater than 0 kg."

    requirements = conn.execute(
        """
        SELECT r.box_profile_id,r.quantity,b.box_name,b.capacity_litre,
               b.max_seafood_weight_kg,b.inventory_quantity,b.status
        FROM order_box_requirements r
        JOIN box_profiles b ON b.box_profile_id=r.box_profile_id
        WHERE r.order_id=?
        ORDER BY b.box_profile_id
        """, (order_id,)
    ).fetchall()
    if not requirements:
        return "Save sufficient box requirements first. The order will become Ready for Loading after they are saved."

    capacity = 0.0
    shortages = []
    for req in requirements:
        quantity = int(req["quantity"] or 0)
        per_box = float(req["max_seafood_weight_kg"] or 0)
        if quantity <= 0 or per_box <= 0 or req["status"] != "Active":
            return f"{req['box_name']} is inactive or has invalid quantity/capacity. Update the box requirement."
        capacity += quantity * per_box
        reserved = conn.execute(
            """
            SELECT COALESCE(SUM(r.quantity),0) reserved
            FROM order_box_requirements r
            JOIN seafood_orders o ON o.order_id=r.order_id
            WHERE r.box_profile_id=? AND o.status NOT IN ('Completed','Cancelled') AND o.order_id<>?
            """, (req["box_profile_id"], order_id)
        ).fetchone()["reserved"]
        available = max(0, int(req["inventory_quantity"] or 0) - int(reserved or 0))
        if quantity > available:
            shortages.append(
                f"{req['box_name']} ({int(req['capacity_litre'])}L): need {quantity}, only {available} available"
            )
    if capacity + 1e-9 < total_weight:
        return f"Insufficient box capacity. {total_weight - capacity:g} kg of seafood still requires box capacity."
    if shortages:
        return "Insufficient box inventory: " + "; ".join(shortages) + "."
    return None


def update_order_status(order_id, new_status, updated_by, note=""):
    """Advance an order through verified operational stages."""
    with db_session() as conn:
        order = conn.execute("SELECT * FROM seafood_orders WHERE order_id=? FOR UPDATE", (order_id,)).fetchone()
        if not order:
            return False, "Order not found."
        current_status = order["status"]
        if current_status == new_status:
            if new_status == "Cancelled":
                return False, "This order is already cancelled."
            return True, "Order status is already up to date."
        allowed = allowed_next_statuses(current_status)
        if new_status not in allowed:
            return False, f"Order cannot move directly from {current_status} to {new_status}."
        if new_status == "Confirmed":
            confirmation_note = note.strip() or "Order confirmed by Staff."
            conn.execute(
                "UPDATE seafood_orders SET status='Confirmed',updated_at=CURRENT_TIMESTAMP WHERE order_id=?",
                (order_id,),
            )
            conn.execute(
                "INSERT INTO order_status_history(order_id,status,updated_by,note) VALUES(?,?,?,?)",
                (order_id, "Confirmed", updated_by, confirmation_note),
            )
            if order["collection_assignment"] == "Local Pickup":
                pickup_note = (
                    f"Ready for pickup at {order['collection_point'] or 'the selected Perlis collection point'}. "
                    "No lorry delivery is required."
                )
                conn.execute(
                    "UPDATE seafood_orders SET status='Ready for Pickup',updated_at=CURRENT_TIMESTAMP WHERE order_id=?",
                    (order_id,),
                )
                conn.execute(
                    "INSERT INTO order_status_history(order_id,status,updated_by,note) VALUES(?,?,?,?)",
                    (order_id, "Ready for Pickup", updated_by, pickup_note),
                )
                return True, "Order confirmed and marked Ready for Pickup at LKIM Fisheries Complex Kuala Perlis. No lorry is required."
            return True, "Order confirmed. Save sufficient box requirements to mark it Ready for Loading."
        if new_status == "Ready for Loading":
            validation = _validate_saved_box_requirements(conn, order_id, order)
            if validation:
                return False, validation
        if new_status == "Cancelled":
            cancellation_notice = cancellation_customer_message(by_staff=True)
            _restore_order_stock(conn, order_id, updated_by, "Staff Cancellation")
            conn.execute("UPDATE payments SET payment_status='Demo Refund Pending' WHERE order_id=? AND payment_status IN ('Paid','Simulated')", (order_id,))
        conn.execute(
            """
            UPDATE seafood_orders
            SET status=?,completed_at=CASE WHEN ?='Completed' THEN CURRENT_TIMESTAMP ELSE completed_at END,
                archived_at=CASE WHEN ? IN ('Completed','Cancelled') THEN CURRENT_TIMESTAMP ELSE archived_at END,
                updated_at=CURRENT_TIMESTAMP
            WHERE order_id=?
            """,
            (new_status, new_status, new_status, order_id),
        )
        status_note = (
            cancellation_notice if new_status == "Cancelled"
            else note.strip() or f"Status manually updated from {current_status} to {new_status}."
        )
        conn.execute(
            "INSERT INTO order_status_history(order_id,status,updated_by,note) VALUES(?,?,?,?)",
            (order_id, new_status, updated_by, status_note),
        )
        released_lorry = _release_lorry_after_completed_trip(conn, order_id) if new_status == "Completed" else None
    if new_status == "Completed":
        message = "Order completed and archived from normal views."
        if released_lorry:
            message += f" Lorry {released_lorry} is now Available for its next trip."
        return True, message
    if new_status == "Cancelled":
        return True, "Order cancelled. The customer cancellation notice is available in My Orders."
    return True, "Order status updated successfully."


def set_collection_point(order_id, collection_point_id, updated_by=None):
    point = get_collection_point(collection_point_id)
    if not point or point["status"] != "Available":
        return False, "Select an available collection point."
    with db_session() as conn:
        customer = conn.execute(
            "SELECT u.state FROM seafood_orders o JOIN users u ON u.user_id=o.customer_id WHERE o.order_id=?",
            (order_id,),
        ).fetchone()
        if customer and (customer["state"] or "").strip() == "Perlis" and point["state"] != "Perlis":
            return False, "Perlis orders must remain at a Perlis pickup point. They cannot be assigned to a lorry route."
        assignment = "Local Pickup" if customer and is_local_kuala_perlis_pickup(dict(customer), point) else "Staff Override"
        result = conn.execute(
            """
            UPDATE seafood_orders
            SET collection_point_id=?,collection_point=?,collection_assignment=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE order_id=? AND archived_at IS NULL
            """,
            (collection_point_id, point["point_name"], assignment, order_id),
        )
        if result.rowcount != 1:
            return False, "Archived orders are read-only."
    if assignment == "Local Pickup":
        return True, f"Collection point updated. This is a Perlis pickup order at {point['point_name']}; no lorry is required."
    return True, "Collection point updated successfully."


def _active_box_templates_for_order(order_id):
    return list_box_inventory(exclude_order_id=order_id)


def recommend_box_combinations(order_id, limit=3):
    """Recommend standardized box combinations for the order's total kg.

    Ranking:
      1) enough total capacity
      2) available physical inventory
      3) fewest boxes
      4) least unused kg capacity
      5) prefer larger templates when otherwise equivalent
    """
    order = get_order(order_id)
    if not order:
        return []
    total_weight = float(order["total_weight_kg"] or 0)
    if total_weight <= 0:
        return []

    templates = [b for b in _active_box_templates_for_order(order_id) if int(b["available_quantity"]) > 0]
    if not templates:
        return []

    # Search only quantities necessary to cover the order. This keeps the
    # combination search small for the four standard AquaLoad templates.
    ranges = []
    for b in templates:
        capacity = max(1.0, float(b["max_seafood_weight_kg"] or 0))
        max_needed = int(total_weight // capacity) + 2
        ranges.append(range(0, min(int(b["available_quantity"]), max_needed) + 1))

    candidates = []
    for quantities in cartesian_product(*ranges):
        box_count = sum(quantities)
        if box_count <= 0:
            continue
        total_capacity = sum(
            qty * float(b["max_seafood_weight_kg"])
            for qty, b in zip(quantities, templates)
        )
        if total_capacity + 1e-9 < total_weight:
            continue
        selected = []
        for qty, b in zip(quantities, templates):
            if qty:
                selected.append({
                    "box_profile_id": b["box_profile_id"],
                    "box_name": b["box_name"],
                    "capacity_litre": b["capacity_litre"],
                    "quantity": int(qty),
                    "capacity_per_box_kg": float(b["max_seafood_weight_kg"]),
                    "dimensions": f"{b['length']:g} × {b['width']:g} × {b['height']:g} cm",
                })
        # Larger boxes are preferred as a final tie-breaker.
        larger_score = -sum(qty * float(b["capacity_litre"] or 0) ** 2 for qty, b in zip(quantities, templates))
        candidates.append({
            "boxes": sorted(selected, key=lambda x: x["capacity_litre"], reverse=True),
            "box_count": box_count,
            "total_capacity_kg": total_capacity,
            "unused_capacity_kg": total_capacity - total_weight,
            "total_weight_kg": total_weight,
            "_score": (box_count, round(total_capacity - total_weight, 6), larger_score),
        })

    candidates.sort(key=lambda c: c["_score"])
    for c in candidates:
        c.pop("_score", None)
    return candidates[:limit]


def box_requirement_shortage_message(order_id):
    """Describe the optimal physical-box shortfall when an order cannot be packed."""
    order = get_order(order_id)
    if not order:
        return "Order not found."
    total_weight = float(order["total_weight_kg"] or 0)
    templates = [
        box for box in _active_box_templates_for_order(order_id)
        if float(box.get("max_seafood_weight_kg") or 0) > 0
    ]
    if not templates:
        return "No active box templates with a maximum seafood weight are available."

    ranges = [
        range(0, max(1, int(ceil(total_weight / float(box["max_seafood_weight_kg"])))) + 1)
        for box in templates
    ]
    candidates = []
    for quantities in cartesian_product(*ranges):
        box_count = sum(quantities)
        total_capacity = sum(
            quantity * float(box["max_seafood_weight_kg"])
            for quantity, box in zip(quantities, templates)
        )
        if box_count and total_capacity + 1e-9 >= total_weight:
            candidates.append((box_count, total_capacity - total_weight, quantities))
    if not candidates:
        return "No active box combination can safely carry this order's seafood weight."

    _, _, quantities = min(candidates, key=lambda item: (item[0], item[1]))
    required, shortages = [], []
    for quantity, box in zip(quantities, templates):
        if not quantity:
            continue
        available = int(box.get("available_quantity") or 0)
        label = f"{int(quantity)} × {int(box['capacity_litre'])}L {box['box_name']}"
        required.append(label)
        if quantity > available:
            shortages.append(
                f"{int(quantity - available)} × {int(box['capacity_litre'])}L {box['box_name']} "
                f"(need {int(quantity)}, available {available})"
            )
    if shortages:
        return f"Insufficient physical boxes. Required: {', '.join(required)}. Short: {', '.join(shortages)}."
    return "Box availability changed. Refresh the recommendation and try again."


def _allocate_loaded_weights(total_weight, selected_boxes):
    remaining = float(total_weight)
    allocations = []
    for box in sorted(selected_boxes, key=lambda b: b["capacity_per_box_kg"], reverse=True):
        qty = int(box["quantity"])
        cap = float(box["capacity_per_box_kg"])
        weights = []
        for _ in range(qty):
            load = min(cap, max(0.0, remaining))
            remaining -= load
            weights.append(load)
        allocations.append((box, weights))
    return allocations


def box_requirement_capacity(order_weight_kg, selected_boxes):
    """Return selected seafood capacity, remaining order weight, and excess capacity."""
    order_weight = float(order_weight_kg or 0)
    capacity = sum(
        float(box.get("capacity_per_box_kg") or 0) * int(box.get("quantity") or 0)
        for box in selected_boxes
    )
    return capacity, max(0.0, order_weight - capacity), max(0.0, capacity - order_weight)


def save_box_combination(order_id, selected_boxes, updated_by=None):
    """Validate, reserve and save boxes while advancing Confirmed orders atomically."""
    if not selected_boxes:
        return False, "Select at least one box before saving the requirement."

    requested = {}
    for box in selected_boxes:
        try:
            profile_id = int(box["box_profile_id"])
            raw_quantity = box["quantity"]
            quantity = int(raw_quantity)
            if quantity != raw_quantity or quantity <= 0:
                raise ValueError
        except (KeyError, TypeError, ValueError, OverflowError):
            return False, "Box quantities must be whole numbers greater than 0."
        if profile_id in requested:
            return False, "Each box size can be selected only once. Combine duplicate quantities and try again."
        requested[profile_id] = quantity

    try:
        with db_session() as conn:
            # Lock the order first. A concurrent cancellation, confirmation or
            # box save must serialize with this transaction.
            order = conn.execute(
                "SELECT * FROM seafood_orders WHERE order_id=? FOR UPDATE", (order_id,)
            ).fetchone()
            if not order:
                return False, "Order not found."
            if order.get("archived_at"):
                return False, "Archived orders are read-only."
            if order["status"] not in {"Confirmed", "Ready for Loading"}:
                return False, (
                    "Only confirmed orders can save lorry box requirements. "
                    f"This order is {order['status']}."
                )
            if order.get("collection_assignment") == "Local Pickup":
                return False, "Local pickup orders do not need boxes or lorry loading."
            if not order.get("collection_point_id"):
                return False, "The customer must choose a collection point before box requirements can be saved."
            payment = conn.execute(
                "SELECT payment_status FROM payments WHERE order_id=?", (order_id,)
            ).fetchone()
            if not payment or payment["payment_status"] not in {"Paid", "Simulated"}:
                return False, "A successful payment is required before saving box requirements."
            total_weight = float(conn.execute(
                "SELECT COALESCE(SUM(CASE WHEN unit='kg' THEN quantity ELSE 0 END),0) total_weight "
                "FROM order_items WHERE order_id=?", (order_id,)
            ).fetchone()["total_weight"] or 0)
            if not isfinite(total_weight) or total_weight <= 0:
                return False, "The order must have a valid seafood weight greater than 0 kg."

            canonical_boxes, shortages = [], []
            # Lock each selected template in stable order to prevent concurrent
            # assignments from over-reserving the same physical inventory.
            for profile_id, quantity in sorted(requested.items()):
                current_box = conn.execute(
                    "SELECT * FROM box_profiles WHERE box_profile_id=? FOR UPDATE", (profile_id,)
                ).fetchone()
                if not current_box or current_box["status"] != "Active":
                    return False, "A selected box template is no longer available. Refresh and try again."
                capacity = float(current_box.get("max_seafood_weight_kg") or 0)
                if not isfinite(capacity) or capacity <= 0:
                    return False, f"{current_box['box_name']} has no valid seafood weight capacity configured."
                reserved = conn.execute(
                    """
                    SELECT COALESCE(SUM(r.quantity),0) reserved
                    FROM order_box_requirements r
                    JOIN seafood_orders o ON o.order_id=r.order_id
                    WHERE r.box_profile_id=? AND o.status NOT IN ('Completed','Cancelled')
                      AND o.order_id<>?
                    """, (profile_id, order_id)
                ).fetchone()["reserved"]
                available = max(0, int(current_box.get("inventory_quantity") or 0) - int(reserved or 0))
                if quantity > available:
                    shortages.append(
                        f"{current_box['box_name']} ({int(current_box['capacity_litre'])}L): "
                        f"need {quantity}, only {available} available"
                    )
                canonical_boxes.append({
                    "box_profile_id": profile_id,
                    "box_name": current_box["box_name"],
                    "capacity_litre": current_box["capacity_litre"],
                    "quantity": quantity,
                    "capacity_per_box_kg": capacity,
                    "dimensions": f"{current_box['length']:g} × {current_box['width']:g} × {current_box['height']:g} cm",
                })

            total_capacity, remaining, _unused = box_requirement_capacity(total_weight, canonical_boxes)
            if remaining > 1e-9:
                return False, (
                    f"Insufficient box capacity. {remaining:g} kg of seafood still requires box capacity "
                    f"({total_capacity:g} kg selected for a {total_weight:g} kg order)."
                )
            if shortages:
                return False, "Insufficient box inventory: " + "; ".join(shortages) + "."

            if order["status"] == "Confirmed":
                changed = conn.execute(
                    """
                    UPDATE seafood_orders
                    SET status='Ready for Loading',updated_at=CURRENT_TIMESTAMP
                    WHERE order_id=? AND status='Confirmed' AND archived_at IS NULL
                    """, (order_id,)
                )
                if changed.rowcount != 1:
                    return False, "The order status changed while saving. Refresh and try again."
                prior_ready_history = conn.execute(
                    "SELECT history_id FROM order_status_history WHERE order_id=? AND status='Ready for Loading' LIMIT 1",
                    (order_id,),
                ).fetchone()
                if not prior_ready_history:
                    conn.execute(
                        "INSERT INTO order_status_history(order_id,status,updated_by,note) VALUES(?,?,?,?)",
                        (order_id, "Ready for Loading", updated_by,
                         "Box requirements validated and saved; order is ready for loading."),
                    )

            allocations = _allocate_loaded_weights(total_weight, canonical_boxes)
            conn.execute("DELETE FROM order_box_requirements WHERE order_id=?", (order_id,))
            for box, weights in allocations:
                quantity = int(box["quantity"])
                positive = [weight for weight in weights if weight > 0]
                # The optimizer expands this template row into individual boxes.
                average_load = sum(positive) / quantity if quantity else 0
                if average_load <= 0:
                    continue
                conn.execute(
                    """
                    INSERT INTO order_box_requirements(order_id,box_profile_id,quantity,loaded_weight_per_box)
                    VALUES(?,?,?,?)
                    """,
                    (order_id, int(box["box_profile_id"]), quantity, average_load),
                )
    except Exception:
        # db_session rolls back the box replacement, status and history together.
        return False, "Box requirements could not be saved. The order status was not advanced. Please retry."
    return True, "Box requirements saved successfully. Order is now Ready for Loading."


def accept_box_recommendation(order_id, recommendation_index=0, updated_by=None):
    recs = recommend_box_combinations(order_id, limit=max(3, recommendation_index + 1))
    if not recs:
        return False, box_requirement_shortage_message(order_id)
    if recommendation_index < 0 or recommendation_index >= len(recs):
        return False, "That recommendation is no longer available. Refresh and try again."
    return save_box_combination(order_id, recs[recommendation_index]["boxes"], updated_by)


def set_manual_box_requirements(order_id, selections, updated_by=None):
    """selections: [(box_profile_id, quantity)]"""
    selected_boxes = []
    for box_profile_id, qty in selections:
        try:
            profile_id = int(box_profile_id)
            quantity = int(qty)
            if quantity != qty or quantity < 0:
                return False, "Box quantities must be whole numbers of 0 or more."
        except (TypeError, ValueError, OverflowError):
            return False, "Choose a valid box size and enter a whole quantity of 0 or more."
        if quantity == 0:
            continue
        selected_boxes.append({
            "box_profile_id": profile_id,
            "quantity": quantity,
        })
    if not selected_boxes:
        return False, "Select at least one box before saving the requirement."
    return save_box_combination(order_id, selected_boxes, updated_by)


def eligible_orders_for_optimization(collection_point_id=None):
    initialize_schema()
    placeholders = ",".join("?" for _ in OPTIMIZATION_ELIGIBLE_STATUSES)
    sql = f"""
        SELECT o.order_id, o.status, o.order_date, o.collection_point_id, o.collection_point,
               u.full_name customer_name,
               COALESCE(SUM(r.quantity),0) required_boxes,
               COALESCE(SUM(r.quantity*r.loaded_weight_per_box),0) estimated_weight
        FROM seafood_orders o
        JOIN users u ON u.user_id=o.customer_id
        LEFT JOIN order_box_requirements r ON r.order_id=o.order_id
        WHERE o.status IN ({placeholders})
          AND COALESCE(o.collection_assignment,'') <> 'Local Pickup'
    """
    params = list(OPTIMIZATION_ELIGIBLE_STATUSES)
    if collection_point_id is not None:
        sql += " AND o.collection_point_id=?"
        params.append(collection_point_id)
    sql += " GROUP BY o.order_id,u.user_id HAVING COALESCE(SUM(r.quantity),0) > 0 ORDER BY o.order_date"
    with db_session() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]
