from math import radians, sin, cos, sqrt, atan2

from database.db import db_session
from database.schema import initialize_schema


DEFAULT_COLLECTION_POINTS = [
    # Official LKIM fisheries complexes/ports, plus a wholesale-market fallback
    # where a state does not have an LKIM seafood complex in this catalogue.
    ("LKIM Fisheries Complex Kuala Perlis", "Lot P.T. 2209, 02000 Kuala Perlis, Perlis", "Kuala Perlis", "Perlis", "02000", 6.3960, 100.1280),
    ("LKIM Fisheries Port Kuala Kedah", "Kg. Kelunchur, Kubang Rotan, 06600 Kuala Kedah, Kedah", "Kuala Kedah", "Kedah", "06600", 6.1010, 100.2980),
    ("LKIM Fisheries Complex Batu Maung", "Jalan Batu Maung, 11960 Bayan Lepas, Pulau Pinang", "Bayan Lepas", "Pulau Pinang", "11960", 5.2910, 100.2760),
    ("LKIM Fisheries Complex Lumut", "Kampung Acheh, 32200 Lumut, Perak", "Lumut", "Perak", "32200", 4.2320, 100.6290),
    ("Fishermen's Jetty Port Klang", "Kg. Sireh Tambahan, Pelabuhan Klang, Selangor", "Pelabuhan Klang", "Selangor", "42000", 3.0060, 101.3880),
    ("Kuala Lumpur Wholesale Market", "Jalan 2/3A, Taman Batu Muda, 68100 Kuala Lumpur", "Kuala Lumpur", "W.P. Kuala Lumpur", "68100", 3.2060, 101.6780),
    ("LKIM Fisheries Complex Teluk Kemang", "Teluk Kemang, 71050 Port Dickson, Negeri Sembilan", "Port Dickson", "Negeri Sembilan", "71050", 2.4800, 101.8500),
    ("LKIM Fisheries Complex Kuala Linggi", "Kuala Linggi, 78200 Kuala Sungai Baru, Melaka", "Kuala Sungai Baru", "Melaka", "78200", 2.3820, 102.0710),
    ("LKIM Fisheries Complex Mersing", "Jalan Dato' Onn, 86000 Mersing, Johor", "Mersing", "Johor", "86000", 2.4370, 103.8400),
    ("LKIM Fisheries Complex Kuantan", "Jalan Tanah Puteh, 25100 Kuantan, Pahang", "Kuantan", "Pahang", "25100", 3.8070, 103.3260),
    ("LKIM Fisheries Port Chendering", "21080 Kuala Terengganu, Terengganu", "Kuala Terengganu", "Terengganu", "21080", 5.2860, 103.1840),
    ("LKIM Fisheries Port Tok Bali", "16700 Pasir Puteh, Kelantan", "Pasir Puteh", "Kelantan", "16700", 5.7540, 102.4960),
    # Additional regional LKIM complexes and Fishermen's Markets keep pickup
    # travel practical instead of forcing a state-wide trip to one hub.
    ("LKIM Fisheries Complex Tanjung Dawai", "08110 Bedong, Kedah", "Bedong", "Kedah", "08110", 5.6960, 100.4050),
    ("LKIM Fisheries Complex Kuala Sala", "06800 Kota Sarang Semut, Kedah", "Kota Sarang Semut", "Kedah", "06800", 5.7890, 100.4100),
    ("LKIM Fisheries Complex Yan", "Sungai Udang, 06900 Yan, Kedah", "Yan", "Kedah", "06900", 5.8010, 100.3630),
    ("LKIM Fisheries Complex Teluk Bahang", "Jalan Hassan Abas, 11050 Teluk Bahang, Pulau Pinang", "Teluk Bahang", "Pulau Pinang", "11050", 5.4660, 100.2100),
    ("Fishermen's Market Sungai Besar", "Kg. Pasir Panjang, Sungai Besar, Selangor", "Sungai Besar", "Selangor", "45300", 3.6820, 100.9870),
    ("Fishermen's Market Kuala Selangor", "Sungai Yu, Kuala Selangor, Selangor", "Kuala Selangor", "Selangor", "45000", 3.3490, 101.2550),
    ("LKIM Fisheries Complex Endau", "Jalan Merlimau, 86900 Endau, Johor", "Endau", "Johor", "86900", 2.6570, 103.6230),
    ("LKIM Fisheries Complex Tanjung Sedili", "81930 Kota Tinggi, Johor", "Kota Tinggi", "Johor", "81930", 1.9280, 104.1160),
    ("LKIM Fisheries Complex Kuala Pahang", "26660 Pekan, Pahang", "Pekan", "Pahang", "26660", 3.5430, 103.4600),
    ("LKIM Fisheries Complex Kuala Rompin", "Jalan Jeti, 26800 Kuala Rompin, Pahang", "Kuala Rompin", "Pahang", "26800", 2.8040, 103.4920),
    ("LKIM Fisheries Complex Nenasi", "26680 Pekan, Pahang", "Pekan", "Pahang", "26680", 3.0850, 103.4350),
    ("LKIM Fish Landing Jetty Kerteh", "Kg. Gelugor, 24300 Kerteh, Terengganu", "Kerteh", "Terengganu", "24300", 4.5140, 103.4480),
    ("LKIM Fisheries Complex Dungun", "Tanjung Kuala Dungun, 23000 Dungun, Terengganu", "Dungun", "Terengganu", "23000", 4.7560, 103.4380),
    ("LKIM Fisheries Complex Kemaman", "24000 Kuala Kemaman, Terengganu", "Chukai", "Terengganu", "24000", 4.2310, 103.4260),
    ("LKIM Fisheries Complex Kuala Besut", "Seberang Kastam, 22200 Besut, Terengganu", "Besut", "Terengganu", "22200", 5.8280, 102.5580),
    ("LKIM Fisheries Complex Marang", "Bandar Marang, 21600 Marang, Terengganu", "Marang", "Terengganu", "21600", 5.2060, 103.2050),
    ("LKIM Fisheries Complex Pulau Kambing", "20300 Kuala Terengganu, Terengganu", "Kuala Terengganu", "Terengganu", "20300", 5.3370, 103.1400),
    ("LKIM Fish Landing Jetty Pengkalan Petah", "Kg. Pengkalan Petah, 16020 Tawang, Kelantan", "Tawang", "Kelantan", "16020", 6.0260, 102.3850),
    ("LKIM Fisheries Complex Geting", "Pengkalan Kubor, 16200 Kelantan", "Pengkalan Kubor", "Kelantan", "16200", 6.2280, 102.0850),
    ("LKIM Fisheries Complex Kuala Besar", "Kedai Buluh, 15350 Kota Bharu, Kelantan", "Kota Bharu", "Kelantan", "15350", 6.1720, 102.2690),
]

# These points are preferred over an older/demo or city-name match. In
# particular, all Perlis towns use the actual LKIM Kuala Perlis complex.
STATE_POINT_PREFERENCE = {"Perlis": "LKIM Fisheries Complex Kuala Perlis"}
STATE_FALLBACK = {"W.P. Putrajaya": "W.P. Kuala Lumpur"}
PRIMARY_COLLECTION_POINT_NAME = "LKIM Fisheries Complex Kuala Perlis"
CITY_POINT_PREFERENCE = {
    ("Kedah", "alor setar"): "LKIM Fisheries Port Kuala Kedah",
    ("Kedah", "sungai petani"): "LKIM Fisheries Complex Tanjung Dawai",
    ("Pulau Pinang", "george town"): "LKIM Fisheries Complex Batu Maung",
    ("Pulau Pinang", "balik pulau"): "LKIM Fisheries Complex Teluk Bahang",
    ("Selangor", "klang"): "Fishermen's Jetty Port Klang",
    ("Selangor", "shah alam"): "Fishermen's Jetty Port Klang",
    ("Selangor", "kuala selangor"): "Fishermen's Market Kuala Selangor",
    ("Selangor", "sabak bernam"): "Fishermen's Market Sungai Besar",
    ("Johor", "kota tinggi"): "LKIM Fisheries Complex Tanjung Sedili",
    ("Johor", "mersing"): "LKIM Fisheries Complex Mersing",
    ("Johor", "endau"): "LKIM Fisheries Complex Endau",
    ("Pahang", "kuantan"): "LKIM Fisheries Complex Kuantan",
    ("Pahang", "pekan"): "LKIM Fisheries Complex Kuala Pahang",
    ("Pahang", "kuala rompin"): "LKIM Fisheries Complex Kuala Rompin",
    ("Terengganu", "kuala terengganu"): "LKIM Fisheries Complex Pulau Kambing",
    ("Terengganu", "dungun"): "LKIM Fisheries Complex Dungun",
    ("Terengganu", "marang"): "LKIM Fisheries Complex Marang",
    ("Terengganu", "kemaman"): "LKIM Fisheries Complex Kemaman",
    ("Kelantan", "kota bharu"): "LKIM Fisheries Complex Kuala Besar",
    ("Kelantan", "pasir puteh"): "LKIM Fisheries Port Tok Bali",
}

# AquaLoad currently dispatches through road lorries only. Islands without a
# road connection are excluded instead of being assigned a mainland depot.
NON_LORRY_DELIVERY_LOCATIONS = {("Kedah", "langkawi")}
NON_LORRY_DELIVERY_STATES = {"Sabah", "Sarawak", "W.P. Labuan"}


def is_local_kuala_perlis_pickup(customer, collection_point):
    """Return whether an order is collected locally instead of sent by lorry.

    Any collection point in Perlis is a self-pickup location. AquaLoad operates
    from LKIM Kuala Perlis, so these orders must never enter the lorry-loading
    or GPS-tracking workflow. The customer value is retained for compatibility
    with existing service calls.
    """
    point_state = (collection_point.get("state") or "").strip()
    return point_state == "Perlis"


def is_lorry_delivery_collection_point(collection_point):
    """Return whether the point belongs in lorry planning and tracking.

    AquaLoad's Perlis points are customer self-pickup locations served from
    the Kuala Perlis base, so they must stay outside every lorry workflow.
    """
    point_state = (collection_point.get("state") or "").strip()
    point_name = (collection_point.get("point_name") or "").strip()
    return point_state != "Perlis" and point_name != PRIMARY_COLLECTION_POINT_NAME


def is_lorry_delivery_supported(customer):
    state = (customer.get("state") or "").strip()
    city = (customer.get("city") or "").strip().lower()
    return state not in NON_LORRY_DELIVERY_STATES and (state, city) not in NON_LORRY_DELIVERY_LOCATIONS


def ensure_default_collection_points():
    """Ensure AquaLoad has real seafood collection points after demo data cleanup."""
    initialize_schema()
    with db_session() as conn:
        for point in DEFAULT_COLLECTION_POINTS:
            conn.execute(
                """
                INSERT INTO collection_points(point_name,address,city,state,postcode,latitude,longitude,status)
                VALUES(?,?,?,?,?,?,?,'Available')
                ON CONFLICT(point_name) DO NOTHING
                """,
                point,
            )
        points = [dict(row) for row in conn.execute(
            "SELECT collection_point_id,point_name,state FROM collection_points WHERE status='Available'"
        ).fetchall()]
        unassigned_orders = conn.execute(
            """
            SELECT o.order_id,u.state,u.city
            FROM seafood_orders o
            JOIN users u ON u.user_id=o.customer_id
            WHERE o.collection_point_id IS NULL
            """
        ).fetchall()
        for order in unassigned_orders:
            customer_state = (order["state"] or "").strip()
            preferred_state = STATE_FALLBACK.get(customer_state, customer_state)
            city = (order["city"] or "").strip().lower()
            preferred_name = (
                STATE_POINT_PREFERENCE.get(preferred_state)
                or CITY_POINT_PREFERENCE.get((preferred_state, city))
            )
            point = next((p for p in points if p["point_name"] == preferred_name), None)
            if point is None:
                point = next((p for p in points if p["state"].lower() == preferred_state.lower()), None)
            if point is None:
                point = next((p for p in points if p["point_name"] == PRIMARY_COLLECTION_POINT_NAME), None)
            if point is None and points:
                point = points[0]
            if point:
                conn.execute(
                    """
                    UPDATE seafood_orders
                    SET collection_point_id=?,collection_point=?,collection_assignment=?,updated_at=CURRENT_TIMESTAMP
                    WHERE order_id=?
                    """,
                    (
                        point["collection_point_id"],
                        point["point_name"],
                        "Local Pickup" if is_local_kuala_perlis_pickup(dict(order), point) else "Automatic",
                        order["order_id"],
                    ),
                )


def list_collection_points(status="Available", state=None):
    ensure_default_collection_points()
    sql = "SELECT * FROM collection_points WHERE 1=1"
    params = []
    if status != "All":
        sql += " AND status=?"
        params.append(status)
    if state:
        sql += " AND state=?"
        params.append(state)
    sql += " ORDER BY CASE WHEN point_name=? THEN 0 ELSE 1 END, state, city, point_name"
    params.append(PRIMARY_COLLECTION_POINT_NAME)
    with db_session() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def list_lorry_delivery_collection_points(status="Available"):
    """List collection points that require road-lorry delivery."""
    return [
        point
        for point in list_collection_points(status)
        if is_lorry_delivery_collection_point(point)
    ]


def get_collection_point(collection_point_id):
    initialize_schema()
    with db_session() as conn:
        row = conn.execute(
            "SELECT * FROM collection_points WHERE collection_point_id=?",
            (collection_point_id,),
        ).fetchone()
    return dict(row) if row else None


def _haversine_km(lat1, lon1, lat2, lon2):
    radius = 6371.0
    p1, p2 = radians(lat1), radians(lat2)
    dp = radians(lat2 - lat1)
    dl = radians(lon2 - lon1)
    a = sin(dp / 2) ** 2 + cos(p1) * cos(p2) * sin(dl / 2) ** 2
    return radius * 2 * atan2(sqrt(a), sqrt(1 - a))


def recommend_collection_point(customer):
    """Choose an available collection point from AquaLoad's configured list.

    Priority:
    1. Same state as Customer.
    2. If coordinates exist, nearest point within the same state.
    3. If no same-state point exists, nearest configured point by coordinates.
    4. Otherwise first available point.
    """
    points = list_collection_points("Available")
    if not points:
        return None

    state = (customer.get("state") or "").strip()
    city = (customer.get("city") or "").strip().lower()
    lat = customer.get("latitude")
    lon = customer.get("longitude")

    preferred_state = STATE_FALLBACK.get(state, state)
    same_state = [p for p in points if preferred_state and p["state"].lower() == preferred_state.lower()]
    candidates = same_state or points

    preferred_name = (
        STATE_POINT_PREFERENCE.get(preferred_state)
        or CITY_POINT_PREFERENCE.get((preferred_state, city))
    )
    if preferred_name:
        preferred = next((p for p in candidates if p["point_name"] == preferred_name), None)
        if preferred:
            return preferred

    # Use an exact local city match for states without a configured preferred
    # seafood wholesale point.
    city_matches = [p for p in candidates if city and p["city"].lower() == city]
    if city_matches:
        return city_matches[0]

    if lat is not None and lon is not None:
        return min(
            candidates,
            key=lambda p: _haversine_km(
                float(lat), float(lon), float(p["latitude"]), float(p["longitude"])
            ),
        )

    primary = next((p for p in points if p["point_name"] == PRIMARY_COLLECTION_POINT_NAME), None)
    return primary or candidates[0]
