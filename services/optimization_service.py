from database.db import db_session
from services.lorry_service import get_lorry
from optimization.optimizer import generate_plan
from optimization.validation import validate_plan


def build_box_instances(order_ids):
    if not order_ids:
        return []
    placeholders = ",".join("?" for _ in order_ids)
    sql = f"""
        SELECT r.order_id, r.box_profile_id, r.quantity, r.loaded_weight_per_box,
               b.box_name, b.capacity_litre, b.length, b.width, b.height,
               u.full_name customer_name
        FROM order_box_requirements r
        JOIN box_profiles b ON b.box_profile_id=r.box_profile_id
        JOIN seafood_orders o ON o.order_id=r.order_id
        JOIN users u ON u.user_id=o.customer_id
        WHERE r.order_id IN ({placeholders}) AND b.status='Active'
        ORDER BY r.order_id, b.capacity_litre DESC
    """
    boxes = []
    order_box_counter = {}
    with db_session() as conn:
        rows = conn.execute(sql, [int(x) for x in order_ids]).fetchall()
    for row in rows:
        order_id = int(row["order_id"])
        for _ in range(1, int(row["quantity"]) + 1):
            order_box_counter[order_id] = order_box_counter.get(order_id, 0) + 1
            order_box_number = order_box_counter[order_id]
            boxes.append({
                "order_id": order_id,
                "box_profile_id": row["box_profile_id"],
                # Unique within the order, regardless of box size/template.
                "box_instance": order_box_number,
                "box_label": f"O{order_id}-B{order_box_number:02d}",
                "customer_name": row["customer_name"],
                "box_name": row["box_name"],
                "capacity_litre": row["capacity_litre"],
                "length": row["length"],
                "width": row["width"],
                "height": row["height"],
                "loaded_weight": row["loaded_weight_per_box"],
            })
    return boxes


def get_requirements_for_orders(order_ids):
    if not order_ids:
        return []
    placeholders = ",".join("?" for _ in order_ids)
    sql = f"""
        SELECT r.order_id, u.full_name customer_name,
               b.box_name, b.capacity_litre, b.length, b.width, b.height,
               r.quantity, r.loaded_weight_per_box,
               (r.quantity * r.loaded_weight_per_box) AS total_weight
        FROM order_box_requirements r
        JOIN box_profiles b ON b.box_profile_id=r.box_profile_id
        JOIN seafood_orders o ON o.order_id=r.order_id
        JOIN users u ON u.user_id=o.customer_id
        WHERE r.order_id IN ({placeholders}) AND b.status='Active'
        ORDER BY r.order_id, b.capacity_litre DESC
    """
    with db_session() as conn:
        return [dict(r) for r in conn.execute(sql, [int(x) for x in order_ids]).fetchall()]


def _collection_point_for_orders(order_ids):
    if not order_ids:
        return None, None
    placeholders = ",".join("?" for _ in order_ids)
    with db_session() as conn:
        rows = conn.execute(
            f"SELECT DISTINCT collection_point_id, collection_point FROM seafood_orders WHERE order_id IN ({placeholders})",
            [int(x) for x in order_ids],
        ).fetchall()
    pairs = [(r["collection_point_id"], r["collection_point"]) for r in rows]
    if len(pairs) != 1:
        return None, None
    return pairs[0]


def preview_optimization(lorry_id, order_ids):
    lorry = get_lorry(lorry_id)
    if not lorry:
        return {"success": False, "message": "Selected lorry could not be found."}
    if lorry["status"] != "Available":
        return {"success": False, "message": "Selected lorry is not currently available."}
    collection_point_id, collection_point = _collection_point_for_orders(order_ids)
    if collection_point_id is None:
        return {"success": False, "message": "Select orders assigned to the same collection point."}
    boxes = build_box_instances(order_ids)
    if not boxes:
        return {"success": False, "message": "Selected orders do not have active box requirements."}
    total_weight = sum(float(box["loaded_weight"] or 0) for box in boxes)
    max_weight = float(lorry["max_weight"] or 0)
    if total_weight > max_weight + 1e-9:
        return {
            "success": False,
            "message": (
                f"{lorry['plate_number']} cannot be used: selected orders weigh {total_weight:,.0f} kg, "
                f"but this lorry can carry only {max_weight:,.0f} kg. "
                f"Choose a lorry with at least {total_weight:,.0f} kg capacity."
            ),
        }
    result = generate_plan(lorry, boxes)
    result["lorry"] = lorry
    result["order_ids"] = [int(x) for x in order_ids]
    result["collection_point_id"] = collection_point_id
    result["collection_point"] = collection_point
    return result


def save_optimization(result, created_by, mark_loaded=False):
    if not result or not result.get("success"):
        return False, "Only a valid loading plan can be saved.", None
    m = result["metrics"]
    lorry = result["lorry"]
    planned_weight = sum(float(p.get("loaded_weight") or 0) for p in result.get("placements", []))
    with db_session() as conn:
        # Re-check against the live lorry record immediately before saving.
        # A preview may be stale if staff changed the lorry or its capacity in
        # another session, so the database write must never rely on UI state.
        current_lorry = conn.execute(
            """
            SELECT lorry_id, plate_number, internal_length, internal_width, internal_height,
                   max_weight, status
            FROM lorry_profiles WHERE lorry_id=?
            """,
            (lorry["lorry_id"],),
        ).fetchone()
        if not current_lorry:
            return False, "The selected lorry no longer exists. Choose another available lorry.", None

        live_capacity = float(current_lorry["max_weight"] or 0)
        if planned_weight > live_capacity + 1e-9:
            excess_weight = planned_weight - live_capacity
            return False, (
                f"Loading plan not saved: {current_lorry['plate_number']} can carry up to "
                f"{live_capacity:,.0f} kg, but the selected orders total {planned_weight:,.0f} kg "
                f"({excess_weight:,.0f} kg over capacity). Choose a larger lorry or remove orders."
            ), None

        # Validate the exact 3D coordinates again at the write boundary. This
        # prevents an old preview or stale browser state from saving boxes that
        # are outside the live lorry dimensions, overlap, or are unsupported.
        physical_lorry = dict(current_lorry)
        layout_valid, layout_errors = validate_plan(
            result.get("placements", []), physical_lorry, planned_weight
        )
        if not layout_valid:
            return False, (
                "Loading plan not saved: the boxes no longer form a safe layout in "
                f"{current_lorry['plate_number']}. " + " ".join(layout_errors)
            ), None

        if mark_loaded and current_lorry["status"] != "Available":
            return False, (
                f"Loading plan not saved: {current_lorry['plate_number']} is currently "
                f"{current_lorry['status']}. Choose an available lorry."
            ), None

        if mark_loaded:
            for order_id in result["order_ids"]:
                order = conn.execute(
                    "SELECT status FROM seafood_orders WHERE order_id=?",
                    (order_id,),
                ).fetchone()
                if not order or order["status"] != "Ready for Loading":
                    return False, f"Order #{order_id} must be Ready for Loading before it can be marked Loaded.", None
        cur = conn.execute(
            """
            INSERT INTO loading_plans(
                lorry_id,collection_point_id,created_by,status,total_boxes,total_volume,
                used_volume,remaining_volume,space_utilization,total_weight,
                remaining_weight_capacity,validation_result,packing_origin
            ) VALUES(?,?,?,'Saved',?,?,?,?,?,?,?,'Valid','Deep')
            """,
            (
                lorry["lorry_id"], result.get("collection_point_id"), created_by,
                m["total_boxes"], m["lorry_volume"], m["used_volume"],
                m["remaining_volume"], m["space_utilization"], planned_weight,
                max(live_capacity - planned_weight, 0.0),
            ),
        )
        plan_id = cur.lastrowid
        for order_id in result["order_ids"]:
            conn.execute("INSERT INTO loading_plan_orders(plan_id,order_id) VALUES(?,?)", (plan_id, order_id))
        for p in result["placements"]:
            conn.execute(
                """
                INSERT INTO box_placements(
                    plan_id,order_id,box_profile_id,box_instance,box_label,x,y,z,
                    placed_length,placed_width,placed_height,orientation,
                    sequence_number,loaded_weight
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    plan_id, p["order_id"], p["box_profile_id"], p["box_instance"],
                    p.get("box_label"), p["x"], p["y"], p["z"], p["placed_length"], p["placed_width"],
                    p["placed_height"], p["orientation"], p["sequence_number"],
                    p["loaded_weight"],
                ),
            )
        if mark_loaded:
            for order_id in result["order_ids"]:
                conn.execute(
                    "UPDATE seafood_orders SET status='Loaded',updated_at=CURRENT_TIMESTAMP WHERE order_id=?",
                    (order_id,),
                )
                conn.execute(
                    "INSERT INTO order_status_history(order_id,status,updated_by,note) VALUES(?,?,?,?)",
                    (order_id, "Loaded", created_by, f"Marked Loaded when loading plan #{plan_id} was saved."),
                )
            conn.execute(
                "UPDATE lorry_profiles SET status='In Transit',updated_at=CURRENT_TIMESTAMP WHERE lorry_id=?",
                (lorry["lorry_id"],),
            )
    message = "Loading plan saved and selected orders marked Loaded." if mark_loaded else "Loading plan saved successfully."
    return True, message, plan_id


def list_plans(limit=None):
    sql = """
        SELECT p.*, l.plate_number, u.full_name created_by_name,
               cp.point_name collection_point,
               (SELECT COUNT(*) FROM loading_plan_orders po WHERE po.plan_id=p.plan_id) order_count
        FROM loading_plans p
        JOIN lorry_profiles l ON l.lorry_id=p.lorry_id
        JOIN users u ON u.user_id=p.created_by
        LEFT JOIN collection_points cp ON cp.collection_point_id=p.collection_point_id
        ORDER BY p.created_at DESC
    """
    params = ()
    if limit:
        sql += " LIMIT ?"
        params = (limit,)
    with db_session() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def get_plan(plan_id):
    with db_session() as conn:
        plan = conn.execute(
            """
            SELECT p.*,l.plate_number,l.internal_length,l.internal_width,l.internal_height,
                   l.max_weight,u.full_name created_by_name,cp.point_name collection_point,
                   cp.city collection_point_city, cp.state collection_point_state
            FROM loading_plans p
            JOIN lorry_profiles l ON l.lorry_id=p.lorry_id
            JOIN users u ON u.user_id=p.created_by
            LEFT JOIN collection_points cp ON cp.collection_point_id=p.collection_point_id
            WHERE p.plan_id=?
            """,
            (plan_id,),
        ).fetchone()
        if not plan:
            return None
        placements = conn.execute(
            """
            SELECT bp.*, b.box_name, b.capacity_litre, u.full_name customer_name
            FROM box_placements bp
            JOIN box_profiles b ON b.box_profile_id=bp.box_profile_id
            JOIN seafood_orders o ON o.order_id=bp.order_id
            JOIN users u ON u.user_id=o.customer_id
            WHERE bp.plan_id=?
            -- Floor boxes first, then upper layers; within a layer, deepest
            -- boxes load before boxes nearest the rear gate.
            ORDER BY bp.z ASC, bp.x DESC, bp.y ASC, bp.order_id ASC,
                     bp.box_instance ASC, bp.placement_id ASC
            """,
            (plan_id,),
        ).fetchall()
        orders = conn.execute(
            """
            SELECT o.order_id,u.full_name customer_name,
                   COALESCE(SUM(oi.quantity),0) seafood_weight_kg
            FROM loading_plan_orders po
            JOIN seafood_orders o ON o.order_id=po.order_id
            JOIN users u ON u.user_id=o.customer_id
            LEFT JOIN order_items oi ON oi.order_id=o.order_id
            WHERE po.plan_id=?
            GROUP BY o.order_id,u.full_name
            ORDER BY o.order_id
            """,
            (plan_id,),
        ).fetchall()
    result = dict(plan)
    placement_rows = [dict(r) for r in placements]
    # Plans saved before gate-aware packing grew from the gate side. Display
    # those historical plans mirrored so all visuals fill the deepest end
    # first and preserve access near the rear gate.
    if result.get("packing_origin") != "Deep":
        lorry_length = float(result["internal_length"])
        for placement in placement_rows:
            placement["x"] = lorry_length - float(placement["x"]) - float(placement["placed_length"])
    placement_rows.sort(
        key=lambda p: (float(p["z"]), -float(p["x"]), float(p["y"]), int(p["order_id"]), int(p["box_instance"]))
    )
    # Derive the crew sequence from physical positions, so it never returns
    # to a deeper location after moving toward the rear gate.
    for sequence, placement in enumerate(placement_rows, start=1):
        placement["sequence_number"] = sequence
    # Old databases may not yet contain box_label values. Build stable display
    # labels from the saved loading sequence as a backward-compatible fallback.
    fallback_counter = {}
    seen_labels = set()
    for placement in placement_rows:
        order_id = int(placement["order_id"])
        label = placement.get("box_label")
        if not label or label in seen_labels:
            fallback_counter[order_id] = fallback_counter.get(order_id, 0) + 1
            label = f"O{order_id}-B{fallback_counter[order_id]:02d}"
        seen_labels.add(label)
        placement["box_label"] = label
    result["placements"] = placement_rows
    result["orders"] = [dict(r) for r in orders]
    result["order_ids"] = [r["order_id"] for r in orders]
    return result
