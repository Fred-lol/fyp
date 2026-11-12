from database.db import db_session
from database.schema import initialize_schema
from services.auth_service import create_user
from services.box_service import ensure_box_templates
from services.order_service import (
    place_order,
    update_order_status,
    accept_box_recommendation,
)
from services.optimization_service import preview_optimization, save_optimization
from services.report_service import generate_report
from constants import ROLES


COLLECTION_POINTS = [
    ("Kangar Wholesale Collection Point", "Kangar", "Perlis", "01000", 6.4414, 100.1986),
    ("Alor Setar Wholesale Collection Point", "Alor Setar", "Kedah", "05000", 6.1210, 100.3600),
    ("George Town Wholesale Collection Point", "George Town", "Pulau Pinang", "10000", 5.4141, 100.3288),
    ("Ipoh Wholesale Collection Point", "Ipoh", "Perak", "30000", 4.5975, 101.0901),
    ("Shah Alam Wholesale Collection Point", "Shah Alam", "Selangor", "40000", 3.0738, 101.5183),
    ("Kuala Lumpur Wholesale Collection Point", "Kuala Lumpur", "W.P. Kuala Lumpur", "50000", 3.1390, 101.6869),
    ("Putrajaya Wholesale Collection Point", "Putrajaya", "W.P. Putrajaya", "62000", 2.9264, 101.6964),
    ("Seremban Wholesale Collection Point", "Seremban", "Negeri Sembilan", "70000", 2.7297, 101.9381),
    ("Melaka Wholesale Collection Point", "Melaka", "Melaka", "75000", 2.1896, 102.2501),
    ("Johor Bahru Wholesale Collection Point", "Johor Bahru", "Johor", "80000", 1.4927, 103.7414),
    ("Kuantan Wholesale Collection Point", "Kuantan", "Pahang", "25000", 3.8077, 103.3260),
    ("Kuala Terengganu Wholesale Collection Point", "Kuala Terengganu", "Terengganu", "20000", 5.3290, 103.1370),
    ("Kota Bharu Wholesale Collection Point", "Kota Bharu", "Kelantan", "15000", 6.1254, 102.2381),
    ("Kota Kinabalu Wholesale Collection Point", "Kota Kinabalu", "Sabah", "88000", 5.9804, 116.0735),
    ("Kuching Wholesale Collection Point", "Kuching", "Sarawak", "93000", 1.5535, 110.3593),
    ("Labuan Wholesale Collection Point", "Labuan", "W.P. Labuan", "87000", 5.2800, 115.2475),
]

SEAFOOD = [
    ("Mackerel", "Fish", "Fresh mackerel suitable for bulk seafood orders.", "kg", 18.00, 900.0),
    ("Red Snapper", "Fish", "Fresh red snapper supplied in kilogram quantities.", "kg", 28.00, 650.0),
    ("Pomfret", "Fish", "Fresh pomfret for wholesale seafood orders.", "kg", 32.00, 520.0),
    ("Prawn", "Crustacean", "Fresh prawns for bulk purchase.", "kg", 38.00, 420.0),
    ("Squid", "Cephalopod", "Fresh squid supplied by weight.", "kg", 24.00, 500.0),
    ("Crab", "Crustacean", "Fresh crab for wholesale orders.", "kg", 45.00, 380.0),
]

LORRIES = [
    ("JTU 4821", 500.0, 220.0, 220.0, 5000.0),
    ("VCA 1234", 560.0, 230.0, 230.0, 6500.0),
    ("BKM 7788", 620.0, 240.0, 240.0, 7500.0),
]


def _user_id(email):
    with db_session() as conn:
        row = conn.execute("SELECT user_id FROM users WHERE LOWER(email)=LOWER(?)", (email,)).fetchone()
    return row["user_id"] if row else None


def _product_id(name):
    with db_session() as conn:
        row = conn.execute("SELECT product_id FROM seafood_products WHERE product_name=?", (name,)).fetchone()
    return row["product_id"] if row else None


def _lorry_id(plate):
    with db_session() as conn:
        row = conn.execute("SELECT lorry_id FROM lorry_profiles WHERE plate_number=?", (plate,)).fetchone()
    return row["lorry_id"] if row else None


def _demo_order(marker):
    with db_session() as conn:
        row = conn.execute(
            "SELECT order_id FROM order_status_history WHERE note=? ORDER BY history_id LIMIT 1",
            (marker,),
        ).fetchone()
    return row["order_id"] if row else None


def seed_collection_points():
    with db_session() as conn:
        for name, city, state, postcode, lat, lon in COLLECTION_POINTS:
            conn.execute(
                """
                INSERT INTO collection_points(point_name,city,state,postcode,latitude,longitude,status)
                VALUES(?,?,?,?,?,?,'Available')
                ON CONFLICT(point_name) DO NOTHING
                """,
                (name, city, state, postcode, lat, lon),
            )


def seed_users():
    create_user(
        "AquaLoad Warehouse Admin", "admin.aquaload@gmail.com", "0123000001",
        "Admin12345", ROLES["WAREHOUSE_ADMIN"], ignore_existing=True,
        city="Kangar", state="Perlis", postcode="01000",
    )
    create_user(
        "AquaLoad Loading Supervisor", "supervisor.aquaload@gmail.com", "0123000002",
        "Supervisor12345", ROLES["LOADING_SUPERVISOR"], ignore_existing=True,
        city="Kangar", state="Perlis", postcode="01000",
    )
    create_user(
        "AquaLoad Seafood Supplier", "supplier.aquaload@gmail.com", "0123000003",
        "Supplier12345", ROLES["SEAFOOD_SUPPLIER"], ignore_existing=True,
        city="Kangar", state="Perlis", postcode="01000",
    )
    create_user(
        "AquaLoad Demo Customer", "demo.customer@gmail.com", "0123888888",
        "Customer12345", ROLES["CUSTOMER"], ignore_existing=True,
        address="Demo Address", city="Kangar", state="Perlis", postcode="01000",
    )


def seed_seafood():
    with db_session() as conn:
        for name, category, description, unit, price, stock in SEAFOOD:
            existing = conn.execute("SELECT product_id FROM seafood_products WHERE product_name=?", (name,)).fetchone()
            if existing:
                conn.execute(
                    "UPDATE seafood_products SET unit_price=? WHERE product_id=? AND COALESCE(unit_price,0)=0",
                    (price, existing["product_id"]),
                )
                continue
            else:
                conn.execute(
                    """
                    INSERT INTO seafood_products(
                        product_name,category,description,unit,unit_price,stock_quantity,availability_status
                    ) VALUES(?,?,?,?,?,?,'Available')
                    """,
                    (name, category, description, unit, price, stock),
                )


def seed_lorries():
    with db_session() as conn:
        for plate, length, width, height, max_weight in LORRIES:
            conn.execute(
                """
                INSERT INTO lorry_profiles(
                    plate_number,internal_length,internal_width,internal_height,max_weight,status
                ) VALUES(?,?,?,?,?,'Available')
                ON CONFLICT(plate_number) DO NOTHING
                """,
                (plate, length, width, height, max_weight),
            )


def seed_boxes():
    ensure_box_templates()
    with db_session() as conn:
        boxes = conn.execute("SELECT box_profile_id,inventory_quantity FROM box_profiles").fetchall()
        for box in boxes:
            movements = conn.execute(
                "SELECT COUNT(*) c FROM box_inventory_movements WHERE box_profile_id=?",
                (box["box_profile_id"],),
            ).fetchone()["c"]
            if int(movements or 0) == 0 and int(box["inventory_quantity"] or 0) == 0:
                conn.execute(
                    "UPDATE box_profiles SET inventory_quantity=40 WHERE box_profile_id=?",
                    (box["box_profile_id"],),
                )
                conn.execute(
                    "INSERT INTO box_inventory_movements(box_profile_id,quantity_change,movement_type,note) VALUES(?,?,?,?)",
                    (box["box_profile_id"], 40, "Initial Stock", "Initial standardized box inventory."),
                )



def _ensure_demo_payment(order_id, customer_id):
    with db_session() as conn:
        existing = conn.execute("SELECT payment_id FROM payments WHERE order_id=?", (order_id,)).fetchone()
        if existing:
            return
        amount = conn.execute(
            """
            SELECT COALESCE(SUM(oi.quantity * COALESCE(p.unit_price,0)),0) amount
            FROM order_items oi
            JOIN seafood_products p ON p.product_id=oi.product_id
            WHERE oi.order_id=?
            """,
            (order_id,),
        ).fetchone()["amount"]
        conn.execute(
            """
            INSERT INTO payments(order_id,customer_id,amount,payment_method,payment_status,transaction_reference)
            VALUES(?,?,?,?,?,?)
            """,
            (order_id, customer_id, float(amount or 0), "Online Banking", "Paid", f"AQPAY-DEMO-{order_id}"),
        )


def _create_ready_demo_order(customer_id, staff_id, marker, items):
    existing = _demo_order(marker)
    if existing:
        _ensure_demo_payment(existing, customer_id)
        return existing
    selected = [(_product_id(name), weight) for name, weight in items]
    ok, _, order_id = place_order(customer_id, selected)
    if not ok:
        return None
    # Replace generic first history note with a repeat-safe marker on an
    # additional history row so the demo order can be found next run.
    with db_session() as conn:
        conn.execute(
            "INSERT INTO order_status_history(order_id,status,updated_by,note) VALUES(?,?,?,?)",
            (order_id, "Pending", staff_id, marker),
        )
    _ensure_demo_payment(order_id, customer_id)
    update_order_status(order_id, "Confirmed", staff_id, "Staff reviewed and confirmed the sample order.")
    accept_box_recommendation(order_id, 0)
    update_order_status(order_id, "Ready for Loading", staff_id, "Box requirement accepted; order is ready for loading.")
    return order_id


def seed_demo_workflow():
    customer_id = _user_id("demo.customer@gmail.com")
    staff_id = _user_id("admin.aquaload@gmail.com")
    if not customer_id or not staff_id:
        return

    orders = [
        _create_ready_demo_order(customer_id, staff_id, "AQUALOAD_DEMO_ORDER_50KG", [("Red Snapper", 50.0)]),
        _create_ready_demo_order(customer_id, staff_id, "AQUALOAD_DEMO_ORDER_100KG", [("Squid", 100.0)]),
        _create_ready_demo_order(customer_id, staff_id, "AQUALOAD_DEMO_ORDER_150KG", [("Mackerel", 150.0)]),
        _create_ready_demo_order(customer_id, staff_id, "AQUALOAD_DEMO_ORDER_324KG", [("Pomfret", 324.0)]),
        _create_ready_demo_order(customer_id, staff_id, "AQUALOAD_DEMO_ORDER_504KG", [("Prawn", 300.0), ("Crab", 204.0)]),
    ]
    orders = [o for o in orders if o]
    if not orders:
        return

    # Keep at least two saved sample plans so the Reports/3D UI is immediately visible.
    with db_session() as conn:
        plan_count = conn.execute("SELECT COUNT(*) c FROM loading_plans").fetchone()["c"]
    if plan_count >= 2:
        return

    first_set = orders[:3]
    second_set = orders[3:]
    for plate, group in [("JTU 4821", first_set), ("BKM 7788", second_set)]:
        if not group:
            continue
        result = preview_optimization(_lorry_id(plate), group)
        if result.get("success"):
            ok, _, plan_id = save_optimization(result, staff_id)
            if ok:
                generate_report(plan_id, staff_id)


def seed_all():
    initialize_schema()
    seed_collection_points()
    seed_users()
    seed_seafood()
    seed_lorries()
    seed_boxes()
    seed_demo_workflow()
