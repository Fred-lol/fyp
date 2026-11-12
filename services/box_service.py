from functools import lru_cache

from database.db import db_session
from database.schema import initialize_schema
from constants import BOX_TEMPLATE_DEFAULTS, BOX_STATUSES


@lru_cache(maxsize=1)
def ensure_box_templates():
    """Create fixed box templates once per server process.

    Running this on every Streamlit interaction previously caused unrelated
    pages to perform several database reads and writes before rendering.
    """
    initialize_schema()
    with db_session() as conn:
        for template in BOX_TEMPLATE_DEFAULTS:
            existing = conn.execute(
                "SELECT * FROM box_profiles WHERE box_name=?", (template["box_name"],)
            ).fetchone()
            if existing:
                conn.execute(
                    """
                    UPDATE box_profiles
                    SET capacity_litre=?, length=?, width=?, height=?,
                        max_seafood_weight_kg=?, weight_parameter=?
                    WHERE box_profile_id=?
                    """,
                    (
                        template["capacity_litre"], template["length"], template["width"],
                        template["height"], template["max_seafood_weight_kg"],
                        template["max_seafood_weight_kg"], existing["box_profile_id"],
                    ),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO box_profiles(
                        box_name,capacity_litre,length,width,height,max_seafood_weight_kg,
                        weight_parameter,inventory_quantity,status
                    ) VALUES(?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        template["box_name"], template["capacity_litre"], template["length"],
                        template["width"], template["height"], template["max_seafood_weight_kg"],
                        template["max_seafood_weight_kg"], 0, "Active",
                    ),
                )


def list_boxes(status="All", search=""):
    ensure_box_templates()
    sql = "SELECT * FROM box_profiles WHERE 1=1"
    params = []
    if status != "All":
        sql += " AND status=?"
        params.append(status)
    if search.strip():
        sql += " AND LOWER(box_name) LIKE ?"
        params.append(f"%{search.strip().lower()}%")
    sql += " ORDER BY capacity_litre"
    with db_session() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def get_box(box_profile_id):
    ensure_box_templates()
    with db_session() as conn:
        row = conn.execute("SELECT * FROM box_profiles WHERE box_profile_id=?", (box_profile_id,)).fetchone()
    return dict(row) if row else None


def reserved_quantity(box_profile_id, exclude_order_id=None):
    """Boxes required by active orders are considered reserved inventory."""
    sql = """
        SELECT COALESCE(SUM(r.quantity),0) reserved
        FROM order_box_requirements r
        JOIN seafood_orders o ON o.order_id=r.order_id
        WHERE r.box_profile_id=?
          AND o.status NOT IN ('Completed','Cancelled')
    """
    params = [box_profile_id]
    if exclude_order_id is not None:
        sql += " AND o.order_id<>?"
        params.append(exclude_order_id)
    with db_session() as conn:
        return int(conn.execute(sql, params).fetchone()["reserved"] or 0)


def available_quantity(box_profile_id, exclude_order_id=None):
    box = get_box(box_profile_id)
    if not box:
        return 0
    return max(0, int(box.get("inventory_quantity") or 0) - reserved_quantity(box_profile_id, exclude_order_id))


def _list_inventory(status="Active", exclude_order_id=None):
    """Load templates and their active-order reservations in one query."""
    ensure_box_templates()
    sql = """
        SELECT b.*, COALESCE(SUM(
            CASE
                WHEN o.status NOT IN ('Completed', 'Cancelled')
                 AND (CAST(? AS BIGINT) IS NULL OR o.order_id <> ?)
                THEN r.quantity ELSE 0
            END
        ), 0) AS reserved_quantity
        FROM box_profiles b
        LEFT JOIN order_box_requirements r ON r.box_profile_id=b.box_profile_id
        LEFT JOIN seafood_orders o ON o.order_id=r.order_id
    """
    params = [exclude_order_id, exclude_order_id]
    if status != "All":
        sql += " WHERE b.status=?"
        params.append(status)
    sql += " GROUP BY b.box_profile_id ORDER BY b.capacity_litre"
    with db_session() as conn:
        boxes = [dict(row) for row in conn.execute(sql, params).fetchall()]
    for box in boxes:
        box["reserved_quantity"] = int(box["reserved_quantity"] or 0)
        box["available_quantity"] = (
            max(0, int(box["inventory_quantity"] or 0) - box["reserved_quantity"])
            if box["status"] == "Active" else 0
        )
    return boxes


def list_box_inventory(exclude_order_id=None):
    return _list_inventory("Active", exclude_order_id)


def list_all_box_inventory(exclude_order_id=None):
    """Return active and inactive templates for staff inventory management."""
    return _list_inventory("All", exclude_order_id)


def create_box_template(
    box_name, capacity_litre, length, width, height, max_seafood_weight_kg,
    initial_quantity=0,
):
    """Create a reusable staff-managed insulated-box template."""
    box_name = (box_name or "").strip()
    if not box_name:
        return False, "Box template name is required."
    try:
        capacity_litre = int(capacity_litre)
        initial_quantity = int(initial_quantity)
        length, width, height, max_seafood_weight_kg = map(
            float, (length, width, height, max_seafood_weight_kg)
        )
    except (TypeError, ValueError):
        return False, "Enter valid numeric box dimensions, capacity and weight."
    if capacity_litre <= 0 or initial_quantity < 0:
        return False, "Capacity must be positive and opening quantity cannot be negative."
    if min(length, width, height) <= 0 or max_seafood_weight_kg < 0:
        return False, "Dimensions must be greater than zero and maximum weight cannot be negative."

    try:
        with db_session() as conn:
            exists = conn.execute(
                "SELECT 1 FROM box_profiles WHERE LOWER(box_name)=LOWER(?)", (box_name,)
            ).fetchone()
            if exists:
                return False, "A box template with this name already exists."
            box_id = conn.execute(
                """INSERT INTO box_profiles(
                    box_name, capacity_litre, length, width, height,
                    max_seafood_weight_kg, weight_parameter, inventory_quantity, status
                ) VALUES(?,?,?,?,?,?,?,?,?)""",
                (
                    box_name, capacity_litre, length, width, height,
                    max_seafood_weight_kg, max_seafood_weight_kg, initial_quantity, "Active",
                ),
            ).lastrowid
            if initial_quantity:
                conn.execute(
                    """INSERT INTO box_inventory_movements(
                        box_profile_id, quantity_change, movement_type, note
                    ) VALUES(?,?,?,?)""",
                    (box_id, initial_quantity, "Opening Stock", "Opening stock when template was created."),
                )
    except Exception:
        return False, "Unable to create this box template. Please try a different name."
    return True, "New box template created successfully."


def delete_box_template(box_profile_id):
    """Delete a custom, unused template while keeping operational history safe."""
    with db_session() as conn:
        box = conn.execute(
            "SELECT box_name FROM box_profiles WHERE box_profile_id=?", (box_profile_id,)
        ).fetchone()
        if not box:
            return False, "Box template could not be found."
        fixed_names = {template["box_name"].lower() for template in BOX_TEMPLATE_DEFAULTS}
        if box["box_name"].lower() in fixed_names:
            return False, "Standard AquaLoad box templates cannot be deleted. Set the template to Inactive instead."
        for table_name in ("order_box_requirements", "box_placements"):
            if conn.execute(
                f"SELECT 1 FROM {table_name} WHERE box_profile_id=? LIMIT 1", (box_profile_id,)
            ).fetchone():
                return False, "This template is used in an order or loading plan. Set it to Inactive instead of deleting it."
        # Custom templates can be removed along with their own stock-adjustment
        # history when they have never been used operationally.
        conn.execute("DELETE FROM box_inventory_movements WHERE box_profile_id=?", (box_profile_id,))
        conn.execute("DELETE FROM box_profiles WHERE box_profile_id=?", (box_profile_id,))
    return True, "Box template deleted permanently."


def add_inventory(box_profile_id, quantity, updated_by=None, note=""):
    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        return False, "Quantity must be a whole number."
    if quantity <= 0:
        return False, "Quantity to add must be greater than zero."
    box = get_box(box_profile_id)
    if not box:
        return False, "Box template not found."
    with db_session() as conn:
        conn.execute(
            "UPDATE box_profiles SET inventory_quantity=inventory_quantity+?,updated_at=CURRENT_TIMESTAMP WHERE box_profile_id=?",
            (quantity, box_profile_id),
        )
        conn.execute(
            "INSERT INTO box_inventory_movements(box_profile_id,quantity_change,movement_type,updated_by,note) VALUES(?,?,?,?,?)",
            (box_profile_id, quantity, "Add Boxes", updated_by, note.strip() or "Added physical boxes to inventory."),
        )
    return True, f"Added {quantity} × {box['box_name']} to box inventory."


def set_inventory(box_profile_id, quantity, updated_by=None, note=""):
    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        return False, "Quantity must be a whole number."
    if quantity < 0:
        return False, "Inventory quantity cannot be negative."
    reserved = reserved_quantity(box_profile_id)
    if quantity < reserved:
        return False, f"Inventory cannot be below {reserved} because those boxes are already required by active orders."
    box = get_box(box_profile_id)
    if not box:
        return False, "Box template not found."
    old = int(box.get("inventory_quantity") or 0)
    change = quantity - old
    with db_session() as conn:
        conn.execute(
            "UPDATE box_profiles SET inventory_quantity=?,updated_at=CURRENT_TIMESTAMP WHERE box_profile_id=?",
            (quantity, box_profile_id),
        )
        if change:
            conn.execute(
                "INSERT INTO box_inventory_movements(box_profile_id,quantity_change,movement_type,updated_by,note) VALUES(?,?,?,?,?)",
                (box_profile_id, change, "Stock Count", updated_by, note.strip() or "Physical box inventory count."),
            )
    return True, "Box inventory quantity saved successfully."


def set_box_status(box_profile_id, status):
    if status not in BOX_STATUSES:
        return False, "Invalid box-template status."
    if status == "Inactive":
        reserved = reserved_quantity(box_profile_id)
        if reserved > 0:
            return False, f"This template is reserved by {reserved} box requirement(s) in active orders and cannot be made Inactive yet."
    with db_session() as conn:
        conn.execute(
            "UPDATE box_profiles SET status=?,updated_at=CURRENT_TIMESTAMP WHERE box_profile_id=?",
            (status, box_profile_id),
        )
    return True, "Box-template status updated."


def inventory_movements(box_profile_id, limit=30):
    with db_session() as conn:
        rows = conn.execute(
            """
            SELECT m.*, COALESCE(u.full_name,'System') updated_by_name
            FROM box_inventory_movements m
            LEFT JOIN users u ON u.user_id=m.updated_by
            WHERE m.box_profile_id=?
            ORDER BY m.created_at DESC, m.movement_id DESC
            LIMIT ?
            """,
            (box_profile_id, int(limit)),
        ).fetchall()
    return [dict(r) for r in rows]
