from database.db import db_session


def analytics_summary():
    with db_session() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) total_plans,
                   COALESCE(AVG(p.space_utilization),0) avg_utilization,
                   COALESCE(MAX(p.space_utilization),0) max_utilization,
                   COALESCE(SUM(p.total_boxes),0) total_boxes,
                   COALESCE(AVG(p.total_boxes),0) avg_boxes,
                   COALESCE(SUM(p.total_weight),0) total_weight,
                   COALESCE(AVG(CASE WHEN l.max_weight > 0 THEN p.total_weight / l.max_weight * 100 ELSE 0 END),0) avg_weight_utilization,
                   COALESCE(SUM(CASE WHEN p.space_utilization < 40 THEN 1 ELSE 0 END),0) low_utilization_plans
            FROM loading_plans p
            JOIN lorry_profiles l ON l.lorry_id=p.lorry_id
            WHERE p.validation_result='Valid'
            """
        ).fetchone()
        frequent = conn.execute(
            """
            SELECT l.plate_number,COUNT(*) uses
            FROM loading_plans p
            JOIN lorry_profiles l ON l.lorry_id=p.lorry_id
            WHERE p.validation_result='Valid'
            GROUP BY p.lorry_id,l.plate_number
            ORDER BY uses DESC,l.plate_number
            LIMIT 1
            """
        ).fetchone()
    return {
        "total_plans": int(row["total_plans"] or 0),
        "avg_utilization": float(row["avg_utilization"] or 0),
        "max_utilization": float(row["max_utilization"] or 0),
        "total_boxes": int(row["total_boxes"] or 0),
        "avg_boxes": float(row["avg_boxes"] or 0),
        "total_weight": float(row["total_weight"] or 0),
        "avg_weight_utilization": float(row["avg_weight_utilization"] or 0),
        "low_utilization_plans": int(row["low_utilization_plans"] or 0),
        "most_used_lorry": frequent["plate_number"] if frequent else "—",
    }


def utilization_series():
    with db_session() as conn:
        rows = conn.execute(
            """
            SELECT p.plan_id,p.created_at,p.space_utilization,p.total_boxes,p.total_weight,
                   CASE WHEN l.max_weight > 0 THEN p.total_weight / l.max_weight * 100 ELSE 0 END weight_utilization,
                   l.plate_number,cp.point_name collection_point
            FROM loading_plans p
            JOIN lorry_profiles l ON l.lorry_id=p.lorry_id
            LEFT JOIN collection_points cp ON cp.collection_point_id=p.collection_point_id
            WHERE p.validation_result='Valid'
            ORDER BY p.created_at
            """
        ).fetchall()
    return [dict(r) for r in rows]


def plans_by_lorry():
    with db_session() as conn:
        rows = conn.execute(
            """
            SELECT l.plate_number,COUNT(*) plan_count,
                   AVG(p.space_utilization) avg_utilization,
                   AVG(CASE WHEN l.max_weight > 0 THEN p.total_weight / l.max_weight * 100 ELSE 0 END) avg_weight_utilization,
                   SUM(p.total_weight) total_weight
            FROM loading_plans p
            JOIN lorry_profiles l ON l.lorry_id=p.lorry_id
            WHERE p.validation_result='Valid'
            GROUP BY p.lorry_id,l.plate_number
            ORDER BY plan_count DESC
            """
        ).fetchall()
    return [dict(r) for r in rows]


def box_usage():
    with db_session() as conn:
        rows = conn.execute(
            """
            SELECT b.box_name,COUNT(*) quantity
            FROM box_placements bp
            JOIN box_profiles b ON b.box_profile_id=bp.box_profile_id
            JOIN loading_plans p ON p.plan_id=bp.plan_id
            WHERE p.validation_result='Valid'
            GROUP BY bp.box_profile_id,b.box_name,b.capacity_litre
            ORDER BY b.capacity_litre
            """
        ).fetchall()
    return [dict(r) for r in rows]


def plans_by_collection_point():
    with db_session() as conn:
        rows = conn.execute(
            """
            SELECT COALESCE(cp.point_name,'Not assigned') collection_point,
                   COUNT(*) plan_count,AVG(p.space_utilization) avg_utilization,
                   SUM(p.total_weight) total_weight
            FROM loading_plans p
            LEFT JOIN collection_points cp ON cp.collection_point_id=p.collection_point_id
            WHERE p.validation_result='Valid'
            GROUP BY p.collection_point_id,cp.point_name
            ORDER BY plan_count DESC
            """
        ).fetchall()
    return [dict(r) for r in rows]
