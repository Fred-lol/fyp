from database.db import db_session
from database.schema import initialize_schema
from constants import USER_STATUSES


def list_users(search="", role="All", status="All"):
    initialize_schema()
    sql = "SELECT user_id, full_name, email, phone_number, role, status, created_at FROM users WHERE 1=1"
    params = []
    if search.strip():
        sql += " AND (LOWER(full_name) LIKE ? OR LOWER(email) LIKE ?)"
        q = f"%{search.strip().lower()}%"
        params += [q, q]
    if role != "All":
        sql += " AND role=?"
        params.append(role)
    if status != "All":
        sql += " AND status=?"
        params.append(status)
    sql += " ORDER BY created_at DESC"
    with db_session() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def user_counts():
    initialize_schema()
    with db_session() as conn:
        active_customers = conn.execute("SELECT COUNT(*) c FROM users WHERE role='Customer' AND status='Active'").fetchone()["c"]
        active_staff = conn.execute("SELECT COUNT(*) c FROM users WHERE role<>'Customer' AND status='Active'").fetchone()["c"]
        inactive = conn.execute("SELECT COUNT(*) c FROM users WHERE status='Inactive'").fetchone()["c"]
    return {"active_customers": active_customers, "active_staff": active_staff, "inactive": inactive}


def load_user_management(search="", role="All", status="All", sort="Newest first"):
    """Load account metrics and the filtered table in one database session."""
    initialize_schema()
    sql = "SELECT user_id, full_name, email, phone_number, role, status, created_at FROM users WHERE 1=1"
    params = []
    if search.strip():
        sql += " AND (LOWER(full_name) LIKE ? OR LOWER(email) LIKE ?)"
        query = f"%{search.strip().lower()}%"
        params += [query, query]
    if role != "All":
        sql += " AND role=?"
        params.append(role)
    if status != "All":
        sql += " AND status=?"
        params.append(status)
    sort_orders = {
        "Newest first": "created_at DESC",
        "Oldest first": "created_at ASC",
        "Name (A–Z)": "full_name ASC, created_at DESC",
        "Name (Z–A)": "full_name DESC, created_at DESC",
        "Role (A–Z)": "role ASC, full_name ASC",
    }
    sql += f" ORDER BY {sort_orders.get(sort, sort_orders['Newest first'])}"

    with db_session() as conn:
        counts = conn.execute(
            """
            SELECT
                COUNT(*) FILTER (WHERE role='Customer' AND status='Active') AS active_customers,
                COUNT(*) FILTER (WHERE role<>'Customer' AND status='Active') AS active_staff,
                COUNT(*) FILTER (WHERE status='Inactive') AS inactive
            FROM users
            """
        ).fetchone()
        rows = [dict(row) for row in conn.execute(sql, params).fetchall()]
    return dict(counts), rows


def set_user_status(user_id, status):
    """Update an account status and return a user-facing result."""
    if status not in USER_STATUSES:
        return False, "Select a valid account status."
    with db_session() as conn:
        updated = conn.execute(
            "UPDATE users SET status=?, updated_at=CURRENT_TIMESTAMP WHERE user_id=?",
            (status, user_id),
        )
    if updated.rowcount != 1:
        return False, "That user account could not be found. Refresh the list and try again."
    return True, "Account status updated successfully."


def delete_user_account(user_id):
    """Permanently delete an account only when no operational history uses it."""
    initialize_schema()
    reference_checks = (
        ("seafood_orders", "customer_id"),
        ("order_status_history", "updated_by"),
        ("seafood_stock_movements", "updated_by"),
        ("payments", "customer_id"),
        ("box_inventory_movements", "updated_by"),
        ("loading_plans", "created_by"),
        ("loading_reports", "generated_by"),
    )
    with db_session() as conn:
        exists = conn.execute("SELECT 1 FROM users WHERE user_id=?", (user_id,)).fetchone()
        if not exists:
            return False, "That user account could not be found."
        for table_name, column_name in reference_checks:
            linked_record = conn.execute(
                f"SELECT 1 FROM {table_name} WHERE {column_name}=? LIMIT 1", (user_id,)
            ).fetchone()
            if linked_record:
                return False, "This account has business records. Set it to Inactive instead of deleting it."
        conn.execute("DELETE FROM users WHERE user_id=?", (user_id,))
    return True, "User account deleted permanently."
