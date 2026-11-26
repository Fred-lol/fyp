"""Resolve current delivery assignments without choosing arbitrary destinations."""
from math import isfinite
from database.db import db_session


def resolve_assignment(rows):
    if not rows:
        return {"stops": [], "valid": False, "message": "No destination assigned to this lorry"}
    stops = {}
    plan_ids = set()
    order_ids = set()
    for row in rows:
        point_id = row.get("collection_point_id")
        if not point_id or row.get("plan_point_id") != point_id:
            return {"stops": [], "valid": False, "message": "Loading plan and order destinations do not match. Correct the assignment before tracking."}
        plan_ids.add(int(row["plan_id"]))
        order_ids.add(int(row["order_id"]))
        stops[point_id] = {key: row.get(key) for key in ("collection_point_id", "point_name", "city", "state", "latitude", "longitude")}
    result = {"stops": list(stops.values()), "plan_ids": sorted(plan_ids), "order_ids": sorted(order_ids)}
    # Existing plans support one destination. Multiple distinct destinations
    # have no persisted route order and must not be silently reordered.
    if len(stops) != 1:
        return dict(result, valid=False, message="Multiple destinations are assigned, but no stop order is saved. Save an ordered route before starting simulation.")
    stop = next(iter(stops.values()))
    try:
        lat, lon = float(stop["latitude"]), float(stop["longitude"])
        valid = bool(stop["point_name"]) and isfinite(lat) and isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180
    except (TypeError, ValueError):
        valid = False
    return dict(result, valid=valid, message="" if valid else "The assigned destination has no valid map coordinates.")


def get_lorry_assignment(lorry_id):
    with db_session() as conn:
        rows = conn.execute("""
            SELECT p.plan_id, p.collection_point_id AS plan_point_id,
                   o.order_id, o.collection_point_id,
                   cp.point_name, cp.city, cp.state, cp.latitude, cp.longitude
            FROM loading_plans p
            JOIN lorry_profiles l ON l.lorry_id=p.lorry_id
            JOIN loading_plan_orders po ON po.plan_id=p.plan_id
            JOIN seafood_orders o ON o.order_id=po.order_id
            LEFT JOIN collection_points cp ON cp.collection_point_id=o.collection_point_id
            WHERE p.lorry_id=? AND l.status='In Transit' AND p.status='Saved'
              AND o.status='Loaded' AND o.archived_at IS NULL
              AND COALESCE(o.collection_assignment,'') <> 'Local Pickup'
              AND NOT EXISTS (
                  SELECT 1 FROM loading_plan_orders newer_po
                  JOIN loading_plans newer ON newer.plan_id=newer_po.plan_id
                  WHERE newer_po.order_id=o.order_id AND newer.status='Saved'
                    AND (newer.created_at, newer.plan_id) > (p.created_at, p.plan_id)
              )
            ORDER BY p.created_at, p.plan_id, o.order_id
        """, (int(lorry_id),)).fetchall()
    return resolve_assignment(rows)
