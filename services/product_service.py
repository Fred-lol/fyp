from database.db import db_session
from database.schema import initialize_schema
from constants import (
    PRODUCT_STATUSES,
    LOW_STOCK_THRESHOLD,
    SEAFOOD_CATEGORIES,
    SEAFOOD_UNITS,
)


LEGACY_CATEGORY_ALIASES = {
    "Marine Finfish": "Fish",
    "Freshwater Fish": "Fish",
    "Crustacean": "Crustaceans (Prawn, Crab & Lobster)",
    "Shellfish": "Molluscs & Shellfish (Cockle, Clam, Mussel & Oyster)",
    "Mollusk": "Molluscs & Shellfish (Cockle, Clam, Mussel & Oyster)",
    "Cephalopod": "Cephalopods (Squid, Cuttlefish & Octopus)",
}


def stock_state(product):
    qty = float(product.get("stock_quantity") or 0)
    if product.get("availability_status") != "Available":
        return "Unavailable"
    if qty <= 0:
        return "Out of Stock"
    if qty <= LOW_STOCK_THRESHOLD:
        return "Low Stock"
    return "Available"


def list_seafood(search="", category="All", status="All"):
    initialize_schema()
    sql = "SELECT * FROM seafood_products WHERE 1=1"
    params = []
    if search.strip():
        q = f"%{search.strip().lower()}%"
        sql += " AND (LOWER(product_name) LIKE ? OR LOWER(category) LIKE ?)"
        params += [q, q]
    if category != "All":
        sql += " AND category=?"
        params.append(category)
    if status in PRODUCT_STATUSES:
        sql += " AND availability_status=?"
        params.append(status)
    sql += " ORDER BY product_name"
    with db_session() as conn:
        rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
    for row in rows:
        row["stock_state"] = stock_state(row)
    return rows


def seafood_categories():
    return SEAFOOD_CATEGORIES.copy()


def seafood_summary():
    products = list_seafood()
    return {
        "total": len(products),
        "available": sum(1 for p in products if p["stock_state"] == "Available"),
        "low_stock": sum(1 for p in products if p["stock_state"] == "Low Stock"),
        "out_of_stock": sum(1 for p in products if p["stock_state"] == "Out of Stock"),
        "unavailable": sum(1 for p in products if p["stock_state"] == "Unavailable"),
    }


def get_product(product_id):
    initialize_schema()
    with db_session() as conn:
        row = conn.execute("SELECT * FROM seafood_products WHERE product_id=?", (product_id,)).fetchone()
    if not row:
        return None
    result = dict(row)
    result["stock_state"] = stock_state(result)
    return result


def _validate_product(product_name, category, unit, availability_status, description=""):
    product_name = str(product_name or "").strip()
    if not product_name:
        return False, "Seafood name is required."
    if len(product_name) < 2:
        return False, "Seafood name must contain at least 2 characters."
    if len(product_name) > 80:
        return False, "Seafood name cannot be longer than 80 characters."
    if category not in SEAFOOD_CATEGORIES:
        return False, "Select a valid seafood category."
    if unit != "kg":
        return False, "Seafood quantities are fixed in kilograms (kg)."
    if availability_status not in PRODUCT_STATUSES:
        return False, "Invalid availability status."
    if len(str(description or "").strip()) > 500:
        return False, "Description cannot be longer than 500 characters."
    return True, ""


def add_product(
    product_name, category, description, unit, stock_quantity, availability_status,
    image_path=None, updated_by=None, unit_price=0.0, image_data=None, image_mime_type=None,
):
    ok, msg = _validate_product(product_name, category, unit, availability_status, description)
    if not ok:
        return ok, msg
    try:
        stock_quantity = float(stock_quantity)
    except (TypeError, ValueError):
        return False, "Stock quantity must be numeric."
    if stock_quantity < 0:
        return False, "Initial stock quantity cannot be negative."
    if stock_quantity > 1_000_000:
        return False, "Initial stock quantity cannot be more than 1,000,000 kg."
    try:
        unit_price = float(unit_price)
    except (TypeError, ValueError):
        return False, "Unit price must be numeric."
    if unit_price <= 0:
        return False, "Price must be greater than RM 0.00 per kg."
    if unit_price > 100_000:
        return False, "Price cannot be more than RM 100,000.00 per kg."
    if availability_status == "Available" and stock_quantity <= 0:
        return False, "Enter stock greater than 0 kg, or set the seafood status to Unavailable."
    try:
        with db_session() as conn:
            existing = conn.execute(
                "SELECT 1 FROM seafood_products WHERE LOWER(product_name)=LOWER(?) LIMIT 1",
                (product_name.strip(),),
            ).fetchone()
            if existing:
                return False, "A seafood product with this name already exists."
            cur = conn.execute(
                """
                INSERT INTO seafood_products(
                    product_name,category,description,unit,unit_price,stock_quantity,
                    availability_status,image_path,image_data,image_mime_type
                ) VALUES(?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    product_name.strip(), category, description.strip(), unit, unit_price,
                    stock_quantity, availability_status, image_path, image_data, image_mime_type,
                ),
            )
            if stock_quantity:
                conn.execute(
                    """
                    INSERT INTO seafood_stock_movements(
                        product_id,quantity_change,movement_type,updated_by,note
                    ) VALUES(?,?,?,?,?)
                    """,
                    (cur.lastrowid, stock_quantity, "Initial Stock", updated_by, "Initial seafood stock."),
                )
        return True, "Seafood product added successfully."
    except Exception as exc:
        if "unique" in str(exc).lower() and "product_name" in str(exc).lower():
            return False, "A seafood product with this name already exists."
        return False, "Unable to add the seafood product."


def update_product(
    product_id, product_name, category, description, unit, availability_status,
    image_path=None, unit_price=None, image_data=None, image_mime_type=None,
):
    category = LEGACY_CATEGORY_ALIASES.get(category, category)
    ok, msg = _validate_product(product_name, category, unit, availability_status, description)
    if not ok:
        return ok, msg
    try:
        with db_session() as conn:
            current = conn.execute("SELECT * FROM seafood_products WHERE product_id=?", (product_id,)).fetchone()
            if not current:
                return False, "Seafood product not found."
            final_image = image_path if image_path is not None else current["image_path"]
            final_image_data = image_data if image_data is not None else current.get("image_data")
            final_image_mime_type = (
                image_mime_type if image_data is not None else current.get("image_mime_type")
            )
            final_price = float(current["unit_price"] or 0) if unit_price is None else float(unit_price)
            if final_price <= 0:
                return False, "Price must be greater than RM 0.00 per kg."
            if final_price > 100_000:
                return False, "Price cannot be more than RM 100,000.00 per kg."
            conn.execute(
                """
                UPDATE seafood_products
                SET product_name=?,category=?,description=?,unit=?,unit_price=?,availability_status=?,
                    image_path=?,image_data=?,image_mime_type=?,updated_at=CURRENT_TIMESTAMP
                WHERE product_id=?
                """,
                (
                    product_name.strip(), category, description.strip(), unit, final_price,
                    availability_status, final_image, final_image_data, final_image_mime_type, product_id,
                ),
            )
        return True, "Seafood product updated successfully."
    except Exception as exc:
        if "unique" in str(exc).lower() and "product_name" in str(exc).lower():
            return False, "A seafood product with this name already exists."
        return False, "Unable to update the seafood product."


def adjust_stock(product_id, quantity_change, updated_by=None, note="Manual stock adjustment"):
    try:
        quantity_change = float(quantity_change)
    except (TypeError, ValueError):
        return False, "Stock adjustment must be numeric."
    if quantity_change == 0:
        return False, "Enter a stock quantity to add or deduct."
    with db_session() as conn:
        seafood = conn.execute("SELECT * FROM seafood_products WHERE product_id=?", (product_id,)).fetchone()
        if not seafood:
            return False, "Seafood product not found."
        new_stock = float(seafood["stock_quantity"] or 0) + quantity_change
        if new_stock < -1e-9:
            return False, f"Stock cannot go below 0 {seafood['unit']}."
        new_stock = max(0.0, new_stock)
        conn.execute(
            "UPDATE seafood_products SET stock_quantity=?,updated_at=CURRENT_TIMESTAMP WHERE product_id=?",
            (new_stock, product_id),
        )
        conn.execute(
            """
            INSERT INTO seafood_stock_movements(
                product_id,quantity_change,movement_type,updated_by,note
            ) VALUES(?,?,?,?,?)
            """,
            (product_id, quantity_change, "Manual Adjustment", updated_by, note.strip() or "Manual stock adjustment"),
        )
    return True, f"Stock updated successfully. Current stock: {new_stock:g} {seafood['unit']}."


def set_stock(product_id, new_stock, updated_by=None, note="Stock count correction"):
    try:
        new_stock = float(new_stock)
    except (TypeError, ValueError):
        return False, "Stock quantity must be numeric."
    if new_stock < 0:
        return False, "Stock quantity cannot be negative."
    with db_session() as conn:
        seafood = conn.execute("SELECT * FROM seafood_products WHERE product_id=?", (product_id,)).fetchone()
        if not seafood:
            return False, "Seafood product not found."
        old_stock = float(seafood["stock_quantity"] or 0)
        change = new_stock - old_stock
        conn.execute(
            "UPDATE seafood_products SET stock_quantity=?,updated_at=CURRENT_TIMESTAMP WHERE product_id=?",
            (new_stock, product_id),
        )
        if abs(change) > 1e-9:
            conn.execute(
                """
                INSERT INTO seafood_stock_movements(
                    product_id,quantity_change,movement_type,updated_by,note
                ) VALUES(?,?,?,?,?)
                """,
                (product_id, change, "Stock Count", updated_by, note.strip() or "Stock count correction"),
            )
    return True, "Stock quantity saved successfully."


def delete_product(product_id):
    with db_session() as conn:
        seafood = conn.execute("SELECT * FROM seafood_products WHERE product_id=?", (product_id,)).fetchone()
        if not seafood:
            return False, "Seafood product not found."
        referenced = conn.execute("SELECT 1 FROM order_items WHERE product_id=? LIMIT 1", (product_id,)).fetchone()
        if referenced:
            conn.execute(
                "UPDATE seafood_products SET availability_status='Unavailable',updated_at=CURRENT_TIMESTAMP WHERE product_id=?",
                (product_id,),
            )
            return False, "This seafood has order history, so it was set to Unavailable instead of being deleted."
        conn.execute("DELETE FROM seafood_stock_movements WHERE product_id=?", (product_id,))
        conn.execute("DELETE FROM seafood_products WHERE product_id=?", (product_id,))
    return True, "Seafood product deleted successfully."


def stock_movements(product_id, limit=30):
    with db_session() as conn:
        rows = conn.execute(
            """
            SELECT m.*, COALESCE(u.full_name,'System') updated_by_name
            FROM seafood_stock_movements m
            LEFT JOIN users u ON u.user_id=m.updated_by
            WHERE m.product_id=?
            ORDER BY m.created_at DESC, m.movement_id DESC
            LIMIT ?
            """,
            (product_id, int(limit)),
        ).fetchall()
    return [dict(r) for r in rows]
